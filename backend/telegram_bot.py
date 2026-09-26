import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Токен бота (ЗАМЕНИ НА СВОЙ ТОКЕН!)
TELEGRAM_TOKEN = "8238637250:AAE-jXOQgJ9LhlZAd5Rj105ekna6UC_BgFY"

# URL твоего FastAPI сервера
API_URL = "http://127.0.0.1:8000"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = """
🤖 *Crypto Trading Assistant*

*Доступные команды:*
/analyze symbol timeframe - Анализ монеты
/analyze_smart symbol - Умный анализ

*Примеры:*
/analyze btcusd 15m
/analyze_smart ethusd
/analyze solusd 1h

*Поддерживаемые таймфреймы:*
1m, 5m, 15m, 30m, 1h, 6h, 1d

*Поддерживаемые монеты:*
btcusd, ethusd, solusd, linkusd
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /analyze"""
    try:
        if len(context.args) < 2:
            await update.message.reply_text("❌ Используйте: /analyze symbol timeframe\nНапример: /analyze btcusd 15m")
            return

        symbol = context.args[0].lower()
        timeframe = context.args[1].lower()

        # Отправляем сообщение о начале анализа
        wait_msg = await update.message.reply_text(f"🔍 Анализирую {symbol.upper()} на таймфрейме {timeframe}...")

        # Делаем запрос к нашему API
        response = requests.post(f"{API_URL}/analyze", params={
            "symbol": symbol,
            "timeframe": timeframe
        })

        if response.status_code == 200:
            data = response.json()

            # Форматируем красивый ответ
            message = format_analysis_message(data)
            await wait_msg.edit_text(message, parse_mode='Markdown')

        else:
            await wait_msg.edit_text("❌ Ошибка при анализе. Попробуйте другой символ или таймфрейм.")

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


async def analyze_smart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /analyze_smart"""
    try:
        if len(context.args) < 1:
            await update.message.reply_text("❌ Используйте: /analyze_smart symbol\nНапример: /analyze_smart btcusd")
            return

        symbol = context.args[0].lower()

        # Отправляем сообщение о начале анализа
        wait_msg = await update.message.reply_text(f"🧠 Запускаю умный анализ для {symbol.upper()}...")

        # Делаем запрос к нашему API
        response = requests.post(f"{API_URL}/analyze-smart", params={
            "symbol": symbol
        })

        if response.status_code == 200:
            data = response.json()

            # Форматируем красивый ответ
            message = format_smart_analysis_message(data)
            await wait_msg.edit_text(message, parse_mode='Markdown')

        else:
            await wait_msg.edit_text("❌ Ошибка при анализе. Попробуйте другой символ.")

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


def format_analysis_message(data):
    """Форматирует сообщение для обычного анализа"""
    if "error" in data:
        return f"❌ Ошибка: {data['error']}"

    # Определяем эмодзи для действия
    action_emoji = {
        "BUY": "🟢",
        "SELL": "🔴",
        "HOLD": "🟡"
    }.get(data.get('action', 'HOLD'), '⚪')

    message = f"""
{action_emoji} *Анализ {data.get('symbol', 'N/A').upper()} ({data.get('timeframe', 'N/A')})*

*Рекомендация:* {data.get('recommendation', data.get('strategy', 'N/A'))}
*Действие:* {data.get('action', 'N/A')} 
*Сила сигнала:* {data.get('strength', 'N/A')}/10

📊 *Сигналы:*
{data.get('signals', 'N/A')}

📈 *Результаты:*
💰 Цена: ${data.get('last_price', 'N/A'):.2f}
📊 Доходность: {data.get('backtest_return_%', 'N/A')}%
🕯️ Кол-во свечей: {data.get('candles_count', 'N/A')}
"""
    return message


def format_smart_analysis_message(data):
    """Форматирует сообщение для умного анализа"""
    if "error" in data:
        return f"❌ Ошибка: {data['error']}"

    # Определяем эмодзи для действия
    action_emoji = {
        "BUY": "🟢",
        "SELL": "🔴",
        "HOLD": "🟡"
    }.get(data.get('action', 'HOLD'), '⚪')

    message = f"""
{action_emoji} *Умный анализ {data.get('symbol', 'N/A').upper()}*

🎯 *Лучший таймфрейм:* {data.get('best_timeframe', 'N/A')}
📈 *Лучшая доходность:* {data.get('best_return_%', 'N/A')}%
💰 *Текущая доходность:* {data.get('backtest_return_%', 'N/A')}%

*Рекомендация:* {data.get('recommendation', 'N/A')}
*Действие:* {data.get('action', 'N/A')}
*Сила сигнала:* {data.get('strength', 'N/A')}/10

📊 *Сигналы:*
{data.get('signals', 'N/A')}

💎 *Детали:*
💰 Цена: ${data.get('last_price', 'N/A'):.2f}
🕐 Протестированные ТФ: {', '.join(data.get('tested_timeframes', []))}
"""
    return message


def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("analyze_smart", analyze_smart_command))

    # Запускаем бота
    print("🤖 Telegram бот запущен...")
    print("⏳ Ожидаю сообщения...")

    application.run_polling()


if __name__ == "__main__":
    main()