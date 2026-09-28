"""Deferred Telegram registration, authorization and guarded handlers."""

import functools
import logging
import os


class BotProxy:
    def __init__(self):
        self.target = None
        self.registrations = []

    def message_handler(self, *args, **kwargs):
        return self._register("message_handler", args, kwargs)

    def callback_query_handler(self, *args, **kwargs):
        return self._register("callback_query_handler", args, kwargs)

    def _register(self, kind, args, kwargs):
        def decorator(fn):
            self.registrations.append((kind, args, kwargs, fn))
            return fn

        return decorator

    def authorized(self, message):
        chat = getattr(message, "chat", None)
        if chat is None:
            chat = getattr(getattr(message, "message", None), "chat", None)
        try:
            return chat is not None and int(chat.id) in allowed_chat_ids()
        except (ValueError, TypeError):
            return False

    def configure(self, target):
        self.target = target
        seen = set()
        for kind, args, kwargs, fn in self.registrations:
            commands = kwargs.get("commands", [])
            if (
                any(c.startswith(("debug", "test_", "force_")) for c in commands)
                and os.environ.get("ENABLE_DIAGNOSTICS") != "1"
            ):
                continue
            # First registered route remains canonical; avoid duplicate handlers.
            if commands:
                commands = [c for c in commands if c not in seen]
                if not commands:
                    continue
                seen.update(commands)
                kwargs = {**kwargs, "commands": commands}

            @functools.wraps(fn)
            def guarded(message, _fn=fn):
                if not self.authorized(message):
                    chat = getattr(message, "chat", None) or getattr(
                        getattr(message, "message", None), "chat", None
                    )
                    chat_id = getattr(chat, "id", None)
                    logging.getLogger(__name__).warning(
                        "Telegram update rejected: chat_id=%s is not in TELEGRAM_ALLOWED_CHAT_IDS",
                        chat_id if isinstance(chat_id, int) else "unknown",
                    )
                    return
                try:
                    logging.getLogger(__name__).info("Telegram handler %s started", _fn.__name__)
                    return _fn(message)
                except Exception as exc:
                    log_telegram_error("handler " + _fn.__name__, exc)

            getattr(target, kind)(*args, **kwargs)(guarded)
        logging.getLogger(__name__).info(
            "Telegram routes registered: commands=%s start=%s", len(seen), "start" in seen
        )

    def __getattr__(self, name):
        if self.target is None:
            raise RuntimeError("Telegram runtime is not configured")
        return getattr(self.target, name)


def allowed_chat_ids():
    """Reject configuration mistakes without echoing environment values."""
    raw = os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", "")
    parts = raw.split(",")
    if not raw.strip() or any(not p.strip().lstrip("-").isdigit() for p in parts):
        raise ValueError("TELEGRAM_ALLOWED_CHAT_IDS must contain numeric chat IDs separated by commas")
    ids = {int(p.strip()) for p in parts}
    if 0 in ids:
        raise ValueError("TELEGRAM_ALLOWED_CHAT_IDS cannot contain zero")
    return ids


def log_telegram_error(operation, exc):
    code = getattr(exc, "error_code", None)
    code = code if isinstance(code, int) else None
    hint = {
        401: "check TELEGRAM_BOT_TOKEN",
        403: "bot cannot access this chat",
        409: "check another polling process or active webhook",
        429: "Telegram rate limit; wait before retry",
    }.get(code, "check network or Telegram request configuration")
    logging.getLogger(__name__).error(
        "Telegram %s failed: type=%s code=%s; %s", operation, type(exc).__name__, code, hint
    )


class SafeTelegramErrors:
    def handle(self, exc):
        log_telegram_error("polling", exc)
        return False  # Preserve library retry/backoff behavior.


class TelegramLogFilter(logging.Filter):
    """Redact library messages too: URLs and exception strings can contain tokens."""

    def __init__(self, token):
        super().__init__()
        self.token = token

    def filter(self, record):
        import re

        message = record.getMessage()
        if self.token:
            message = message.replace(self.token, "[REDACTED]")
        record.msg = re.sub(r"\b\d{5,}:[A-Za-z0-9_-]{20,}\b", "[REDACTED]", message)
        record.args = ()
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        return True


def run_polling(actual):
    logger = logging.getLogger(__name__)
    try:
        logger.info("Telegram connection check starting (getMe, timeout=10s)")
        actual.get_me(timeout=10)
        logger.info("Telegram authentication succeeded; checking webhook (timeout=10s)")
        webhook = actual.get_webhook_info(timeout=10)
        if webhook.url:
            logger.error(
                "Telegram polling blocked: active webhook; review webhook configuration before polling"
            )
            return False
        logger.info("Telegram polling starting: message,callback_query; pending updates preserved")
        actual.infinity_polling(
            timeout=20,
            long_polling_timeout=20,
            allowed_updates=["message", "callback_query"],
            skip_pending=False,
            logger_level=logging.ERROR,
        )
        return True
    except Exception as exc:
        log_telegram_error("startup/polling", exc)
        return False
    finally:
        logger.info("Telegram polling stopped")
