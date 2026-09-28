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
        allowed = {x.strip() for x in os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", "").split(",") if x.strip()}
        return chat is not None and str(chat.id) in allowed

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
                    return
                try:
                    return _fn(message)
                except Exception as exc:
                    logging.getLogger(__name__).error(
                        "Handler %s failed: %s", _fn.__name__, type(exc).__name__
                    )

            getattr(target, kind)(*args, **kwargs)(guarded)

    def __getattr__(self, name):
        if self.target is None:
            raise RuntimeError("Telegram runtime is not configured")
        return getattr(self.target, name)
