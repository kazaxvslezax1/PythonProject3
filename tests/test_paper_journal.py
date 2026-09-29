import json
import sqlite3
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pandas as pd
import pytest
from ai_facts import fact_catalog, relation
from deepseek_analyzer import AIAnalysisResult, AIResponse
from hybrid_strategy import AIMode, HybridDecision
from paper_journal import PaperJournal
from position_manager import AutoTradeManager
from signal_models import Direction
from telegram_ai import register_ai_handlers
from test_deepseek import valid_result
from test_positions import Bot, paper_rules
from test_telegram_ai import Bot as CommandBot


def analysis(snapshot):
    return {
        "technical_signal": snapshot.technical,
        "frame": pd.DataFrame([c.model_dump() for c in snapshot.candles]),
        "indicators": snapshot.indicators,
        "symbol": snapshot.symbol,
        "timeframe": snapshot.timeframe,
        "as_of": pd.Timestamp(snapshot.as_of),
        "volume_ratio": snapshot.indicators["Volume_Ratio"],
    }


def unavailable(snapshot):
    return HybridDecision(
        technical=snapshot.technical,
        final=snapshot.technical,
        mode=AIMode.ADVISORY,
        ai=AIResponse(
            status="AI_UNAVAILABLE",
            model="deepseek-flash",
            reason="API_UNAVAILABLE",
            fact_check_status="NOT_CHECKED",
        ),
    )


def verified(snapshot, ai_direction, technical=None):
    payload = valid_result(ai_direction)
    key, fact = next(iter(fact_catalog(snapshot).items()))
    payload["facts"] = [{"fact_id": key, "relation": relation(fact)}]
    ai = AIResponse(
        status="OK",
        model="deepseek-flash",
        fact_check_status="PASSED",
        result=AIAnalysisResult.model_validate(payload),
    )
    return HybridDecision(
        technical=technical or snapshot.technical,
        final=technical or snapshot.technical,
        mode=AIMode.ADVISORY,
        ai=ai,
    )


def test_signal_dedup_hold_and_ai_failure_survive_restart(tmp_path, snapshot):
    path = tmp_path / "paper.db"
    j = PaperJournal(path)
    data = analysis(snapshot)
    signal_id = j.record_signal(data)
    assert j.record_signal(data, origin="TELEGRAM") == signal_id
    j.record_ai(signal_id, unavailable(snapshot))
    j.record_ai(signal_id, unavailable(snapshot))
    again = PaperJournal(path)
    report = again.report()
    assert report["signals"] == 1
    assert report["ai_unavailable"] == 1
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM journal_events WHERE kind='AI_RETRY'").fetchone()[0] == 1
    held = snapshot.technical.model_copy(update={"direction": Direction.HOLD, "plan": None})
    data["technical_signal"] = held
    data["technical_signal"] = held.model_copy(update={"timestamp": held.timestamp + pd.Timedelta(hours=1)})
    frame = data["frame"].copy()
    frame[["time", "close_time"]] += pd.Timedelta(hours=1)
    data["frame"] = frame
    j.record_signal(data)
    assert again.report()["hold"] == 1


def test_future_or_misaligned_candle_is_not_recorded(tmp_path, snapshot):
    journal = PaperJournal(tmp_path / "paper.db")
    data = analysis(snapshot)
    data["technical_signal"] = snapshot.technical.model_copy(
        update={"timestamp": datetime.now(timezone.utc) + timedelta(hours=1)}
    )
    with pytest.raises(ValueError):
        journal.record_signal(data)
    assert journal.report()["signals"] == 0


def test_cost_assumptions_cannot_rewrite_existing_journal(tmp_path, monkeypatch):
    path = tmp_path / "paper.db"
    PaperJournal(path)
    monkeypatch.setenv("PAPER_JOURNAL_FEE_RATE", "0.002")
    with pytest.raises(ValueError, match="cost settings changed"):
        PaperJournal(path)


def test_controls_freeze_first_ai_and_portfolio_limit(tmp_path, snapshot):
    j = PaperJournal(tmp_path / "paper.db")
    signal_id = j.record_signal(analysis(snapshot))
    portfolio = {
        "active_slots_global": 0,
        "slot_limit": 1,
        "reserved_usd": 0,
        "capital_model_usd": 10000,
        "available_model_usd": 10000,
        "requested_notional_usd": 1000,
        "manager_scope": "per-chat",
    }
    j.record_ai(signal_id, unavailable(snapshot))
    j.record_attempt(signal_id, 1, "PENDING", "PAPER_ENTRY_PENDING", portfolio)
    assert j.report()["control_decisions"] == {
        "technical_allow": 1,
        "ai_allow": 0,
        "ai_veto": 0,
        "ai_unknown": 1,
        "actual_vs_global_model_mismatch": 0,
    }
    j.record_attempt(signal_id, 1, "PENDING", "PAPER_ENTRY_PENDING", portfolio)
    with sqlite3.connect(j.path) as db:
        assert db.execute("SELECT COUNT(*) FROM entry_attempts").fetchone()[0] == 1
    another = snapshot.technical.model_copy(update={"symbol": "ETHUSDT"})
    data = analysis(snapshot)
    data["technical_signal"] = another
    other_id = j.record_signal(data)
    j.record_attempt(
        other_id,
        1,
        "PENDING",
        "PAPER_ENTRY_PENDING",
        {**portfolio, "active_slots_global": 1, "reserved_usd": 1000, "available_model_usd": 9000},
    )
    assert j.report()["control_decisions"]["technical_allow"] == 1


def test_verified_ai_control_agreement_and_veto_do_not_change_paper_signal(tmp_path, snapshot):
    j = PaperJournal(tmp_path / "paper.db")
    data = analysis(snapshot)
    first = j.record_signal(data)
    same_side = snapshot.technical.direction.value
    j.record_ai(first, verified(snapshot, same_side))
    j.record_ai(first, unavailable(snapshot))  # Later outage cannot rewrite the first decision.
    portfolio = {
        "active_slots_global": 0,
        "slot_limit": 5,
        "reserved_usd": 0,
        "capital_model_usd": 10000,
        "available_model_usd": 10000,
        "requested_notional_usd": 1000,
        "manager_scope": "per-chat",
    }
    j.record_attempt(first, 1, "PENDING", "PAPER_ENTRY_PENDING", portfolio)
    other = snapshot.technical.model_copy(update={"symbol": "ETHUSDT"})
    data["technical_signal"] = other
    second = j.record_signal(data)
    disagree = "SHORT" if same_side == "LONG" else "LONG"
    j.record_ai(second, verified(snapshot, disagree, technical=other))
    j.record_attempt(second, 1, "PENDING", "PAPER_ENTRY_PENDING", portfolio)
    report = j.report()
    assert report["control_decisions"]["technical_allow"] == 2
    assert report["control_decisions"]["ai_allow"] == 1
    assert report["control_decisions"]["ai_veto"] == 1
    with sqlite3.connect(j.path) as db:
        assert db.execute("SELECT COUNT(*) FROM observations WHERE final_direction='LONG'").fetchone()[0] == 2
        assert db.execute("SELECT ai_status FROM observations WHERE id=?", (first,)).fetchone()[0] == "OK"


def test_late_ai_cannot_retroactively_make_entry_comparable(tmp_path, snapshot):
    journal = PaperJournal(tmp_path / "paper.db")
    signal_id = journal.record_signal(analysis(snapshot))
    journal.record_attempt(
        signal_id,
        1,
        "PENDING",
        "PAPER_ENTRY_PENDING",
        {
            "active_slots_global": 0,
            "slot_limit": 5,
            "reserved_usd": 0,
            "capital_model_usd": 10000,
            "available_model_usd": 10000,
            "requested_notional_usd": 1000,
            "manager_scope": "per-chat",
        },
    )
    journal.record_ai(signal_id, verified(snapshot, snapshot.technical.direction.value))
    report = journal.report()
    assert report["ai_ok"] == 1
    assert report["paired_ai_observations"] == 0
    assert report["control_decisions"]["ai_unknown"] == 1


def test_ai_recovers_before_entry_without_rewriting_first_failure(tmp_path, snapshot):
    journal = PaperJournal(tmp_path / "paper.db")
    signal_id = journal.record_signal(analysis(snapshot))
    journal.record_ai(signal_id, unavailable(snapshot))
    journal.record_ai(signal_id, verified(snapshot, snapshot.technical.direction.value))
    journal.record_attempt(
        signal_id,
        1,
        "PENDING",
        "PAPER_ENTRY_PENDING",
        {
            "active_slots_global": 0,
            "slot_limit": 5,
            "reserved_usd": 0,
            "capital_model_usd": 10000,
            "available_model_usd": 10000,
            "requested_notional_usd": 1000,
            "manager_scope": "per-chat",
        },
    )
    result = journal.report()
    assert result["ai_unavailable"] == result["ai_retry_ok"] == 1
    assert result["paired_ai_observations"] == 1
    assert result["control_decisions"]["ai_allow"] == 1


def test_actual_paper_reconciliation_costs_restart_and_backup(tmp_path, monkeypatch, snapshot):
    j = PaperJournal(tmp_path / "paper.db")
    signal_id = j.record_signal(analysis(snapshot))
    m = AutoTradeManager(Bot(), rules_loader=lambda _: paper_rules(), journal=PaperJournal(j.path))
    m.data_path = tmp_path / "positions.json"
    monkeypatch.setattr(m, "start_monitoring", lambda: None)
    monkeypatch.setattr(m, "_get_current_price", lambda _: 100)
    args = (1, "BTCUSDT", 100, 98, [102, 104, 106], "LONG", 8, 2)
    pid = m.create_auto_trade(*args, signal_id=signal_id, timeframe="1h")
    assert pid and m.create_auto_trade(*args, signal_id=signal_id, timeframe="1h") is None
    import paper_journal

    monkeypatch.setattr(paper_journal, "MARK_INTERVAL_SECONDS", 0)
    j.record_mark(pid, 100, m.active_positions[pid])
    j.record_mark(pid, 95, m.active_positions[pid])
    assert j.report()["sampled_max_position_drawdown_pct"] > 0
    assert j.report()["paper_positions"] == 1
    restarted = AutoTradeManager(Bot(), rules_loader=lambda _: paper_rules(), journal=PaperJournal(j.path))
    restarted.data_path = m.data_path
    assert restarted.load_data()
    assert pid in restarted.get_active_positions()
    restarted._execute_take_profit(restarted.active_positions[pid], "TP1", 102, 102)
    assert restarted.close_position_manually(pid, 100)
    assert restarted.load_data()  # No duplicated fills, close or PnL after a replay.
    report = j.report()
    assert report["paper_positions"] == report["closed_positions"] == 1
    actual = restarted.trade_history[0]
    assert report["net_pnl_usd_closed"] == pytest.approx(
        actual["paper_notional"] * actual["realized_pnl_pct"] / 100
    )
    costs = report["modeled_same_fills_costs"]
    assert costs["covered_positions"] == 1
    assert costs["base_usd"] == pytest.approx(report["net_pnl_usd_closed"], abs=0.1)
    assert costs["double_usd"] < costs["base_usd"]
    with sqlite3.connect(j.path) as db:
        assert db.execute("SELECT COUNT(*) FROM paper_fills").fetchone()[0] == 2
        assert (
            db.execute("SELECT COUNT(*) FROM journal_events WHERE kind='POSITION_CLOSE'").fetchone()[0] == 1
        )
        assert (
            db.execute("SELECT COUNT(*) FROM journal_events WHERE kind='POSITION_UPDATE'").fetchone()[0] == 1
        )
    backup = tmp_path / "backup.sqlite3"
    j.backup(backup)
    assert PaperJournal(backup).report()["net_pnl_usd_closed"] == report["net_pnl_usd_closed"]


def test_json_paper_entry_recovers_after_journal_write_failure(tmp_path, monkeypatch, snapshot):
    journal = PaperJournal(tmp_path / "paper.db")
    signal_id = journal.record_signal(analysis(snapshot))
    manager = AutoTradeManager(Bot(), rules_loader=lambda _: paper_rules(), journal=journal)
    manager.data_path = tmp_path / "positions.json"
    monkeypatch.setattr(manager, "start_monitoring", lambda: None)
    monkeypatch.setattr(manager, "_get_current_price", lambda _: 100)

    def storage_error(*args, **kwargs):
        raise sqlite3.OperationalError("temporary busy")

    monkeypatch.setattr(journal, "reconcile_positions", storage_error)
    pid = manager.create_auto_trade(
        1,
        "BTCUSDT",
        100,
        98,
        [102, 104, 106],
        "LONG",
        8,
        2,
        signal_id=signal_id,
        timeframe="1h",
    )
    assert pid and manager.data_path.exists()
    assert PaperJournal(journal.path).report()["paper_positions"] == 0
    restarted = AutoTradeManager(
        Bot(), rules_loader=lambda _: paper_rules(), journal=PaperJournal(journal.path)
    )
    restarted.data_path = manager.data_path
    assert restarted.load_data()
    assert pid in restarted.get_active_positions()
    assert restarted.journal.report()["paper_positions"] == 1


def test_api_records_before_unavailable_ai_and_export_is_redacted(tmp_path, monkeypatch, snapshot):
    monkeypatch.setenv("PAPER_JOURNAL_PATH", str(tmp_path / "paper.db"))
    monkeypatch.setenv("DEEPSEEK_API_KEY", "private-test-secret")
    import ai_runtime
    import app as api

    monkeypatch.setattr(api, "analyze_market", lambda *args: analysis(snapshot))
    monkeypatch.setattr(ai_runtime, "review_analysis", lambda data, **kwargs: unavailable(snapshot))
    out = api.analyze("BTCUSDT", "1h")
    assert out["action"] == "BUY"
    assert api.ai_review("BTCUSDT", "1h")["source"] == "API_SERVER"
    j = PaperJournal()
    assert j.report()["signals"] == 1
    assert j.report()["ai_unavailable"] == 1
    assert "private-test-secret" not in j.export("json")
    assert "private-test-secret" not in j.export("csv")
    assert "chat_id" not in j.export("json")
    assert all(
        b"private-test-secret" not in path.read_bytes()
        for path in tmp_path.glob("paper.db*")
        if path.is_file()
    )
    assert len(json.loads(j.export("json"))["observations"]) == 1


def test_telegram_paper_commands_and_compact_deepseek(tmp_path, monkeypatch, snapshot):
    monkeypatch.setenv("PAPER_JOURNAL_PATH", str(tmp_path / "paper.db"))
    PaperJournal().record_signal(analysis(snapshot))
    bot = CommandBot()
    bot.documents = []
    bot.send_document = lambda chat_id, stream: bot.documents.append((chat_id, stream.read()))
    register_ai_handlers(bot, api_client=SimpleNamespace())
    message = SimpleNamespace(text="/paper_journal", chat=SimpleNamespace(id=1))
    bot.handlers["paper_journal"](message)
    message.text = "/paper_report"
    bot.handlers["paper_report"](message)
    message.text = "/paper_export json"
    bot.handlers["paper_export"](message)
    assert "PAPER-журнал" in "\n".join(bot.messages)
    assert len(bot.documents) == 1 and bot.documents[0][0] == 1
    assert "BTCUSDT" in bot.documents[0][1].decode()
