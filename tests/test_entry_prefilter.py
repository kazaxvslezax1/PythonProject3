"""Prospective PAPER AI request policy, with no external network or live orders."""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from deepseek_analyzer import AnalysisStore, DeepSeekAnalyzer
from entry_prefilter import (
    AI_REQUEST_POLICY,
    LEGACY_AI_REQUEST_POLICY,
    PREFILTER_REJECTED,
    evaluate_entry_prefilter,
)
from paper_journal import PaperJournal
from paper_research import ResearchStore
from test_paper_execution_isolation import research_position
from test_paper_journal import analysis, verified
from test_paper_scanner import FakeAnalyzer, scanner_for


def fixture_scan(
    candles, tmp_path, monkeypatch, *, side="SHORT", quality=None, volume=None, ai=None, **settings
):
    from analysis_service import analyze_market

    frame = candles(n=130, slope=0.05 if side == "LONG" else 0, end="2026-09-28T10:00:00Z")
    frame.loc[len(frame) - 1, "volume"] = 400.0
    if side == "LONG":
        index = len(frame) - 1
        frame.loc[index, "close"] -= 2.0
        frame.loc[index, "low"] = min(frame.low.iloc[-1], frame.close.iloc[-1] - 0.5)
    closed = frame.tail(120).reset_index(drop=True)
    as_of = frame.close_time.iloc[-1].to_pydatetime() + timedelta(milliseconds=1)
    data = analyze_market("BTCUSDT", "1h", as_of, loader=lambda *args, **kwargs: closed)
    assert data["technical_signal"].direction.value == side
    if quality is not None:
        data["technical_signal"] = data["technical_signal"].model_copy(update={"quality": quality})
    if volume is not None:
        data["indicators"] = {**data["indicators"], "Volume_Ratio": volume}
    monkeypatch.setattr("paper_scanner.analyze_market", lambda *args, **kwargs: data)
    scanner = scanner_for(frame, tmp_path, monkeypatch, ai=ai, prefilter_pass=False, **settings)
    asyncio.run(scanner.scan_once())
    return scanner


def today_status(scanner):
    return scanner.store.status(scanner.config.experiment_id, datetime.now(timezone.utc).date().isoformat())


@pytest.mark.parametrize("side", ["LONG", "SHORT"])
def test_rejected_prefilter_saves_observation_without_ai_http_or_budget(candles, tmp_path, monkeypatch, side):
    requests = []
    provider_store = AnalysisStore(tmp_path / "ai.sqlite3")
    analyzer = DeepSeekAnalyzer(
        store=provider_store,
        api_key="test-placeholder",
        transport=httpx.MockTransport(lambda request: requests.append(request)),
    )
    scanner = fixture_scan(candles, tmp_path, monkeypatch, side=side, quality=6.0, volume=1.0, ai=analyzer)
    report = scanner.journal.report()
    assert report["signals"] == report["signal_directions"][side] == 1
    assert report["ai_skipped_by_prefilter"] == 1
    assert report["ai_unavailable"] == 0
    assert report["ai_request_policies"] == {AI_REQUEST_POLICY: 1}
    with sqlite3.connect(scanner.journal.path) as db:
        assert (
            db.execute("SELECT ai_request_policy FROM research_observations").fetchone()[0]
            == AI_REQUEST_POLICY
        )
        assert db.execute(
            "SELECT state, attempts, budget_decision, reason FROM research_ai_requests"
        ).fetchone() == ("SKIPPED", 0, "NOT_REQUESTED", PREFILTER_REJECTED)
    assert requests == []
    assert provider_store.spent(scanner.clock().date().isoformat()) == 0
    assert provider_store.attempt_count(scanner.clock().date().isoformat()) == 0
    status = today_status(scanner)
    assert status["ai_skipped_by_prefilter_today"] == 1
    assert status["ai_eligible_after_prefilter_today"] == 0
    assert status["ai_requested_today"] == status["ai_budget_exhausted_today"] == 0
    asyncio.run(scanner.scan_once())
    assert scanner.journal.report()["signals"] == 1


def test_passing_prefilter_keeps_normal_advisory_ai_pipeline(candles, tmp_path, monkeypatch):
    ai = FakeAnalyzer()
    scanner = fixture_scan(candles, tmp_path, monkeypatch, ai=ai)
    assert ai.calls == 1
    assert scanner.journal.report()["ai_ok"] == 1
    assert scanner.journal.report()["ai_skipped_by_prefilter"] == 0
    status = today_status(scanner)
    assert status["ai_eligible_after_prefilter_today"] == 1
    assert status["ai_requested_today"] == status["ai_ok_today"] == 1
    asyncio.run(scanner.scan_once())
    assert ai.calls == 1
    assert scanner.journal.report()["paper_positions"] == 0


def test_hold_keeps_existing_skip_policy(candles, snapshot, tmp_path, monkeypatch):
    from signal_models import Direction

    frame = candles(n=130, end="2026-09-28T10:00:00Z")
    data = analysis(snapshot)
    data["technical_signal"] = data["technical_signal"].model_copy(
        update={"direction": Direction.HOLD, "plan": None}
    )
    monkeypatch.setattr("paper_scanner.analyze_market", lambda *args, **kwargs: data)
    ai = FakeAnalyzer()
    scanner = scanner_for(frame, tmp_path, monkeypatch, ai=ai, prefilter_pass=False, ai_on_hold=False)
    asyncio.run(scanner.scan_once())
    assert ai.calls == 0
    with sqlite3.connect(scanner.journal.path) as db:
        assert db.execute("SELECT reason FROM research_ai_requests").fetchone()[0] == "HOLD_COST_POLICY"
    assert today_status(scanner)["ai_skipped_hold_today"] == 1


def test_shared_prefilter_is_rechecked_by_paper_bridge(tmp_path, monkeypatch, snapshot, caplog):
    from paper_scanner import evaluate_entry_prefilter as scanner_gate
    from position_manager import evaluate_entry_prefilter as manager_gate

    assert scanner_gate is manager_gate is evaluate_entry_prefilter
    journal, manager, bridge, signal_id = research_position(tmp_path, monkeypatch, snapshot)
    with sqlite3.connect(journal.path) as db:
        db.execute(
            "UPDATE research_observations SET ai_request_policy=? WHERE signal_id=?",
            (AI_REQUEST_POLICY, signal_id),
        )
    ResearchStore(journal).skip_ai(signal_id, "MISSING_API_KEY")
    manager.trading_config["MIN_AI_CONFIDENCE"] = 9.0
    assert evaluate_entry_prefilter(8.0, 2.0).passed
    assert bridge.process_once() == 1
    with sqlite3.connect(journal.path) as db:
        assert db.execute("SELECT reason FROM entry_attempts").fetchone()[0] == (
            "Quality or volume filter rejected"
        )
    assert len(manager.get_active_positions()) == 0
    assert "PAPER prefilter disagreement" in caplog.text


def test_advisory_veto_still_opens_paper_position(tmp_path, monkeypatch, snapshot):
    journal, manager, bridge, signal_id = research_position(tmp_path, monkeypatch, snapshot)
    with sqlite3.connect(journal.path) as db:
        db.execute(
            "UPDATE research_observations SET ai_request_policy=? WHERE signal_id=?",
            (AI_REQUEST_POLICY, signal_id),
        )
    technical = snapshot.technical.model_copy(update={"quality": 8.0})
    journal.record_ai(signal_id, verified(snapshot, "HOLD", technical=technical))
    assert bridge.process_once() == 1
    assert journal.report(experiment_id="prospective-baseline-v1")["control_decisions"]["ai_veto"] == 1
    assert len(manager.get_active_positions()) == 1


def test_auto_paper_entries_remain_enabled_after_passing_prefilter(candles, tmp_path, monkeypatch):
    from paper_execution_bridge import PaperExecutionBridge
    from position_manager import AutoTradeManager
    from test_positions import Bot, paper_rules

    scanner = fixture_scan(candles, tmp_path, monkeypatch, ai=FakeAnalyzer(), auto_paper_entries=True)
    manager = AutoTradeManager(Bot(), rules_loader=lambda _: paper_rules(), journal=scanner.journal)
    manager.data_path = tmp_path / "positions.json"
    monkeypatch.setattr(manager, "start_monitoring", lambda: None)
    with sqlite3.connect(scanner.journal.path) as db:
        requested_entry = json.loads(db.execute("SELECT signal_json FROM observations").fetchone()[0])[
            "plan"
        ]["entry"]
    monkeypatch.setattr(manager, "_get_current_price", lambda _: requested_entry)
    bridge = PaperExecutionBridge(
        manager,
        1,
        experiment_id=scanner.config.experiment_id,
        clock=lambda: scanner.clock() + timedelta(seconds=5),
    )
    assert bridge.process_once() == 1
    assert bridge.process_once() == 0
    assert scanner.journal.report()["paper_positions"] == 1


def test_v3_migration_preserves_old_policy_and_rows(tmp_path, snapshot):
    journal = PaperJournal(tmp_path / "paper.sqlite3")
    signal_id = journal.record_signal(
        analysis(snapshot),
        research={
            "experiment_id": "prospective-baseline-v1",
            "origin": "LIVE",
            "data_source": "BINANCE_SPOT_KLINES",
            "regime": {"version": "regime-v1"},
            "quality_bucket": "7-10",
        },
    )
    with sqlite3.connect(journal.path) as db:
        db.execute("ALTER TABLE research_observations DROP COLUMN ai_request_policy")
        db.execute("PRAGMA user_version=3")
    reopened = PaperJournal(journal.path)
    assert ResearchStore(reopened).observation(signal_id)["ai_request_policy"] == LEGACY_AI_REQUEST_POLICY
    assert reopened.report(experiment_id="prospective-baseline-v1")["signals"] == 1
    assert reopened.report(experiment_id="prospective-baseline-v1")["ai_request_policies"] == {
        LEGACY_AI_REQUEST_POLICY: 1
    }
    with sqlite3.connect(journal.path) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 5
        assert db.execute("SELECT COUNT(*) FROM observations").fetchone()[0] == 1


@pytest.mark.parametrize(
    ("reason", "counter"),
    [
        ("BUDGET_EXHAUSTED", "ai_budget_exhausted_today"),
        ("AI_REFERENCE_VALIDATION_FAILED", "ai_validation_failed_today"),
    ],
)
def test_ai_error_counters_are_distinct_from_prefilter(candles, tmp_path, monkeypatch, reason, counter):
    ai = FakeAnalyzer(reason)
    scanner = fixture_scan(candles, tmp_path, monkeypatch, ai=ai)
    assert ai.calls == 1
    status = today_status(scanner)
    assert status[counter] == status["ai_requested_today"] == 1
    assert status["ai_skipped_by_prefilter_today"] == 0
    assert scanner.journal.report()["ai_skipped_by_prefilter"] == 0
