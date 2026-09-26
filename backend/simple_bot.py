import requests
import telebot

# Токен бота (ЗАМЕНИ НА СВОЙ!)
TELEGRAM_TOKEN = "8238637250:AAE-jXOQgJ9LhlZAd5Rj105ekna6UC_BgFY"
API_URL = "http://127.0.0.1:8000"

# Создаем бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Главное меню бота"""
    try:
        welcome_text = """
🤖 *Crypto Trading Assistant* 🚀

🎯 *ДОБРО ПОЖАЛОВАТЬ В AI-ТРЕЙДИНГ!*

✨ *БЫСТРЫЙ СТАРТ:*
/ai_help - 📖 Основные команды для начинающих
/pro_help - 🚀 PRO команды для опытных

⚡ *САМОЕ ВАЖНОЕ:*
/activate_all - ✅ Запустить все системы
/trading_ideas - 💡 Готовые торговые идеи
/consensus SYMBOL - 🎯 Проверить надежность

📊 *БЫСТРЫЙ АНАЛИЗ:*
/analyze_smart BTCUSDT - 🔎 Умный анализ
/trend ETHUSDT - 📉 Анализ тренда
/volume_scan - 📈 Сканер объемов

💡 *СОВЕТ ДЛЯ НОВИЧКА:*
1. Начните с /ai_help - узнайте основные команды
2. Используйте /consensus для проверки сигналов
3. Входите только при AI уверенности ≥7.0

*Примеры:*
/analyze_smart btcusdt
/trend ethusdt  
/consensus solusdt
/ai_help

🎊 *Удачи в торговле!* 💰
"""
        bot.reply_to(message, welcome_text, parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['ai_help'])
def ai_help_command(message):
    """Основные команды для новичков - простая версия"""
    try:
        help_text = """
🟢 *ОСНОВНЫЕ КОМАНДЫ ДЛЯ НАЧИНАЮЩИХ* 🟢

🤖 *БЫСТРЫЙ СТАРТ:*
/activate_all - ✅ Запустить ВСЕ системы
/deactivate_all - ❌ Остановить ВСЕ системы  
/ai_help - 📖 Это меню помощи

🎯 *ПОИСК СИГНАЛОВ:*
/trading_ideas - 💡 Готовые торговые идеи
/volume_scan - 📊 Сканер всплесков объемов  
/anomaly - 🔍 Активные аномалии
/ai_recommendations - 🤖 AI рекомендации

📈 *АНАЛИЗ И ВХОД:*
/analyze_smart SYMBOL - 🔎 Умный анализ монеты
/advanced_targets SYMBOL - 🎯 Цели с Фибо
/trend SYMBOL - 📉 Анализ тренда
/risk SYMBOL БАЛАНС 2 - ⚡ Расчет риска

✅ *ПРОВЕРКА НАДЕЖНОСТИ:*
/consensus SYMBOL - 🎯 Несколько подтверждений

⚡ *ПРИМЕРЫ ДЛЯ НАЧАЛА:*
/analyze_smart BTCUSDT
/trend ETHUSDT  
/risk SOLUSDT 1000 2
/consensus BTCUSDT

💡 *СОВЕТ ДЛЯ НОВИЧКА:*
Всегда начинайте с /consensus SYMBOL 
Если консенсус ≥50% - тогда /advanced_targets SYMBOL
Если AI <7.0 - ❌ ПРОПУСТИТЕ сделку!

🚀 *ДЛЯ ОПЫТНЫХ:*
/pro_help - Показать PRO команды

*Пример: /ai_help*
"""
        bot.reply_to(message, help_text, parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['pro_help'])
def pro_help_command(message):
    """PRO команды для опытных пользователей"""
    try:
        pro_text = """
🚀 *PRO COMMANDS - ДЛЯ ОПЫТНЫХ ТРЕЙДЕРОВ* 🚀

💎 *АВТО-МОНИТОРИНГ ПРЕМИУМ СИГНАЛОВ:*
/premium_monitor_start - Запуск авто-сканирования
/premium_monitor_stop - Остановка мониторинга
/premium_monitor_status - Статус мониторинга
/premium_signals - Разовое сканирование

🤖 *AI-СУПЕРАНАЛИТИКА (НОВОЕ):*
/crypto_ai_master - 🤖 Полный анализ от AI-мастера
/ai_market_status - 📊 Глубокая диагностика рынка
/risk_dashboard - 🎯 Панель управления рисками
/quick_ai_scan - ⚡ Быстрый анализ за 10 сек
/instant_scan - 🚀 Мгновенный скан (кэш)
/ai_scan_volume - 📈 Только проверенные объемы

🔍 *АВТО-СКРИНЕР АНОМАЛИЙ:*
/anomaly_start - Детектор аномалий
/anomaly_stop - Остановка детектора
/anomaly_status - Статус аномалий

--Фазы рынка-- УМНЫЕ УВЕДОМЛЕНИЯ:
/market_phase_start - Мониторинг рыночных фаз
/market_phase_stop - Остановка мониторинга
/market_phase_status - Статус фаз

📊 *AI-ПРЕДСКАЗАНИЕ ВОЛАТИЛЬНОСТИ:*
/volatility_prediction SYMBOL - Прогноз волатильности
/market_sessions - Расписание торговых сессий
/volatility_scan - Сканер волатильности топ-монет

🚀 *АВТО-МОНИТОРИНГ ОБЪЕМОВ:*
/volume_monitor_start - Запуск авто-сканирования
/volume_monitor_popular - Мониторинг топ-20 монет
/volume_monitor_stop - Остановка мониторинга
/volume_monitor_status - Статус мониторинга

🎯 *УМНЫЕ ТЕЙК-ПРОФИТЫ:*
/smart_tp_start - Умное управление позициями
/smart_tp_stop - Остановка управления
/smart_tp_status - Статус позиций
/smart_tp_add - Добавить позицию

🌍 *SMART-ФИЛЬТРЫ ДЛЯ СЕССИЙ:*
/session_filters_start - Автокорректировка фильтров
/session_filters_stop - Остановка корректировки
/session_filters_status - Текущие настройки
/session_filters_info - Подробности о системе

📈 *РАСШИРЕННЫЕ ФУНКЦИИ:*
/ai_scan - Сканирование топ-10 монет
/smart_scan - Умное сканирование (только качественные)
/confluence - Сканирование конфлюэнса
/backtest SYMBOL - Бэктестинг стратегии
/best_opportunity - Лучшая возможность сейчас
/prediction_history SYMBOL - История прогнозов
/live_signals - Активные сигналы в реальном времени

📋 *АВТОМАТИЧЕСКИЕ ОТЧЕТЫ:*
/reports_daily - Ежедневные торговые отчеты
/reports_weekly - Еженедельные аналитические отчеты
/reports_stop - Остановка всех отчетов
/reports_status - Статус системы отчетов
/report_now - Мгновенный отчет

📊 *ОСНОВНЫЕ КОМАНДЫ:*
/better_targets SYMBOL - Улучшенные цели
/simple_confluence SYMBOL - Конфлюэнс анализ
/market_overview - Обзор рынка
/analyze SYMBOL TIMEFRAME - Анализ монеты
/chart SYMBOL TIMEFRAME - График цены
/predict SYMBOL - AI прогноз цены
/targets SYMBOL - Цели и стоп-лосс

🔔 *АВТО-МОНИТОРИНГ:*
/monitor_extended - Мониторинг топ-20
/monitor_quality - Мониторинг только качественных
/monitor_stop - Остановка мониторинга
/monitor_status - Статус мониторинга

/ai_help - 🔙 Вернуться к основным командам

*Пример: /pro_help*
"""
        bot.reply_to(message, pro_text, parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['analyze'])
def analyze_command(message):
    try:
        text = message.text.split()
        if len(text) < 3:
            bot.reply_to(message, "❌ Используйте: /analyze symbol timeframe")
            return

        symbol = text[1].lower()
        timeframe = text[2].lower()

        bot.reply_to(message, f"🔍 Анализирую {symbol.upper()} на {timeframe}...")

        response = requests.post(f"{API_URL}/analyze", params={
            "symbol": symbol,
            "timeframe": timeframe
        })

        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                bot.reply_to(message, f"❌ {data['error']}")
            else:
                result = f"""
📊 {data.get('symbol', '').upper()} ({data.get('timeframe', '')})
Рекомендация: {data.get('recommendation', data.get('strategy', 'N/A'))}
Доходность: {data.get('backtest_return_%', 'N/A')}%
Цена: ${data.get('last_price', 'N/A'):.2f}
"""
                bot.reply_to(message, result)
        else:
            bot.reply_to(message, "❌ Ошибка API")

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


@bot.message_handler(commands=['analyze_smart'])
def analyze_smart_command(message):
    try:
        text = message.text.split()
        if len(text) < 2:
            bot.reply_to(message, "❌ Используйте: /analyze_smart symbol")
            return

        symbol = text[1].lower()

        bot.reply_to(message, f"🧠 Умный анализ {symbol.upper()}...")

        response = requests.post(f"{API_URL}/analyze-smart", params={"symbol": symbol})

        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                bot.reply_to(message, f"❌ {data['error']}")
            else:
                result = f"""
🧠 {data.get('symbol', '').upper()} - Умный анализ
Лучший ТФ: {data.get('best_timeframe', 'N/A')}
Доходность: {data.get('backtest_return_%', 'N/A')}%
Рекомендация: {data.get('recommendation', 'N/A')}
Цена: ${data.get('last_price', 'N/A'):.2f}
"""
                bot.reply_to(message, result)
        else:
            bot.reply_to(message, "❌ Ошибка API")

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


print("🤖 Простой бот запущен...")
bot.infinity_polling()