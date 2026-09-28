import logging
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from telegram_runtime import (
    SafeTelegramErrors,
    TelegramLogFilter,
    allowed_chat_ids,
    run_polling,
)


@pytest.mark.parametrize("value", ["", " ", "@username", "123;456", "123,", "0"])
def test_invalid_allowlist(value, monkeypatch):
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", value)
    with pytest.raises(ValueError):
        allowed_chat_ids()


def test_allowlist_accepts_private_and_group_ids(monkeypatch):
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", " 123, -100456 ")
    assert allowed_chat_ids() == {123, -100456}


def test_polling_explicitly_subscribes_to_messages(caplog):
    actual = Mock()
    actual.get_webhook_info.return_value.url = ""
    with caplog.at_level(logging.INFO):
        assert run_polling(actual)
    actual.get_me.assert_called_once_with()
    actual.get_webhook_info.assert_called_once_with(timeout=10)
    assert actual.infinity_polling.call_args.kwargs["allowed_updates"] == ["message", "callback_query"]
    assert actual.infinity_polling.call_args.kwargs["skip_pending"] is False
    assert "authentication succeeded" in caplog.text
    assert "polling starting" in caplog.text
    assert "polling stopped" in caplog.text


def test_active_webhook_is_reported_without_disclosing_url(caplog):
    actual = Mock()
    actual.get_webhook_info.return_value.url = "https://private.example/secret-path"
    assert not run_polling(actual)
    actual.infinity_polling.assert_not_called()
    assert "active webhook" in caplog.text
    assert "secret-path" not in caplog.text


@pytest.mark.parametrize("operation", ["get_me", "get_webhook_info", "infinity_polling"])
def test_polling_errors_do_not_disclose_token(operation, caplog):
    actual = Mock()
    actual.get_webhook_info.return_value.url = ""
    error = RuntimeError("https://api.telegram.org/botPRIVATE_TOKEN/getUpdates")
    error.error_code = 409
    getattr(actual, operation).side_effect = error
    assert not run_polling(actual)
    assert "code=409" in caplog.text and "another polling process" in caplog.text
    assert "PRIVATE_TOKEN" not in caplog.text


def test_library_log_filter_removes_token_and_traceback():
    record = logging.LogRecord("TeleBot", logging.ERROR, "", 0, "request %s", ("private-token",), None)
    record.exc_text = "traceback with private-token"
    record.stack_info = "private-token"
    assert TelegramLogFilter("private-token").filter(record)
    assert "private-token" not in record.getMessage()
    assert record.exc_text is None and record.stack_info is None


def test_polling_error_handler_preserves_backoff(caplog, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "private-token")
    assert SafeTelegramErrors().handle(TimeoutError("private-token")) is False
    assert "TimeoutError" in caplog.text
    assert "private-token" not in caplog.text


def test_actual_start_dispatch_and_rejected_chat(monkeypatch, caplog):
    import telebot
    import telegram_handlers as handlers

    actual = telebot.TeleBot("123:placeholder", threaded=False)
    sent = []
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "42")
    monkeypatch.setattr(actual, "send_message", lambda chat_id, text, **kw: sent.append((chat_id, text)))
    monkeypatch.setattr(handlers.bot, "target", None)
    handlers.bot.configure(actual)

    def update(chat_id):
        return telebot.types.Update.de_json(
            {
                "update_id": chat_id,
                "message": {
                    "message_id": 1,
                    "date": 1,
                    "chat": {"id": chat_id, "type": "private"},
                    "text": "/start",
                },
            }
        )

    with caplog.at_level(logging.INFO):
        actual.process_new_updates([update(42), update(43)])
    assert len(sent) == 1 and sent[0][0] == 42
    assert "/analyze" in sent[0][1]
    assert "send_welcome started" in caplog.text
    assert "chat_id=43 is not in TELEGRAM_ALLOWED_CHAT_IDS" in caplog.text


def test_handler_error_logs_safe_code(monkeypatch, caplog):
    from telegram_runtime import BotProxy
    from test_telegram_ai import Bot

    proxy = BotProxy()
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "private-token")
    error = RuntimeError("private-token")
    error.error_code = 403

    @proxy.message_handler(commands=["start"])
    def start(message):
        raise error

    actual = Bot()
    proxy.configure(actual)
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "42")
    actual.handlers["start"](SimpleNamespace(chat=SimpleNamespace(id=42)))
    assert "code=403" in caplog.text and "private-token" not in caplog.text


def test_main_reaches_polling_without_background_work(monkeypatch):
    import final_bot
    import telebot
    import telegram_ai
    import telegram_handlers as handlers
    import telegram_runtime

    actual = SimpleNamespace()
    run = Mock(return_value=True)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "placeholder")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "42")
    monkeypatch.setattr(telebot, "TeleBot", lambda token: actual)
    monkeypatch.setattr(telegram_ai, "register_ai_handlers", lambda *a, **kw: None)
    monkeypatch.setattr(handlers.bot, "configure", lambda bot: None)
    monkeypatch.setattr(handlers.auto_trade_manager, "load_data", lambda: True)
    monkeypatch.setattr(telegram_runtime, "run_polling", run)
    final_bot.main()
    run.assert_called_once_with(actual)
    assert isinstance(actual.exception_handler, SafeTelegramErrors)


def test_real_telebot_reproduces_bad_keyword_then_reaches_getupdates(monkeypatch):
    import json

    import telebot
    from telebot import apihelper

    actual = telebot.TeleBot("123:placeholder", threaded=False)
    calls = []

    def transport(method, url, **kwargs):
        name = url.rsplit("/", 1)[-1]
        calls.append((name, kwargs))
        if name == "getMe":
            result = {"id": 123, "is_bot": True, "first_name": "Test", "username": "test_bot"}
        elif name == "getWebhookInfo":
            result = {"url": "", "has_custom_certificate": False, "pending_update_count": 0}
        elif name == "getUpdates":
            actual.stop_polling()
            result = []
        else:
            raise AssertionError("Unexpected Telegram method")
        payload = {"ok": True, "result": result}
        return SimpleNamespace(status_code=200, text=json.dumps(payload), json=lambda: payload)

    monkeypatch.setattr(apihelper, "CUSTOM_REQUEST_SENDER", transport)
    monkeypatch.setattr(apihelper, "CONNECT_TIMEOUT", 15)
    monkeypatch.setattr(apihelper, "READ_TIMEOUT", 30)
    # Reproduce the exact regression against the real installed library, before HTTP.
    with pytest.raises(TypeError, match="unexpected keyword argument 'timeout'"):
        actual.get_me(timeout=10)
    assert calls == []
    # Exercise real get_me, get_webhook_info AND infinity_polling, only HTTP is fake.
    assert run_polling(actual)
    assert [name for name, _ in calls] == ["getMe", "getWebhookInfo", "getMe", "getUpdates"]
    assert all(kwargs["timeout"] == (10, 10) for name, kwargs in calls if name != "getUpdates")
    updates = calls[-1][1]
    assert updates["timeout"] == (20, 25)
    assert json.loads(updates["params"]["allowed_updates"]) == ["message", "callback_query"]


def test_traceback_preserves_frames_and_chain_without_secrets(monkeypatch, caplog):
    from telegram_runtime import log_telegram_error

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-telegram-value")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-value")
    monkeypatch.setenv("DATABASE_PASSWORD", "test-database-value")

    def inner_failure():
        raise ValueError("test-telegram-value test-deepseek-value test-database-value password=hidden")

    try:
        try:
            inner_failure()
        except ValueError as cause:
            raise TypeError("unexpected keyword argument 'timeout'") from cause
    except TypeError as exc:
        log_telegram_error("test", exc)
    assert "Traceback (most recent call last)" in caplog.text
    assert "inner_failure" in caplog.text and "test_telegram_runtime.py" in caplog.text
    assert "direct cause" in caplog.text
    assert "unexpected keyword argument 'timeout'" in caplog.text
    for value in ("test-telegram-value", "test-deepseek-value", "test-database-value", "password=hidden"):
        assert value not in caplog.text


def test_library_filter_preserves_sanitized_exception_frames():
    try:
        raise TypeError("unexpected keyword argument 'timeout'; password=hidden")
    except TypeError as exc:
        record = logging.LogRecord(
            "TeleBot", logging.ERROR, "", 0, "failure", (), (type(exc), exc, exc.__traceback__)
        )
    TelegramLogFilter("").filter(record)
    assert "Traceback (most recent call last)" in record.getMessage()
    assert "unexpected keyword argument 'timeout'" in record.getMessage()
    assert "hidden" not in record.getMessage()
    assert record.exc_info is None
