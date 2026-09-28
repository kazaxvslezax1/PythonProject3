import importlib
from types import SimpleNamespace

import pytest


def test_startup_refuses_unrestored_ledger(monkeypatch):
    import final_bot
    import telebot
    import telegram_ai
    import telegram_handlers as handlers

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-placeholder")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "1")
    monkeypatch.setattr(telegram_ai, "register_ai_handlers", lambda *a, **k: None)
    monkeypatch.setattr(handlers.bot, "configure", lambda actual: None)
    monkeypatch.setattr(handlers.auto_trade_manager, "load_data", lambda: False)
    monkeypatch.setattr(telebot, "TeleBot", lambda token: SimpleNamespace())
    with pytest.raises(SystemExit, match="ledger could not be restored"):
        final_bot.main()


def test_import_does_not_poll_or_network(monkeypatch):
    import telebot

    monkeypatch.setattr(
        telebot, "TeleBot", lambda *a, **k: (_ for _ in ()).throw(AssertionError("Bot constructed on import"))
    )
    importlib.import_module("final_bot")
    handlers = importlib.import_module("telegram_handlers")
    assert handlers.bot.target is None
    assert len(handlers.bot.registrations) > 50


def test_api_technical_and_smart(candles, monkeypatch):
    import app
    from analysis_service import analyze_market

    df = candles(n=120)

    def analysis(symbol, tf):
        return analyze_market(
            symbol, tf, df.close_time.iloc[-1].to_pydatetime(), loader=lambda *a, **kw: df.iloc[:-1]
        )

    monkeypatch.setattr(app, "analyze_market", analysis)
    monkeypatch.setenv("AI_MODE", "OFF")
    a = app.analyze("BTCUSDT", "1h")
    b = app.analyze_smart("BTCUSDT")
    assert "error" not in a
    assert a["signal"] == b["signal"]


def test_proxy_authorization_and_duplicates(monkeypatch):
    from telegram_runtime import BotProxy

    proxy = BotProxy()
    seen = []

    @proxy.message_handler(commands=["hello"])
    def hello(message):
        seen.append(message.chat.id)

    @proxy.message_handler(commands=["hello"])
    def duplicate(message):
        raise AssertionError("duplicate")

    from test_telegram_ai import Bot

    actual = Bot()
    proxy.configure(actual)
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "1")
    actual.handlers["hello"](SimpleNamespace(chat=SimpleNamespace(id=2)))
    actual.handlers["hello"](SimpleNamespace(chat=SimpleNamespace(id=1)))
    assert seen == [1]


def test_main_commands_and_monitors_with_mocks(candles, monkeypatch):
    import telegram_handlers as h
    import telegram_signal_commands as commands
    from analysis_service import analyze_market

    df = candles(n=84, slope=0.005)
    df.loc[len(df) - 1, "volume"] = 400
    data = analyze_market(
        "BTCUSDT",
        "1h",
        df.close_time.iloc[-1] + __import__("pandas").Timedelta(milliseconds=1),
        loader=lambda *a, **kw: df,
    )
    sent = []
    monkeypatch.setenv("AI_MODE", "OFF")
    monkeypatch.setattr(commands, "analyze_market", lambda *a, **kw: data)
    monkeypatch.setattr(h.top_coins_manager, "get_top_coins_by_marketcap", lambda n: ["BTCUSDT"])

    class Reply:
        status_code = 200

        def json(self):
            return data

    monkeypatch.setattr(h.requests, "post", lambda *a, **kw: Reply())
    monkeypatch.setattr(h.time, "sleep", lambda *a: None)

    class FakeBot:
        def reply_to(self, m, text, **kwargs):
            sent.append(text)
            return SimpleNamespace(chat=SimpleNamespace(id=1), message_id=1)

        def send_message(self, *args, **kwargs):
            sent.append(str(args))

        def edit_message_text(self, text, **kwargs):
            sent.append(text)

    fake = FakeBot()
    monkeypatch.setattr(h.bot, "target", fake)
    message = SimpleNamespace(text="/analyze BTCUSDT 1h", chat=SimpleNamespace(id=1))
    h.analyze_command(message)
    h.premium_signals_command(message)
    h.live_signals_command(message)
    monitor = h.SimpleMonitor(fake)
    monitor.monitored_symbols = ["BTCUSDT"]
    monitor.monitoring_active = True
    monitor.chat_id = 1
    monitor._check_symbols()
    assert any("LONG" in text for text in sent)
    assert any("RSI=" in text for text in sent)


def test_ai_storage_failure_does_not_change_advisory(snapshot, monkeypatch):
    import ai_runtime
    import deepseek_analyzer
    import pandas as pd

    df = pd.DataFrame([c.model_dump() for c in snapshot.candles])
    analysis = {
        "frame": df,
        "symbol": snapshot.symbol,
        "timeframe": snapshot.timeframe,
        "as_of": snapshot.as_of,
        "technical_signal": snapshot.technical,
    }
    monkeypatch.setattr(ai_runtime, "_worker", None)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    def broken():
        raise OSError("storage blocked")

    monkeypatch.setattr(deepseek_analyzer, "DeepSeekAnalyzer", broken)
    monkeypatch.setenv("AI_MODE", "ADVISORY")
    decision = ai_runtime.review_analysis(analysis)
    assert decision.final == snapshot.technical and decision.ai.status == "AI_UNAVAILABLE"
    monkeypatch.setenv("AI_MODE", "FILTER")
    assert ai_runtime.review_analysis(analysis).final.direction.value == "HOLD"
