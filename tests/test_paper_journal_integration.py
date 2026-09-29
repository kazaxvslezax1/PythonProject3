"""Telegram -> local API -> SQLite -> Telegram report, without network or paid AI calls."""

import os
import sqlite3
from datetime import timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest
from deepseek_analyzer import AIResponse
from fastapi.testclient import TestClient
from hybrid_strategy import AIMode, HybridDecision
from paper_journal import PaperJournal, journal_path
from signal_models import Direction, TradePlan
from telegram_ai import register_ai_handlers
from test_paper_journal import analysis, verified
from test_telegram_ai import Bot


class LocalAPI:
    def __init__(self, api):
        self.client = TestClient(api.app)

    def post(self, url, *, params, timeout):
        assert url.endswith("/ai/review") and timeout == (3, 100)
        return self.client.post("/ai/review", params=params)

    def get(self, url, *, timeout):
        assert url.endswith("/paper/journal/status") and timeout == (3, 5)
        return self.client.get("/paper/journal/status")


def technical(snapshot, side, *, quality=3.4, symbol="BTCUSDT", timeframe="1h"):
    price = snapshot.candles[-1].close
    plan = None
    if side == Direction.LONG:
        plan = TradePlan(
            direction=side,
            entry=price,
            stop_loss=price - 2,
            take_profits=[price + 2, price + 4, price + 6],
        )
    elif side == Direction.SHORT:
        plan = TradePlan(
            direction=side,
            entry=price,
            stop_loss=price + 2,
            take_profits=[price - 2, price - 4, price - 6],
        )
    return snapshot.technical.model_copy(
        update={"direction": side, "plan": plan, "quality": quality, "symbol": symbol, "timeframe": timeframe}
    )


def market(snapshot, side, **kwargs):
    data = analysis(snapshot)
    data["technical_signal"] = technical(snapshot, side, **kwargs)
    data["symbol"] = data["technical_signal"].symbol
    data["timeframe"] = data["technical_signal"].timeframe
    data["ai_snapshot"] = snapshot
    return data


def ai_decision(snapshot, signal, status):
    if status == "OK":
        return verified(snapshot, signal.direction.value, technical=signal)
    return HybridDecision(
        technical=signal,
        final=signal,
        mode=AIMode.ADVISORY,
        ai=AIResponse(
            status="AI_UNAVAILABLE",
            model="deepseek-flash",
            reason="AI_FACT_CHECK_FAILED" if status == "FACT_FAILED" else "API_UNAVAILABLE",
            fact_check_status="FAILED" if status == "FACT_FAILED" else "NOT_CHECKED",
        ),
    )


def telegram(api):
    bot = Bot()
    register_ai_handlers(bot, api_client=LocalAPI(api))
    return bot


def command(bot, name, text=None):
    bot.handlers[name](SimpleNamespace(text=text or f"/{name} BTCUSDT 1h", chat=SimpleNamespace(id=1)))
    return bot.messages[-1]


@pytest.mark.parametrize(
    ("side", "ai_status", "paired"),
    [
        (Direction.SHORT, "OK", 1),
        (Direction.LONG, "OK", 1),
        (Direction.HOLD, "OK", 1),
        (Direction.SHORT, "UNAVAILABLE", 0),
        (Direction.SHORT, "FACT_FAILED", 0),
    ],
)
def test_telegram_api_journal_report_route(monkeypatch, snapshot, side, ai_status, paired):
    import ai_runtime
    import app as api

    data = market(snapshot, side)
    monkeypatch.setattr(api, "analyze_market", lambda *_: data)
    monkeypatch.setattr(
        ai_runtime,
        "review_analysis",
        lambda current, **_: ai_decision(snapshot, current["technical_signal"], ai_status),
    )
    bot = telegram(api)
    message = command(bot, "deepseek")
    assert "AI_UNAVAILABLE: API_ANALYSIS_ERROR" not in message
    assert f"Технический сигнал: {side.value}" in message
    report_text = command(bot, "paper_report", "/paper_report")
    report = PaperJournal().report()
    assert report["signals"] == 1
    assert report["signal_directions"][side.value] == 1
    assert report["hold"] == (side == Direction.HOLD)
    assert report["ai_ok"] == (ai_status == "OK")
    assert report["ai_unavailable"] == (ai_status != "OK")
    assert report["paired_ai_observations"] == paired
    assert report["ai_observations"] == 1
    assert report["paper_positions"] == 0
    assert "Telegram SQLite:" in report_text and "API SQLite:" in report_text
    assert "ВНИМАНИЕ: API и Telegram читают разные" not in report_text
    with sqlite3.connect(journal_path()) as db:
        row = db.execute(
            "SELECT id, quality, ai_status, ai_reason, final_direction FROM observations"
        ).fetchone()
        assert row[1] == pytest.approx(3.4)
        assert row[2] == ("OK" if ai_status == "OK" else "AI_UNAVAILABLE")
        expected_reason = {
            "OK": None,
            "UNAVAILABLE": "API_UNAVAILABLE",
            "FACT_FAILED": "AI_FACT_CHECK_FAILED",
        }[ai_status]
        assert row[3] == expected_reason
        assert row[4] == side.value  # ADVISORY never rewrites the technical direction.
        assert (
            db.execute("SELECT signal_id FROM journal_events WHERE kind='AI_REVIEW'").fetchone()[0] == row[0]
        )


def test_duplicate_candle_and_reopen_do_not_duplicate_observation(monkeypatch, snapshot):
    import ai_runtime
    import app as api

    data = market(snapshot, Direction.SHORT)
    monkeypatch.setattr(api, "analyze_market", lambda *_: data)
    monkeypatch.setattr(
        ai_runtime,
        "review_analysis",
        lambda current, **_: ai_decision(snapshot, current["technical_signal"], "OK"),
    )
    bot = telegram(api)
    command(bot, "deepseek")
    command(bot, "deepseek")
    report = PaperJournal(journal_path()).report()
    assert report["signals"] == report["ai_ok"] == report["paired_ai_observations"] == 1
    assert report["paper_positions"] == 0
    assert report["net_pnl_usd_closed"] == 0
    with sqlite3.connect(journal_path()) as db:
        assert db.execute("SELECT COUNT(*) FROM observations").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM journal_events WHERE kind='AI_REVIEW'").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM journal_events WHERE kind='AI_RETRY'").fetchone()[0] == 1


def test_api_restart_after_technical_commit_recovers_same_observation(monkeypatch, snapshot):
    import ai_runtime
    import app as api

    data = market(snapshot, Direction.LONG)
    monkeypatch.setattr(api, "analyze_market", lambda *_: data)

    def failure(*_, **__):
        raise RuntimeError("synthetic AI interruption")

    monkeypatch.setattr(ai_runtime, "review_analysis", failure)
    first = api.ai_review("BTCUSDT", "1h", advisory=True)
    assert first["text"] == "AI_UNAVAILABLE: API_ANALYSIS_ERROR"
    assert PaperJournal().report()["signals"] == 1
    assert PaperJournal().report()["ai_not_reviewed"] == 1
    monkeypatch.setattr(
        ai_runtime,
        "review_analysis",
        lambda current, **_: ai_decision(snapshot, current["technical_signal"], "OK"),
    )
    assert "Технический сигнал: LONG" in api.ai_review("BTCUSDT", "1h", advisory=True)["text"]
    reopened = PaperJournal(journal_path()).report()
    assert reopened["signals"] == reopened["ai_ok"] == reopened["paired_ai_observations"] == 1


def test_api_and_telegram_relative_path_same_across_cwd(tmp_path, monkeypatch, snapshot):
    import ai_runtime
    import app as api

    root = Path(__file__).resolve().parents[1]
    relative = os.path.relpath(tmp_path / "shared.sqlite3", root)
    monkeypatch.setenv("PAPER_JOURNAL_PATH", relative)
    api_cwd = tmp_path / "api"
    telegram_cwd = tmp_path / "telegram"
    api_cwd.mkdir()
    telegram_cwd.mkdir()
    data = market(snapshot, Direction.SHORT)
    monkeypatch.setattr(api, "analyze_market", lambda *_: data)
    monkeypatch.setattr(
        ai_runtime,
        "review_analysis",
        lambda current, **_: ai_decision(snapshot, current["technical_signal"], "OK"),
    )
    bot = telegram(api)
    monkeypatch.chdir(api_cwd)
    command(bot, "deepseek")
    monkeypatch.chdir(telegram_cwd)
    output = command(bot, "paper_report", "/paper_report")
    assert journal_path() == (tmp_path / "shared.sqlite3").resolve()
    assert PaperJournal().report()["signals"] == 1
    assert "ВНИМАНИЕ: API и Telegram читают разные" not in output
    assert not (api_cwd / relative).exists()
    assert not (telegram_cwd / relative).exists()


def test_paper_report_warns_when_api_and_telegram_paths_differ(tmp_path, monkeypatch, snapshot):
    import app as api

    api_path = tmp_path / "api.sqlite3"
    telegram_path = tmp_path / "telegram.sqlite3"
    PaperJournal(api_path).record_signal(market(snapshot, Direction.SHORT))
    monkeypatch.setenv("PAPER_JOURNAL_PATH", str(telegram_path))

    class OtherProcess(LocalAPI):
        def get(self, url, *, timeout):
            monkeypatch.setenv("PAPER_JOURNAL_PATH", str(api_path))
            try:
                return super().get(url, timeout=timeout)
            finally:
                monkeypatch.setenv("PAPER_JOURNAL_PATH", str(telegram_path))

    bot = Bot()
    register_ai_handlers(bot, api_client=OtherProcess(api))
    output = command(bot, "paper_report", "/paper_report")
    assert f"Telegram SQLite: {telegram_path}" in output
    assert f"API SQLite: {api_path}" in output
    assert "ВНИМАНИЕ: API и Telegram читают разные PAPER-журналы" in output
    assert PaperJournal().report()["signals"] == 0
    assert PaperJournal(api_path).report()["signals"] == 1


def test_paper_report_keeps_local_counts_when_api_unavailable(snapshot):
    PaperJournal().record_signal(market(snapshot, Direction.SHORT))

    class OfflineAPI:
        def get(self, *_, **__):
            raise ConnectionError("synthetic disconnected API")

    bot = Bot()
    register_ai_handlers(bot, api_client=OfflineAPI())
    output = command(bot, "paper_report", "/paper_report")
    assert "Сигналы/наблюдения 1" in output
    assert "API SQLite: диагностика недоступна" in output


def test_utc_candle_key_and_unfiltered_report(tmp_path, snapshot):
    journal = PaperJournal(tmp_path / "paper.sqlite3")
    data = market(snapshot, Direction.SHORT)
    first = journal.record_signal(data)
    offset = timezone(timedelta(hours=2))
    shifted = data.copy()
    shifted["technical_signal"] = data["technical_signal"].model_copy(
        update={"timestamp": data["technical_signal"].timestamp.astimezone(offset)}
    )
    assert journal.record_signal(shifted) == first
    journal.record_ai(first, ai_decision(snapshot, shifted["technical_signal"], "OK"))
    with sqlite3.connect(journal.path) as db:
        close = db.execute("SELECT candle_close FROM observations WHERE id=?", (first,)).fetchone()[0]
        assert close == data["technical_signal"].timestamp.astimezone(timezone.utc).isoformat()
        db.execute("UPDATE observations SET first_seen=? WHERE id=?", ("2026-01-01T00:00:00+00:00", first))
    assert PaperJournal(journal.path).report()["paired_ai_observations"] == 1
    assert PaperJournal(journal.path).report()["signals"] == 1


def test_revised_signal_on_same_candle_cannot_replace_original(tmp_path, snapshot):
    journal = PaperJournal(tmp_path / "paper.sqlite3")
    original = market(snapshot, Direction.SHORT)
    first = journal.record_signal(original)
    revised = market(snapshot, Direction.LONG)
    with pytest.raises(ValueError, match="Conflicting analysis"):
        journal.record_signal(revised)
    with pytest.raises(ValueError, match="identity mismatch"):
        journal.record_ai(first, ai_decision(snapshot, revised["technical_signal"], "OK"))
    report = PaperJournal(journal.path).report()
    assert report["signals"] == 1
    assert report["signal_directions"]["SHORT"] == 1
    assert report["ai_not_reviewed"] == 1


def test_multiple_symbols_timeframes_get_independent_ids(tmp_path, snapshot):
    journal = PaperJournal(tmp_path / "paper.sqlite3")
    first = journal.record_signal(market(snapshot, Direction.SHORT))
    second = journal.record_signal(market(snapshot, Direction.SHORT, symbol="ETHUSDT"))
    third_data = market(snapshot, Direction.SHORT, timeframe="4h")
    frame = third_data["frame"].copy()
    frame["time"] = pd.date_range(end=frame.time.iloc[-1], periods=len(frame), freq="4h")
    frame["close_time"] = frame.time + timedelta(hours=4) - timedelta(milliseconds=1)
    third_data["frame"] = frame
    third_data["technical_signal"] = third_data["technical_signal"].model_copy(
        update={"timestamp": frame.close_time.iloc[-1].to_pydatetime()}
    )
    third = journal.record_signal(third_data)
    assert len({first, second, third}) == 3
    assert journal.report()["signals"] == 3
