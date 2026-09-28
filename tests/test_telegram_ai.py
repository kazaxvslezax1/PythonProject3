import asyncio
from types import SimpleNamespace

from telegram_ai import register_ai_handlers
from test_deepseek import analyzer, response  # noqa: F401


class Bot:
    def __init__(self):
        self.handlers = {}
        self.messages = []

    def message_handler(self, commands):
        def register(fn):
            for c in commands:
                self.handlers[c] = fn
            return fn

        return register

    def reply_to(self, message, text, **kwargs):
        self.messages.append(text)


def test_commands(tmp_path, snapshot):
    bot = Bot()
    a = analyzer(tmp_path, snapshot, lambda req: response())
    register_ai_handlers(bot, analyzer=a, snapshot_loader=lambda *a: snapshot, runner=asyncio.run)
    for cmd in ("deepseek", "ai_signal", "ai_status", "ai_performance"):
        bot.handlers[cmd](SimpleNamespace(text="/" + cmd + " BTCUSDT 1h"))
    output = "\n".join(bot.messages)
    assert "Entry" in output and "AI_MODE=ADVISORY" in output and "not established" in output


def test_unauthorized(tmp_path, snapshot):
    bot = Bot()
    register_ai_handlers(bot, authorized=lambda m: False)
    bot.handlers["ai_status"](SimpleNamespace(text="/ai_status"))
    assert bot.messages == []
