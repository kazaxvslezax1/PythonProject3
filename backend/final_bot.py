"""Entrypoint for the existing Telegram bot. No polling/network at import."""

import logging
import os


def main():
    from telegram_runtime import SafeTelegramErrors, TelegramLogFilter, allowed_chat_ids, run_polling

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN in the run environment")
    try:
        allowed = allowed_chat_ids()
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    import telebot
    import telegram_handlers as handlers
    from paper_journal import PaperJournal
    from telegram_ai import register_ai_handlers

    telebot.logger.addFilter(TelegramLogFilter(token))
    logging.getLogger(__name__).info("Telegram configuration: token present; allowed chats=%s", len(allowed))
    register_ai_handlers(handlers.bot, authorized=handlers.bot.authorized)
    actual = telebot.TeleBot(token)
    actual.exception_handler = SafeTelegramErrors()
    handlers.bot.configure(actual)
    handlers.auto_trade_manager.journal = PaperJournal()
    if not handlers.auto_trade_manager.load_data():
        raise SystemExit("Paper ledger could not be restored; inspect storage before restarting")
    if handlers.auto_trade_manager.get_active_positions():
        handlers.auto_trade_manager.start_monitoring()
    logging.getLogger(__name__).info("Paper-only bot starting; background scanners require explicit commands")
    if not run_polling(actual):
        raise SystemExit("Telegram polling failed; see safe diagnostics above")


if __name__ == "__main__":
    main()
