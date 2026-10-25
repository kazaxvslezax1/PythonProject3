"""Bounded, chronological PAPER research recovery without historical execution."""

import asyncio
import sqlite3
from datetime import timedelta
from types import SimpleNamespace

import pytest
from paper_execution_bridge import PaperExecutionBridge
from paper_journal import PaperJournal
from paper_research import ResearchStore
from paper_scanner import ResearchScanner, ScannerConfig, baseline_config
from test_paper_scanner import FakeAnalyzer, scanner_for
from test_positions import Bot, paper_rules
from test_telegram_ai import Bot as CommandBot


def _rows(scanner, query):
    path = scanner.journal.path if hasattr(scanner, "journal") else scanner.path
    with sqlite3.connect(path) as db:
        return db.execute(query).fetchall()


@pytest.mark.parametrize("gap", [71, 72, 73, 106])
def test_gap_is_chunked_and_historical_observations_stay_isolated(candles, tmp_path, monkeypatch, gap):
    from position_manager import AutoTradeManager

    frame = candles(n=230, end="2026-09-28T10:00:00Z")
    latest = frame.close_time.iloc[-1].to_pydatetime()
    now = latest + timedelta(minutes=10)
    analyzer = FakeAnalyzer()
    scanner = scanner_for(
        frame,
        tmp_path,
        monkeypatch,
        now=now,
        start=latest - timedelta(hours=gap),
        ai=analyzer,
        max_backfill_bars=72,
        auto_paper_entries=True,
    )
    asyncio.run(scanner.scan_once())
    assert len(_rows(scanner, "SELECT id FROM observations")) == min(gap, 72)
    first = scanner.status()
    assert first["healthy"]
    assert first["recovery_active"] is (gap > 72)
    assert first["caught_up"] is (gap <= 72)
    assert first["timeframe_progress"]["1h"]["missing_bars"] == max(0, gap - 72)
    if gap > 72:
        assert first["last_success_at"] is None
        asyncio.run(scanner.scan_once())
    final = scanner.status()
    assert final["caught_up"] and not final["recovery_active"]
    assert final["last_success_at"] is not None
    assert len(_rows(scanner, "SELECT id FROM observations")) == gap
    rows = _rows(
        scanner,
        "SELECT o.candle_close,r.origin FROM observations o JOIN research_observations r "
        "ON r.signal_id=o.id ORDER BY r.observed_at",
    )
    assert [row[0] for row in rows] == sorted(row[0] for row in rows)
    assert {row[1] for row in rows} == {"BACKFILL_TECHNICAL"}
    assert analyzer.calls == 0
    assert _rows(
        scanner, "SELECT SUM(attempts),SUM(COALESCE(estimated_cost_usd,0)) FROM research_ai_requests"
    ) == [(0, 0)]
    assert not _rows(scanner, "SELECT id FROM entry_attempts")
    assert not _rows(scanner, "SELECT id FROM paper_positions")
    assert not _rows(scanner, "SELECT signal_id FROM research_execution WHERE reason='PAPER_BRIDGE_PENDING'")
    manager = AutoTradeManager(Bot(), rules_loader=lambda _: paper_rules(), journal=scanner.journal)
    bridge = PaperExecutionBridge(manager, 1, experiment_id=scanner.config.experiment_id)
    assert bridge.process_once() == 0
    assert not _rows(scanner, "SELECT id FROM paper_positions")
    if gap > 72:
        markers = _rows(
            scanner, "SELECT kind,payload_json FROM journal_events WHERE kind='SCANNER_RECOVERY_GAP'"
        )
        assert markers and f'"missing_bars":{gap}' in markers[0][1]


def test_106_bar_recovery_restart_retry_and_next_live(candles, tmp_path, monkeypatch):
    frame = candles(n=231, end="2026-09-28T11:00:00Z")
    historical_close = frame.close_time.iloc[-2].to_pydatetime()
    now = [historical_close + timedelta(minutes=10)]
    analyzer = FakeAnalyzer()
    scanner = scanner_for(
        frame,
        tmp_path,
        monkeypatch,
        now=now[0],
        start=historical_close - timedelta(hours=106),
        ai=analyzer,
        max_backfill_bars=72,
    )
    scanner.clock = lambda: now[0]
    asyncio.run(scanner.scan_once())
    assert len(_rows(scanner, "SELECT id FROM observations")) == 72
    restarted = ResearchScanner(
        journal=scanner.journal,
        config=scanner.config,
        loader=scanner.loader,
        analyzer=analyzer,
        clock=lambda: now[0],
    )
    asyncio.run(restarted.scan_once())
    assert len(_rows(restarted, "SELECT id FROM observations")) == 106
    assert restarted.status()["caught_up"]
    asyncio.run(restarted.scan_once())
    assert len(_rows(restarted, "SELECT id FROM observations")) == 106
    now[0] = frame.close_time.iloc[-1].to_pydatetime() + timedelta(seconds=15, milliseconds=1)
    asyncio.run(restarted.scan_once())
    assert len(_rows(restarted, "SELECT id FROM observations")) == 107
    assert _rows(
        restarted,
        "SELECT r.origin FROM observations o JOIN research_observations r ON r.signal_id=o.id "
        "ORDER BY o.candle_close DESC LIMIT 1",
    ) == [("LIVE",)]
    assert restarted.status()["caught_up"]


def test_partial_chunk_write_resumes_without_duplicates(candles, tmp_path, monkeypatch):
    frame = candles(n=230, end="2026-09-28T10:00:00Z")
    latest = frame.close_time.iloc[-1].to_pydatetime()
    scanner = scanner_for(
        frame,
        tmp_path,
        monkeypatch,
        now=latest + timedelta(minutes=10),
        start=latest - timedelta(hours=106),
        max_backfill_bars=72,
    )
    original = scanner._record_execution_metadata
    calls = 0

    def fail_once(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 20:
            raise RuntimeError("test-only interrupted chunk")
        return original(*args, **kwargs)

    scanner._record_execution_metadata = fail_once
    asyncio.run(scanner.scan_once())
    assert not scanner.healthy
    assert len(_rows(scanner, "SELECT id FROM observations")) == 20
    restarted = ResearchScanner(
        journal=scanner.journal,
        config=scanner.config,
        loader=scanner.loader,
        analyzer=FakeAnalyzer(),
        clock=scanner.clock,
    )
    asyncio.run(restarted.scan_once())
    asyncio.run(restarted.scan_once())
    assert restarted.status()["caught_up"]
    assert len(_rows(restarted, "SELECT id FROM observations")) == 106
    assert not _rows(
        restarted,
        "SELECT symbol,timeframe,candle_close FROM observations GROUP BY 1,2,3 HAVING COUNT(*)>1",
    )
    assert not _rows(restarted, "SELECT id FROM entry_attempts")
    assert _rows(restarted, "PRAGMA quick_check") == [("ok",)]


def test_one_pair_failure_does_not_block_other_pair_or_4h(candles, tmp_path, monkeypatch):
    one_hour = candles(n=205, end="2026-09-28T08:00:00Z")
    four_hour = candles(n=150, end="2026-09-28T08:00:00Z", timeframe="4h")
    latest = one_hour.close_time.iloc[-1].to_pydatetime()
    now = latest + timedelta(minutes=10)
    unavailable = [True]

    def loader(symbol, timeframe, *, limit, as_of):
        if symbol == "ETHUSDT" and timeframe == "1h" and unavailable[0]:
            raise ConnectionError("private test-only payload")
        frame = one_hour if timeframe == "1h" else four_hour
        return frame.loc[frame.close_time < as_of].tail(limit).reset_index(drop=True)

    config = ScannerConfig(
        enabled=True,
        symbols=("BTCUSDT", "ETHUSDT"),
        timeframes=("1h", "4h"),
        max_backfill_bars=72,
    )
    journal = PaperJournal(tmp_path / "research.sqlite3")
    ResearchStore(journal).register_experiment(
        config.experiment_id, baseline_config(config), latest - timedelta(hours=73)
    )
    scanner = ResearchScanner(
        journal=journal, config=config, loader=loader, analyzer=FakeAnalyzer(), clock=lambda: now
    )
    asyncio.run(scanner.scan_once())
    first = scanner.status()
    assert not first["healthy"]
    assert first["timeframe_progress"]["1h"]["last_error_code"] == "BINANCE_FETCH_FAILED"
    assert first["timeframe_progress"]["4h"]["missing_bars"] == 0
    four_hour_count = _rows(scanner, "SELECT COUNT(*) FROM observations WHERE timeframe='4h'")[0][0]
    assert four_hour_count > 0
    assert _rows(scanner, "SELECT COUNT(*) FROM observations WHERE symbol='BTCUSDT' AND timeframe='1h'") == [
        (72,)
    ]
    unavailable[0] = False
    asyncio.run(scanner.scan_once())
    asyncio.run(scanner.scan_once())
    assert scanner.status()["healthy"] and scanner.status()["caught_up"]
    assert scanner.status()["timeframe_progress"]["1h"]["last_error_code"] is None
    assert _rows(scanner, "SELECT COUNT(*) FROM observations WHERE timeframe='4h'") == [(four_hour_count,)]
    assert _rows(scanner, "SELECT COUNT(*) FROM observations WHERE timeframe='1h'") == [(146,)]
    assert "private test-only payload" not in journal.export("json")


def test_v4_error_table_migrates_without_erasing_existing_rows(tmp_path):
    journal = PaperJournal(tmp_path / "old.sqlite3")
    with sqlite3.connect(journal.path) as db:
        db.execute(
            "INSERT INTO scanner_errors(occurred_at,stage,error_type,symbol,timeframe,error_code) "
            "VALUES ('2026-10-21T12:00:00+00:00','MARKET_OR_JOURNAL','ValueError','BTCUSDT','1h',NULL)"
        )
        db.execute("ALTER TABLE scanner_errors DROP COLUMN error_code")
        db.execute("PRAGMA user_version=4")
    migrated = PaperJournal(journal.path)
    assert _rows(migrated, "PRAGMA user_version") == [(5,)]
    assert _rows(migrated, "SELECT symbol,error_code FROM scanner_errors") == [("BTCUSDT", None)]
    assert _rows(migrated, "PRAGMA quick_check") == [("ok",)]


def test_telegram_status_shows_recovery_instead_of_fresh_global_candle():
    from telegram_ai import register_ai_handlers

    status = {
        "enabled": True,
        "running": True,
        "healthy": True,
        "recovery_active": True,
        "caught_up": False,
        "auto_paper_entries": True,
        "experiment_id": "prospective-baseline-v1",
        "strategy_version": "technical-v1",
        "symbols": ["BTCUSDT"],
        "timeframes": ["1h"],
        "journal_path": "/tmp/paper-journal-test.sqlite3",
        "last_candle_close": "2026-10-25T19:59:59.999000+00:00",
        "timeframe_progress": {
            "1h": {
                "latest_recorded_candle": "2026-10-21T11:59:59.999000+00:00",
                "oldest_pair_candle": "2026-10-21T11:59:59.999000+00:00",
                "expected_latest_closed_candle": "2026-10-25T21:59:59.999000+00:00",
                "missing_bars": 106,
                "recovery_state": "RECOVERING",
                "last_successful_processing": "2026-10-21T12:00:24+00:00",
                "last_error_code": None,
            }
        },
    }

    class Remote:
        def get(self, url, *, timeout):
            assert url.endswith("/paper/scanner/status") and timeout == (3, 5)
            return SimpleNamespace(json=lambda: status, raise_for_status=lambda: None)

    bot = CommandBot()
    register_ai_handlers(bot, api_client=Remote())
    bot.handlers["paper_scanner_status"](SimpleNamespace(text="/paper_scanner_status"))
    assert "recovery=True; caught up=False" in bot.messages[0]
    assert "1h: RECOVERING, missing=106" in bot.messages[0]
