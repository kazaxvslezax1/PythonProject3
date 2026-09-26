import asyncio
import requests
import schedule
import time
import threading
from datetime import datetime
from typing import Dict, List


class TradingAlertSystem:
    def __init__(self, bot):
        self.bot = bot
        self.monitoring_active = False
        self.monitored_symbols = []
        self.chat_id = None
        self.alerted_signals = {}  # Для избежания спама

    def start_monitoring(self, chat_id: int, symbols: List[str], check_interval_minutes: int = 5):
        """Запускает мониторинг выбранных монет"""
        self.chat_id = chat_id
        self.monitored_symbols = symbols
        self.monitoring_active = True

        # Запускаем в отдельном потоке
        monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(check_interval_minutes,),
            daemon=True
        )
        monitor_thread.start()

        return f"✅ Мониторинг запущен для: {', '.join(symbols)}\n⏰ Проверка каждые {check_interval_minutes} минут"

    def stop_monitoring(self):
        """Останавливает мониторинг"""
        self.monitoring_active = False
        return "⏹️ Мониторинг остановлен"

    def _monitoring_loop(self, check_interval_minutes: int):
        """Основной цикл мониторинга"""
        check_interval_seconds = check_interval_minutes * 60

        while self.monitoring_active:
            try:
                self._check_all_symbols()
                time.sleep(check_interval_seconds)
            except Exception as e:
                print(f"❌ Ошибка в мониторинге: {e}")
                time.sleep(60)  # Ждём минуту при ошибке

    def _check_all_symbols(self):
        """Проверяет все отслеживаемые символы"""
        strong_signals = []

        for symbol in self.monitored_symbols:
            try:
                signal = self._analyze_symbol(symbol)
                if signal and self._is_strong_signal(signal):
                    strong_signals.append(signal)

                # Пауза между запросами к API
                time.sleep(1)

            except Exception as e:
                print(f"❌ Ошибка анализа {symbol}: {e}")

        # Отправляем уведомления
        if strong_signals:
            self._send_alerts(strong_signals)

    def _analyze_symbol(self, symbol: str) -> Dict:
        """Анализирует один символ и возвращает сигнал"""
        try:
            # Используем умный анализ
            response = requests.post(
                "http://127.0.0.1:8000/analyze-smart",
                params={"symbol": symbol.lower()},
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()

                # Проверяем на ошибки
                if "error" in data:
                    return None

                # Создаем уникальный ключ для сигнала
                signal_key = f"{symbol}_{data.get('action')}_{data.get('best_timeframe')}"

                # Проверяем, не отправляли ли уже этот сигнал
                current_strength = data.get('strength', 0)
                if (signal_key not in self.alerted_signals or
                        self.alerted_signals[signal_key] != current_strength):
                    # Обновляем запись
                    self.alerted_signals[signal_key] = current_strength

                    return {
                        "symbol": symbol,
                        "action": data.get('action'),
                        "strength": current_strength,
                        "recommendation": data.get('recommendation'),
                        "best_timeframe": data.get('best_timeframe'),
                        "price": data.get('last_price'),
                        "returns": data.get('backtest_return_%'),
                        "signals": data.get('signals', '')
                    }

        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка запроса для {symbol}: {e}")
        except Exception as e:
            print(f"❌ Неожиданная ошибка для {symbol}: {e}")

        return None

    def _is_strong_signal(self, signal: Dict) -> bool:
        """Определяет, является ли сигнал достаточно сильным для уведомления"""
        strength = signal.get('strength', 0)
        action = signal.get('action', '')

        # Сильные сигналы на покупку/продажу
        if action in ['BUY', 'SELL'] and abs(strength) >= 3:
            return True

        # Очень сильные сигналы
        if abs(strength) >= 4:
            return True

        return False

    def _send_alerts(self, signals: List[Dict]):
        """Отправляет уведомления о сильных сигналах"""
        for signal in signals:
            try:
                alert_message = self._format_alert_message(signal)

                # Отправляем сообщение
                asyncio.run_coroutine_threadsafe(
                    self._async_send_alert(alert_message),
                    asyncio.get_event_loop()
                )

                print(f"✅ Отправлен алерт для {signal['symbol']}")

            except Exception as e:
                print(f"❌ Ошибка отправки алерта для {signal['symbol']}: {e}")

    def _format_alert_message(self, signal: Dict) -> str:
        """Форматирует сообщение уведомления"""
        symbol = signal['symbol']
        action = signal['action']
        strength = signal['strength']

        # Выбираем эмодзи и заголовок
        if action == 'BUY':
            emoji = "🟢"
            title = "🚨 СИГНАЛ ПОКУПКИ!"
        elif action == 'SELL':
            emoji = "🔴"
            title = "🚨 СИГНАЛ ПРОДАЖИ!"
        else:
            emoji = "🟡"
            title = "⚠️ ВАЖНЫЙ СИГНАЛ"

        message = f"""
{emoji} {title} {emoji}

*Монета:* {symbol.upper()}
*Таймфрейм:* {signal['best_timeframe']}
*Сила сигнала:* {strength}/10

*Рекомендация:*
{signal['recommendation']}

*Цена:* ${signal['price']:,.2f}
*Доходность:* {signal['returns']}%

*Сигналы:*
{signal['signals']}

_🕐 {datetime.now().strftime('%H:%M %d.%m.%Y')}_
"""
        return message

    async def _async_send_alert(self, message: str):
        """Асинхронно отправляет уведомление"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"❌ Ошибка отправки в Telegram: {e}")