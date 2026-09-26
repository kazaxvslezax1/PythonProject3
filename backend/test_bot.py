import telebot
import requests
import time

# ТВОЙ ТОКЕН (замени на настоящий!)
TELEGRAM_TOKEN = "8238637250:AAE-jXOQgJ9LhlZAd5Rj105ekna6UC_BgFY"

# Создаем бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)


@bot.message_handler(commands=['start', 'test'])
def send_welcome(message):
    print(f"📨 Получено сообщение: {message.text}")
    bot.reply_to(message, "🤖 Бот работает! Отправь /check для проверки API")


@bot.message_handler(commands=['check'])
def check_api(message):
    print("🔍 Проверяем API...")

    try:
        # Проверяем доступность сервера
        response = requests.get("http://127.0.0.1:8000/", timeout=5)

        if response.status_code == 200:
            bot.reply_to(message, "✅ Сервер работает! API доступен")
            print("✅ Сервер доступен")
        else:
            bot.reply_to(message, f"❌ Сервер недоступен. Код: {response.status_code}")
            print(f"❌ Сервер недоступен: {response.status_code}")

    except requests.exceptions.ConnectionError:
        bot.reply_to(message, "❌ Не могу подключиться к серверу. Запущен ли uvicorn?")
        print("❌ Ошибка подключения к серверу")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
        print(f"❌ Ошибка: {e}")


@bot.message_handler(commands=['analyze'])
def analyze_test(message):
    print(f"🔍 Анализ запрошен: {message.text}")

    try:
        text_parts = message.text.split()
        if len(text_parts) < 3:
            bot.reply_to(message, "❌ Используйте: /analyze btcusd 15m")
            return

        symbol = text_parts[1]
        timeframe = text_parts[2]

        bot.reply_to(message, f"🔍 Анализирую {symbol} на {timeframe}...")
        print(f"🔍 Запрос анализа: {symbol} {timeframe}")

        # Пробуем сделать запрос к API
        response = requests.post(
            "http://127.0.0.1:8000/analyze",
            params={"symbol": symbol, "timeframe": timeframe},
            timeout=10
        )

        print(f"📡 Статус ответа API: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"📊 Данные получены: {data}")

            if "error" in data:
                bot.reply_to(message, f"❌ Ошибка анализа: {data['error']}")
            else:
                result = f"""
📊 Анализ {data.get('symbol', 'N/A')} ({data.get('timeframe', 'N/A')})

💰 Цена: ${data.get('last_price', 'N/A')}
📈 Доходность: {data.get('backtest_return_%', 'N/A')}%
📊 Свечей: {data.get('candles_count', 'N/A')}

Рекомендация: {data.get('recommendation', data.get('strategy', 'N/A'))}
"""
                bot.reply_to(message, result)
        else:
            bot.reply_to(message, f"❌ Ошибка API: {response.status_code}")
            print(f"❌ Текст ошибки: {response.text}")

    except Exception as e:
        error_msg = f"❌ Ошибка: {e}"
        bot.reply_to(message, error_msg)
        print(error_msg)


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    print(f"📨 Получено сообщение: {message.text}")
    bot.reply_to(message, f"🤖 Получил: {message.text}\nИспользуй /start для справки")


print("🤖 Тестовый бот запускается...")
print("📡 Ожидаю сообщения...")

try:
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
except Exception as e:
    print(f"❌ Ошибка запуска бота: {e}")