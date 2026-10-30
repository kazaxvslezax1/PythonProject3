"""Regression coverage for provenance and PAPER experiment isolation."""

import sqlite3
from datetime import timedelta
from types import SimpleNamespace

import pytest
import requests
from deepseek_analyzer import AIResponse
from hybrid_strategy import AIMode, HybridDecision
from paper_execution_bridge import PaperExecutionBridge
from paper_journal import PaperJournal
from paper_research import ResearchStore
from paper_scanner import ScannerConfig, baseline_config
from position_manager import AutoTradeManager
from requests.exceptions import ReadTimeout
from test_paper_journal import analysis
from test_positions import Bot, paper_rules
from test_telegram_ai import Bot as CommandBot


def research_position(tmp_path, monkeypatch, snapshot):
    journal = PaperJournal(tmp_path / "paper.sqlite3")
    store = ResearchStore(journal)
    store.register_experiment("prospective-baseline-v1", {"strategy_version": "technical-v1"})
    store.record_operation_mode("prospective-baseline-v1", True)
    data = analysis(snapshot)
    data["technical_signal"] = snapshot.technical.model_copy(update={"quality": 8.0})
    data["indicators"] = {**data["indicators"], "Volume_Ratio": 2.0}
    signal_id = journal.record_signal(
        data,
        origin="SCANNER_LIVE",
        research={
            "experiment_id": "prospective-baseline-v1",
            "origin": "LIVE",
            "data_source": "BINANCE_SPOT_KLINES",
            "regime": {"version": "regime-v1"},
            "quality_bucket": "7-10",
        },
    )
    store.record_execution(signal_id, "NOT_ATTEMPTED", "PAPER_BRIDGE_PENDING")
    manager = AutoTradeManager(Bot(), rules_loader=lambda _: paper_rules(), journal=journal)
    manager.data_path = tmp_path / "positions.json"
    monkeypatch.setattr(manager, "start_monitoring", lambda: None)
    monkeypatch.setattr(manager, "_get_current_price", lambda _: snapshot.technical.plan.entry)
    bridge = PaperExecutionBridge(
        manager,
        1,
        experiment_id="prospective-baseline-v1",
        clock=lambda: snapshot.technical.timestamp + timedelta(seconds=20),
    )
    return journal, manager, bridge, signal_id


def test_existing_prospective_config_rejects_all_source_transitions(tmp_path):
    store = ResearchStore(PaperJournal(tmp_path / "paper.sqlite3"))
    old_hash = "3b4ac4fe4ed621dea7cdcc1fec042af01c999d5b9d6be9c286b5b89c1934a712"
    new_hash = "583cb7bb3d6429a3796b5f4d58a0ec27f9074e54021ff33f744538b2c2c168b1"
    old = {"strategy_version": "technical-v1", "code_sha256": old_hash, "symbols": ["BTCUSDT"]}
    store.register_experiment("prospective-baseline-v1", old)
    assert store.register_experiment("prospective-baseline-v1", old)
    with pytest.raises(ValueError, match="new PAPER_EXPERIMENT_ID"):
        store.register_experiment("prospective-baseline-v1", {**old, "code_sha256": new_hash})
    policy_hash = baseline_config(ScannerConfig())["code_sha256"]
    with pytest.raises(ValueError, match="new PAPER_EXPERIMENT_ID"):
        store.register_experiment("prospective-baseline-v1", {**old, "code_sha256": policy_hash})
    assert store.experiment_config("prospective-baseline-v1")["code_sha256"] == old_hash
    with pytest.raises(ValueError):
        store.register_experiment(
            "prospective-baseline-v1", {**old, "code_sha256": new_hash, "symbols": ["ETHUSDT"]}
        )


def test_bridge_provenance_restart_and_paper_only(tmp_path, monkeypatch, snapshot):
    journal, manager, bridge, signal_id = research_position(tmp_path, monkeypatch, snapshot)

    def forbidden(*args, **kwargs):
        raise AssertionError("real order placement is forbidden")

    monkeypatch.setattr(requests, "post", forbidden)
    assert bridge.process_once() == 1
    assert bridge.process_once() == 0
    from telegram_runtime import SafeTelegramErrors

    assert SafeTelegramErrors().handle(ReadTimeout("network delayed")) is False
    assert bridge.process_once() == 0
    position = next(iter(manager.get_active_positions().values()))
    assert position["execution_source"] == "PAPER_RESEARCH_BRIDGE"
    assert position["experiment_id"] == "prospective-baseline-v1"
    assert position["strategy_version"] == "technical-v1"
    assert position["observation_id"] == signal_id
    assert position["entry_attempt_id"]
    with sqlite3.connect(journal.path) as db:
        row = db.execute(
            "SELECT experiment_id, strategy_version, observation_id, entry_attempt_id, "
            "execution_source FROM paper_positions WHERE id=?",
            (position["position_id"],),
        ).fetchone()
    assert row == (
        "prospective-baseline-v1",
        "technical-v1",
        signal_id,
        position["entry_attempt_id"],
        "PAPER_RESEARCH_BRIDGE",
    )
    restarted = AutoTradeManager(Bot(), rules_loader=lambda _: paper_rules(), journal=journal)
    restarted.data_path = manager.data_path
    assert restarted.load_data()
    assert len(restarted.get_active_positions()) == 1
    second = PaperExecutionBridge(
        restarted,
        1,
        experiment_id="prospective-baseline-v1",
        clock=lambda: snapshot.technical.timestamp + timedelta(seconds=25),
    )
    assert second.process_once() == 0
    assert journal.report(experiment_id="prospective-baseline-v1")["paper_positions"] == 1


def test_ai_reference_failure_does_not_veto_advisory_paper_entry(tmp_path, monkeypatch, snapshot):
    journal, manager, bridge, signal_id = research_position(tmp_path, monkeypatch, snapshot)
    technical = snapshot.technical.model_copy(update={"quality": 8.0})
    journal.record_ai(
        signal_id,
        HybridDecision(
            technical=technical,
            final=technical,
            mode=AIMode.ADVISORY,
            ai=AIResponse(
                status="AI_UNAVAILABLE",
                model="deepseek-flash",
                reason="AI_REFERENCE_VALIDATION_FAILED",
            ),
        ),
    )
    assert bridge.process_once() == 1
    assert len(manager.get_active_positions()) == 1


def test_legacy_position_does_not_pollute_research_report(tmp_path, monkeypatch, snapshot):
    journal, manager, bridge, signal_id = research_position(tmp_path, monkeypatch, snapshot)
    assert bridge.process_once() == 1
    research = next(iter(manager.get_active_positions().values()))
    monkeypatch.setattr(manager, "should_open_trade", lambda *args: (True, "Paper entry allowed"))
    legacy_id = manager.create_auto_trade(
        1,
        "ETHUSDT",
        100,
        98,
        [102, 104, 106],
        "LONG",
        8,
        2,
        execution_source="LEGACY_TELEGRAM_SCANNER",
    )
    assert legacy_id
    manager.close_position_manually(legacy_id, 95)
    manager.record_skipped_signal(
        2,
        "SCANNER_QUALITY_VOLUME_FILTER",
        signal_id=signal_id,
        symbol="BTCUSDT",
        execution_source="LEGACY_TELEGRAM_SCANNER",
    )
    isolated = journal.report(experiment_id="prospective-baseline-v1")
    assert isolated["paper_positions"] == 1
    assert isolated["closed_positions"] == 0
    assert isolated["net_pnl_usd_closed"] == 0
    assert isolated["outside_experiment_positions"] == 1
    assert isolated["rejected_entries"] == 0
    assert journal.report()["closed_positions"] == 1
    assert journal.report()["rejected_entries"] == 1
    assert manager.active_positions[legacy_id]["execution_source"] == "LEGACY_TELEGRAM_SCANNER"
    assert research["observation_id"] == signal_id
    restarted = AutoTradeManager(Bot(), rules_loader=lambda _: paper_rules(), journal=journal)
    restarted.data_path = manager.data_path
    assert restarted.load_data()
    assert legacy_id not in restarted.get_active_positions()
    assert any(item["position_id"] == legacy_id for item in restarted.trade_history)


def test_old_research_position_is_attributed_by_verified_linkage(tmp_path, monkeypatch, snapshot):
    journal, manager, bridge, signal_id = research_position(tmp_path, monkeypatch, snapshot)
    assert bridge.process_once() == 1
    position = next(iter(manager.get_active_positions().values()))
    for key in (
        "execution_source",
        "experiment_id",
        "strategy_version",
        "observation_id",
        "entry_attempt_id",
    ):
        position.pop(key)
    manager.save_data()
    with sqlite3.connect(journal.path) as db:
        db.execute(
            "UPDATE paper_positions SET execution_source=NULL, experiment_id=NULL, "
            "strategy_version=NULL, observation_id=NULL, entry_attempt_id=NULL"
        )
    restarted = AutoTradeManager(Bot(), rules_loader=lambda _: paper_rules(), journal=journal)
    restarted.data_path = manager.data_path
    assert restarted.load_data()
    assert len(restarted.get_active_positions()) == 1
    assert journal.report(experiment_id="prospective-baseline-v1")["paper_positions"] == 1
    assert journal.has_attempt(signal_id, 1)["status"] == "OPEN"


def test_v2_position_schema_migrates_without_replacing_existing_entry(tmp_path, monkeypatch, snapshot):
    journal, manager, bridge, _ = research_position(tmp_path, monkeypatch, snapshot)
    assert bridge.process_once() == 1
    position_id = next(iter(manager.get_active_positions()))
    with sqlite3.connect(journal.path) as db:
        for column in (
            "experiment_id",
            "strategy_version",
            "observation_id",
            "entry_attempt_id",
            "execution_source",
        ):
            db.execute(f"ALTER TABLE paper_positions DROP COLUMN {column}")
        db.execute("PRAGMA user_version=2")
    upgraded = PaperJournal(journal.path)
    with sqlite3.connect(upgraded.path) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 5
        assert db.execute("SELECT id FROM paper_positions").fetchone()[0] == position_id
    assert upgraded.report(experiment_id="prospective-baseline-v1")["paper_positions"] == 1


def test_legacy_activation_guard_and_source(monkeypatch):
    from telegram_handlers import AutoTradingScanner

    calls = []
    manager = SimpleNamespace(create_auto_trade=lambda *a, **kw: calls.append(kw) or "paper-id")
    scanner = AutoTradingScanner(Bot(), manager)
    monkeypatch.setenv("PAPER_SCANNER_AUTO_PAPER_ENTRIES", "true")
    assert scanner.start_auto_trading(1) is False
    assert not scanner.status()["enabled"]
    assert not scanner.status()["running"]
    monkeypatch.setenv("PAPER_SCANNER_AUTO_PAPER_ENTRIES", "false")
    scanner.scanning_active = True
    assert (
        scanner._create_auto_trade(
            1,
            "BTCUSDT",
            {
                "entry_price": 100,
                "stop_loss": 98,
                "take_profits": [102, 104, 106],
                "direction": "LONG",
                "ai_confidence": 8,
                "volume_ratio": 2,
            },
        )
        == "paper-id"
    )
    assert calls[0]["execution_source"] == "LEGACY_TELEGRAM_SCANNER"


def test_deactivate_all_stops_only_legacy_scanner(monkeypatch):
    import telegram_handlers as handlers

    stopped = []
    monkeypatch.setenv("PAPER_SCANNER_AUTO_PAPER_ENTRIES", "true")
    monkeypatch.setattr(handlers.auto_trading_scanner, "stop_auto_trading", lambda: stopped.append("legacy"))
    monkeypatch.setattr(handlers.bot, "target", SimpleNamespace(reply_to=lambda *a, **kw: None))
    for name in (
        "premium_monitor",
        "market_phase_monitor",
        "anomaly_detector",
        "volume_monitor",
        "takeprofit_manager",
        "report_generator",
        "session_filter_manager",
        "monitor",
    ):
        monkeypatch.setattr(
            handlers,
            name,
            SimpleNamespace(
                **{
                    method: lambda: None
                    for method in (
                        "stop_premium_monitoring",
                        "stop_market_phase_monitoring",
                        "stop_anomaly_detection",
                        "stop_volume_monitoring",
                        "stop_takeprofit_monitoring",
                        "stop_reports",
                        "stop_auto_adjust",
                        "stop_monitoring",
                    )
                }
            ),
        )
    monkeypatch.setattr(
        handlers,
        "takeprofit_manager",
        SimpleNamespace(stop_takeprofit_monitoring=lambda: stopped.append("position-monitor")),
    )
    handlers.deactivate_all_systems_command(SimpleNamespace(chat=SimpleNamespace(id=1)))
    assert stopped == ["legacy"]


def test_bridge_status_command_has_no_entry_side_effects(tmp_path, monkeypatch, snapshot):
    import telegram_handlers as handlers
    from telegram_ai import register_ai_handlers

    journal, manager, bridge, _ = research_position(tmp_path, monkeypatch, snapshot)
    monkeypatch.setattr(handlers, "paper_execution_bridge", bridge, raising=False)
    monkeypatch.setattr(
        handlers.auto_trading_scanner,
        "status",
        lambda: {
            "enabled": False,
            "running": False,
            "last_scan_at": None,
        },
    )
    bot = CommandBot()
    register_ai_handlers(bot)
    before = journal.report()["paper_positions"]
    bot.handlers["paper_bridge_status"](SimpleNamespace(text="/paper_bridge_status"))
    assert "PAPER bridge" in bot.messages[-1]
    assert "prospective-baseline-v1" in bot.messages[-1]
    assert journal.report()["paper_positions"] == before == 0
    assert not journal.has_attempt("missing", 1)
