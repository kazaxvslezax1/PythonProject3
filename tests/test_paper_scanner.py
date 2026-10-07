import asyncio
import json
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest
import requests
from ai_facts import FactClaim, fact_catalog, relation
from deepseek_analyzer import AIResponse
from fastapi.testclient import TestClient
from paper_execution_bridge import PaperExecutionBridge, bridge_from_env
from paper_journal import PaperJournal
from paper_research import ResearchStore, evaluate_outcome
from paper_scanner import ResearchScanner, ScannerConfig, baseline_config, next_due
from signal_models import Direction, TradePlan
from test_paper_journal import analysis, verified
from test_positions import Bot, paper_rules
from test_telegram_ai import Bot as CommandBot


class FakeAIStore:
    def __init__(self):
        self.saved = None

    def get(self, key):
        return self.saved

    def usage(self, key):
        return {"prompt_tokens": 100, "completion_tokens": 50} if self.saved else None

    def spent(self, day):
        return 0.0


class FakeAnalyzer:
    model = "deepseek-flash"
    daily_budget = 1.0

    def __init__(self, reason=None):
        self.calls = 0
        self.reason = reason
        self.store = FakeAIStore()

    def identity(self, snapshot):
        return snapshot.technical.timestamp.isoformat()

    async def analyze(self, snapshot, **kwargs):
        self.calls += 1
        if self.reason:
            return AIResponse(
                status="AI_UNAVAILABLE",
                model=self.model,
                reason=self.reason,
                fact_check_status="FAILED" if self.reason == "AI_FACT_CHECK_FAILED" else "NOT_CHECKED",
            )
        result = full_response(snapshot)
        result.request_hash = self.identity(snapshot)
        self.store.saved = result
        return result


def full_response(snapshot):
    response = verified(snapshot, snapshot.technical.direction.value).ai
    response.result.facts = [
        FactClaim(fact_id=key, relation=relation(value)) for key, value in fact_catalog(snapshot).items()
    ]
    return response


def scanner_for(
    candles,
    tmp_path,
    monkeypatch,
    *,
    timeframe="1h",
    now=None,
    start=None,
    ai=None,
    prefilter_pass=True,
    ai_on_hold=True,
    **settings,
):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    if prefilter_pass:
        # These legacy tests exercise the AI/recovery path, independent of eligibility.
        monkeypatch.setattr(
            "paper_scanner.evaluate_entry_prefilter",
            lambda quality, volume: SimpleNamespace(passed=True),
        )
    step = timedelta(hours=4 if timeframe == "4h" else 1)
    now = now or candles.close_time.iloc[-1].to_pydatetime() + timedelta(milliseconds=1, seconds=15)
    start = start or now - step
    config = ScannerConfig(
        enabled=True,
        symbols=("BTCUSDT",),
        timeframes=(timeframe,),
        ai_on_hold=ai_on_hold,
        **settings,
    )

    def loader(symbol, tf, *, limit, as_of):
        assert symbol == "BTCUSDT" and tf == timeframe
        return candles.loc[candles.close_time < as_of].tail(limit).reset_index(drop=True)

    journal = PaperJournal(tmp_path / "research.sqlite3")
    result = ResearchScanner(
        journal=journal,
        config=config,
        loader=loader,
        analyzer=ai or FakeAnalyzer(),
        clock=lambda: now,
    )
    result.store.register_experiment(config.experiment_id, baseline_config(config), start)
    return result


@pytest.mark.parametrize("timeframe", ["1h", "4h"])
def test_new_closed_candle_ai_idempotence_and_status(candles, tmp_path, monkeypatch, timeframe):
    end = "2026-09-28T08:00:00Z" if timeframe == "4h" else "2026-09-28T10:00:00Z"
    frame = candles(n=130, slope=0.1, end=end, timeframe=timeframe)
    ai = FakeAnalyzer()
    scanner = scanner_for(frame, tmp_path, monkeypatch, timeframe=timeframe, ai=ai)
    asyncio.run(scanner.scan_once())
    report = scanner.journal.report()
    assert report["signals"] == 1
    assert report["research_origins"]["LIVE"] == 1
    assert report["ai_ok"] == report["paired_ai_observations"] == 1
    assert report["paper_positions"] == 0
    assert ai.calls == 1
    assert scanner.status()["observations_today"] in (0, 1)  # Fixture dates are historical.
    assert scanner.status()["last_success_at"] is not None
    asyncio.run(scanner.scan_once())
    assert scanner.journal.report()["signals"] == 1
    assert ai.calls == 1
    with sqlite3.connect(scanner.journal.path) as db:
        assert db.execute("SELECT COUNT(*) FROM research_ai_requests").fetchone()[0] == 1
        assert db.execute("SELECT attempts FROM research_ai_requests").fetchone()[0] == 1


@pytest.mark.parametrize(
    ("slope", "drop", "expected"),
    [(-0.1, 1, "LONG"), (0.1, 0, "SHORT"), (-0.1, 0, "HOLD")],
)
def test_scanner_preserves_actual_strategy_direction(candles, tmp_path, monkeypatch, slope, drop, expected):
    frame = candles(n=130, slope=slope, end="2026-09-28T10:00:00Z")
    if drop:
        index = len(frame) - 1
        frame.loc[index, "open"] = frame.close.iloc[-2]
        frame.loc[index, "close"] -= drop
        frame.loc[index, "low"] = min(frame.low.iloc[-1], frame.close.iloc[-1] - 0.5)
        frame.loc[index, "high"] = max(frame.high.iloc[-1], frame.open.iloc[-1] + 0.5)
    scanner = scanner_for(frame, tmp_path, monkeypatch)
    asyncio.run(scanner.scan_once())
    assert scanner.journal.report()["signal_directions"][expected] == 1


def test_unfinished_candle_ignored(candles, tmp_path, monkeypatch):
    frame = candles(n=130, end="2026-09-28T10:00:00Z")
    open_bar = frame.iloc[-1].copy()
    open_bar["time"] += timedelta(hours=1)
    open_bar["close_time"] += timedelta(hours=1)
    frame.loc[len(frame)] = open_bar
    now = frame.close_time.iloc[-2].to_pydatetime() + timedelta(seconds=15)
    scanner = scanner_for(frame, tmp_path, monkeypatch, now=now)
    asyncio.run(scanner.scan_once())
    assert scanner.journal.report()["signals"] == 1
    with sqlite3.connect(scanner.journal.path) as db:
        close = db.execute("SELECT candle_close FROM observations").fetchone()[0]
    assert close == frame.close_time.iloc[-2].to_pydatetime().isoformat()


@pytest.mark.parametrize("legacy_market", [False, True])
def test_manual_review_after_scanner_reuses_candle_and_ai(candles, tmp_path, monkeypatch, legacy_market):
    from analysis_service import analyze_market

    frame = candles(n=130, end="2026-09-28T10:00:00Z")
    ai = FakeAnalyzer()
    scanner = scanner_for(frame, tmp_path, monkeypatch, ai=ai)
    asyncio.run(scanner.scan_once())
    if legacy_market:
        with sqlite3.connect(scanner.journal.path) as db:
            row = db.execute("SELECT id, market_json FROM observations").fetchone()
            market = json.loads(row[1])
            market.pop("support")
            market.pop("resistance")
            db.execute("UPDATE observations SET market_json=? WHERE id=?", (json.dumps(market), row[0]))
    close = frame.close_time.iloc[-1].to_pydatetime() + timedelta(milliseconds=1)
    manual = analyze_market("BTCUSDT", "1h", close, loader=lambda *_, **__: frame.tail(120))
    signal_id = scanner.journal.record_signal(manual, origin="TELEGRAM_REVIEW")
    assert scanner.journal.report()["signals"] == 1
    assert scanner.journal.report()["ai_observations"] == 1
    assert scanner.store.ai_request(signal_id)["attempts"] == 1
    assert ai.calls == 1


def test_binance_late_candle_retried_without_assuming_close(candles, tmp_path, monkeypatch):
    frame = candles(n=130, end="2026-09-28T10:00:00Z")
    latest = frame.close_time.iloc[-1].to_pydatetime()
    now = latest + timedelta(seconds=15, milliseconds=1)
    current = [frame.iloc[:-1]]

    def loader(symbol, timeframe, *, limit, as_of):
        return current[0].tail(limit).reset_index(drop=True)

    scanner = scanner_for(frame, tmp_path, monkeypatch, now=now)
    scanner.loader = loader
    asyncio.run(scanner.scan_once())
    assert not scanner.healthy and scanner.journal.report()["signals"] == 0
    current[0] = frame
    asyncio.run(scanner.scan_once())
    assert scanner.healthy and scanner.journal.report()["signals"] == 1


@pytest.mark.parametrize(
    "reason",
    [
        "API_TIMEOUT_OR_TRANSPORT",
        "AI_FACT_CHECK_FAILED",
        "AI_REFERENCE_VALIDATION_FAILED",
        "BUDGET_EXHAUSTED",
    ],
)
def test_ai_failure_does_not_stop_technical_collection(candles, tmp_path, monkeypatch, reason):
    frame = candles(n=130, end="2026-09-28T10:00:00Z")
    ai = FakeAnalyzer(reason)
    scanner = scanner_for(frame, tmp_path, monkeypatch, ai=ai)
    asyncio.run(scanner.scan_once())
    report = scanner.journal.report()
    assert report["signals"] == report["ai_unavailable"] == 1
    assert report["paired_ai_observations"] == 0
    assert report["paper_positions"] == 0
    with sqlite3.connect(scanner.journal.path) as db:
        state = db.execute(
            "SELECT state, attempts, reason, budget_decision FROM research_ai_requests"
        ).fetchone()
    assert state == ("DONE", 1, reason, "EXCEEDED" if reason == "BUDGET_EXHAUSTED" else "RESERVED_OR_CACHED")


def test_configured_retry_is_bounded_and_first_ai_result_is_frozen(candles, tmp_path, monkeypatch):
    frame = candles(n=130, end="2026-09-28T10:00:00Z")
    ai = FakeAnalyzer("API_TIMEOUT_OR_TRANSPORT")
    scanner = scanner_for(frame, tmp_path, monkeypatch, ai=ai, ai_max_requests=2)
    asyncio.run(scanner.scan_once())
    assert ai.calls == 2
    assert scanner.journal.report()["signals"] == 1
    assert scanner.journal.report()["ai_unavailable"] == 1
    with sqlite3.connect(scanner.journal.path) as db:
        assert db.execute("SELECT attempts FROM research_ai_requests").fetchone()[0] == 2
        assert db.execute("SELECT COUNT(*) FROM journal_events WHERE kind='AI_RETRY'").fetchone()[0] == 1


def test_missed_candles_backfill_without_historical_ai(candles, tmp_path, monkeypatch):
    frame = candles(n=130, end="2026-09-28T10:00:00Z")
    now = frame.close_time.iloc[-1].to_pydatetime() + timedelta(seconds=15)
    ai = FakeAnalyzer()
    scanner = scanner_for(
        frame,
        tmp_path,
        monkeypatch,
        now=now,
        start=now - timedelta(hours=3),
        ai=ai,
    )
    asyncio.run(scanner.scan_once())
    report = scanner.journal.report()
    assert report["signals"] == 3
    assert report["research_origins"]["BACKFILL_TECHNICAL"] == 2
    assert report["research_origins"]["LIVE"] == 1
    assert ai.calls == 1
    with sqlite3.connect(scanner.journal.path) as db:
        assert (
            db.execute(
                "SELECT COUNT(*) FROM research_ai_requests WHERE reason='BACKFILL_NO_HISTORICAL_AI'"
            ).fetchone()[0]
            == 2
        )


def test_crash_after_technical_persist_recovers_without_double_ai(candles, tmp_path, monkeypatch):
    frame = candles(n=130, end="2026-09-28T10:00:00Z")
    ai = FakeAnalyzer()
    scanner = scanner_for(frame, tmp_path, monkeypatch, ai=ai)
    scanner.initialize()
    closed = frame.iloc[-120:].reset_index(drop=True)
    from analysis_service import analyze_market
    from paper_research import quality_bucket, regime_labels

    cutoff = closed.close_time.iloc[-1].to_pydatetime() + timedelta(milliseconds=1)
    data = analyze_market("BTCUSDT", "1h", cutoff, loader=lambda *_, **__: closed)
    signal_id = scanner.journal.record_signal(
        data,
        research={
            "experiment_id": scanner.config.experiment_id,
            "origin": "LIVE",
            "data_source": "BINANCE_SPOT_KLINES",
            "regime": regime_labels(data),
            "quality_bucket": quality_bucket(data["technical_signal"].quality),
        },
    )
    scanner.store.claim_ai(signal_id, ai.model, "market-review-v3")
    restarted = scanner_for(frame, tmp_path, monkeypatch, ai=ai)
    asyncio.run(restarted.scan_once())
    assert ai.calls == 0  # Unknown in-flight outcome never starts another paid call.
    assert restarted.journal.report()["signals"] == 1
    assert restarted.journal.report()["ai_unavailable"] == 1
    assert restarted.store.ai_request(signal_id)["reason"] == "UNKNOWN_AFTER_CRASH"
    with sqlite3.connect(restarted.journal.path) as db:
        assert (
            db.execute("SELECT COUNT(*) FROM research_execution WHERE signal_id=?", (signal_id,)).fetchone()[
                0
            ]
            == 1
        )


def test_recovery_uses_saved_ai_response_without_paid_call(candles, tmp_path, monkeypatch):
    frame = candles(n=130, end="2026-09-28T10:00:00Z")
    scanner = scanner_for(frame, tmp_path, monkeypatch)
    scanner.initialize()
    from analysis_service import analyze_market
    from market_snapshot import build_snapshot
    from paper_research import quality_bucket, regime_labels

    closed = frame.iloc[-120:].reset_index(drop=True)
    cutoff = closed.close_time.iloc[-1].to_pydatetime() + timedelta(milliseconds=1)
    data = analyze_market("BTCUSDT", "1h", cutoff, loader=lambda *_, **__: closed)
    signal_id = scanner.journal.record_signal(
        data,
        research={
            "experiment_id": scanner.config.experiment_id,
            "origin": "LIVE",
            "data_source": "BINANCE_SPOT_KLINES",
            "regime": regime_labels(data),
            "quality_bucket": quality_bucket(data["technical_signal"].quality),
        },
    )
    ai = FakeAnalyzer()
    snapshot = build_snapshot(closed, "BTCUSDT", "1h", cutoff)
    saved = full_response(snapshot)
    saved.request_hash = ai.identity(snapshot)
    ai.store.saved = saved
    scanner.store.claim_ai(signal_id, ai.model, "market-review-v3")
    restarted = scanner_for(frame, tmp_path, monkeypatch, ai=ai)
    asyncio.run(restarted.scan_once())
    assert ai.calls == 0
    assert restarted.journal.report()["ai_ok"] == 1
    assert restarted.store.ai_request(signal_id)["state"] == "DONE"
    with sqlite3.connect(restarted.journal.path) as db:
        assert (
            db.execute("SELECT COUNT(*) FROM research_execution WHERE signal_id=?", (signal_id,)).fetchone()[
                0
            ]
            == 1
        )


def test_scanner_status_reads_shared_ai_budget_before_first_review(candles, tmp_path, monkeypatch):
    frame = candles(n=130, end="2026-09-28T10:00:00Z")
    scanner = scanner_for(frame, tmp_path, monkeypatch)
    scanner.analyzer = None
    monkeypatch.setenv("DEEPSEEK_DAILY_BUDGET_USD", "1.0")
    import paper_scanner

    class SharedBudget:
        def __init__(self, path):
            assert path.name == "ai.sqlite3"

        def spent(self, day):
            assert len(day) == 10
            return 0.4

    monkeypatch.setattr(paper_scanner, "AnalysisStore", SharedBudget)
    assert scanner.status()["budget_used_usd"] == 0.4
    assert scanner.status()["budget_remaining_usd"] == pytest.approx(0.6)


def test_experiment_freeze_and_new_version(tmp_path):
    store = ResearchStore(PaperJournal(tmp_path / "paper.sqlite3"))
    config = {"strategy_version": "technical-v1", "costs": {"fee": 0.001}}
    first = store.register_experiment("baseline-a", config)
    assert store.register_experiment("baseline-a", config) == first
    with pytest.raises(ValueError, match="Experiment configuration changed"):
        store.register_experiment("baseline-a", {"strategy_version": "technical-v2"})
    assert store.register_experiment("baseline-b", {"strategy_version": "technical-v2"})


@pytest.mark.parametrize("auto_entries", [False, True])
def test_existing_experiment_starts_after_paper_entry_mode_change(
    candles, tmp_path, monkeypatch, auto_entries
):
    frame = candles(n=130, slope=0.1, end="2026-09-28T10:00:00Z")
    scanner = scanner_for(
        frame,
        tmp_path,
        monkeypatch,
        experiment_id="prospective-baseline-v1",
        auto_paper_entries=False,
    )
    asyncio.run(scanner.scan_once())
    before = scanner.journal.report()
    assert before["signals"] == before["research_origins"]["LIVE"] == 1
    # Emulate an on-disk experiment created by the previous release.
    with sqlite3.connect(scanner.journal.path) as db:
        row = db.execute(
            "SELECT config_json FROM research_experiments WHERE id='prospective-baseline-v1'"
        ).fetchone()
        frozen = json.loads(row[0])
        frozen["auto_paper_entries"] = False
        db.execute(
            "UPDATE research_experiments SET config_json=? WHERE id='prospective-baseline-v1'",
            (json.dumps(frozen),),
        )
        db.execute("DELETE FROM journal_events WHERE kind='RESEARCH_OPERATION_MODE'")
    restarted = ResearchScanner(
        journal=scanner.journal,
        config=replace(scanner.config, auto_paper_entries=auto_entries),
        loader=scanner.loader,
        analyzer=FakeAnalyzer(),
        clock=scanner.clock,
    )

    async def check_running():
        task = asyncio.create_task(restarted.run())
        for _ in range(100):
            if restarted._next_run is not None:
                break
            await asyncio.sleep(0.01)
        assert restarted.running and restarted.healthy
        assert restarted.status()["auto_paper_entries"] is auto_entries
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(check_running())
    assert restarted.last_error is None
    assert scanner.journal.report()["signals"] == before["signals"]
    assert scanner.journal.report()["paper_positions"] == 0
    assert restarted.store.current_operation_mode("prospective-baseline-v1") is auto_entries
    assert restarted.store.experiment_config("prospective-baseline-v1")["auto_paper_entries"] is False


def test_immutable_experiment_mismatch_still_stops_with_safe_reason(candles, tmp_path, monkeypatch, caplog):
    frame = candles(n=130, end="2026-09-28T10:00:00Z")
    scanner = scanner_for(frame, tmp_path, monkeypatch)
    with sqlite3.connect(scanner.journal.path) as db:
        db.execute(
            "UPDATE research_experiments SET config_json=? WHERE id=?",
            (json.dumps({"strategy_version": "different"}), scanner.config.experiment_id),
        )
    monkeypatch.setenv("DEEPSEEK_API_KEY", "never-log-this-test-value")
    asyncio.run(scanner.run())
    assert not scanner.running and not scanner.healthy
    assert scanner.status()["error"] == "EXPERIMENT_CONFIG_MISMATCH"
    assert "reason=EXPERIMENT_CONFIG_MISMATCH" in caplog.text
    assert "never-log-this-test-value" not in caplog.text


def test_api_status_exposes_safe_background_startup_reason(monkeypatch):
    import paper_scanner
    from app import app

    store = ResearchStore(PaperJournal())
    store.register_experiment("paper-baseline-v1", {"strategy_version": "different"})
    monkeypatch.setenv("PAPER_SCANNER_ENABLED", "true")

    class EmptyBudget:
        def __init__(self, path):
            pass

        def spent(self, day):
            return 0.0

    monkeypatch.setattr(paper_scanner, "AnalysisStore", EmptyBudget)
    with TestClient(app) as client:
        for _ in range(100):
            status = client.get("/paper/scanner/status").json()
            if status.get("error") == "EXPERIMENT_CONFIG_MISMATCH":
                break
            time.sleep(0.01)
        assert status["enabled"] is True
        assert status["running"] is False
        assert status["healthy"] is False
        assert status["error"] == "EXPERIMENT_CONFIG_MISMATCH"


def test_fastapi_lifespan_runs_existing_experiment_with_paper_mode_true(candles, monkeypatch):
    import paper_scanner
    from app import app

    frame = candles(n=130, slope=0.1, end="2026-09-28T10:00:00Z")
    now = frame.close_time.iloc[-1].to_pydatetime() + timedelta(seconds=15)
    config = ScannerConfig(
        enabled=True,
        auto_paper_entries=True,
        experiment_id="prospective-baseline-v1",
        symbols=("BTCUSDT",),
        timeframes=("1h",),
    )
    monkeypatch.setenv("AI_MODE", "ADVISORY")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    legacy = baseline_config(replace(config, auto_paper_entries=False))
    legacy["auto_paper_entries"] = False
    journal = PaperJournal()
    ResearchStore(journal).register_experiment(config.experiment_id, legacy, now - timedelta(hours=1))
    monkeypatch.setattr(paper_scanner.ScannerConfig, "from_env", classmethod(lambda cls: config))
    monkeypatch.setattr(paper_scanner, "utc_now", lambda: now)
    monkeypatch.setattr(
        paper_scanner,
        "get_candles",
        lambda symbol, timeframe, *, limit, as_of: frame.tail(limit).reset_index(drop=True),
    )

    class EmptyBudget:
        def __init__(self, path):
            pass

        def spent(self, day):
            return 0.0

    monkeypatch.setattr(paper_scanner, "AnalysisStore", EmptyBudget)
    with TestClient(app) as client:
        for _ in range(100):
            status = client.get("/paper/scanner/status").json()
            if status.get("last_success_at"):
                break
            time.sleep(0.01)
        assert status["enabled"] is True
        assert status["running"] is True
        assert status["healthy"] is True
        assert status["auto_paper_entries"] is True
        assert status["experiment_id"] == "prospective-baseline-v1"
    assert PaperJournal().report()["signals"] == 1
    assert (
        ResearchStore(PaperJournal()).experiment_config(config.experiment_id)["auto_paper_entries"] is False
    )


def test_enabled_paper_bridge_only_handles_new_live_candle(candles, tmp_path, monkeypatch):
    from position_manager import AutoTradeManager

    first = candles(n=130, slope=0.1, end="2026-09-28T10:00:00Z")
    scanner = scanner_for(first, tmp_path, monkeypatch, auto_paper_entries=False)
    asyncio.run(scanner.scan_once())
    assert scanner.journal.report()["signals"] == 1
    second = candles(n=131, slope=0.1, end="2026-09-28T11:00:00Z")
    now = second.close_time.iloc[-1].to_pydatetime() + timedelta(seconds=15)
    resumed = ResearchScanner(
        journal=scanner.journal,
        config=replace(scanner.config, auto_paper_entries=True),
        loader=lambda symbol, timeframe, *, limit, as_of: second.tail(limit).reset_index(drop=True),
        analyzer=FakeAnalyzer(),
        clock=lambda: now,
    )
    asyncio.run(resumed.scan_once())
    assert resumed.healthy and resumed.journal.report()["signals"] == 2
    with sqlite3.connect(resumed.journal.path) as db:
        reasons = [row[0] for row in db.execute("SELECT reason FROM research_execution ORDER BY recorded_at")]
    assert sorted(reasons) == ["PAPER_BRIDGE_PENDING", "RESEARCH_ONLY_NO_AUTOMATED_ENTRY"]
    monkeypatch.setenv("PAPER_SCANNER_AUTO_PAPER_ENTRIES", "true")
    monkeypatch.setenv("PAPER_SCANNER_CHAT_ID", "1")
    manager = AutoTradeManager(Bot(), rules_loader=lambda _: paper_rules(), journal=resumed.journal)
    manager.should_open_trade = lambda *args: (False, "Quality or volume filter rejected")

    def forbidden(*args, **kwargs):
        raise AssertionError("No order or entry path may run for a rejected signal")

    manager.create_auto_trade = forbidden
    bridge = bridge_from_env(manager, {1})
    bridge.clock = lambda: now
    assert bridge.process_once() == 1
    assert bridge.process_once() == 0
    with sqlite3.connect(resumed.journal.path) as db:
        assert db.execute("SELECT COUNT(*) FROM entry_attempts").fetchone()[0] == 1
        assert (
            db.execute("SELECT reason FROM entry_attempts").fetchone()[0]
            == "Quality or volume filter rejected"
        )
    assert resumed.journal.report()["signals"] == 2
    assert resumed.journal.report()["paper_positions"] == 0


def test_crash_recovery_does_not_retroactively_enable_old_paper_entry(snapshot, tmp_path):
    journal = PaperJournal(tmp_path / "paper.sqlite3")
    config = ScannerConfig(enabled=True, auto_paper_entries=False)
    scanner = ResearchScanner(journal=journal, config=config, analyzer=FakeAnalyzer())
    scanner.initialize()
    signal_id = journal.record_signal(
        analysis(snapshot),
        research={
            "experiment_id": config.experiment_id,
            "origin": "LIVE",
            "data_source": "BINANCE_SPOT_KLINES",
            "regime": {"version": "regime-v1"},
            "quality_bucket": "4-<7",
        },
    )
    observed_at = scanner.store.observation(signal_id)["first_seen"]
    resumed = ResearchScanner(
        journal=journal,
        config=replace(config, auto_paper_entries=True),
        analyzer=FakeAnalyzer(),
    )
    resumed.initialize()
    assert resumed.store.current_operation_mode(config.experiment_id) is True
    assert resumed.store.operation_mode_at(config.experiment_id, observed_at) is False
    resumed._recover_execution_metadata()
    with sqlite3.connect(journal.path) as db:
        assert db.execute("SELECT reason FROM research_execution").fetchone()[0] == (
            "RESEARCH_ONLY_NO_AUTOMATED_ENTRY"
        )


def test_enabled_paper_mode_never_opens_hold(candles, tmp_path, monkeypatch):
    from position_manager import AutoTradeManager

    frame = candles(n=130, slope=-0.1, end="2026-09-28T10:00:00Z")
    scanner = scanner_for(frame, tmp_path, monkeypatch, auto_paper_entries=True)
    asyncio.run(scanner.scan_once())
    assert scanner.journal.report()["signal_directions"]["HOLD"] == 1
    manager = AutoTradeManager(Bot(), rules_loader=lambda _: paper_rules(), journal=scanner.journal)
    bridge = PaperExecutionBridge(manager, 1)
    assert bridge.process_once() == 0
    with sqlite3.connect(scanner.journal.path) as db:
        assert db.execute("SELECT status FROM research_execution").fetchone()[0] == "NOT_ELIGIBLE"
        assert db.execute("SELECT COUNT(*) FROM entry_attempts").fetchone()[0] == 0


def test_paper_bridge_isolates_one_observation_failure(snapshot, tmp_path):
    from position_manager import AutoTradeManager

    journal = PaperJournal(tmp_path / "paper.sqlite3")
    store = ResearchStore(journal)
    store.register_experiment("paper-baseline-v1", {"strategy_version": "technical-v1"})
    store.record_operation_mode("paper-baseline-v1", True)
    ids = []
    for symbol in ("BTCUSDT", "ETHUSDT"):
        data = analysis(snapshot)
        data["technical_signal"] = snapshot.technical.model_copy(update={"symbol": symbol})
        signal_id = journal.record_signal(
            data,
            research={
                "experiment_id": "paper-baseline-v1",
                "origin": "LIVE",
                "data_source": "BINANCE_SPOT_KLINES",
                "regime": {"version": "regime-v1"},
                "quality_bucket": "7-10",
            },
        )
        store.record_execution(signal_id, "NOT_ATTEMPTED", "PAPER_BRIDGE_PENDING")
        ids.append(signal_id)
    manager = AutoTradeManager(Bot(), rules_loader=lambda _: paper_rules(), journal=journal)
    calls = 0

    def risk_check(*args):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("test-only paper risk failure")
        return False, "Quality or volume filter rejected"

    manager.should_open_trade = risk_check
    bridge = PaperExecutionBridge(
        manager, 1, clock=lambda: snapshot.technical.timestamp + timedelta(seconds=20)
    )
    assert bridge.process_once() == 2
    assert calls == 2
    with sqlite3.connect(journal.path) as db:
        states = {row[0]: row[1] for row in db.execute("SELECT signal_id, status FROM research_execution")}
    assert states[ids[0]] == "CLAIMED"
    assert states[ids[1]] == "REJECTED"
    assert store.errors()[0]["stage"] == "PAPER_EXECUTION"


def test_strategy_version_and_experiment_cannot_mix_same_candle(snapshot, tmp_path):
    journal = PaperJournal(tmp_path / "paper.sqlite3")
    data = analysis(snapshot)
    first = journal.record_signal(data)
    changed = analysis(snapshot)
    changed["technical_signal"] = snapshot.technical.model_copy(update={"strategy_version": "technical-v2"})
    second = journal.record_signal(changed)
    assert first != second and journal.report()["signals"] == 2
    metadata = {
        "experiment_id": "baseline-a",
        "origin": "LIVE",
        "data_source": "BINANCE_SPOT_KLINES",
        "regime": {"version": "regime-v1"},
        "quality_bucket": "4-<7",
    }
    journal.record_signal(data, research=metadata)
    with pytest.raises(ValueError, match="another research experiment"):
        journal.record_signal(data, research={**metadata, "experiment_id": "baseline-b"})


def test_v1_journal_migrates_without_losing_observations(snapshot, tmp_path):
    journal = PaperJournal(tmp_path / "paper.sqlite3")
    journal.record_signal(analysis(snapshot))
    with sqlite3.connect(journal.path) as db:
        for name in (
            "research_experiments",
            "research_observations",
            "research_ai_requests",
            "research_execution",
            "research_outcomes",
            "scanner_state",
            "scanner_errors",
        ):
            db.execute(f"DROP TABLE {name}")
        db.execute("PRAGMA user_version=1")
    reopened = PaperJournal(journal.path)
    assert reopened.report()["signals"] == 1
    with sqlite3.connect(journal.path) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 4
        assert db.execute("SELECT COUNT(*) FROM observations").fetchone()[0] == 1


def test_failed_worker_cycle_reports_unhealthy_and_safe_error(candles, tmp_path, monkeypatch):
    frame = candles(n=130, end="2026-09-28T10:00:00Z")
    scanner = scanner_for(frame, tmp_path, monkeypatch)

    def offline(*args, **kwargs):
        raise ConnectionError("synthetic sensitive text must not be stored")

    scanner.loader = offline
    asyncio.run(scanner.scan_once())
    state = scanner.status()
    assert not state["healthy"] and state["next_scan_at"] is not None
    errors = scanner.store.errors()
    assert errors[0]["error_type"] == "ConnectionError"
    assert "sensitive text" not in scanner.journal.export("json")


def test_api_and_telegram_scanner_status_are_read_only(monkeypatch):
    import app as api
    from telegram_ai import register_ai_handlers

    monkeypatch.setenv("PAPER_SCANNER_ENABLED", "false")
    with TestClient(api.app) as client:
        status = client.get("/paper/scanner/status")
        assert status.status_code == 200
        assert not status.json()["enabled"] and not status.json()["running"]
        assert client.get("/paper/scanner/errors").json() == {"errors": []}

        class LocalAPI:
            def get(self, url, *, timeout):
                assert timeout == (3, 5)
                return client.get(url.removeprefix("http://127.0.0.1:8000"))

        bot = CommandBot()
        register_ai_handlers(bot, api_client=LocalAPI())
        bot.handlers["paper_scanner_status"](SimpleNamespace(text="/paper_scanner_status"))
        bot.handlers["paper_errors"](SimpleNamespace(text="/paper_errors"))
        assert "enabled=False" in bot.messages[0]
        assert "Ошибок PAPER scanner нет" in bot.messages[1]


def test_ambiguous_intrabar_outcome_is_not_ordered(snapshot):
    signal = snapshot.technical.model_copy(
        update={
            "direction": Direction.LONG,
            "plan": TradePlan(
                direction=Direction.LONG,
                entry=100,
                stop_loss=98,
                take_profits=[102, 104, 106],
            ),
        }
    )
    bar = SimpleNamespace(high=103, low=97)
    outcome = evaluate_outcome(signal, [bar], horizon=1)
    assert outcome["status"] == "AMBIGUOUS_INTRABAR"
    assert outcome["bars_to_outcome"] == 1
    assert not outcome["reached_sl"] and not outcome["reached_tp1"]


def test_concurrent_reader_writer_single_observation(snapshot, tmp_path):
    journal = PaperJournal(tmp_path / "paper.sqlite3")
    data = analysis(snapshot)

    def writer():
        return journal.record_signal(data)

    def reader():
        return journal.report()["signals"]

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(writer if i % 2 else reader) for i in range(32)]
        for future in futures:
            future.result()
    assert PaperJournal(journal.path).report()["signals"] == 1


def test_research_export_contains_provenance_not_secrets(candles, tmp_path, monkeypatch):
    frame = candles(n=130, end="2026-09-28T10:00:00Z")
    scanner = scanner_for(frame, tmp_path, monkeypatch)
    asyncio.run(scanner.scan_once())
    payload = json.loads(scanner.journal.export("json"))
    observed = payload["observations"][0]
    assert observed["origin"] == "LIVE"
    assert observed["data_source"] == "BINANCE_SPOT_KLINES"
    assert observed["strategy_version"] == "technical-v1"
    assert observed["market"]["candles"] and observed["market"]["indicators"]
    assert observed["market"]["support"] == frame.low.tail(20).min()
    assert observed["market"]["resistance"] == frame.high.tail(20).max()
    assert observed["regime"]["version"] == "regime-v1"
    assert "chat_id" not in json.dumps(payload)
    assert "origin" in scanner.journal.export("csv")


def test_scheduler_uses_utc_boundary_and_delay():
    now = datetime(2026, 9, 29, 10, 0, 5, tzinfo=timezone.utc)
    assert next_due(now, ("1h",), 15) == now + timedelta(seconds=10)
    assert next_due(now + timedelta(seconds=11), ("1h",), 15) == datetime(
        2026, 9, 29, 11, 0, 15, tzinfo=timezone.utc
    )


def test_scanner_has_no_exchange_order_endpoint(monkeypatch, candles, tmp_path):
    frame = candles(n=130, end="2026-09-28T10:00:00Z")
    scanner = scanner_for(frame, tmp_path, monkeypatch)
    called = []

    def forbidden(*args, **kwargs):
        called.append(True)
        raise AssertionError("order placement prohibited")

    monkeypatch.setattr(httpx.AsyncClient, "post", forbidden)
    asyncio.run(scanner.scan_once())
    assert called == []
    assert scanner.journal.report()["paper_positions"] == 0


@pytest.mark.parametrize("quality,expected", [(3.4, "REJECTED"), (8.0, "OPEN")])
def test_optional_paper_bridge_uses_existing_manager(snapshot, tmp_path, monkeypatch, quality, expected):
    from position_manager import AutoTradeManager

    journal = PaperJournal(tmp_path / "paper.sqlite3")
    store = ResearchStore(journal)
    store.register_experiment("paper-baseline-v1", {"auto_paper_entries": False})
    store.record_operation_mode("paper-baseline-v1", True)
    data = analysis(snapshot)
    data["technical_signal"] = snapshot.technical.model_copy(update={"quality": quality})
    data["indicators"] = {**data["indicators"], "Volume_Ratio": 2.0}
    signal_id = journal.record_signal(
        data,
        research={
            "experiment_id": "paper-baseline-v1",
            "origin": "LIVE",
            "data_source": "BINANCE_SPOT_KLINES",
            "regime": {"version": "regime-v1"},
            "quality_bucket": "7-10" if quality >= 7 else "0-<4",
        },
    )
    store.record_execution(signal_id, "NOT_ATTEMPTED", "PAPER_BRIDGE_PENDING")
    manager = AutoTradeManager(Bot(), rules_loader=lambda _: paper_rules(), journal=journal)
    manager.data_path = tmp_path / "positions.json"
    monkeypatch.setattr(manager, "start_monitoring", lambda: None)
    monkeypatch.setattr(manager, "_get_current_price", lambda _: snapshot.technical.plan.entry)

    def forbidden_order(*args, **kwargs):
        raise AssertionError("Real order request is prohibited")

    monkeypatch.setattr(requests, "post", forbidden_order)
    monkeypatch.setattr(httpx.AsyncClient, "post", forbidden_order)
    bridge = PaperExecutionBridge(
        manager,
        1,
        clock=lambda: snapshot.technical.timestamp + timedelta(seconds=20),
    )
    assert bridge.process_once() == 1
    assert bridge.process_once() == 0
    assert (
        PaperExecutionBridge(
            manager, 1, clock=lambda: snapshot.technical.timestamp + timedelta(seconds=30)
        ).process_once()
        == 0
    )
    with sqlite3.connect(journal.path) as db:
        assert db.execute("SELECT status FROM research_execution").fetchone()[0] == expected
        assert db.execute("SELECT COUNT(*) FROM entry_attempts").fetchone()[0] == 1
    assert journal.report()["paper_positions"] == (expected == "OPEN")


def test_interrupted_paper_bridge_never_replays_unknown_entry(snapshot, tmp_path):
    from position_manager import AutoTradeManager

    journal = PaperJournal(tmp_path / "paper.sqlite3")
    store = ResearchStore(journal)
    store.register_experiment("paper-baseline-v1", {"auto_paper_entries": True})
    signal_id = journal.record_signal(
        analysis(snapshot),
        research={
            "experiment_id": "paper-baseline-v1",
            "origin": "LIVE",
            "data_source": "BINANCE_SPOT_KLINES",
            "regime": {"version": "regime-v1"},
            "quality_bucket": "4-<7",
        },
    )
    store.record_execution(signal_id, "NOT_ATTEMPTED", "PAPER_BRIDGE_PENDING")
    assert store.claim_execution(signal_id)
    manager = AutoTradeManager(Bot(), rules_loader=lambda _: paper_rules(), journal=journal)
    bridge = PaperExecutionBridge(
        manager,
        1,
        clock=lambda: datetime.now(timezone.utc) + timedelta(minutes=3),
    )
    bridge.recover_claimed()
    with sqlite3.connect(journal.path) as db:
        assert db.execute("SELECT status, reason FROM research_execution").fetchone() == (
            "UNKNOWN",
            "INTERRUPTED_NO_RETRY",
        )
    assert manager.active_positions == {}
