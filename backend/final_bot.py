"""Entrypoint for the existing Telegram bot. No polling/network at import."""

import logging
import os


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN in the run environment")
    if not os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS"):
        raise SystemExit("Set TELEGRAM_ALLOWED_CHAT_IDS to your authorized chat IDs")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    import telebot
    import telegram_handlers as handlers
    from telegram_ai import register_ai_handlers

    register_ai_handlers(handlers.bot, authorized=handlers.bot.authorized)
    actual = telebot.TeleBot(token)
    handlers.bot.configure(actual)
    if not handlers.auto_trade_manager.load_data():
        raise SystemExit("Paper ledger could not be restored; inspect storage before restarting")
    logging.getLogger(__name__).info("Paper-only bot starting; background scanners require explicit commands")
    actual.infinity_polling(timeout=20, long_polling_timeout=20)


if __name__ == "__main__":
    main()
