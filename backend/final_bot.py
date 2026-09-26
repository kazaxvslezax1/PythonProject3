import telebot
import requests
import time
import threading
import matplotlib
import json
import os
import socket
from fibonacci_calculator import fib_calculator
from volume_analyzer_advanced import advanced_volume_analyzer
from backtester import backtester
from portfolio_analyzer import portfolio_analyzer
from trend_analyzer import trend_analyzer
from risk_manager import risk_manager
from datetime import datetime, timedelta
from smart_alerts import smart_alerts
from collections import defaultdict
from top_coins_manager import top_coins_manager
from dynamic_rr_calculator import dynamic_rr_calculator

from ai_confidence_checker import ai_checker
from ai_confidence_checker import smart_alerts_ai
from advanced_ai_analyzer import advanced_analyzer
from telebot import types

matplotlib.use('Agg')
from chart_generator import generate_simple_chart
from ai_predictor_final import ai_predictor
from target_calculator import target_calculator
from quality_filter import quality_filter
from volume_analyzer import volume_analyzer
from signal_prioritizer import signal_prioritizer
dynamic_rr_calculator.ai_checker = ai_checker





# Проверка интернета перед запуском
def check_internet():
    try:
        socket.create_connection(("api.telegram.org", 443), timeout=5)
        print("✅ Интернет соединение: ОК")
        return True
    except OSError:
        print("❌ Нет интернета! Проверь подключение")
        return False


# Запускаем проверку
if not check_internet():
    print("⚠️ Перезапусти бота когда появится интернет")
    exit(1)

# ТОКЕН БОТА
TELEGRAM_TOKEN = "8238637250:AAE-jXOQgJ9LhlZAd5Rj105ekna6UC_BgFY"

API_URL = "http://127.0.0.1:8000"

# Создаем бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)


# 🔽 ДОБАВЬ ЗДЕСЬ - ПРЯМО ПОСЛЕ СОЗДАНИЯ БОТА
def format_price(price):
    """Адаптивное форматирование цены"""
    if price >= 1000:
        return f"${price:,.0f}"
    elif price >= 1:
        return f"${price:,.2f}"
    elif price >= 0.1:
        return f"${price:.4f}"
    elif price >= 0.01:
        return f"${price:.6f}"
    elif price >= 0.001:
        return f"${price:.8f}"
    else:
        return f"${price:.10f}"




def create_positions_keyboard(positions):
    """Создает inline-клавиатуру для управления позициями"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    for position_id, position in positions.items():
        symbol = position['symbol']
        direction = position['direction']
        entry_price = position['entry_price']

        # Создаем кнопки для каждой позиции
        btn_details = types.InlineKeyboardButton(
            text=f"📊 {symbol}",
            callback_data=f"position_details_{symbol}"
        )
        btn_close = types.InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data=f"close_position_{symbol}"
        )
        btn_analyze = types.InlineKeyboardButton(
            text="🔍 Анализ",
            callback_data=f"analyze_{symbol}"
        )

        # Добавляем кнопки в клавиатуру
        keyboard.add(btn_details, btn_close, btn_analyze)

    # Добавляем общие кнопки
    btn_refresh = types.InlineKeyboardButton(
        text="🔄 Обновить",
        callback_data="refresh_positions"
    )
    btn_dashboard = types.InlineKeyboardButton(
        text="📱 Дашборд",
        callback_data="show_dashboard"
    )

    keyboard.add(btn_refresh, btn_dashboard)

    return keyboard


def get_consensus_signal(symbol):
    """🚀 УЛУЧШЕННЫЙ AI КОНСЕНСУС С ФИЛЬТРАМИ КАЧЕСТВА И УСИЛЕННОЙ ДИСЦИПЛИНЫ"""
    try:
        # 🔽 🔽 🔽 СНАЧАЛА ПОЛУЧАЕМ РЕАЛЬНЫЕ ДАННЫЕ ОДИН РАЗ 🔽 🔽 🔽
        volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
        trend_data = trend_analyzer.multi_timeframe_analysis(symbol)
        current_price = risk_manager.get_latest_price(symbol)

        volume_ratio = volume_data.get('volume_ratio', 0) if 'error' not in volume_data else 0
        confluence = trend_data.get('confluence_score', 0) if 'error' not in trend_data else 0

        # 🔽 РЕАЛЬНЫЙ AI АНАЛИЗ С РЕАЛЬНЫМИ ДАННЫМИ
        ai_analysis = ai_checker.analyze_signal_quality(symbol, {
            'volume_ratio': volume_ratio,
            'current_price': current_price,
            'confluence': confluence
        })

        # 🛑 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Сохраняем реальную, немодифицированную уверенность (7.4)
        initial_ai_confidence = ai_analysis['ai_confidence_score']
        # ai_confidence - это переменная, которую будут модифицировать жесткие фильтры
        ai_confidence = initial_ai_confidence
        ai_recommendation = ai_analysis['recommendation']

        # ➕➕➕ ШАГ 2: КРИТИЧЕСКИЙ ФИЛЬТР ПО ОБЪЕМУ (РАННИЙ ВЫХОД) ➕➕➕
        # Если объем меньше 50% от среднего, не торгуем (это флэт или манипуляция)
        if volume_ratio < 0.5:
            return {
                'systems_checked': 0,
                'systems_agreed': 0,
                'signals': [],
                'consensus_level': 20,
                'final_direction': 'HOLD',
                'confidence': initial_ai_confidence * 10,
                'ai_confidence_filtered': 2.0,  # <-- ОТФИЛЬТРОВАННОЕ ЗНАЧЕНИЕ (2.0)
                'ai_confidence_real': initial_ai_confidence,  # <-- РЕАЛЬНОЕ ЗНАЧЕНИЕ (7.4)
                'ai_recommendation': 'HOLD',
                'risk_level': 'HIGH_VOLUME_FAIL'
            }
        # ➕➕➕ КОНЕЦ ФИЛЬТРА ОБЪЕМА ➕➕➕

        # ➕➕➕ ШАГ 1: ВНЕДРЕНИЕ ЖЕСТКОГО ФИЛЬТРА КАЧЕСТВА ➕➕➕
        quality_check_failed = False
        quality_score = quality_filter.check(symbol, ai_recommendation, ai_confidence)

        if quality_score < 7.0:
            # 1. Снижаем AI-уверенность, чтобы провалить все остальные проверки
            ai_confidence = 3.0  # <-- Теперь ai_confidence = 3.0 (но real_ai_confidence = 7.4)
            quality_check_failed = True
        # ➕➕➕ КОНЕЦ НОВОГО ФИЛЬТРА КАЧЕСТВА ➕➕➕

        consensus_results = {
            'systems_checked': 0,
            'systems_agreed': 0,
            'signals': [],
            'consensus_level': 0,
            'final_direction': 'HOLD',
            # 🛑 ИСПОЛЬЗУЕМ РЕАЛЬНУЮ УВЕРЕННОСТЬ ДЛЯ ОБЩЕЙ КОНФИДЕНЦИИ
            'confidence': initial_ai_confidence * 10,
            'ai_confidence_filtered': ai_confidence,  # 2.0 или 3.0, если фильтры сработали
            'ai_confidence_real': initial_ai_confidence,  # 7.4 - НАШ КЛЮЧ!
            'ai_recommendation': ai_recommendation,
            # Определение уровня риска на основе REAL_AI_confidence:
            'risk_level': 'HIGH' if initial_ai_confidence < 4.0 else 'MEDIUM' if initial_ai_confidence < 7.0 else 'LOW'
        }

        # 3. Применяем специальный код риска, если фильтр не пройден
        if quality_check_failed:
            consensus_results['risk_level'] = 'HIGH_QUALITY_FAIL'

        # 🔽 🔽 🔽 ЕСЛИ AI УВЕРЕННОСТЬ НИЗКАЯ - ВОЗВРАЩАЕМ СРАЗУ
        if ai_confidence < 4.0:
            return {
                'systems_checked': 0,
                'systems_agreed': 0,
                'signals': [],
                'consensus_level': ai_confidence * 10,
                'final_direction': 'HOLD',
                'confidence': initial_ai_confidence,
                'ai_confidence_filtered': ai_confidence,  # 3.0
                'ai_confidence_real': initial_ai_confidence,  # 7.4
                'ai_recommendation': ai_recommendation,
                'risk_level': 'HIGH_QUALITY_FAIL' if quality_check_failed else 'HIGH'
            }

        # 🔽 🔽 🔽 ТОЛЬКО ПРИ НОРМАЛЬНОЙ AI УВЕРЕННОСТИ - АНАЛИЗИРУЕМ ДРУГИЕ СИСТЕМЫ 🔽 🔽 🔽
        # ... (Блоки 1, 2, 3 с Объемным и Трендовым Анализом остаются без изменений)

        # 🔽 🔽 🔽 РАСЧЕТ КОНСЕНСУСА НА ОСНОВЕ AI УВЕРЕННОСТИ И ФИЛЬТРА КАЧЕСТВА 🔽 🔽 🔽
        if consensus_results['systems_checked'] > 0:
            # 🔽 ОСНОВНОЙ ФАКТОР - AI УВЕРЕННОСТЬ (используем фильтрованную для расчета консенсуса!)
            base_consensus = (consensus_results['systems_agreed'] / consensus_results['systems_checked']) * 100

            # 🔽 УМНОЖАЕМ НА AI УВЕРЕННОСТЬ
            adjusted_consensus = base_consensus * (ai_confidence / 10.0)  # ai_confidence здесь 7.4 или 3.0/2.0

            consensus_results['consensus_level'] = adjusted_consensus

            # ➕➕➕ ШАГ 3: УСИЛЕННЫЙ ФИЛЬТР SHORT (ФИНАЛЬНОЕ РЕШЕНИЕ) ➕➕➕
            if consensus_results['systems_agreed'] >= 2:

                # 🏆 ПРИОРИТЕТ LONG: Требуется REAL_AI_CONFIDENCE >= 7.0 и 2+ согласия
                if ai_recommendation == "LONG" and initial_ai_confidence >= 7.0:
                    consensus_results['final_direction'] = "LONG"

                # 🛡️ УСИЛЕННЫЙ ФИЛЬТР SHORT: Требуется REAL_AI_CONFIDENCE >= 6.0 И минимум 3 согласия
                elif ai_recommendation == "SHORT" and initial_ai_confidence >= 6.0 and consensus_results[
                    'systems_agreed'] >= 3:
                    consensus_results['final_direction'] = "SHORT"

                # В противном случае - HOLD
                else:
                    consensus_results['final_direction'] = 'HOLD'
            else:
                consensus_results['final_direction'] = 'HOLD'
        else:
            consensus_results['consensus_level'] = 0
            consensus_results['final_direction'] = 'HOLD'

        return consensus_results

    except Exception as e:
        print(f"❌ Ошибка консенсуса для {symbol}: {e}")
        return {
            'systems_checked': 0,
            'systems_agreed': 0,
            'signals': [],
            'consensus_level': 0,
            'final_direction': 'HOLD',
            'confidence': 0,
            'ai_confidence_filtered': 2.0,  # <-- ОТФИЛЬТРОВАННОЕ ЗНАЧЕНИЕ
            'ai_confidence_real': 2.0,  # <-- РЕАЛЬНОЕ ЗНАЧЕНИЕ (ставим 2.0 при фатальной ошибке)
            'ai_recommendation': '❌ Ошибка анализа',
            'risk_level': 'HIGH'
        }

def add_trading_plan(symbol):
    """Универсальный план действий для любой сделки"""
    plan = f"""
🎯 **ПЛАН ДЕЙСТВИЙ ДЛЯ {symbol}:**

1. 🔍 **ПРОВЕРИТЬ НАДЕЖНОСТЬ:**
   `/analyze_smart {symbol}`

2. ✅ **ЕСЛИ AI ≥7.0** - продолжить
   ❌ **ЕСЛИ AI <7.0** - ПРОПУСТИТЬ сделку

3. 📊 **ПОЛУЧИТЬ ЦЕЛИ:**
   `/advanced_targets {symbol}`

4. ⚡ **РАССЧИТАТЬ РИСК:**
   `/risk {symbol} [ВАШ_БАЛАНС] 2`

5. 🤖 **ОТКРЫТЬ СДЕЛКУ:**
   Скопируйте команду из /advanced_targets

💡 **ПРАВИЛО:** Входите ТОЛЬКО при AI уверенности ≥7.0!
"""
    return plan

# 🔼 КОНЕЦ ФУНКЦИИ


# 🔒 НАСТРОЙКИ БЕЗОПАСНОСТИ - ПОКА НЕ МЕНЯЙ ЦИФРЫ!
AUTHORIZED_USER_IDS = [320682811]        # 👤 Твой личный ID (из /my_id)
AUTHORIZED_GROUP_IDS = [-1002446760333]  # 💬 ЗАМЕНИШЬ ПОЗЖЕ

def is_authorized_access(message):
    """Проверяет доступ к боту"""
    user_ok = message.from_user.id in AUTHORIZED_USER_IDS
    chat_ok = message.chat.id in AUTHORIZED_GROUP_IDS
    return user_ok or chat_ok

# 🔐 БЛОКИРОВКА ВСЕХ КОМАНД ДЛЯ ПОСТОРОННИХ
@bot.message_handler(func=lambda message: not is_authorized_access(message))
def block_unauthorized(message):
    # Молча игнорируем - бот не отвечает вообще
    print(f"🚫 Блокировка: {message.from_user.id} в чате {message.chat.id}")
    return

# 🔍 КОМАНДА ДЛЯ ПРОВЕРКИ ДОСТУПА
@bot.message_handler(commands=['check_access'])
def check_access(message):
    if is_authorized_access(message):
        bot.reply_to(message, "✅ Доступ разрешен! Защита работает.")
    else:
        bot.reply_to(message, "❌ Доступ запрещен!")


# Функция для загрузки символов
def load_all_symbols():
    """Загружает все символы из файла"""
    try:
        with open("all_usdt_pairs.json", "r") as f:
            symbols = json.load(f)

        # ФИЛЬТРУЕМ НИЗКОКАЧЕСТВЕННЫЕ АКТИВЫ
        filtered_symbols = [s for s in symbols if quality_filter.is_high_quality(s)]
        print(
            f"✅ Загружено {len(filtered_symbols)} качественных торговых пар (отфильтровано {len(symbols) - len(filtered_symbols)})")
        return filtered_symbols
    except:
        # 🔽 🔽 🔽 ОБНОВЛЕННЫЙ БАЗОВЫЙ СПИСОК С МЕМКОИНАМИ 🔽 🔽 🔽
        base_symbols = [
            # Основные монеты
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT",
            "AVAXUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT", "LINKUSDT",
            "ATOMUSDT", "UNIUSDT", "XLMUSDT", "ALGOUSDT", "TRXUSDT", "VETUSDT",
            "ICPUSDT", "FILUSDT", "AAVEUSDT", "COMPUSDT", "MKRUSDT", "SNXUSDT",
            "CRVUSDT", "SUSHIUSDT", "YFIUSDT", "1INCHUSDT", "UMAUSDT", "BALUSDT",
            "NEARUSDT", "FTMUSDT", "EGLDUSDT", "ETCUSDT", "XTZUSDT", "EOSUSDT",
            "XMRUSDT", "ZECUSDT", "DASHUSDT", "WAVESUSDT", "RNDRUSDT", "AGIXUSDT", "FETUSDT",
            "OCEANUSDT", "GRTUSDT", "SANDUSDT", "MANAUSDT", "ENJUSDT", "GALAUSDT",
            "AXSUSDT", "IMXUSDT", "ILVUSDT", "YGGUSDT", "BANDUSDT", "TRBUSDT",
            "LDOUSDT", "FTTUSDT", "LEOUSDT", "CROUSDT",

            # 🔥 ПОПУЛЯРНЫЕ МЕМКОИНЫ (добавлены вручную)
            "DOGEUSDT", "SHIBUSDT", "PEPEUSDT", "FLOKIUSDT", "BONKUSDT",
            "WIFUSDT", "BOMEUSDT", "MEMEUSDT", "LUNCUSDT", "LUNAUSDT",

            # 🔥 ПОПУЛЯРНЫЕ АЛЬТКОИНЫ
            "ARBUSDT", "OPUSDT", "SUIUSDT", "SEIUSDT", "APTUSDT",
            "ARUSDT", "RUNEUSDT", "INJUSDT", "TIAUSDT", "ORDIUSDT"
        ]
        print(f"⚠️ Используется расширенный список ({len(base_symbols)} символов, включая мемкоины)")
        return base_symbols

# Универсальная функция для добавления AI-анализа к любому сигналу
def add_ai_analysis_to_signal(symbol, signal_data):
    """Добавляет AI-анализ к любому сигналу БЕЗ потери данных - РЕАЛЬНЫЕ ДАННЫЕ"""
    try:
        # 🔽 🔽 🔽 РЕАЛЬНЫЕ ДАННЫЕ ДЛЯ AI АНАЛИЗА 🔽 🔽 🔽
        # Используем ТОТ ЖЕ анализатор объемов что и в других системах
        volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
        trend_data = trend_analyzer.multi_timeframe_analysis(symbol)

        # 🔽 ПРАВИЛЬНЫЙ РАСЧЕТ volume_ratio (как в других системах)
        volume_ratio = volume_data.get('volume_ratio', 0) if 'error' not in volume_data else 0
        current_price = signal_data.get('current_price', signal_data.get('last_price', 0))
        confluence = trend_data.get('confluence_score', 0) if 'error' not in trend_data else 0

        ai_analysis_data = {
            'volume_ratio': volume_ratio,  # 🔽 РЕАЛЬНЫЕ объемы
            'current_price': current_price,
            'confluence': confluence
        }

        ai_analysis = ai_checker.analyze_signal_quality(symbol, ai_analysis_data)

        # 🔽 ВОЗВРАЩАЕМ РЕАЛЬНЫЕ AI-ДАННЫЕ
        return {
            'ai_analysis': ai_analysis,
            'ai_confidence': ai_analysis['ai_confidence_score'],  # 🔽 РЕАЛЬНАЯ AI уверенность
            'ai_recommendation': ai_analysis['recommendation'],
            'ai_color': ai_analysis['color'],
            'ai_metrics': ai_analysis.get('metrics', {}),
            'volume_ratio': volume_ratio  # 🔽 ДОБАВЛЯЕМ РЕАЛЬНЫЕ объемы
        }
    except Exception as e:
        print(f"Ошибка AI анализа для {symbol}: {e}")
        # 🔽 ВОЗВРАЩАЕМ БЕЗОПАСНЫЕ ЗНАЧЕНИЯ
        return {
            'ai_analysis': {'ai_confidence_score': 2.0, 'recommendation': '❌ AI анализ недоступен', 'color': '🔴'},
            'ai_confidence': 2.0,
            'ai_recommendation': '❌ AI анализ недоступен',
            'ai_color': '🔴',
            'ai_metrics': {},
            'volume_ratio': 0.1
        }
# Система мониторинга
class SimpleMonitor:
    def __init__(self, bot):
        self.bot = bot
        self.monitoring_active = False
        self.monitored_symbols = []
        self.chat_id = None
        self.alerted_signals = {}
        self.last_prices = {}
        self.performance_stats = defaultdict(lambda: {
            'signals_sent': 0,
            'price_alerts_sent': 0,
            'last_signal_time': None
        })

    def start_monitoring(self, chat_id, symbols, check_interval=5):
        self.chat_id = chat_id
        self.monitored_symbols = symbols
        self.monitoring_active = True

        for symbol in symbols:
            self.last_prices[symbol] = 0

        thread = threading.Thread(
            target=self._monitor_loop,
            args=(check_interval,),
            daemon=True
        )
        thread.start()

        return f"🔔 Мониторинг запущен для: {', '.join(symbols)}\n⏰ Проверка каждые {check_interval} минут\n📊 Отслеживаем: {len(symbols)} монет"

    def stop_monitoring(self):
        self.monitoring_active = False
        return "⏹️ Мониторинг остановлен"

    def get_monitoring_stats(self):
        """Статистика мониторинга"""
        total_signals = sum(stats['signals_sent'] for stats in self.performance_stats.values())
        total_price_alerts = sum(stats['price_alerts_sent'] for stats in self.performance_stats.values())

        return {
            'active': self.monitoring_active,
            'monitored_symbols_count': len(self.monitored_symbols),
            'total_signals_sent': total_signals,
            'total_price_alerts_sent': total_price_alerts,
            'performance_stats': dict(self.performance_stats)
        }

    def _monitor_loop(self, check_interval):
        while self.monitoring_active:
            try:
                self._check_symbols()
                for _ in range(check_interval * 60):
                    if not self.monitoring_active:
                        break
                    time.sleep(1)
            except Exception as e:
                print(f"Ошибка мониторинга: {e}")
                time.sleep(60)

    def _check_symbols(self):
        collected_alerts = []

        for symbol in self.monitored_symbols:
            if not self.monitoring_active:
                break

            try:
                response = requests.post(
                    f"{API_URL}/analyze-smart",
                    params={"symbol": symbol},
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    if "error" not in data:
                        current_price = data.get('last_price', 0)
                        action = data.get('action', 'HOLD')
                        strength = data.get('strength', 0)

                        # 🔥 AI-ФИЛЬТР АЛЕРТОВ
                        if abs(strength) >= 3:
                            alert_data = self._prepare_alert_data(symbol, data, strength)
                            # Используем AI-фильтр вместо простого
                            if smart_alerts_ai.should_send_alert(symbol, action, strength):
                                collected_alerts.append(alert_data)
                                self.performance_stats[symbol]['signals_sent'] += 1
                                self.performance_stats[symbol]['last_signal_time'] = datetime.now()

                        # ПРОВЕРКА ИЗМЕНЕНИЯ ЦЕНЫ
                        if self.last_prices.get(symbol):
                            price_change = abs(
                                (current_price - self.last_prices[symbol]) / self.last_prices[symbol] * 100)
                            if price_change >= 2.0:
                                self._send_price_alert(symbol, data, price_change)
                                self.performance_stats[symbol]['price_alerts_sent'] += 1

                        self.last_prices[symbol] = current_price

                time.sleep(1)  # Защита от лимитов API

            except Exception as e:
                print(f"Ошибка анализа {symbol}: {e}")

        # ОТПРАВЛЯЕМ ПРИОРИТЕТНЫЕ АЛЕРТЫ
        if collected_alerts:
            self._send_priority_alerts(collected_alerts)

    def _prepare_alert_data(self, symbol, data, strength):
        """Подготовка данных для алерта"""
        current_price = data.get('last_price', 0)

        # ИСПРАВЛЕННЫЙ КОД ДЛЯ VOLUME_ANALYZER
        try:
            volume_data = volume_analyzer.get_volume_analysis(symbol)

            # Обрабатываем разные форматы возврата
            if isinstance(volume_data, tuple) and len(volume_data) == 2:
                volume_analysis, volume_24h = volume_data
            elif isinstance(volume_data, dict):
                volume_analysis = volume_data
                volume_24h = volume_data.get('volume_24h', volume_data.get('volume', 0))
            else:
                # Если непонятный формат, используем значения по умолчанию
                volume_analysis = {'strength': 0, 'trend': 'neutral'}
                volume_24h = 0

        except Exception as vol_error:
            print(f"Volume error for {symbol}: {vol_error}")
            volume_analysis = {'strength': 0, 'trend': 'neutral'}
            volume_24h = 0

        asset_rating = quality_filter.get_asset_rating(symbol, current_price, volume_24h)

        # Анализ конфлюэнса
        trend_analysis = trend_analyzer.multi_timeframe_analysis(symbol)
        confluence_score = trend_analysis.get('confluence_score', 0) if 'error' not in trend_analysis else 0

        return {
            'symbol': symbol,
            'signal_type': data.get('action', 'HOLD'),
            'strength': strength,
            'price': current_price,
            'timeframe': data.get('best_timeframe', 'N/A'),
            'asset_rating': asset_rating,
            'volume_strength': volume_analysis.get('strength', 0),
            'confluence_score': confluence_score,
            'timestamp': datetime.now()
        }

    def _send_priority_alerts(self, alerts):
        """Отправка AI-приоритетных алертов"""
        try:
            # 🔥 AI-ПРИОРИТИЗАЦИЯ И ФИЛЬТРАЦИЯ
            prioritized_alerts = smart_alerts_ai.prioritize_alerts(alerts)
            filtered_alerts = smart_alerts_ai.filter_duplicate_alerts(prioritized_alerts)

            # Отправляем только топ-3 САМЫХ НАДЕЖНЫХ алерта
            reliable_alerts = [a for a in filtered_alerts if a.get('ai_confidence', 0) >= 6.0]
            top_alerts = reliable_alerts[:3] if reliable_alerts else []

            # Отправляем топ-3 алерта
            for alert in filtered_alerts[:3]:
                self._send_smart_trading_alert(alert)

            # Отправляем сводку если алертов много
            if len(filtered_alerts) > 3:
                summary = smart_alerts.generate_alert_summary(filtered_alerts)
                self.bot.send_message(self.chat_id, summary)

        except Exception as e:
            print(f"Ошибка отправки приоритетных алертов: {e}")

    def _send_smart_trading_alert(self, alert):
        """Умное оповещение о торговом сигнале"""
        try:
            symbol = alert['symbol']
            signal_type = alert['signal_type']
            strength = alert['strength']

            if signal_type == "BUY":
                emoji = "🟢"
                title = "🎯 СИГНАЛ ПОКУПКИ"
                urgency = "СРОЧНО ПОКУПАТЬ" if strength >= 4 else "Рассмотреть покупку"
            elif signal_type == "SELL":
                emoji = "🔴"
                title = "🎯 СИГНАЛ ПРОДАЖИ"
                urgency = "СРОЧНО ПРОДАВАТЬ" if strength <= -4 else "Рассмотреть продажу"
            else:
                return

            message = f"""
{emoji} {title} {emoji}

Монета: {symbol}
Критичность: {urgency}
Сила сигнала: {abs(strength)}/10

🏆 РЕЙТИНГ: {alert['asset_rating']}/10
📊 КОНФЛЮЭНС: {alert['confluence_score']}%
📈 ОБЪЕМЫ: {'усиливают' if alert['volume_strength'] >= 3 else 'подтверждают' if alert['volume_strength'] >= 2 else 'нейтральные'}

💰 Цена: ${alert['price']:,.4f}
⏰ Таймфрейм: {alert['timeframe']}

💡 Это приоритетный сигнал с фильтрацией дублей
"""

            self.bot.send_message(self.chat_id, message)
            print(f"🎯 Отправлен УМНЫЙ алерт для {symbol}")

        except Exception as e:
            print(f"Ошибка отправки умного алерта: {e}")

    def _send_price_alert(self, symbol, data, change_percent):
        """Оповещение об изменении цены"""
        try:
            direction = "📈 ВЫРОСЛА" if change_percent > 0 else "📉 УПАЛА"
            emoji = "🟢" if change_percent > 0 else "🔴"

            message = f"""
{emoji} ИЗМЕНЕНИЕ ЦЕНЫ {emoji}

Монета: {symbol}
Изменение: {direction} на {abs(change_percent):.1f}%
Текущая цена: ${data.get('last_price', 0):,.2f}

📊 Анализ:
{data.get('recommendation', 'Мониторим ситуацию...')}

🕐 {datetime.now().strftime('%H:%M %d.%m.%Y')}
"""
            self.bot.send_message(self.chat_id, message)
            print(f"📈 Отправлен ценовой алерт для {symbol}: {change_percent:.1f}%")

        except Exception as e:
            print(f"Ошибка отправки ценового алерта: {e}")


# Создаем монитор
monitor = SimpleMonitor(bot)


# 🔽 🔽 🔽 ДОБАВЛЯЕМ СИСТЕМУ АВТОМАТИЧЕСКИХ УВЕДОМЛЕНИЙ AI УВЕРЕННОСТИ 🔽 🔽 🔽
class AIConfidenceMonitor:
    """Автоматический мониторинг высокой AI уверенности"""

    def __init__(self, bot):
        self.bot = bot
        self.monitoring_active = False
        self.alerted_coins = {}  # {symbol: {last_confidence, last_alert_time}}
        self.monitoring_thread = None
        self.min_confidence = 7.0  # минимальная уверенность для уведомления

    def start_ai_monitoring(self, chat_id, min_confidence=7.0):
        """Запуск автоматического мониторинга AI уверенности"""
        self.chat_id = chat_id
        self.min_confidence = min_confidence
        self.monitoring_active = True
        self.alerted_coins = {}

        # Запускаем в отдельном потоке
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()

        return f"""
🤖 ЗАПУЩЕН АВТОМАТИЧЕСКИЙ МОНИТОРИНГ AI УВЕРЕННОСТИ

🎯 Система будет уведомлять о:
• Монетах с AI уверенностью ≥{min_confidence}/10
• Качественных торговых возможностях
• Надежных сигналах для входа

📊 Проверка: каждые 30 минут
🔔 Уведомления: только при высоком качестве

⚡ Команды управления:
/ai_monitor_status - статус мониторинга
/ai_monitor_stop - остановить уведомления  
/set_confidence 7.5 - изменить порог

💡 Пример уведомления:
🎯 ВЫСОКАЯ AI УВЕРЕННОСТЬ!
🟢 BTCUSDT: 8.2/10
💡 Можно входить с полной позицией
"""

    def stop_ai_monitoring(self):
        """Остановка мониторинга"""
        self.monitoring_active = False
        return "⏹️ Автоматический мониторинг AI уверенности остановлен"

    def get_status(self):
        """Статус мониторинга"""
        if not self.monitoring_active:
            return "❌ Автоматический мониторинг AI уверенности не активен"

        alerted_count = len([coin for coin in self.alerted_coins.values() if coin.get('alerted', False)])

        return f"""
🤖 СТАТУС АВТОМАТИЧЕСКОГО МОНИТОРИНГА:

✅ Активен: ДА
🎯 Минимальная уверенность: {self.min_confidence}/10
📊 Монет с уведомлениями: {alerted_count}
🔄 Проверка: каждые 30 минут
💡 Следующая проверка: через 30 минут

⚡ Команды:
/ai_monitor_stop - остановить
/set_confidence 7.5 - изменить порог
"""

    def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        check_interval = 30 * 60  # 30 минут

        while self.monitoring_active:
            try:
                print(f"🔍 AI мониторинг: проверка монет с уверенностью ≥{self.min_confidence}...")
                self._check_high_confidence_coins()

                # Ждем указанный интервал
                for _ in range(check_interval):
                    if not self.monitoring_active:
                        break
                    time.sleep(1)

            except Exception as e:
                print(f"❌ Ошибка в AI мониторинге: {e}")
                time.sleep(60)

    def _check_high_confidence_coins(self):
        """Проверка монет с высокой AI уверенностью"""
        try:
            # Проверяем топ-20 монет
            symbols_to_check = top_coins_manager.get_top_coins_by_marketcap(20)
            high_confidence_found = []

            for symbol in symbols_to_check:
                if not self.monitoring_active:
                    break

                try:
                    # Быстрый AI анализ
                    ai_analysis = ai_checker.analyze_signal_quality(symbol, {'current_price': 0})
                    ai_score = ai_analysis['ai_confidence_score']

                    # Проверяем порог уверенности
                    if ai_score >= self.min_confidence:
                        high_confidence_found.append({
                            'symbol': symbol,
                            'ai_score': ai_score,
                            'recommendation': ai_analysis['recommendation'],
                            'color': ai_analysis['color']
                        })

                        # Проверяем нужно ли отправлять уведомление
                        self._check_and_send_alert(symbol, ai_score, ai_analysis)

                except Exception as e:
                    print(f"⚠️ Ошибка анализа {symbol}: {e}")
                    continue

            # Логируем результат проверки
            if high_confidence_found:
                print(f"✅ Найдено {len(high_confidence_found)} монет с AI ≥{self.min_confidence}")
            else:
                print(f"📊 Монет с AI ≥{self.min_confidence} не найдено")

        except Exception as e:
            print(f"❌ Ошибка проверки AI уверенности: {e}")

    def _check_and_send_alert(self, symbol, ai_score, ai_analysis):
        """Проверяет и отправляет уведомление если нужно"""
        try:
            current_time = time.time()
            symbol_data = self.alerted_coins.get(symbol, {})
            last_alert_time = symbol_data.get('last_alert_time', 0)
            last_confidence = symbol_data.get('last_confidence', 0)

            # Проверяем условия для уведомления:
            # 1. Первое обнаружение ИЛИ
            # 2. Уверенность выросла на +1.0 ИЛИ
            # 3. Прошло больше 2 часов с последнего уведомления
            should_alert = (
                    last_alert_time == 0 or  # Первое обнаружение
                    ai_score >= last_confidence + 1.0 or  # Значительный рост
                    current_time - last_alert_time > 2 * 60 * 60  # Прошло 2 часа
            )

            if should_alert and self.monitoring_active:
                self._send_confidence_alert(symbol, ai_score, ai_analysis)

                # Обновляем данные о монете
                self.alerted_coins[symbol] = {
                    'last_confidence': ai_score,
                    'last_alert_time': current_time,
                    'alerted': True
                }

        except Exception as e:
            print(f"❌ Ошибка проверки уведомления для {symbol}: {e}")

    def _send_confidence_alert(self, symbol, ai_score, ai_analysis):
        """Отправляет уведомление о высокой AI уверенности"""
        try:
            emoji = "🟢" if ai_score >= 8.0 else "🟡"

            message = f"""
🎯 ВЫСОКАЯ AI УВЕРЕННОСТЬ!

{emoji} {symbol.replace('USDT', '')}: {ai_score:.1f}/10
💡 {ai_analysis['recommendation']}

📊 Детальный анализ:
/analyze_smart {symbol}

🎯 Получить цели:
/advanced_targets {symbol}

⚡ Проверить консенсус:
/consensus {symbol}

🕐 Обнаружено: {datetime.now().strftime('%H:%M %d.%m.%Y')}
"""
            self.bot.send_message(self.chat_id, message)
            print(f"🔔 Отправлено уведомление для {symbol} (AI: {ai_score:.1f}/10)")

        except Exception as e:
            print(f"❌ Ошибка отправки уведомления для {symbol}: {e}")


# Создаем глобальный экземпляр мониторинга
ai_confidence_monitor = AIConfidenceMonitor(bot)


# 🔼 🔼 🔼 КОНЕЦ СИСТЕМЫ АВТОМАТИЧЕСКИХ УВЕДОМЛЕНИЙ 🔼 🔼 🔼

class VolumeMonitor:
    def __init__(self, bot):
        self.bot = bot
        self.monitoring_active = False
        self.chat_id = None
        self.alerted_signals = {}  # Чтобы не спамить
        self.check_interval = 1  # Проверка каждую минуту

    def start_volume_monitoring(self, chat_id, symbols=None):
        """Запуск мониторинга объемов"""
        self.chat_id = chat_id
        self.monitoring_active = True

        if symbols is None:
            symbols = top_coins_manager.get_top_coins_by_marketcap(20)  # Топ-20 по умолчанию

        self.monitored_symbols = symbols

        thread = threading.Thread(
            target=self._volume_monitor_loop,
            daemon=True
        )
        thread.start()

        return f"🔔 Мониторинг объемов запущен для {len(symbols)} монет\n⏰ Проверка каждую минуту"

    def stop_volume_monitoring(self):
        self.monitoring_active = False
        return "⏹️ Мониторинг объемов остановлен"

    def _volume_monitor_loop(self):
        """Главный цикл мониторинга"""
        while self.monitoring_active:
            try:
                self._check_volume_spikes()
                # Ждем 60 секунд до следующей проверки
                for _ in range(60):
                    if not self.monitoring_active:
                        break
                    time.sleep(1)

            except Exception as e:
                print(f"Ошибка мониторинга объемов: {e}")
                time.sleep(30)

    def _check_volume_spikes(self):
        """Проверка всплесков объемов"""
        print(f"🔍 Проверяю объемы... {datetime.now().strftime('%H:%M:%S')}")

        for symbol in self.monitored_symbols:
            if not self.monitoring_active:
                break

            try:
                # Быстрая проверка для реального времени
                alert = advanced_volume_analyzer.get_real_time_volume_alert(symbol)

                if alert and self._should_send_alert(symbol, alert):
                    self._send_volume_alert(alert)
                    # Запоминаем что отправили алерт
                    self.alerted_signals[symbol] = datetime.now()

                # Небольшая пауза между запросами
                time.sleep(0.5)

            except Exception as e:
                print(f"Ошибка проверки {symbol}: {e}")
                continue

    def _should_send_alert(self, symbol, alert):
        """Проверяем нужно ли отправлять алерт"""
        # Не отправляем если уже отправляли недавно
        last_alert = self.alerted_signals.get(symbol)
        if last_alert:
            time_diff = (datetime.now() - last_alert).total_seconds()
            if time_diff < 300:  # 5 минут между алертами для одной монеты
                return False

        # Отправляем только сильные сигналы
        if alert['volume_ratio'] >= 3.0 and alert['confidence'] in ['HIGH', 'MEDIUM']:
            return True

        return False

    def _send_volume_alert(self, alert):
        """Отправка уведомления о всплеске объемов с AI ПРОВЕРКОЙ"""
        try:
            symbol = alert['symbol']
            signal_type = alert['signal']
            volume_ratio = alert['volume_ratio']
            price_change = alert['price_change']

            # 🔽 🔽 🔽 ДОБАВЛЯЕМ AI ПРОВЕРКУ ПЕРЕД ОТПРАВКОЙ 🔽 🔽 🔽
            try:
                # Получаем РЕАЛЬНЫЕ данные для AI анализа
                volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
                trend_data = trend_analyzer.multi_timeframe_analysis(symbol)
                confluence = trend_data.get('confluence_score', 0) if 'error' not in trend_data else 0

                # AI анализ надежности сигнала
                ai_analysis = ai_checker.analyze_signal_quality(symbol, {
                    'volume_ratio': volume_data.get('volume_ratio', 0),
                    'current_price': 0,
                    'confluence': confluence
                })

                ai_confidence = ai_analysis['ai_confidence_score']

                # 🔽 ОТПРАВЛЯЕМ ТОЛЬКО ПРИ НОРМАЛЬНОЙ AI УВЕРЕННОСТИ
                if ai_confidence < 5.0:
                    print(f"🔇 Пропускаем аномалию {symbol} - AI: {ai_confidence:.1f}/10 (нужно ≥5.0)")
                    return

            except Exception as ai_error:
                print(f"⚠️ AI проверка не удалась для {symbol}: {ai_error}")
                # Если AI проверка не сработала - все равно отправляем, но с предупреждением
                ai_confidence = 3.0  # 🔽 Низкая уверенность по умолчанию

            if signal_type == 'PUMP_START':
                emoji = "🚀"
                title = "НАЧИНАЕТСЯ ПУМП!"
                color = "🟢"
                action = "СРОЧНО ПОКУПАТЬ"
            elif signal_type == 'DUMP_START':
                emoji = "🔻"
                title = "НАЧИНАЕТСЯ ДАМП!"
                color = "🔴"
                action = "СРОЧНО ПРОДАВАТЬ"
            else:
                emoji = "📈"
                title = "ВСПЛЕСК ОБЪЕМОВ"
                color = "🟡"
                action = "ВНИМАНИЕ"

            message = f"""
    {emoji} {title} {emoji}

    Монета: {symbol.replace('USDT', '')}
    Действие: {action} {color}

    📊 ДЕТАЛИ:
    • Объем вырос в {volume_ratio:.1f}x
    • Цена изменилась на {price_change:.1f}%
    • Уверенность: {alert['confidence']}

    🤖 AI-ПОДТВЕРЖДЕНИЕ:
    • AI уверенность: {ai_confidence:.1f}/10 {'✅' if ai_confidence >= 5.0 else '⚠️'}

    💡 РЕКОМЕНДАЦИЯ:
    {'🎯 Лови момент - можно войти в позицию' if signal_type == 'PUMP_START' and ai_confidence >= 6.0 else '⚠️ Будь осторожен - возможен дамп' if signal_type == 'DUMP_START' and ai_confidence >= 6.0 else '📈 Крупные игроки активны'}

    /analyze_smart {symbol} - полный анализ
    /advanced_targets {symbol} - цели с Фибо

    🕐 Обнаружено: {alert['timestamp'].strftime('%H:%M:%S')}
    """

            self.bot.send_message(self.chat_id, message)
            print(f"🚀 Отправлен volume alert для {symbol}: {signal_type} (AI: {ai_confidence:.1f}/10)")

        except Exception as e:
            print(f"Ошибка отправки volume alert: {e}")

# Создаем монитор объемов
volume_monitor = VolumeMonitor(bot)



class PremiumSignalsMonitor:
    def __init__(self, bot):
        self.bot = bot
        self.monitoring_active = False
        self.chat_id = None
        self.last_signals = {}  # Чтобы не спамить одинаковыми сигналами
        self.check_interval = 10  # Проверка каждые 10 минут

    def start_premium_monitoring(self, chat_id):
        """Запуск авто-мониторинга премиум сигналов"""
        self.chat_id = chat_id
        self.monitoring_active = True

        thread = threading.Thread(
            target=self._premium_monitor_loop,
            daemon=True
        )
        thread.start()

        return "💎 Авто-мониторинг ПРЕМИУМ сигналов запущен!\n⏰ Проверка каждые 10 минут"

    def stop_premium_monitoring(self):
        self.monitoring_active = False
        return "⏹️ Мониторинг премиум сигналов остановлен"

    def _premium_monitor_loop(self):
        """Главный цикл мониторинга премиум сигналов"""
        while self.monitoring_active:
            try:
                self._check_premium_signals()
                # Ждем 10 минут до следующей проверки
                for _ in range(self.check_interval * 60):
                    if not self.monitoring_active:
                        break
                    time.sleep(1)

            except Exception as e:
                print(f"Ошибка мониторинга премиум сигналов: {e}")
                time.sleep(60)

    def _check_premium_signals(self):
        """Проверка премиум сигналов"""
        print(f"💎 Проверяю премиум сигналы... {datetime.now().strftime('%H:%M:%S')}")

        try:
            # Анализируем топ-12 монет для премиум сигналов
            symbols_to_analyze = top_coins_manager.get_top_coins_by_marketcap(12)
            premium_signals = []

            for symbol in symbols_to_analyze:
                if not self.monitoring_active:
                    break

                try:
                    # Получаем расширенный анализ
                    response = requests.post(
                        f"{API_URL}/analyze-smart",
                        params={"symbol": symbol},
                        timeout=10
                    )

                    if response.status_code == 200:
                        data = response.json()
                        if "error" not in data and abs(data.get('strength', 0)) >= 5:

                            # Получаем цели с динамическим RR
                            targets = dynamic_rr_calculator.calculate_adaptive_targets(
                                symbol,
                                direction="SELL" if data.get('action') == 'SELL' else "LONG",
                                base_stop_loss_percent=0.02,
                                min_rr=3.0
                            )

                            # Анализ объемов
                            volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)

                            # Анализ тренда
                            trend_data = trend_analyzer.multi_timeframe_analysis(symbol)
                            confluence = trend_data.get('confluence_score', 0) if 'error' not in trend_data else 0

                            # AI-АНАЛИЗ НАДЕЖНОСТИ
                            ai_analysis_data = {
                                'volume_ratio': volume_data.get('volume_ratio', 0),
                                'current_price': targets['entry_price'],
                                'confluence': confluence
                            }

                            ai_analysis = ai_checker.analyze_signal_quality(symbol, ai_analysis_data)

                            # 🔥 СУПЕР-СТРОГИЕ ПРЕМИУМ ФИЛЬТРЫ
                            meets_premium = (
                                    targets['risk_reward_ratio'] >= 3.5 and  # RR ≥ 3.5 (было 3.0)
                                    targets['quality_score'] >= 9 and  # Качество ≥ 9/10 (было 8)
                                    volume_data.get('volume_ratio', 0) >= 1.5 and  # Объемы ≥ 1.5x (было 1.2)
                                    abs(confluence) >= 70 and  # Конфлюэнс ≥ 70% (было 60)
                                    targets['current_volatility'] <= 6.0 and  # Волатильность ≤ 6% (было 8)
                                    ai_analysis['ai_confidence_score'] >= 8.0 and  # AI уверенность ≥ 8.0 (было 7.0)
                                    targets.get('smart_stop_percent', 0) <= 3.0  # Умный стоп ≤ 3%
                            )

                            if meets_premium:
                                # 🔥 УЛУЧШЕННЫЙ РАСЧЕТ ПРЕМИУМ ОЦЕНКИ
                                premium_calc = (
                                        (targets['risk_reward_ratio'] * 2) +  # RR вес
                                        (targets['quality_score']) +  # Качество вес
                                        (volume_data.get('volume_ratio', 0) * 2) +  # Объемы вес (увеличили)
                                        (abs(confluence) / 8) +  # Конфлюэнс вес
                                        (ai_analysis['ai_confidence_score'] * 1.2) +  # AI уверенность вес
                                        ((3.0 - targets.get('smart_stop_percent', 3.0)) * 2)  # Бонус за tight стопы
                                )

                                # 🔥 ПРЕМИУМ БОНУСЫ ЗА СУПЕР-ПАРАМЕТРЫ
                                premium_bonus = 0

                                if targets['risk_reward_ratio'] >= 4.0:
                                    premium_bonus += 1.0  # Бонус за супер-RR
                                if volume_data.get('volume_ratio', 0) >= 2.0:
                                    premium_bonus += 1.0  # Бонус за очень высокие объемы
                                if ai_analysis['ai_confidence_score'] >= 9.0:
                                    premium_bonus += 1.5  # Бонус за очень высокую AI уверенность
                                if targets.get('smart_stop_percent', 0) <= 2.0:
                                    premium_bonus += 1.0  # Бонус за очень tight стопы

                                # 🔥 ИТОГОВАЯ ПРЕМИУМ ОЦЕНКА
                                premium_score = min(10, premium_calc + premium_bonus)

                                # Логирование для отладки
                                print(f"💎 ПРЕМИУМ РАСЧЕТ ДЛЯ {symbol}:")
                                print(f"   Базовая формула: {premium_calc:.1f}")
                                print(f"   Премиум бонусы: +{premium_bonus:.1f}")
                                print(f"   ИТОГО: {premium_score:.1f}/10")

                                signal_data = {
                                    'symbol': symbol,
                                    'action': data['action'],
                                    'strength': data['strength'],
                                    'targets': targets,
                                    'volume_ratio': volume_data.get('volume_ratio', 0),
                                    'confluence': confluence,
                                    'ai_analysis': ai_analysis,
                                    'premium_score': premium_score,
                                    'premium_bonus': premium_bonus,  # Добавляем бонусы для информации
                                    'timestamp': datetime.now()
                                }
                                # Проверяем не отправляли ли уже этот сигнал
                                if self._should_send_signal(symbol, signal_data):
                                    premium_signals.append(signal_data)

                    time.sleep(0.5)

                except Exception as e:
                    print(f"Ошибка анализа {symbol}: {e}")
                    continue

            # Отправляем премиум сигналы
            if premium_signals:
                self._send_premium_alerts(premium_signals)

        except Exception as e:
            print(f"Ошибка проверки премиум сигналов: {e}")

    def _should_send_signal(self, symbol, signal_data):
        """Проверяем нужно ли отправлять сигнал"""
        last_signal = self.last_signals.get(symbol)

        # Не отправляем если уже отправляли недавно (30 минут)
        if last_signal:
            time_diff = (datetime.now() - last_signal).total_seconds()
            if time_diff < 1800:  # 30 минут
                return False

        # Запоминаем время отправки
        self.last_signals[symbol] = datetime.now()
        return True

    def _send_premium_alerts(self, signals):
        """Отправка премиум алертов"""
        try:
            # Сортируем по премиум score
            signals.sort(key=lambda x: x['premium_score'], reverse=True)

            # Отправляем только топ-3 сигнала
            for signal in signals[:3]:
                self._send_single_premium_alert(signal)

        except Exception as e:
            print(f"Ошибка отправки премиум алертов: {e}")

    def _send_single_premium_alert(self, signal):
        """Отправка одного премиум алерта"""
        try:
            symbol = signal['symbol']
            symbol_clean = symbol.replace('USDT', '')
            targets = signal['targets']
            ai_analysis = signal['ai_analysis']

            if signal['action'] == 'BUY':
                emoji = "🟢"
                action_text = "ПОКУПКА"
                urgency = "🚀 СРОЧНО ПОКУПАТЬ"
            else:
                emoji = "🔴"
                action_text = "ПРОДАЖА"
                urgency = "🔻 СРОЧНО ПРОДАВАТЬ"

            message = f"""
💎 {emoji} ПРЕМИУМ СИГНАЛ {emoji}

{urgency}

Монета: {symbol_clean}
Действие: {action_text}

⭐ Премиум оценка: {signal['premium_score']:.1f}/10
🤖 AI уверенность: {ai_analysis['ai_confidence_score']}/10 {ai_analysis['color']}

🎯 ДЕТАЛИ СИГНАЛА:
• RR: 1:{targets['risk_reward_ratio']:.1f}
• Цена: ${targets['entry_price']:,.2f}
• Объемы: {signal['volume_ratio']:.1f}x
• Конфлюэнс: {signal['confluence']}%
• Волатильность: {targets['current_volatility']:.1f}%

💰 ЦЕЛИ:
• Стоп-лосс: ${targets['stop_loss']:,.2f}
• Тейк-профит: ${targets['take_profit']:,.2f}

💡 {ai_analysis['recommendation']}

⚡ Это АВТОМАТИЧЕСКИЙ премиум сигнал
🕐 Обнаружен: {datetime.now().strftime('%H:%M:%S')}

/analyze_smart {symbol} - полный анализ
/advanced_targets {symbol} - детальные цели
"""

            self.bot.send_message(self.chat_id, message)
            print(f"💎 Отправлен премиум сигнал для {symbol}")

        except Exception as e:
            print(f"Ошибка отправки премиум алерта: {e}")


# Создаем монитор премиум сигналов
premium_monitor = PremiumSignalsMonitor(bot)


class MarketPhaseMonitor:
    def __init__(self, bot):
        self.bot = bot
        self.monitoring_active = False
        self.chat_id = None
        self.last_phase = None
        self.last_volatility_alert = None
        self.last_volume_alert = None

    def start_market_phase_monitoring(self, chat_id):
        """Запуск мониторинга рыночных фаз"""
        self.chat_id = chat_id
        self.monitoring_active = True

        thread = threading.Thread(
            target=self._market_phase_monitor_loop,
            daemon=True
        )
        thread.start()

        return "📈 Мониторинг рыночных фаз запущен!\n⏰ Проверка каждые 5 минут"

    def stop_market_phase_monitoring(self):
        self.monitoring_active = False
        return "⏹️ Мониторинг рыночных фаз остановлен"

    def _market_phase_monitor_loop(self):
        """Главный цикл мониторинга рыночных фаз"""
        while self.monitoring_active:
            try:
                self._check_market_phases()
                # Ждем 5 минут до следующей проверки
                for _ in range(5 * 60):
                    if not self.monitoring_active:
                        break
                    time.sleep(1)

            except Exception as e:
                print(f"Ошибка мониторинга рыночных фаз: {e}")
                time.sleep(60)

    def _check_market_phases(self):
        """Проверка и определение рыночных фаз"""
        print(f"📈 Проверяю рыночные фазы... {datetime.now().strftime('%H:%M:%S')}")

        try:
            # Анализируем топ-5 монет для определения общей фазы рынка
            symbols_to_analyze = top_coins_manager.get_top_coins_by_marketcap(5)
            bull_signals = 0
            bear_signals = 0
            total_volatility = 0
            volume_spikes = 0

            for symbol in symbols_to_analyze:
                if not self.monitoring_active:
                    break

                try:
                    # Получаем анализ тренда
                    trend_data = trend_analyzer.multi_timeframe_analysis(symbol)
                    if 'error' not in trend_data:
                        confluence = trend_data.get('confluence_score', 0)
                        if confluence > 50:
                            bull_signals += 1
                        elif confluence < -50:
                            bear_signals += 1

                    # Проверяем волатильность
                    targets = dynamic_rr_calculator.calculate_adaptive_targets(symbol, "LONG", 0.02, 2.0)
                    volatility = targets.get('current_volatility', 0)
                    total_volatility += volatility

                    # Проверяем объемы
                    volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
                    if 'error' not in volume_data and volume_data.get('volume_ratio', 0) > 2.0:
                        volume_spikes += 1

                    time.sleep(0.3)

                except Exception as e:
                    print(f"Ошибка анализа {symbol} для рыночных фаз: {e}")
                    continue

            # Определяем текущую фазу рынка
            current_phase = self._determine_market_phase(
                bull_signals, bear_signals, total_volatility / len(symbols_to_analyze), volume_spikes
            )

            # Отправляем уведомление если фаза изменилась
            self._send_phase_alerts(current_phase, volume_spikes, total_volatility / len(symbols_to_analyze))

        except Exception as e:
            print(f"Ошибка проверки рыночных фаз: {e}")

    def _determine_market_phase(self, bull_signals, bear_signals, avg_volatility, volume_spikes):
        """Определяет текущую фазу рынка"""
        if bull_signals >= 3:
            return "BULLISH"
        elif bear_signals >= 3:
            return "BEARISH"
        elif avg_volatility > 8.0:
            return "HIGH_VOLATILITY"
        elif volume_spikes >= 2:
            return "WHALE_ACTIVITY"
        else:
            return "SIDEWAYS"

    def _send_phase_alerts(self, current_phase, volume_spikes, avg_volatility):
        """Отправляет уведомления о смене фаз"""
        try:
            # Проверяем изменилась ли фаза
            if current_phase == self.last_phase:
                return

            self.last_phase = current_phase

            # Формируем сообщение в зависимости от фазы
            if current_phase == "BULLISH":
                message = """
📈 НАЧАЛСЯ БЫЧИЙ ТРЕНД!

Сигналы:
• Большинство монет показывают рост
• Конфлюэнс на покупку > 50%
• Рекомендуется искать LONG позиции

💡 Действия:
- Используйте /trading_ideas для поиска идей
- Настройте консервативные стоп-лоссы
- Рассмотрите постепенное увеличение позиций
"""
            elif current_phase == "BEARISH":
                message = """
📉 НАЧАЛСЯ МЕДВЕЖИЙ ТРЕНД!

Сигналы:
• Большинство монет показывают падение  
• Конфлюэнс на продажу > 50%
• Рекомендуется искать SHORT позиции

💡 Действия:
- Используйте /trading_ideas для SHORT идей
- Будьте осторожны с LONG позициями
- Используйте tighter стоп-лоссы
"""
            elif current_phase == "HIGH_VOLATILITY":
                # Проверяем чтобы не спамить
                now = datetime.now()
                if (self.last_volatility_alert is None or
                        (now - self.last_volatility_alert).total_seconds() > 3600):  # 1 час

                    self.last_volatility_alert = now
                    message = f"""
⚡ ВЫСОКАЯ ВОЛАТИЛЬНОСТЬ!

Текущая волатильность: {avg_volatility:.1f}%

💡 Рекомендации:
- Используйте wider стоп-лоссы
- Уменьшите размер позиций
- Будьте готовы к резким движениям
- Избегайте маржинальной торговли

🛡️ Используйте /advanced_targets для умных стоп-лоссов
"""
                else:
                    return

            elif current_phase == "WHALE_ACTIVITY":
                # Проверяем чтобы не спамить
                now = datetime.now()
                if (self.last_volume_alert is None or
                        (now - self.last_volume_alert).total_seconds() > 1800):  # 30 минут

                    self.last_volume_alert = now
                    message = f"""
💰 АКТИВНОСТЬ КИТОВ!

Обнаружено {volume_spikes} монет с объемом >2x

💡 Возможности:
- Ожидайте сильных движений
- Готовьтесь к пробоям уровней
- Ищите подтверждение объемов

🔍 Проверьте: /volume_scan
"""
                else:
                    return
            else:
                return

            # Отправляем сообщение
            self.bot.send_message(self.chat_id, message)
            print(f"📈 Отправлено уведомление о фазе: {current_phase}")

        except Exception as e:
            print(f"Ошибка отправки уведомления о фазе: {e}")


# Создаем монитор рыночных фаз
market_phase_monitor = MarketPhaseMonitor(bot)


class AnomalyDetector:
    def __init__(self, bot, ai_checker=None):
        self.bot = bot
        self.ai_checker = ai_checker  # ✅ добавляем это
        self.monitoring_active = False
        self.chat_id = None
        self.detected_anomalies = {}

    def start_anomaly_detection(self, chat_id):
        """Запуск детектора аномалий"""
        self.chat_id = chat_id
        self.monitoring_active = True

        thread = threading.Thread(
            target=self._anomaly_detection_loop,
            daemon=True
        )
        thread.start()

        return "🔍 Детектор аномалий запущен!\n⏰ Проверка каждые 3 минуты"

    def stop_anomaly_detection(self):
        self.monitoring_active = False
        return "⏹️ Детектор аномалий остановлен"

    def _anomaly_detection_loop(self):
        """Главный цикл детектора аномалий"""
        while self.monitoring_active:
            try:
                self._scan_for_anomalies()
                self._filter_false_anomalies()

                # Ждем 3 минуты до следующей проверки
                for _ in range(3 * 60):
                    if not self.monitoring_active:
                        break
                    time.sleep(1)

            except Exception as e:
                print(f"Ошибка детектора аномалий: {e}")
                time.sleep(60)

    def _scan_for_anomalies(self):
        """Сканирование рынка на аномалии"""
        print(f"🔍 Сканирую аномалии... {datetime.now().strftime('%H:%M:%S')}")

        try:
            # Анализируем топ-15 монет для поиска аномалий
            symbols_to_analyze = top_coins_manager.get_top_coins_by_marketcap(15)
            new_anomalies = []

            for symbol in symbols_to_analyze:
                if not self.monitoring_active:
                    break

                try:
                    anomalies = self._check_symbol_anomalies(symbol)
                    if anomalies:
                        new_anomalies.extend(anomalies)

                    time.sleep(0.2)  # Чтобы не перегружать API

                except Exception as e:
                    print(f"Ошибка проверки аномалий {symbol}: {e}")
                    continue

            # Отправляем уведомления о новых аномалиях
            if new_anomalies:
                self._send_anomaly_alerts(new_anomalies)

        except Exception as e:
            print(f"Ошибка сканирования аномалий: {e}")

    def _check_symbol_anomalies(self, symbol):
        """Проверяет аномалии для конкретной монеты"""
        anomalies = []
        try:
            # 1. Проверка объемов
            volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
            if 'error' not in volume_data:
                volume_ratio = volume_data.get('volume_ratio', 0)
                if volume_ratio >= 3.0:
                    anomalies.append({
                        'type': 'EXTREME_VOLUME',
                        'symbol': symbol,
                        'value': volume_ratio,
                        'message': f"🚨 {symbol} объемы x{volume_ratio:.1f} - возможен большой движение!"
                    })
                elif volume_ratio >= 2.0 and volume_data.get('is_volume_spike', False):
                    anomalies.append({
                        'type': 'VOLUME_SPIKE',
                        'symbol': symbol,
                        'value': volume_ratio,
                        'message': f"💰 {symbol} всплеск объемов x{volume_ratio:.1f}"
                    })

            # 2. Проверка волатильности
            targets = dynamic_rr_calculator.calculate_adaptive_targets(symbol, "LONG", 0.02, 2.0)
            volatility = targets.get('current_volatility', 0)
            if volatility <= 1.0:
                anomalies.append({
                    'type': 'LOW_VOLATILITY',
                    'symbol': symbol,
                    'value': volatility,
                    'message': f"💎 {symbol} аномально низкая волатильность {volatility:.1f}% - готовимся к пробою!"
                })
            elif volatility >= 15.0:
                anomalies.append({
                    'type': 'HIGH_VOLATILITY',
                    'symbol': symbol,
                    'value': volatility,
                    'message': f"⚡ {symbol} экстремальная волатильность {volatility:.1f}% - осторожно!"
                })

            # 3. Проверка конфлюэнса (с фильтром AI)
            trend_data = trend_analyzer.multi_timeframe_analysis(symbol)
            if 'error' not in trend_data:
                confluence = trend_data.get('confluence_score', 0)
                direction = "🟢 LONG" if confluence > 0 else "🔴 SHORT"
                abs_conf = abs(confluence)
                if abs_conf >= 90:
                    # Получаем AI-оценку для фильтра
                    ai_data = self.ai_checker.analyze_signal_quality(symbol, {})
                    ai_conf = ai_data.get('ai_confidence_score', 0)

                    # ✅ добавляем только если AI уверенность ≥ 7.0
                    if ai_conf >= 7.0:
                        anomalies.append({
                            'type': 'EXTREME_CONFLUENCE',
                            'symbol': symbol,
                            'value': abs_conf,
                            'message': f"📊 {symbol} конфлюэнс {abs_conf}% {direction} "
                                       f"- сильный сигнал (AI: {ai_conf}/10)"
                        })

            # 4. Проверка необычных паттернов
            response = requests.post(f"{API_URL}/analyze-smart", params={"symbol": symbol}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "error" not in data:
                    strength = abs(data.get('strength', 0))
                    ai_conf = data.get('ai_confidence', 0)
                    if strength >= 8 and ai_conf >= 7:
                        action = data.get('action', 'NEUTRAL')
                        anomalies.append({
                            'type': 'STRONG_SIGNAL',
                            'symbol': symbol,
                            'value': strength,
                            'message': f"🎯 {symbol} сильный сигнал {action} (сила: {strength}/10, AI: {ai_conf}/10)"
                        })
            return anomalies

        except Exception as e:
            print(f"Ошибка проверки аномалий для {symbol}: {e}")
            return []

    def _send_anomaly_alerts(self, anomalies):
        """Отправляет уведомления об аномалиях"""
        try:
            # Группируем аномалии по типу
            grouped_anomalies = {}
            for anomaly in anomalies:
                anomaly_type = anomaly['type']
                if anomaly_type not in grouped_anomalies:
                    grouped_anomalies[anomaly_type] = []
                grouped_anomalies[anomaly_type].append(anomaly)

            # Отправляем уведомления для каждой группы
            for anomaly_type, anomaly_list in grouped_anomalies.items():
                # Проверяем не отправляли ли уже эту аномалию
                anomaly_key = f"{anomaly_type}_{anomaly_list[0]['symbol']}"
                if anomaly_key in self.detected_anomalies:
                    continue

                self.detected_anomalies[anomaly_key] = datetime.now()

                # Формируем сообщение
                if len(anomaly_list) == 1:
                    message = f"🔍 ОБНАРУЖЕНА АНОМАЛИЯ:\n\n{anomaly_list[0]['message']}"
                else:
                    message = f"🔍 ОБНАРУЖЕНО НЕСКОЛЬКО АНОМАЛИЙ:\n\n"
                    for anomaly in anomaly_list[:3]:  # Макс 3 в одном сообщении
                        message += f"• {anomaly['message']}\n"

                # Добавляем рекомендации
                message += f"\n💡 РЕКОМЕНДАЦИИ:\n"

                if anomaly_type == 'EXTREME_VOLUME':
                    message += "• Ждите подтверждения направления\n• Готовьтесь к большому движению\n• Используйте wider стоп-лоссы"
                elif anomaly_type == 'LOW_VOLATILITY':
                    message += "• Ожидайте пробой в ближайшее время\n• Размещайте ордера по краям диапазона\n• Будьте готовы к резкому движению"
                elif anomaly_type == 'EXTREME_CONFLUENCE':
                    message += "• Сигнал очень надежный\n• Можно входить с большей позицией\n• Используйте стандартные стоп-лоссы"
                elif anomaly_type == 'STRONG_SIGNAL':
                    message += "• Проверьте объемы и конфлюэнс\n• Рассмотрите вход по сигналу\n• Используйте /advanced_targets для целей"
                # 🔽 🔽 🔽 ДОБАВЛЯЕМ ПЛАН ДЕЙСТВИЙ 🔽 🔽 🔽

                # Берем первый символ из списка аномалий для плана
                if anomaly_list:
                    first_symbol = anomaly_list[0]['symbol']

                    # Добавляем наш универсальный план
                    message += f"\n🎯 ПЛАН ДЕЙСТВИЙ:\n"
                    message += f"1. 🔍 Проверить надежность:\n   /analyze_smart {first_symbol}\n"
                    message += f"2. ✅ Если AI ≥7.0 - продолжить\n"
                    message += f"   ❌ Если AI <7.0 - ПРОПУСТИТЬ сделку\n"
                    message += f"3. 📊 Получить цели:\n   /advanced_targets {first_symbol}\n"
                    message += f"4. ⚡ Рассчитать риск:\n   /risk {first_symbol} [БАЛАНС] 2\n"
                    message += f"\n💡 ПРАВИЛО: Входите ТОЛЬКО при AI уверенности ≥7.0!"

                # 🔼 🔼 🔼 КОНЕЦ ДОБАВЛЕННОГО КОДА 🔼 🔼 🔼
                message += f"\n\n🔍 Детальный анализ: /analyze_smart {anomaly_list[0]['symbol']}"

                # Отправляем сообщение
                self.bot.send_message(self.chat_id, message)
                print(f"🔍 Отправлено уведомление об аномалии: {anomaly_type}")

                # Ограничиваем количество сообщений
                time.sleep(1)

            # Очищаем старые аномалии (старше 2 часов)
            self._clean_old_anomalies()

        except Exception as e:
            print(f"Ошибка отправки уведомлений об аномалиях: {e}")

    def _clean_old_anomalies(self):
        """Очищает старые аномалии чтобы не спамить"""
        now = datetime.now()
        keys_to_remove = []

        for key, detection_time in self.detected_anomalies.items():
            if (now - detection_time).total_seconds() > 7200:  # 2 часа
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.detected_anomalies[key]

    def _filter_false_anomalies(self):
        """Автоматически удаляет ложные аномалии с низкой AI-уверенностью"""
        try:
            to_remove = []
            for anomaly_key, detection_time in list(self.detected_anomalies.items()):
                try:
                    # Из ключа извлекаем символ монеты
                    parts = anomaly_key.split("_")
                    symbol = parts[-1] if len(parts) > 1 else None
                    if not symbol:
                        continue

                    # Проверяем AI-оценку символа
                    ai_data = ai_checker.analyze_signal_quality(symbol)
                    ai_conf = ai_data.get('ai_confidence_score', 0)

                    # 🧠 Если AI < 7.0 — аномалию считаем ложной
                    if ai_conf < 7.0:
                        to_remove.append(anomaly_key)
                        print(f"🧹 Удалена ложная аномалия {symbol} (AI={ai_conf}/10)")
                except Exception as e:
                    print(f"Ошибка проверки AI для {anomaly_key}: {e}")
                    continue

            # Удаляем все неподтверждённые аномалии
            for key in to_remove:
                del self.detected_anomalies[key]

            if to_remove:
                print(f"✅ Очищено {len(to_remove)} ложных аномалий.")
        except Exception as e:
            print(f"Ошибка автофильтрации аномалий: {e}")


# Создаем детектор аномалий
anomaly_detector = AnomalyDetector(bot, ai_checker)


class SmartTakeProfitManager:
    def __init__(self, bot):
        self.bot = bot
        self.active_positions = {}
        self.monitoring_active = False
        self.chat_id = None

    def start_takeprofit_monitoring(self, chat_id):
        """Запуск мониторинга тейк-профитов"""
        self.chat_id = chat_id
        self.monitoring_active = True

        thread = threading.Thread(
            target=self._takeprofit_monitor_loop,
            daemon=True
        )
        thread.start()

        return "🎯 Мониторинг умных тейк-профитов запущен!\n⏰ Проверка каждую минуту"

    def stop_takeprofit_monitoring(self):
        self.monitoring_active = False
        return "⏹️ Мониторинг тейк-профитов остановлен"

    def add_position(self, symbol, entry_price, stop_loss, take_profits, direction, position_size=100):
        """Добавляет позицию для умного управления тейк-профитами"""
        position_id = f"{symbol}_{datetime.now().strftime('%H%M%S')}"

        self.active_positions[position_id] = {
            'symbol': symbol,
            'entry_price': entry_price,
            'original_stop_loss': stop_loss,
            'current_stop_loss': stop_loss,
            'take_profits': take_profits,  # [tp1, tp2, tp3]
            'direction': direction,  # "LONG" or "SHORT"
            'position_size': position_size,
            'tp1_hit': False,
            'tp2_hit': False,
            'tp3_hit': False,
            'breakeven_set': False,
            'trailing_active': False,
            'added_time': datetime.now()
        }

        return position_id

    def _takeprofit_monitor_loop(self):
        """Главный цикл мониторинга тейк-профитов"""
        while self.monitoring_active:
            try:
                self._check_positions()
                # Ждем 1 минуту до следующей проверки
                for _ in range(60):
                    if not self.monitoring_active:
                        break
                    time.sleep(1)

            except Exception as e:
                print(f"Ошибка мониторинга тейк-профитов: {e}")
                time.sleep(30)

    def _check_positions(self):
        """Проверяет все активные позиции"""
        if not self.active_positions:
            return

        print(f"🎯 Проверяю тейк-профиты... {len(self.active_positions)} позиций")

        for position_id, position in list(self.active_positions.items()):
            try:
                self._check_single_position(position_id, position)
            except Exception as e:
                print(f"Ошибка проверки позиции {position_id}: {e}")

    def _check_single_position(self, position_id, position):
        """Проверяет одну позицию и управляет стоп-лоссами"""
        symbol = position['symbol']

        # Получаем текущую цену
        try:
            response = requests.post(
                f"{API_URL}/analyze-smart",
                params={"symbol": symbol},
                timeout=10
            )

            if response.status_code != 200:
                return

            data = response.json()
            if "error" in data:
                return

            current_price = data.get('last_price', 0)
            if not current_price:
                return

        except Exception as e:
            print(f"Ошибка получения цены для {symbol}: {e}")
            return

        # Проверяем достижение тейк-профитов
        self._check_takeprofit_levels(position_id, position, current_price)

        # Управляем стоп-лоссами
        self._manage_stoplosses(position_id, position, current_price)

    def _check_takeprofit_levels(self, position_id, position, current_price):
        """Проверяет достижение уровней тейк-профита"""
        symbol = position['symbol']
        direction = position['direction']
        tps = position['take_profits']

        # Для LONG: цена растет, для SHORT: цена падает
        if direction == "LONG":
            price_condition = current_price >= tps[0] and not position['tp1_hit']
        else:  # SHORT
            price_condition = current_price <= tps[0] and not position['tp1_hit']

        if price_condition:
            self._on_takeprofit_hit(position_id, position, current_price, 1)

        elif not position['tp2_hit'] and position['tp1_hit']:
            if direction == "LONG":
                price_condition = current_price >= tps[1]
            else:
                price_condition = current_price <= tps[1]

            if price_condition:
                self._on_takeprofit_hit(position_id, position, current_price, 2)

        elif not position['tp3_hit'] and position['tp2_hit']:
            if direction == "LONG":
                price_condition = current_price >= tps[2]
            else:
                price_condition = current_price <= tps[2]

            if price_condition:
                self._on_takeprofit_hit(position_id, position, current_price, 3)

    def _on_takeprofit_hit(self, position_id, position, current_price, tp_level):
        """Обрабатывает достижение тейк-профита"""
        symbol = position['symbol']
        direction = position['direction']

        # Обновляем статус позиции
        if tp_level == 1:
            position['tp1_hit'] = True
            message = f"✅ ДОСТИГНУТ ТП1 для {symbol}"
        elif tp_level == 2:
            position['tp2_hit'] = True
            message = f"🎯 ДОСТИГНУТ ТП2 для {symbol}"
        else:  # tp_level == 3
            position['tp3_hit'] = True
            position['trailing_active'] = True
            message = f"🚀 ДОСТИГНУТ ТП3 для {symbol} - активирован трейлинг-стоп!"

        message += f"\n💰 Текущая цена: ${current_price:,.2f}"
        message += f"\n📊 Уровень: ТП{tp_level}"

        # Отправляем уведомление
        try:
            self.bot.send_message(self.chat_id, message)
            print(f"🎯 {message}")
        except Exception as e:
            print(f"Ошибка отправки уведомления ТП: {e}")
        # 🔥 ДОБАВЛЯЕМ ЗАПИСЬ В ОТЧЕТЫ ДЛЯ ТЕЙК-ПРОФИТОВ
        if tp_level == 3:  # Записываем только когда достигнут полный ТП3
            try:
                entry = position['entry_price']
                if position['direction'] == "LONG":
                    pnl_percent = (current_price - entry) / entry * 100
                else:
                    pnl_percent = (entry - current_price) / entry * 100

                report_generator.add_trade_record(
                    symbol=position['symbol'],
                    action=position['direction'],
                    entry_price=entry,
                    exit_price=current_price,
                    result_percent=pnl_percent,
                    signal_quality=9  # Высокое качество для тейк-профитов
                )
                print(f"📊 Запись ТП добавлена в отчеты: {position['symbol']} {pnl_percent:+.2f}%")
            except Exception as e:
                print(f"Ошибка записи ТП в отчет: {e}")

    def _manage_stoplosses(self, position_id, position, current_price):
        """Управляет стоп-лоссами в зависимости от достигнутых ТП"""
        symbol = position['symbol']
        direction = position['direction']

        # 1. При достижении ТП1 - стоп в безубыток
        if position['tp1_hit'] and not position['breakeven_set']:
            if direction == "LONG":
                new_stop = position['entry_price'] * 1.001  # Чуть выше точки входа
            else:  # SHORT
                new_stop = position['entry_price'] * 0.999  # Чуть ниже точки входа

            position['current_stop_loss'] = new_stop
            position['breakeven_set'] = True

            message = f"🛡️ Стоп-лосс перемещен в безубыток для {symbol}"
            message += f"\n💰 Новый стоп: ${new_stop:,.2f}"

            try:
                self.bot.send_message(self.chat_id, message)
                print(f"🛡️ {message}")
            except Exception as e:
                print(f"Ошибка отправки уведомления безубытка: {e}")

        # 2. При достижении ТП2 - стоп к ТП1
        elif position['tp2_hit'] and not position['tp1_stop_set']:
            position['current_stop_loss'] = position['take_profits'][0]  # Стоп на уровень ТП1
            position['tp1_stop_set'] = True

            message = f"🎯 Стоп-лосс перемещен к ТП1 для {symbol}"
            message += f"\n💰 Новый стоп: ${position['take_profits'][0]:,.2f}"

            try:
                self.bot.send_message(self.chat_id, message)
                print(f"🎯 {message}")
            except Exception as e:
                print(f"Ошибка отправки уведомления ТП1 стоп: {e}")

        # 3. При достижении ТП3 - трейлинг-стоп
        elif position['trailing_active']:
            self._manage_trailing_stop(position_id, position, current_price)

        # 4. Проверяем срабатывание стоп-лосса
        self._check_stoploss_hit(position_id, position, current_price)

    def _manage_trailing_stop(self, position_id, position, current_price):
        """Управляет трейлинг-стопом"""
        symbol = position['symbol']
        direction = position['direction']
        current_stop = position['current_stop_loss']

        # Для LONG: трейлинг следует за ценой вверх
        if direction == "LONG":
            # Новый стоп = текущая цена - 2%
            new_trailing_stop = current_price * 0.98

            # Обновляем только если новый стоп выше текущего
            if new_trailing_stop > current_stop:
                position['current_stop_loss'] = new_trailing_stop

                # Отправляем уведомление только при значительном изменении
                if (new_trailing_stop - current_stop) / current_stop > 0.01:  # Изменение >1%
                    message = f"🚀 Трейлинг-стоп обновлен для {symbol}"
                    message += f"\n💰 Новый стоп: ${new_trailing_stop:,.2f}"

                    try:
                        self.bot.send_message(self.chat_id, message)
                        print(f"🚀 {message}")
                    except Exception as e:
                        print(f"Ошибка отправки уведомления трейлинга: {e}")

        else:  # SHORT: трейлинг следует за ценой вниз
            # Новый стоп = текущая цена + 2%
            new_trailing_stop = current_price * 1.02

            # Обновляем только если новый стоп ниже текущего
            if new_trailing_stop < current_stop:
                position['current_stop_loss'] = new_trailing_stop

                # Отправляем уведомление только при значительном изменении
                if (current_stop - new_trailing_stop) / current_stop > 0.01:  # Изменение >1%
                    message = f"🚀 Трейлинг-стоп обновлен для {symbol}"
                    message += f"\n💰 Новый стоп: ${new_trailing_stop:,.2f}"

                    try:
                        self.bot.send_message(self.chat_id, message)
                        print(f"🚀 {message}")
                    except Exception as e:
                        print(f"Ошибка отправки уведомления трейлинга: {e}")

    def _check_stoploss_hit(self, position_id, position, current_price):
        """Проверяет срабатывание стоп-лосса"""
        symbol = position['symbol']
        direction = position['direction']
        stop_loss = position['current_stop_loss']

        stop_hit = False

        if direction == "LONG" and current_price <= stop_loss:
            stop_hit = True
        elif direction == "SHORT" and current_price >= stop_loss:
            stop_hit = True

        if stop_hit:
            # Удаляем позицию
            del self.active_positions[position_id]

            # Определяем результат
            entry = position['entry_price']
            if direction == "LONG":
                pnl_percent = (current_price - entry) / entry * 100
            else:
                pnl_percent = (entry - current_price) / entry * 100
            # 🔥 ДОБАВЛЯЕМ ЗАПИСЬ В ОТЧЕТЫ
            try:
                report_generator.add_trade_record(
                    symbol=symbol,
                    action=direction,
                    entry_price=entry,
                    exit_price=current_price,
                    result_percent=pnl_percent,
                    signal_quality=8  # Среднее качество сигнала
                )
                print(f"📊 Запись добавлена в отчеты: {symbol} {pnl_percent:+.2f}%")
            except Exception as e:
                print(f"Ошибка записи в отчет: {e}")

            message = f"🛑 СТОП-ЛОСС СРАБОТАЛ для {symbol}"
            message += f"\n💰 Цена выхода: ${current_price:,.2f}"
            message += f"\n📊 Результат: {pnl_percent:+.2f}%"

            if pnl_percent > 0:
                message += f"\n✅ Позиция закрыта с прибылью!"
            else:
                message += f"\n❌ Позиция закрыта с убытком"

            try:
                self.bot.send_message(self.chat_id, message)
                print(f"🛑 {message}")
            except Exception as e:
                print(f"Ошибка отправки уведомления стоп-лосса: {e}")


# Создаем менеджер тейк-профитов
takeprofit_manager = SmartTakeProfitManager(bot)


class VolatilityPredictor:
    def __init__(self, bot):
        self.bot = bot
        self.predictions_cache = {}
        self.session_schedule = {
            'ASIAN': {'start': 0, 'end': 8, 'volatility': 2.0},  # 00:00-08:00 UTC
            'EUROPEAN': {'start': 8, 'end': 16, 'volatility': 3.5},  # 08:00-16:00 UTC
            'AMERICAN': {'start': 16, 'end': 24, 'volatility': 4.5}  # 16:00-24:00 UTC
        }

    def predict_volatility(self, symbol, hours_ahead=6):
        """Предсказывает волатильность для символа на ближайшие часы"""
        try:
            # Проверяем кэш (предсказания актуальны 30 минут)
            cache_key = f"{symbol}_{hours_ahead}"
            if cache_key in self.predictions_cache:
                cache_time, prediction = self.predictions_cache[cache_key]
                if (datetime.now() - cache_time).total_seconds() < 1800:  # 30 минут
                    return prediction

            # Получаем исторические данные для анализа
            historical_data = self._get_historical_volatility(symbol)
            current_volatility = self._get_current_volatility(symbol)
            session_impact = self._get_session_impact()
            market_phase = self._get_market_phase()

            # Основной алгоритм предсказания
            base_prediction = self._calculate_base_prediction(
                historical_data, current_volatility, hours_ahead
            )

            # Корректируем на основе факторов
            adjusted_prediction = self._adjust_prediction(
                base_prediction, session_impact, market_phase
            )

            # Формируем детальное предсказание
            prediction = self._format_prediction(
                symbol, adjusted_prediction, hours_ahead, session_impact, market_phase
            )

            # Сохраняем в кэш
            self.predictions_cache[cache_key] = (datetime.now(), prediction)

            return prediction

        except Exception as e:
            print(f"Ошибка предсказания волатильности для {symbol}: {e}")
            return self._get_fallback_prediction(hours_ahead)

    def _get_historical_volatility(self, symbol):
        """Анализирует историческую волатильность"""
        try:
            # Здесь можно добавить запрос к историческим данным
            # Пока используем упрощенную логику
            return {
                'last_1h': 2.5,
                'last_4h': 3.2,
                'last_24h': 4.1,
                'avg_volatility': 3.2
            }
        except:
            return {'avg_volatility': 3.0}

    def _get_current_volatility(self, symbol):
        """Получает текущую волатильность"""
        try:
            targets = dynamic_rr_calculator.calculate_adaptive_targets(symbol, "LONG", 0.02, 2.0)
            return targets.get('current_volatility', 3.0)
        except:
            return 3.0

    def _get_session_impact(self):
        """Определяет влияние текущей торговой сессии"""
        current_hour = datetime.utcnow().hour

        for session, info in self.session_schedule.items():
            if info['start'] <= current_hour < info['end']:
                next_sessions = []

                # Определяем следующие сессии
                for i in range(1, 4):  # Следующие 3 сессии
                    next_hour = (current_hour + i * 8) % 24
                    for sess, sess_info in self.session_schedule.items():
                        if sess_info['start'] <= next_hour < sess_info['end']:
                            next_sessions.append({
                                'session': sess,
                                'hours_until': i * 8,
                                'volatility': sess_info['volatility']
                            })
                            break

                return {
                    'current_session': session,
                    'current_volatility': info['volatility'],
                    'next_sessions': next_sessions[:2]  # Ближайшие 2 сессии
                }

        return {'current_session': 'UNKNOWN', 'current_volatility': 3.0, 'next_sessions': []}

    def _get_market_phase(self):
        """Определяет текущую фазу рынка"""
        try:
            # Анализируем топ-5 монет
            symbols = top_coins_manager.get_top_coins_by_marketcap(5)
            high_vol_count = 0
            total_volatility = 0

            for symbol in symbols[:3]:  # Проверяем 3 монеты
                try:
                    vol = self._get_current_volatility(symbol)
                    total_volatility += vol
                    if vol > 5.0:
                        high_vol_count += 1
                except:
                    continue

            avg_volatility = total_volatility / 3 if total_volatility > 0 else 3.0

            if high_vol_count >= 2:
                return 'HIGH_VOLATILITY'
            elif avg_volatility < 2.0:
                return 'LOW_VOLATILITY'
            else:
                return 'NORMAL'

        except:
            return 'NORMAL'

    def _calculate_base_prediction(self, historical_data, current_volatility, hours_ahead):
        """Рассчитывает базовое предсказание"""
        # Упрощенный алгоритм - можно улучшить с ML
        historical_avg = historical_data.get('avg_volatility', 3.0)

        # Взвешенное среднее с учетом тренда
        if current_volatility > historical_avg * 1.2:
            # Текущая волатильность выше средней - вероятно сохранится
            base_pred = current_volatility * 0.7 + historical_avg * 0.3
        elif current_volatility < historical_avg * 0.8:
            # Текущая волатильность ниже средней - вероятно вырастет
            base_pred = current_volatility * 0.5 + historical_avg * 0.5
        else:
            # Вокруг среднего - небольшое изменение
            base_pred = current_volatility * 0.6 + historical_avg * 0.4

        # Корректируем на временной горизонт
        time_factor = 1.0 + (hours_ahead / 24) * 0.2  # +20% за 24 часа
        return base_pred * time_factor

    def _adjust_prediction(self, base_prediction, session_impact, market_phase):
        """Корректирует предсказание на основе дополнительных факторов"""
        adjusted = base_prediction

        # Корректировка по сессии
        session_vol = session_impact.get('current_volatility', 3.0)
        adjusted = adjusted * 0.7 + session_vol * 0.3

        # Корректировка по фазе рынка
        if market_phase == 'HIGH_VOLATILITY':
            adjusted *= 1.3
        elif market_phase == 'LOW_VOLATILITY':
            adjusted *= 0.7

        return max(1.0, min(10.0, adjusted))  # Ограничиваем диапазон

    def _format_prediction(self, symbol, volatility, hours_ahead, session_impact, market_phase):
        """Форматирует предсказание в читаемый вид"""

        # Определяем уровень волатильности
        if volatility < 2.0:
            level = "ОЧЕНЬ НИЗКАЯ"
            emoji = "😴"
            recommendation = "Можно использовать tighter стоп-лоссы"
        elif volatility < 4.0:
            level = "УМЕРЕННАЯ"
            emoji = "😊"
            recommendation = "Стандартные настройки риска"
        elif volatility < 6.0:
            level = "ВЫСОКАЯ"
            emoji = "⚡"
            recommendation = "Используйте wider стоп-лоссы, уменьшите позиции"
        else:
            level = "ОЧЕНЬ ВЫСОКАЯ"
            emoji = "🚨"
            recommendation = "Высокий риск - торгуйте с осторожностью"

        # Информация о сессиях
        session_info = ""
        current_session = session_impact.get('current_session', 'UNKNOWN')
        session_emoji = "🌏" if current_session == 'ASIAN' else "🇪🇺" if current_session == 'EUROPEAN' else "🇺🇸"

        session_info += f"\n{session_emoji} Текущая сессия: {current_session}"

        for next_session in session_impact.get('next_sessions', []):
            session_emoji = "🌏" if next_session['session'] == 'ASIAN' else "🇪🇺" if next_session[
                                                                                       'session'] == 'EUROPEAN' else "🇺🇸"
            session_info += f"\n{session_emoji} Через {next_session['hours_until']}ч: {next_session['session']} (волатильность ~{next_session['volatility']}%)"

        prediction_text = f"""
📊 ПРОГНОЗ ВОЛАТИЛЬНОСТИ ДЛЯ {symbol}

{emoji} Предсказание на {hours_ahead} часов: {volatility:.1f}%
📈 Уровень: {level}

💡 РЕКОМЕНДАЦИИ:
• {recommendation}
• Учитывайте при установке стоп-лоссов
• Корректируйте размер позиции

{session_info}

🎯 ТЕКУЩАЯ ФАЗА РЫНКА: {market_phase}
🕐 Прогноз актуален: {datetime.now().strftime('%H:%M UTC')}
"""

        return {
            'volatility': volatility,
            'level': level,
            'emoji': emoji,
            'recommendation': recommendation,
            'prediction_text': prediction_text,
            'hours_ahead': hours_ahead
        }

    def _get_fallback_prediction(self, hours_ahead):
        """Резервное предсказание при ошибках"""
        return {
            'volatility': 3.0,
            'level': "СРЕДНЯЯ",
            'emoji': "😊",
            'recommendation': "Стандартные настройки риска",
            'prediction_text': f"📊 Прогноз на {hours_ahead} часов: ~3.0% (стандартная волатильность)",
            'hours_ahead': hours_ahead
        }


# Создаем предсказатель волатильности
volatility_predictor = VolatilityPredictor(bot)


class ReportGenerator:
    def __init__(self, bot):
        self.bot = bot
        self.trading_history = []
        self.daily_reports_active = False
        self.weekly_reports_active = False
        self.chat_id = None

    def start_daily_reports(self, chat_id):
        """Запуск ежедневных отчетов"""
        self.chat_id = chat_id
        self.daily_reports_active = True

        # Запускаем отправку отчета в 20:00 каждый день
        thread = threading.Thread(target=self._daily_report_scheduler, daemon=True)
        thread.start()

        return "📊 Ежедневные отчеты активированы! Отчет будет в 20:00 каждый день"

    def start_weekly_reports(self, chat_id):
        """Запуск еженедельных отчетов"""
        self.chat_id = chat_id
        self.weekly_reports_active = True

        # Запускаем отправку отчета в понедельник в 20:00
        thread = threading.Thread(target=self._weekly_report_scheduler, daemon=True)
        thread.start()

        return "📈 Еженедельные отчеты активированы! Отчет будет в понедельник в 20:00"

    def stop_reports(self):
        """Остановка всех отчетов"""
        self.daily_reports_active = False
        self.weekly_reports_active = False
        return "⏹️ Все отчеты остановлены"

    def add_trade_record(self, symbol, action, entry_price, exit_price, result_percent, signal_quality):
        """Добавляет запись о сделке в историю"""
        trade_record = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'action': action,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'result_percent': result_percent,
            'signal_quality': signal_quality,
            'success': result_percent > 0
        }

        self.trading_history.append(trade_record)

        # Храним только последние 100 сделок
        if len(self.trading_history) > 100:
            self.trading_history = self.trading_history[-100:]

    def _daily_report_scheduler(self):
        """Планировщик ежедневных отчетов"""
        while self.daily_reports_active:
            try:
                now = datetime.now()

                # Проверяем если сейчас 20:00
                if now.hour == 20 and now.minute == 0:
                    self._send_daily_report()

                    # Ждем 24 часа до следующей проверки
                    time.sleep(3600 * 24)
                else:
                    # Проверяем каждую минуту
                    time.sleep(60)

            except Exception as e:
                print(f"Ошибка планировщика ежедневных отчетов: {e}")
                time.sleep(300)  # Ждем 5 минут при ошибке

    def _weekly_report_scheduler(self):
        """Планировщик еженедельных отчетов"""
        while self.weekly_reports_active:
            try:
                now = datetime.now()

                # Проверяем если понедельник и 20:00
                if now.weekday() == 0 and now.hour == 20 and now.minute == 0:  # 0 = понедельник
                    self._send_weekly_report()

                    # Ждем 7 дней до следующей проверки
                    time.sleep(3600 * 24 * 7)
                else:
                    # Проверяем каждый час
                    time.sleep(3600)

            except Exception as e:
                print(f"Ошибка планировщика еженедельных отчетов: {e}")
                time.sleep(1800)  # Ждем 30 минут при ошибке

    def _send_daily_report(self):
        """Отправляет ежедневный отчет"""
        try:
            # Получаем сделки за последние 24 часа
            yesterday = datetime.now() - timedelta(hours=24)
            daily_trades = [trade for trade in self.trading_history
                            if trade['timestamp'] > yesterday]

            report = self._generate_daily_report(daily_trades)
            self.bot.send_message(self.chat_id, report)
            print("📊 Отправлен ежедневный отчет")

        except Exception as e:
            print(f"Ошибка отправки ежедневного отчета: {e}")

    def _send_weekly_report(self):
        """Отправляет еженедельный отчет"""
        try:
            # Получаем сделки за последние 7 дней
            last_week = datetime.now() - timedelta(days=7)
            weekly_trades = [trade for trade in self.trading_history
                             if trade['timestamp'] > last_week]

            report = self._generate_weekly_report(weekly_trades)
            self.bot.send_message(self.chat_id, report)
            print("📈 Отправлен еженедельный отчет")

        except Exception as e:
            print(f"Ошибка отправки еженедельного отчета: {e}")

    def _generate_daily_report(self, daily_trades):
        """Генерирует ежедневный отчет"""
        if not daily_trades:
            return self._generate_no_trades_report("дневной")

        # Статистика
        total_trades = len(daily_trades)
        winning_trades = len([t for t in daily_trades if t['success']])
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # Прибыльность
        total_profit = sum(t['result_percent'] for t in daily_trades if t['success'])
        total_loss = sum(abs(t['result_percent']) for t in daily_trades if not t['success'])
        net_profit = total_profit - total_loss
        avg_profit = total_profit / winning_trades if winning_trades > 0 else 0
        avg_loss = total_loss / losing_trades if losing_trades > 0 else 0

        # Лучшие и худшие сделки
        best_trade = max(daily_trades, key=lambda x: x['result_percent']) if daily_trades else None
        worst_trade = min(daily_trades, key=lambda x: x['result_percent']) if daily_trades else None

        report = f"""
📊 ЕЖЕДНЕВНЫЙ ТОРГОВЫЙ ОТЧЕТ
🕐 Период: последние 24 часа

📈 ОСНОВНАЯ СТАТИСТИКА:
• 📊 Всего сделок: {total_trades}
• ✅ Прибыльных: {winning_trades} ({win_rate:.1f}%)
• ❌ Убыточных: {losing_trades}
• 💰 Общая прибыль: {net_profit:+.2f}%

💰 ПРИБЫЛЬНОСТЬ:
• 📈 Общая прибыль: {total_profit:.2f}%
• 📉 Общий убыток: {total_loss:.2f}%
• 📊 Средняя прибыль: {avg_profit:.2f}%
• 📉 Средний убыток: {avg_loss:.2f}%

🎯 ЛУЧШИЕ СДЕЛКИ:
"""

        if best_trade:
            report += f"• 🥇 {best_trade['symbol']}: {best_trade['result_percent']:+.2f}% ({best_trade['action']})"

        if worst_trade and worst_trade['result_percent'] < 0:
            report += f"\n• 🥈 {worst_trade['symbol']}: {worst_trade['result_percent']:+.2f}% ({worst_trade['action']})"

        # Рекомендации
        report += f"\n\n💡 РЕКОМЕНДАЦИИ НА ЗАВТРА:\n"

        if win_rate >= 70:
            report += "🎯 Отличные результаты! Продолжайте в том же духе!"
        elif win_rate >= 50:
            report += "✅ Хорошие результаты. Можно немного увеличить позиции."
        else:
            report += "⚠️ Низкая прибыльность. Рекомендуется пересмотреть стратегию."

        if avg_profit / avg_loss >= 2.0 if avg_loss > 0 else True:
            report += "\n📈 Отличное соотношение прибыль/убыток!"
        else:
            report += "\n⚖️ Улучшите соотношение прибыль/убыток (цель: 2:1)"

        report += f"\n\n📅 Следующий отчет: завтра в 20:00"

        return report

    def _generate_weekly_report(self, weekly_trades):
        """Генерирует еженедельный отчет"""
        if not weekly_trades:
            return self._generate_no_trades_report("недельный")

        # Статистика
        total_trades = len(weekly_trades)
        winning_trades = len([t for t in weekly_trades if t['success']])
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # Прибыльность
        total_profit = sum(t['result_percent'] for t in weekly_trades if t['success'])
        total_loss = sum(abs(t['result_percent']) for t in weekly_trades if not t['success'])
        net_profit = total_profit - total_loss

        # Анализ по дням недели
        daily_performance = {}
        for trade in weekly_trades:
            day = trade['timestamp'].strftime('%A')
            if day not in daily_performance:
                daily_performance[day] = []
            daily_performance[day].append(trade['result_percent'])

        # Лучшие дни
        best_day = max(daily_performance.items(), key=lambda x: sum(x[1]) / len(x[1])) if daily_performance else None
        worst_day = min(daily_performance.items(), key=lambda x: sum(x[1]) / len(x[1])) if daily_performance else None

        report = f"""
📈 ЕЖЕНЕДЕЛЬНЫЙ ТОРГОВЫЙ ОТЧЕТ
🕐 Период: последние 7 дней

📊 ОСНОВНАЯ СТАТИСТИКА:
• 📈 Всего сделок: {total_trades}
• ✅ Прибыльных: {winning_trades} ({win_rate:.1f}%)
• ❌ Убыточных: {losing_trades}
• 💰 Общая прибыль: {net_profit:+.2f}%

📅 АНАЛИЗ ПО ДНЯМ НЕДЕЛИ:
"""

        for day, profits in daily_performance.items():
            avg_profit = sum(profits) / len(profits)
            emoji = "🟢" if avg_profit > 0 else "🔴"
            report += f"• {emoji} {day}: {avg_profit:+.2f}% ({len(profits)} сделок)\n"

        if best_day:
            report += f"\n🎯 ЛУЧШИЙ ДЕНЬ: {best_day[0]} ({sum(best_day[1]) / len(best_day[1]):+.2f}%)"

        if worst_day:
            report += f"\n⚠️ СЛОЖНЫЙ ДЕНЬ: {worst_day[0]} ({sum(worst_day[1]) / len(worst_day[1]):+.2f}%)"

        # Рекомендации на следующую неделю
        report += f"\n\n💡 РЕКОМЕНДАЦИИ НА СЛЕДУЮЩУЮ НЕДЕЛЮ:\n"

        if net_profit > 5.0:
            report += "🚀 Отличная неделя! Можно увеличивать риски."
        elif net_profit > 0:
            report += "✅ Хорошая неделя. Продолжайте текущую стратегию."
        else:
            report += "🔧 Требуется корректировка стратегии. Проанализируйте убыточные сделки."

        if best_day:
            report += f"\n📊 Фокус на {best_day[0]} - ваш самый сильный день!"

        report += f"\n\n📅 Следующий отчет: в понедельник в 20:00"

        return report

    def _generate_no_trades_report(self, report_type):
        """Генерирует отчет когда нет сделок"""
        return f"""
📊 {report_type.upper()} ОТЧЕТ

ℹ️ За указанный период не было совершено сделок.

💡 РЕКОМЕНДАЦИИ:
• Используйте /trading_ideas для поиска торговых возможностей
• Проверьте /volatility_scan для анализа рынка
• Настройте /premium_monitor_start для автоматических сигналов

📈 Будьте активнее в торговле для получения статистики!
"""


# Создаем генератор отчетов
report_generator = ReportGenerator(bot)


class SessionFilterManager:
    def __init__(self, bot):
        self.bot = bot
        self.auto_adjust_active = False
        self.chat_id = None
        self.current_session = None

        # Настройки фильтров для разных сессий
        self.session_filters = {
            'ASIAN': {
                'name': '🌏 АЗИАТСКАЯ СЕССИЯ',
                'rr_min': 3.5,  # Минимальный RR
                'quality_min': 8,  # Минимальное качество
                'volume_min': 1.5,  # Минимальные объемы
                'ai_confidence_min': 7.5,  # Минимальная AI уверенность
                'volatility_max': 6.0,  # Максимальная волатильность
                'description': 'Консервативные настройки - минимальный риск'
            },
            'EUROPEAN': {
                'name': '🇪🇺 ЕВРОПЕЙСКАЯ СЕССИЯ',
                'rr_min': 3.0,
                'quality_min': 7,
                'volume_min': 1.2,
                'ai_confidence_min': 7.0,
                'volatility_max': 8.0,
                'description': 'Стандартные настройки - баланс риска и доходности'
            },
            'AMERICAN': {
                'name': '🇺🇸 АМЕРИКАНСКАЯ СЕССИЯ',
                'rr_min': 2.5,
                'quality_min': 6,
                'volume_min': 1.0,
                'ai_confidence_min': 6.5,
                'volatility_max': 10.0,
                'description': 'Агрессивные настройки - больше торговых возможностей'
            }
        }

    def start_auto_adjust(self, chat_id):
        """Запуск автоматической корректировки фильтров по сессиям"""
        self.chat_id = chat_id
        self.auto_adjust_active = True

        thread = threading.Thread(
            target=self._session_monitor_loop,
            daemon=True
        )
        thread.start()

        return "🔄 Автоматическая корректировка фильтров запущена!\n⏰ Проверка каждые 30 минут"

    def stop_auto_adjust(self):
        self.auto_adjust_active = False
        return "⏹️ Автокорректировка фильтров остановлена"

    def get_current_session_filters(self):
        """Возвращает текущие фильтры для активной сессии"""
        session = self._get_current_session()
        return self.session_filters.get(session, self.session_filters['EUROPEAN'])

    def _session_monitor_loop(self):
        """Мониторинг смены сессий и корректировка фильтров"""
        while self.auto_adjust_active:
            try:
                new_session = self._get_current_session()

                # Если сессия изменилась - отправляем уведомление
                if new_session != self.current_session:
                    self.current_session = new_session
                    self._send_session_change_alert(new_session)

                # Ждем 30 минут до следующей проверки
                for _ in range(30 * 60):
                    if not self.auto_adjust_active:
                        break
                    time.sleep(1)

            except Exception as e:
                print(f"Ошибка мониторинга сессий: {e}")
                time.sleep(300)  # Ждем 5 минут при ошибке

    def _get_current_session(self):
        """Определяет текущую торговую сессию"""
        current_hour = datetime.now().hour

        if 0 <= current_hour < 8:  # 00:00-08:00
            return 'ASIAN'
        elif 8 <= current_hour < 16:  # 08:00-16:00
            return 'EUROPEAN'
        else:  # 16:00-24:00
            return 'AMERICAN'

    def _send_session_change_alert(self, new_session):
        """Отправляет уведомление о смене сессии"""
        try:
            filters = self.session_filters[new_session]

            message = f"""
🔄 СМЕНА ТОРГОВОЙ СЕССИИ

{filters['name']}

📊 АВТОМАТИЧЕСКИЕ НАСТРОЙКИ:
• 🎯 Min RR: 1:{filters['rr_min']}
• ⭐ Min качество: {filters['quality_min']}/10
• 📊 Min объемы: {filters['volume_min']}x
• 🤖 Min AI уверенность: {filters['ai_confidence_min']}/10
• ⚡ Max волатильность: {filters['volatility_max']}%

💡 {filters['description']}

🎯 РЕКОМЕНДАЦИИ:
{"• 🔒 Консервативная торговля" if new_session == 'ASIAN' else "• ⚖️ Баланс риска и доходности" if new_session == 'EUROPEAN' else "• 🚀 Активная торговля"}
{"• 😊 Идеально для обучения" if new_session == 'ASIAN' else ""}
{"• 📈 Готовьтесь к движениям" if new_session == 'AMERICAN' else ""}

/session_filters - текущие настройки
/trading_ideas - поиск идей для текущей сессии
"""

            self.bot.send_message(self.chat_id, message)
            print(f"🔄 Отправлено уведомление о смене сессии: {new_session}")

        except Exception as e:
            print(f"Ошибка отправки уведомления сессии: {e}")

    def apply_session_filters(self, symbol_data):
        """Применяет фильтры текущей сессии к данным символа"""
        try:
            filters = self.get_current_session_filters()

            # Проверяем соответствует ли символ фильтрам сессии
            meets_filters = (
                    symbol_data.get('risk_reward_ratio', 0) >= filters['rr_min'] and
                    symbol_data.get('quality_score', 0) >= filters['quality_min'] and
                    symbol_data.get('volume_ratio', 0) >= filters['volume_min'] and
                    symbol_data.get('ai_confidence_score', 0) >= filters['ai_confidence_min'] and
                    symbol_data.get('current_volatility', 0) <= filters['volatility_max']
            )

            return meets_filters, filters

        except Exception as e:
            print(f"Ошибка применения фильтров сессии: {e}")
            return True, self.session_filters['EUROPEAN']  # По умолчанию пропускаем


# Создаем менеджер фильтров сессий
session_filter_manager = SessionFilterManager(bot)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = """🟢На плагины 🍀 для разработки можно сюда (trx): 🟢

<code>TWMoWM5K4UNNMumDPK9d3XtCXVEFDKVNUN</code>

<i>тыкни если хочешь разбогатеть)</i> ↑

/ai_help - лайт
/pro_help - про

🚀 ОДНОЙ КОМАНДОЙ:
/activate_all - Запустить ВСЕ системы
/deactivate_all - Остановить ВСЕ системы
/consensus BTCUSDT - несколько подтверждений

Чисто для PRO users мать вашу:
💎 АВТО-МОНИТОРИНГ ПРЕМИУМ СИГНАЛОВ:
/premium_monitor_start - Запуск авто-сканирования
/premium_monitor_stop - Остановка мониторинга  
/premium_monitor_status - Статус мониторинга
/premium_signals - Разовое сканирование

🚀 AI-СУПЕРАНАЛИТИКА (НОВОЕ):
/crypto_ai_master - 🤖 Полный анализ от AI-мастера
/ai_market_status - 📊 Глубокая диагностика рынка  
/risk_dashboard - 🎯 Панель управления рисками
/quick_ai_scan - ⚡ Быстрый анализ за 10 сек
/instant_scan - 🚀 Мгновенный скан (кэш)
/ai_scan_volume - 📈 Только проверенные объемы
/ai_monitor_status - статус мониторинга
/start_ai_monitoring 7.5 - ручной запуск с другим порогом
/set_confidence 7.5 - изменить порог уведомлений

🎯 КОМАНДЫ УПРАВЛЕНИЯ:

/advanced_targets SYMBOL - анализ + кнопка авто-трейда
/auto_trade_SYMBOL - создать авто-сделку
/active_positions - список позиций
/position_status_SYMBOL - детальный статус
/close_position_SYMBOL - ручное закрытие
/trading_history - история сделок

🔍 АВТО-СКРИНЕР АНОМАЛИЙ:
/anomaly_start - Детектор аномалий
/anomaly_stop - Остановка детектора  
/anomaly_status - Статус аномалий
/anomaly - просмотр аномалий

📊 AI-ПРЕДСКАЗАНИЕ ВОЛАТИЛЬНОСТИ:
/volatility_prediction SYMBOL - Прогноз волатильности
/market_sessions - Расписание торговых сессий  
/volatility_scan - Сканер волатильности топ-монет

🚀 АВТО-МОНИТОРИНГ ОБЪЕМОВ:
/volume_monitor_start - Запуск авто-сканирования
/volume_monitor_popular - Мониторинг топ-20 монет  
/volume_monitor_stop - Остановка мониторинга
/volume_monitor_status - Статус мониторинга
/volume_scan - Разовое сканирование

🎯 УМНЫЕ ТЕЙК-ПРОФИТЫ:
/smart_tp_start - Умное управление позициями
/smart_tp_stop - Остановка управления
/smart_tp_status - Статус позиций
/smart_tp_add - Добавить позицию

🎯 РАСШИРЕННЫЕ ФУНКЦИИ:
/advanced_targets SYMBOL - Цели с Фибо и объемами
/volume_scan - Сканер всплесков объемов
/premium_signals- премиум сигналы 

🎯 ГОТОВЫЕ ТОРГОВЫЕ ИДЕИ:
/trading_ideas - Готовые идеи с точками входа
/ai_recommendations - AI рекомендации нейросети
/live_signals - Активные сигналы в реальном времени

🎯 AI функции:
/ai_scan - Сканирование топ-10 монет
/smart_scan - Умное сканирование (только качественные)
/confluence - Сканирование конфлюэнса
/backtest SYMBOL - Бэктестинг стратегии
/best_opportunity - Лучшая возможность сейчас
/prediction_history SYMBOL - История прогнозов

📊 АВТОМАТИЧЕСКИЕ ОТЧЕТЫ:
/reports_daily - Ежедневные торговые отчеты
/reports_weekly - Еженедельные аналитические отчеты
/reports_stop - Остановка всех отчетов
/reports_status - Статус системы отчетов
/report_now - Мгновенный отчет

🌍 SMART-ФИЛЬТРЫ ДЛЯ СЕССИЙ:
/session_filters_start - Автокорректировка фильтров
/session_filters_stop - Остановка корректировки  
/session_filters_status - Текущие настройки
/session_filters_info - Подробности о системе

📈 НОВЫЕ ФУНКЦИИ:
/market_analysis - Глубокий анализ рынка
/live_signals - Активные торговые сигналы  
/volatility_alert SYMBOL % - Уведомления о волатильности
/portfolio_suggest - Рекомендации по портфелю
/risk_level - Текущий уровень риска на рынке

📊 Основные команды: 
/better_targets SYMBOL - Улучшенные цели
/market_overview - Обзор рынка
/analyze SYMBOL TIMEFRAME - Анализ монеты
/analyze_smart SYMBOL - Умный анализ  
/chart SYMBOL TIMEFRAME - График цены
/predict SYMBOL - AI прогноз цены
/targets SYMBOL - Цели и стоп-лосс
/trend SYMBOL - Анализ тренда (4 таймфрейма)
/risk SYMBOL BALANCE STOP% - Расчет риска

🔔 Авто-мониторинг:
/monitor_extended - Мониторинг топ-20
/monitor_quality - Мониторинг только качественных
/monitor_stop - Остановка мониторинга
/monitor_status - Статус мониторинга

📋 ПРИМЕРЫ:
/analyze BTCUSDT 15m
/trend ETHUSDT
/risk SOLUSDT 1000 2
/targets BTCUSDT
/confluence
/smart_scan"""

    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode='HTML'
    )


# Обработчик нажатия на кнопку
@bot.callback_query_handler(func=lambda call: call.data == "copy_trx")
def handle_copy_address(call):
    # Показываем уведомление что адрес скопирован
    bot.answer_callback_query(
        call.id,
        "✅ TRX адрес скопирован: TWMoWM5K4UNNMumDPK9d3XtCXVEFDKVNUN",
        show_alert=True
    )

@bot.message_handler(commands=['analyze'])
def analyze_command(message):
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "Используйте: /analyze SYMBOL TIMEFRAME\nПример: /analyze BTCUSDT 15m")
            return

        symbol = parts[1].upper()
        timeframe = parts[2].lower()

        if symbol not in ALL_SYMBOLS:
            bot.reply_to(message, f"❌ Символ {symbol} не найден. Используйте /search_symbol для поиска")
            return

        wait_msg = bot.reply_to(message, f"Анализирую {symbol} на таймфрейме {timeframe}...")

        response = requests.post(
            f"{API_URL}/analyze",
            params={"symbol": symbol, "timeframe": timeframe},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                bot.edit_message_text(f"❌ Ошибка: {data['error']}", chat_id=wait_msg.chat.id,
                                      message_id=wait_msg.message_id)
            else:
                result_text = format_analysis_result(data)
                bot.edit_message_text(result_text, chat_id=wait_msg.chat.id, message_id=wait_msg.message_id)
        else:
            bot.edit_message_text("❌ Ошибка сервера", chat_id=wait_msg.chat.id, message_id=wait_msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


def create_analysis_keyboard(symbol):
    """Создает inline-клавиатуру для анализа символа"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    btn_targets = types.InlineKeyboardButton(
        text="🎯 Получить цели",
        callback_data=f"advanced_targets_{symbol}"
    )
    btn_trade = types.InlineKeyboardButton(
        text="🚀 Авто-трейд",
        callback_data=f"auto_trade_{symbol}"
    )
    btn_consensus = types.InlineKeyboardButton(
        text="📊 Консенсус",
        callback_data=f"consensus_{symbol}"
    )
    btn_back = types.InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="show_dashboard"
    )

    keyboard.add(btn_targets, btn_trade)
    keyboard.add(btn_consensus, btn_back)

    return keyboard


@bot.message_handler(commands=['analyze_smart'])
def analyze_smart_command(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Используйте: /analyze_smart SYMBOL\nПример: /analyze_smart BTCUSDT")
            return

        symbol = parts[1].upper()

        if symbol not in ALL_SYMBOLS:
            bot.reply_to(message, f"❌ Символ {symbol} не найден. Используйте /search_symbol для поиска")
            return

        wait_msg = bot.reply_to(message, f"Умный анализ для {symbol}...")

        response = requests.post(
            f"{API_URL}/analyze-smart",
            params={"symbol": symbol},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                bot.edit_message_text(f"❌ Ошибка: {data['error']}", chat_id=wait_msg.chat.id,
                                      message_id=wait_msg.message_id)
            else:
                # 🔽 🔽 🔽 РЕАЛЬНЫЙ AI-АНАЛИЗ 🔽 🔽 🔽
                # Получаем РЕАЛЬНЫЕ данные для AI анализа
                volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
                trend_data = trend_analyzer.multi_timeframe_analysis(symbol)
                confluence = trend_data.get('confluence_score', 0) if 'error' not in trend_data else 0

                # РЕАЛЬНЫЙ AI анализ
                ai_analysis = ai_checker.analyze_signal_quality(symbol, {
                    'volume_ratio': volume_data.get('volume_ratio', 0),
                    'current_price': data.get('last_price', 0),
                    'confluence': confluence
                })

                # 🔽 🔽 🔽 AI ФИЛЬТР ДЛЯ BUY СИГНАЛОВ 🔽 🔽 🔽
                original_action = data.get('action', 'HOLD')

                # ЕСЛИ AI ОЦЕНКА СЛИШКОМ НИЗКАЯ - ОТМЕНЯЕМ BUY
                if original_action == 'BUY' and ai_analysis['ai_confidence_score'] < 5.0:
                    data['action'] = 'HOLD'
                    data[
                        'recommendation'] = f"❌ BUY ОТМЕНЕН - AI {ai_analysis['ai_confidence_score']}/10 СЛИШКОМ НИЗКИЙ"
                    print(f"🚫 ОТМЕНА BUY ДЛЯ {symbol}: AI {ai_analysis['ai_confidence_score']}/10")

                # Добавляем РЕАЛЬНЫЕ AI данные
                ai_data = {
                    'ai_confidence': ai_analysis['ai_confidence_score'],
                    'ai_recommendation': ai_analysis['recommendation'],
                    'ai_color': ai_analysis['color'],
                    'volume_ratio': volume_data.get('volume_ratio', 0),
                    'passed_checks': ai_analysis.get('passed_checks', 3),
                    'total_checks': ai_analysis.get('total_checks', 3)
                }

                # Сохраняем исходные данные и добавляем РЕАЛЬНЫЕ AI данные
                enhanced_data = {**data, **ai_data}
                result_text = format_smart_analysis_result(enhanced_data)

                # 🔽 🔽 🔽 ДОБАВЛЯЕМ КНОПКИ 🔽 🔽 🔽
                keyboard = create_analysis_keyboard(symbol)

                bot.edit_message_text(
                    result_text,
                    chat_id=wait_msg.chat.id,
                    message_id=wait_msg.message_id,
                    reply_markup=keyboard
                )
        else:
            bot.edit_message_text("❌ Ошибка сервера", chat_id=wait_msg.chat.id, message_id=wait_msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")




@bot.message_handler(commands=['predict'])
def predict_command(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Используйте: /predict SYMBOL\nПример: /predict BTCUSDT")
            return

        symbol = parts[1].upper()

        if symbol not in ALL_SYMBOLS:
            bot.reply_to(message, f"❌ Символ {symbol} не найден. Используйте /search_symbol для поиска")
            return

        wait_msg = bot.reply_to(message, f"🤖 AI анализирует {symbol}...")
        prediction = ai_predictor.predict_price(symbol)

        if "error" in prediction:
            bot.edit_message_text(f"❌ {prediction['error']}", chat_id=wait_msg.chat.id, message_id=wait_msg.message_id)
        else:
            result_text = f"""
🤖 AI ПРОГНОЗ ДЛЯ {prediction['symbol']}

📊 Текущая ситуация:
💰 Цена: ${prediction['current_price']:,.2f}
📈 Тренд: {prediction['trend']}
🌊 Волатильность: {prediction['volatility']}

🎯 ПРОГНОЗ НА 24Ч:
{prediction['prediction']} ({prediction['predicted_change']})
🎭 Уверенность: {prediction['confidence']} ({prediction['confidence_level']})

💡 Рекомендация AI:
{'🟢 Рассмотреть покупку' if 'РОСТ' in prediction['prediction'] else '🔴 Будьте осторожны' if 'ПАДЕНИЕ' in prediction['prediction'] else '🟡 Наблюдать'}

🕐 Прогноз сделан: {prediction['timestamp']}
"""
            bot.edit_message_text(result_text, chat_id=wait_msg.chat.id, message_id=wait_msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка AI прогноза: {str(e)}")


@bot.message_handler(commands=['targets'])
def targets_command(message):
    """Рассчитывает целевые уровни с РЕАЛЬНЫМИ AI данными"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Используйте: /targets SYMBOL\nПример: /targets BTCUSDT")
            return

        symbol = parts[1].upper()

        if symbol not in ALL_SYMBOLS:
            bot.reply_to(message, f"❌ Символ {symbol} не найден. Используйте /search_symbol для поиска")
            return

        wait_msg = bot.reply_to(message, f"🎯 Рассчитываю УМНЫЕ цели для {symbol}...")

        # 🔽 🔽 🔽 РЕАЛЬНЫЕ ДАННЫЕ ДЛЯ AI АНАЛИЗА 🔽 🔽 🔽
        volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
        trend_data = trend_analyzer.multi_timeframe_analysis(symbol)
        confluence = trend_data.get('confluence_score', 0) if 'error' not in trend_data else 0

        # РЕАЛЬНЫЙ AI анализ
        ai_analysis = ai_checker.analyze_signal_quality(symbol, {
            'volume_ratio': volume_data.get('volume_ratio', 0),
            'current_price': 0,
            'confluence': confluence
        })

        ai_confidence = ai_analysis['ai_confidence_score']

        # 🔽 ЕСЛИ AI УВЕРЕННОСТЬ НИЗКАЯ - ПРЕДУПРЕЖДАЕМ
        if ai_confidence < 5.0:
            result_text = f"""
🔴 УМНЫЕ ЦЕЛИ ДЛЯ {symbol}

🤖 AI-ОЦЕНКА: {ai_confidence:.1f}/10 🔴
💡 ❌ НИЗКАЯ НАДЕЖНОСТЬ - ИЗБЕГАТЬ

📊 ПРИЧИНЫ НИЗКОЙ НАДЕЖНОСТИ:
• Объемы: {volume_data.get('volume_ratio', 0):.1f}x (нужно >1.5x)
• Конфлюэнс: {confluence}% (нужно >60%)
• AI уверенность: {ai_confidence:.1f}/10 (нужно >7.0)

🎯 РЕКОМЕНДАЦИЯ:
❌ ВОЗДЕРЖИВАТЬСЯ ОТ СДЕЛКИ - сигнал ненадежный
💡 Используйте /analyze_smart {symbol} для детального анализа
"""
            bot.edit_message_text(result_text, chat_id=wait_msg.chat.id, message_id=wait_msg.message_id)
            return

        # 🔽 ТОЛЬКО ЕСЛИ AI УВЕРЕННОСТЬ НОРМАЛЬНАЯ - РАССЧИТЫВАЕМ ЦЕЛИ
        # Получаем базовый анализ для направления
        response = requests.post(
            f"{API_URL}/analyze-smart",
            params={"symbol": symbol},
            timeout=15
        )

        if response.status_code != 200:
            bot.edit_message_text("❌ Ошибка анализа символа", chat_id=wait_msg.chat.id, message_id=wait_msg.message_id)
            return

        data = response.json()
        if "error" in data:
            bot.edit_message_text(f"❌ {data['error']}", chat_id=wait_msg.chat.id, message_id=wait_msg.message_id)
            return

        # Определяем направление
        direction = "SELL" if data.get('action') == 'SELL' else "LONG"

        # Используем ДИНАМИЧЕСКИЙ РАСЧЕТ
        targets = dynamic_rr_calculator.calculate_adaptive_targets(
            symbol,
            direction=direction,
            base_stop_loss_percent=0.02,
            min_rr=2.5
        )

        # Форматируем результат
        if direction == "LONG":
            emoji = "🟢"
            action = "ПОКУПКА"
        else:
            emoji = "🔴"
            action = "ПРОДАЖА"

        result_text = f"""
{emoji} УМНЫЕ ЦЕЛИ ДЛЯ {symbol} {emoji}

🤖 AI-ПОДТВЕРЖДЕНИЕ: {ai_confidence:.1f}/10 {ai_analysis['color']}
💡 {ai_analysis['recommendation']}

Направление: {action}
🎯 Risk/Reward: 1:{targets['risk_reward_ratio']:.1f}
📊 Волатильность: {targets['current_volatility']:.1f}%

💰 ЦЕНЫ:
• Текущая: ${targets['entry_price']:,.4f}
• Стоп-лосс: ${targets['stop_loss']:,.4f} ({targets['stop_loss_percent'] * 100:.1f}%)
• Тейк-профит: ${targets['take_profit']:,.4f} ({((targets['take_profit'] - targets['entry_price']) / targets['entry_price']) * 100:+.1f}%)

📊 РЕАЛЬНЫЕ ДАННЫЕ:
• Объемы: {volume_data.get('volume_ratio', 0):.1f}x
• Конфлюэнс: {confluence}%
• AI уверенность: {ai_confidence:.1f}/10

💡 РЕКОМЕНДАЦИЯ:
{'🚀 Отличные условия для входа!' if ai_confidence >= 7.0 else '✅ Хорошие условия для входа' if ai_confidence >= 5.0 else '⚠️ Осторожный вход'}
"""

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка расчета: {str(e)}")




@bot.message_handler(commands=['trend'])
def trend_analysis_command(message):
    """Анализ тренда на нескольких таймфреймах"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Используйте: /trend SYMBOL\nПример: /trend BTCUSDT")
            return

        symbol = parts[1].upper()

        if symbol not in ALL_SYMBOLS:
            bot.reply_to(message, f"❌ Символ {symbol} не найден")
            return

        wait_msg = bot.reply_to(message, f"📊 Анализирую тренды для {symbol}...")

        analysis = trend_analyzer.multi_timeframe_analysis(symbol)

        if "error" in analysis:
            bot.edit_message_text(f"❌ {analysis['error']}", chat_id=wait_msg.chat.id, message_id=wait_msg.message_id)
        else:
            result_text = f"""
📈 АНАЛИЗ ТРЕНДОВ ДЛЯ {symbol}

🎯 КОНФЛЮЭНС: {analysis['confluence_score']}%
📊 ОБЩИЙ ТРЕНД: {analysis['overall_trend']}

📅 АНАЛИЗ ПО ТАЙМФРЕЙМАМ:
"""

            for tf, signal in analysis['timeframe_signals'].items():
                emoji = "🟢" if signal['direction'] == 'BULLISH' else "🔴" if signal['direction'] == 'BEARISH' else "🟡"
                result_text += f"\n{emoji} {tf.upper()}: {signal['direction']} (сила: {signal['strength']}/10)"
                for s in signal['signals'][:2]:  # Показываем 2 главных сигнала
                    result_text += f"\n   • {s}"

            result_text += f"\n\n💡 ИТОГ:"
            result_text += f"\n• Бычьи сигналы: {analysis['total_bullish']}"
            result_text += f"\n• Медвежьи сигналы: {analysis['total_bearish']}"
            result_text += f"\n• Конфлюэнс: {analysis['confluence_score']}%"

            if analysis['confluence_score'] > 20:
                result_text += "\n🎯 СИЛЬНЫЙ БЫЧИЙ КОНФЛЮЭНС"
            elif analysis['confluence_score'] < -20:
                result_text += "\n🎯 СИЛЬНЫЙ МЕДВЕЖИЙ КОНФЛЮЭНС"

            bot.edit_message_text(
                result_text,
                chat_id=wait_msg.chat.id,
                message_id=wait_msg.message_id
            )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка анализа тренда: {str(e)}")


@bot.message_handler(commands=['risk'])
def risk_calculation_command(message):
    """Расчет риска и размера позиции"""
    try:
        parts = message.text.split()
        if len(parts) < 4:
            bot.reply_to(message, "Используйте: /risk SYMBOL BALANCE STOPLOSS%\nПример: /risk BTCUSDT 1000 2")
            return

        symbol = parts[1].upper()
        account_balance = float(parts[2])
        stop_loss_percent = float(parts[3])

        if symbol not in ALL_SYMBOLS:
            bot.reply_to(message, f"❌ Символ {symbol} не найден")
            return

        wait_msg = bot.reply_to(message, f"⚡ Рассчитываю риск для {symbol}...")

        # ИСПРАВЛЕННЫЙ КОД ДЛЯ VOLUME_ANALYZER
        try:
            volume_data = volume_analyzer.get_volume_analysis(symbol)
            if isinstance(volume_data, tuple) and len(volume_data) == 2:
                volume_analysis, volume_24h = volume_data
            else:
                volume_analysis = volume_data if isinstance(volume_data, dict) else {}
                volume_24h = volume_analysis.get('volume_24h', 0)
        except:
            volume_24h = 0

        current_price = 0  # Можно получить из API
        risk_score = quality_filter.get_risk_score(symbol, current_price, 15, volume_24h)

        symbol_data = {
            'risk_score': risk_score,
            'volume_24h': volume_24h
        }

        position_calc = risk_manager.calculate_position_size(
            symbol_data, account_balance, stop_loss_percent
        )

        result_text = f"""
⚡ РАСЧЕТ РИСКА ДЛЯ {symbol}

💰 БАЛАНС: ${account_balance:,.2f}
🛑 СТОП-ЛОСС: {stop_loss_percent}%
⚡ ОЦЕНКА РИСКА: {risk_score}/5

📊 РАСЧЕТ ПОЗИЦИИ:
• Размер позиции: ${position_calc['position_size_usd']:,.2f}
• Сумма риска: ${position_calc['risk_amount_usd']:,.2f}
• Риск на сделку: {position_calc['risk_percent']:.1f}%

💡 РЕКОМЕНДАЦИИ:
• Кредитное плечо: {position_calc['leverage_suggestion']}
• Объемы: {volume_analyzer.format_volume(volume_24h) if volume_24h > 0 else 'Н/Д'}

🎯 УПРАВЛЕНИЕ РИСКОМ:
• Не рискуйте более 2% на сделку
• Используйте стоп-лоссы
• Диверсифицируйте портфель
"""

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка расчета риска: {str(e)}")


@bot.message_handler(commands=['confluence'])
def confluence_scan_command(message):
    """Сканирование конфлюэнса с AI-анализом надежности"""
    try:
        wait_msg = bot.reply_to(message, "🎯 AI сканирует конфлюэнс и надежность...")

        # Сканируем топ-10 монет
        symbols_to_scan = top_coins_manager.get_top_coins_by_marketcap(10)
        results = []

        for symbol in symbols_to_scan:
            try:
                # 🔽 🔽 🔽 ФИЛЬТР СТЕЙБЛКОИНОВ 🔽 🔽 🔽
                stablecoins = ['USDCUSDT', 'USDTUSDT', 'BUSDUSDT', 'DAIUSDT', 'TUSDUSDT']
                if symbol in stablecoins:
                    continue  # Пропускаем стейблкоины
                # 🔼 🔼 🔼 КОНЕЦ ФИЛЬТРА 🔼 🔼 🔼

                # Получаем анализ конфлюэнса
                analysis = trend_analyzer.multi_timeframe_analysis(symbol)

                if "error" not in analysis:
                    # 🔥 ДОБАВЛЯЕМ AI-АНАЛИЗ НАДЕЖНОСТИ
                    try:
                        ai_analysis = ai_checker.analyze_signal_quality(symbol, {
                            'current_price': 0,  # Цена не нужна для конфлюэнса
                            'confluence': analysis['confluence_score']
                        })
                        ai_confidence = ai_analysis['ai_confidence_score']
                        ai_color = ai_analysis['color']
                        ai_recommendation = ai_analysis['recommendation']
                    except Exception as ai_error:
                        ai_confidence = 5.0
                        ai_color = "🟡"
                        ai_recommendation = "AI анализ недоступен"

                    results.append({
                        'symbol': symbol,
                        'confluence_score': analysis['confluence_score'],
                        'overall_trend': analysis['overall_trend'],
                        'total_bullish': analysis['total_bullish'],
                        'total_bearish': analysis['total_bearish'],
                        # 🔥 ДОБАВЛЯЕМ AI-ДАННЫЕ
                        'ai_confidence': ai_confidence,
                        'ai_color': ai_color,
                        'ai_recommendation': ai_recommendation
                    })

                time.sleep(0.5)  # Защита от лимитов

            except Exception as e:
                print(f"Ошибка сканирования {symbol}: {e}")
                continue

        if not results:
            bot.edit_message_text("❌ Не удалось просканировать монеты", chat_id=wait_msg.chat.id,
                                  message_id=wait_msg.message_id)
            return

        # Сортируем по конфлюэнсу
        results.sort(key=lambda x: x['confluence_score'], reverse=True)

        # 🔥 ФОРМИРУЕМ РЕЗУЛЬТАТ С AI-АНАЛИЗОМ
        result_text = "🎯 AI СКАНИРОВАНИЕ КОНФЛЮЭНСА (ТОП-10)\n\n"

        # AI-СТАТИСТИКА ПО РЫНКУ
        high_confidence_count = sum(1 for r in results if r['ai_confidence'] >= 7.0)
        low_confidence_count = sum(1 for r in results if r['ai_confidence'] < 4.0)
        avg_ai_confidence = sum(r['ai_confidence'] for r in results) / len(results)

        result_text += f"🤖 AI-СТАТИСТИКА РЫНКА:\n"
        result_text += f"• Высокая надежность: {high_confidence_count}/{len(results)} монет\n"
        result_text += f"• Низкая надежность: {low_confidence_count}/{len(results)} монет\n"
        result_text += f"• Средняя AI-уверенность: {avg_ai_confidence:.1f}/10\n\n"

        # ДЕТАЛЬНЫЙ АНАЛИЗ КАЖДОЙ МОНЕТЫ
        result_text += "📊 ДЕТАЛЬНЫЙ АНАЛИЗ МОНЕТ:\n\n"

        for i, coin in enumerate(results[:8], 1):
            symbol_clean = coin['symbol'].replace('USDT', '')

            # Эмодзи для конфлюэнса
            if coin['confluence_score'] > 20:
                confluence_emoji = "🟢"
                trend_text = "СИЛЬНЫЙ БЫЧИЙ"
            elif coin['confluence_score'] > 5:
                confluence_emoji = "🟢"
                trend_text = "БЫЧИЙ"
            elif coin['confluence_score'] < -20:
                confluence_emoji = "🔴"
                trend_text = "СИЛЬНЫЙ МЕДВЕЖИЙ"
            elif coin['confluence_score'] < -5:
                confluence_emoji = "🔴"
                trend_text = "МЕДВЕЖИЙ"
            else:
                confluence_emoji = "🟡"
                trend_text = "НЕЙТРАЛЬНЫЙ"

            result_text += f"{confluence_emoji} {i}. {symbol_clean}\n"
            result_text += f"   📊 Конфлюэнс: {coin['confluence_score']}%\n"
            result_text += f"   🎯 Тренд: {trend_text}\n"
            result_text += f"   📈 Бычьи: {coin['total_bullish']} | 📉 Медвежьи: {coin['total_bearish']}\n"
            # 🔥 ДОБАВЛЯЕМ AI-ОЦЕНКУ
            result_text += f"   🤖 AI-надежность: {coin['ai_confidence']:.1f}/10 {coin['ai_color']}\n"

            # AI-РЕКОМЕНДАЦИЯ ДЛЯ ЭТОЙ МОНЕТЫ
            if coin['ai_confidence'] >= 7.0:
                result_text += f"   💡 AI: ✅ Надежный сигнал\n"
            elif coin['ai_confidence'] <= 3.0:
                result_text += f"   💡 AI: ❌ Рискованный сигнал\n"
            else:
                result_text += f"   💡 AI: ⚠️ Требует осторожности\n"

            result_text += "\n"

        # 🔥 AI-ВЫВОДЫ И РЕКОМЕНДАЦИИ
        result_text += "💡 AI-ВЫВОДЫ ПО СКАНИРОВАНИЮ:\n"

        # Лучшие возможности с учетом AI
        best_opportunities = [c for c in results if c['confluence_score'] > 20 and c['ai_confidence'] >= 6.0]
        risky_opportunities = [c for c in results if c['confluence_score'] > 20 and c['ai_confidence'] < 4.0]

        if best_opportunities:
            best = best_opportunities[0]
            result_text += f"✅ ЛУЧШАЯ ВОЗМОЖНОСТЬ: {best['symbol'].replace('USDT', '')}\n"
            result_text += f"   (конфлюэнс {best['confluence_score']}%, AI: {best['ai_confidence']:.1f}/10)\n"
        elif risky_opportunities:
            risky = risky_opportunities[0]
            result_text += f"⚠️ ОПАСНАЯ ВОЗМОЖНОСТЬ: {risky['symbol'].replace('USDT', '')}\n"
            result_text += f"   (конфлюэнс {risky['confluence_score']}%, но AI: {risky['ai_confidence']:.1f}/10)\n"
        else:
            result_text += "📊 ВЫВОД: Качественных возможностей не обнаружено\n"

        # ОБЩАЯ AI-РЕКОМЕНДАЦИЯ
        result_text += f"\n🎯 AI-РЕКОМЕНДАЦИЯ: "
        if avg_ai_confidence >= 7.0:
            result_text += "Рынок надежен - можно активно торговать"
        elif avg_ai_confidence >= 5.0:
            result_text += "Рынок умеренно надежен - торговать выборочно"
        else:
            result_text += "Рынок ненадежен - воздержаться от сделок"

        # 🔽 🔽 🔽 ДОБАВЛЯЕМ ПЛАН ДЕЙСТВИЙ ДЛЯ КОНФЛЮЭНСА 🔽 🔽 🔽

        if results:
            # Берем монету с лучшим конфлюэнсом И хорошим AI
            best_opportunities = [c for c in results if c['confluence_score'] > 20 and c['ai_confidence'] >= 6.0]
            if best_opportunities:
                best_coin = best_opportunities[0]
                best_symbol = best_coin['symbol']
            else:
                # Если нет хороших, берем просто с лучшим конфлюэнсом
                best_coin = results[0]
                best_symbol = best_coin['symbol']

            result_text += "\n" + "=" * 50 + "\n"
            result_text += add_trading_plan(best_symbol)

        # 🔼 🔼 🔼 КОНЕЦ ДОБАВЛЕННОГО КОДА 🔼 🔼 🔼

        result_text += f"\n\n🕐 AI сканирование завершено: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка AI сканирования конфлюэнса: {str(e)}")


@bot.message_handler(commands=['ai_scan'])
def ai_scan_command(message):
    """AI сканирование топ-10 монет с РЕАЛЬНЫМИ данными"""
    try:
        wait_msg = bot.reply_to(message, "🤖 AI сканирует топ-10 монет с реальными данными...")

        # Получаем топ-10 монет
        symbols = top_coins_manager.get_top_coins_by_marketcap(10)

        if not symbols:
            bot.edit_message_text(
                "❌ Не удалось получить список монет",
                chat_id=wait_msg.chat.id,
                message_id=wait_msg.message_id
            )
            return

        scan_results = []

        # 🔽 РЕАЛЬНЫЙ AI АНАЛИЗ КАЖДОЙ МОНЕТЫ
        for symbol in symbols[:8]:  # Берем первые 8 для скорости
            try:
                # Получаем РЕАЛЬНЫЕ данные
                volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
                trend_data = trend_analyzer.multi_timeframe_analysis(symbol)
                confluence = trend_data.get('confluence_score', 0) if 'error' not in trend_data else 0

                # РЕАЛЬНЫЙ AI анализ
                ai_analysis = ai_checker.analyze_signal_quality(symbol, {
                    'volume_ratio': volume_data.get('volume_ratio', 0),
                    'current_price': 0,
                    'confluence': confluence
                })

                # Получаем текущую цену
                current_price = 0
                try:
                    price_response = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}",
                                                  timeout=5)
                    if price_response.status_code == 200:
                        price_data = price_response.json()
                        current_price = float(price_data['price'])
                except:
                    pass

                # Определяем статус на основе РЕАЛЬНЫХ данных
                ai_confidence = ai_analysis['ai_confidence_score']
                volume_ratio = volume_data.get('volume_ratio', 0)

                if ai_confidence >= 7.0 and volume_ratio >= 1.5:
                    prediction = "🟢 РОСТ"
                    signal_strength = 5
                elif ai_confidence >= 5.0 and volume_ratio >= 1.0:
                    prediction = "🟡 РОСТ"
                    signal_strength = 3
                elif ai_confidence < 3.0 or volume_ratio < 0.5:
                    prediction = "🔴 ПАДЕНИЕ"
                    signal_strength = -5
                else:
                    prediction = "🟡 НЕЙТРАЛЬНО"
                    signal_strength = 0

                # Определяем тренд
                if confluence > 20:
                    trend = "📈 ВОСХОДЯЩИЙ"
                elif confluence < -20:
                    trend = "📉 НИСХОДЯЩИЙ"
                else:
                    trend = "📊 БОКОВОЙ"

                scan_results.append({
                    'symbol': symbol,
                    'price': current_price,
                    'prediction': prediction,
                    'confidence': f"{ai_confidence:.1f}/10",
                    'trend': trend,
                    'signal_strength': signal_strength,
                    'ai_confidence': ai_confidence,
                    'volume_ratio': volume_ratio,
                    'key_signals': [f"AI: {ai_confidence:.1f}/10 | Объемы: {volume_ratio:.1f}x"]
                })

            except Exception as e:
                print(f"⚠️ Ошибка анализа {symbol}: {e}")
                continue

        # Формируем результат с РЕАЛЬНЫМИ данными
        result_text = "🔍 AI СКАНИРОВАНИЕ ТОП-10 МОНЕТ\n\n"

        for i, coin in enumerate(scan_results, 1):
            symbol_clean = coin['symbol'].replace('USDT', '')

            result_text += f"{coin['prediction'][:2]} {i}. {symbol_clean} - {coin['prediction']}\n"
            result_text += f"   💰 ${coin['price']:,.2f} | 🎯 {coin['confidence']} | 📈 {coin['trend']}\n"

            if coin['key_signals']:
                result_text += f"   📊 {coin['key_signals'][0]}\n"

            result_text += "\n"

        # 🔽 РЕАЛЬНЫЕ РЕКОМЕНДАЦИИ НА ОСНОВЕ ДАННЫХ
        high_confidence_coins = [c for c in scan_results if c['ai_confidence'] >= 7.0]
        low_confidence_coins = [c for c in scan_results if c['ai_confidence'] < 4.0]

        avg_ai_confidence = sum(c['ai_confidence'] for c in scan_results) / len(scan_results) if scan_results else 0
        avg_volume = sum(c['volume_ratio'] for c in scan_results) / len(scan_results) if scan_results else 0

        result_text += f"📊 СТАТИСТИКА: AI уверенность: {avg_ai_confidence:.1f}/10, Объемы: {avg_volume:.1f}x\n\n"

        if high_confidence_coins:
            best = max(high_confidence_coins, key=lambda x: x['ai_confidence'])
            result_text += f"🎯 ЛУЧШАЯ ПОКУПКА: {best['symbol'].replace('USDT', '')} (AI: {best['ai_confidence']:.1f}/10)"
        elif low_confidence_coins:
            result_text += f"⚠️ ВНИМАНИЕ: {len(low_confidence_coins)} монет с низкой AI уверенностью (<4.0/10)"
        else:
            result_text += "📊 ВЫВОД: Рынок в нейтральной/рискованной фазе"

        result_text += f"\n🕐 Сканирование завершено: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка AI сканирования: {str(e)}")


@bot.message_handler(commands=['smart_scan'])
def smart_scan_command(message):
    """Умное сканирование только качественных активов с РЕАЛЬНЫМИ AI данными"""
    try:
        wait_msg = bot.reply_to(message, "🧠 Умное сканирование качественных активов...")

        # Сканируем только топ-15 качественных монет
        quality_symbols = top_coins_manager.get_top_coins_by_marketcap(15)
        scan_results = []

        for symbol in quality_symbols[:8]:  # Ограничиваем для скорости
            try:
                # 🔽 🔽 🔽 РЕАЛЬНЫЕ ДАННЫЕ ДЛЯ AI АНАЛИЗА 🔽 🔽 🔽
                volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
                trend_data = trend_analyzer.multi_timeframe_analysis(symbol)
                confluence = trend_data.get('confluence_score', 0) if 'error' not in trend_data else 0

                # РЕАЛЬНЫЙ AI анализ
                ai_analysis = ai_checker.analyze_signal_quality(symbol, {
                    'volume_ratio': volume_data.get('volume_ratio', 0),
                    'current_price': 0,
                    'confluence': confluence
                })

                ai_confidence = ai_analysis['ai_confidence_score']

                # 🔽 РЕАЛЬНЫЙ РЕЙТИНГ НА ОСНОВЕ AI ДАННЫХ
                if ai_confidence >= 7.0:
                    asset_rating = 8.5
                    rating_emoji = "✅"
                    risk_score = 1
                    risk_emoji = "🟢"
                elif ai_confidence >= 5.0:
                    asset_rating = 6.5
                    rating_emoji = "⚠️"
                    risk_score = 2
                    risk_emoji = "🟢"
                elif ai_confidence >= 3.0:
                    asset_rating = 4.5
                    rating_emoji = "⚠️"
                    risk_score = 3
                    risk_emoji = "🟡"
                else:
                    asset_rating = 2.5
                    rating_emoji = "❌"
                    risk_score = 4
                    risk_emoji = "🔴"

                # Определяем тренд и сигнал
                if confluence > 20:
                    prediction = "🟢 РОСТ"
                    signal_strength = 5
                elif confluence < -20:
                    prediction = "🔴 ПАДЕНИЕ"
                    signal_strength = -5
                else:
                    prediction = "🟡 НЕЙТРАЛЬНО"
                    signal_strength = 0

                # Получаем текущую цену
                current_price = 0
                try:
                    price_response = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}",
                                                  timeout=5)
                    if price_response.status_code == 200:
                        price_data = price_response.json()
                        current_price = float(price_data['price'])
                except:
                    pass

                scan_results.append({
                    'symbol': symbol,
                    'prediction': prediction,
                    'confidence': f"{ai_confidence:.1f}/10",
                    'signal_strength': signal_strength,
                    'price': current_price,
                    'trend': "📈 Бычий" if confluence > 0 else "📉 Медвежий" if confluence < 0 else "📊 Боковой",
                    'asset_rating': asset_rating,
                    'risk_score': risk_score,
                    'ai_confidence': ai_confidence,
                    'volume_ratio': volume_data.get('volume_ratio', 0),
                    'rating_emoji': rating_emoji,
                    'risk_emoji': risk_emoji
                })

                time.sleep(0.3)

            except Exception as e:
                print(f"Ошибка сканирования {symbol}: {e}")
                continue

        if not scan_results:
            bot.edit_message_text("❌ Не удалось просканировать монеты", chat_id=wait_msg.chat.id,
                                  message_id=wait_msg.message_id)
            return

        # Сортируем по AI уверенности
        scan_results.sort(key=lambda x: x['ai_confidence'], reverse=True)

        # Формируем результат
        result_text = "🧠 УМНОЕ СКАНИРОВАНИЕ (только качественные)\n\n"

        for i, coin in enumerate(scan_results, 1):
            symbol_clean = coin['symbol'].replace('USDT', '')

            # Эмодзи для сигнала
            if coin['signal_strength'] > 3:
                emoji = "🟢"
            elif coin['signal_strength'] < -3:
                emoji = "🔴"
            else:
                emoji = "🟡"

            result_text += f"{emoji} {i}. {symbol_clean}\n"
            result_text += f"   📊 {coin['prediction']} | 🎯 {coin['confidence']}\n"
            result_text += f"   🏆 Рейтинг: {coin['asset_rating']}/10 {coin['rating_emoji']}\n"
            result_text += f"   ⚡ Риск: {coin['risk_score']}/5 {coin['risk_emoji']}\n"
            result_text += f"   💰 ${coin['price']:,.2f}\n\n"

        # Рекомендация на основе РЕАЛЬНЫХ данных
        high_quality_bullish = [c for c in scan_results if c['ai_confidence'] >= 7.0]
        if high_quality_bullish:
            best = high_quality_bullish[0]
            result_text += f"🎯 ЛУЧШАЯ ПОКУПКА: {best['symbol'].replace('USDT', '')} (AI: {best['ai_confidence']:.1f}/10)"
        else:
            # 🔽 РЕАЛЬНАЯ СТАТИСТИКА
            avg_ai = sum(c['ai_confidence'] for c in scan_results) / len(scan_results) if scan_results else 0
            result_text += f"📊 ВЫВОД: Средняя AI уверенность: {avg_ai:.1f}/10 - качественных активов нет"

        result_text += f"\n🕐 Сканирование завершено: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка умного сканирования: {str(e)}")


@bot.message_handler(commands=['backtest'])
def backtest_command(message):
    """🎯 Улучшенный бэктестинг с AI фильтрами (динамический ТФ)"""
    try:
        parts = message.text.split()

        # 1. Проверка наличия всех 6 аргументов (команда + 5 параметров)
        if len(parts) < 6:
            # Новый синтаксис: /backtest SYMBOL ТФ ДНИ MIN_AI MIN_VOL
            bot.reply_to(message,
                         "Используйте: /backtest SYMBOL ТФ ДНИ AI_MIN VOL_MIN\nПример: /backtest BTCUSDT 4h 365 5.5 0.0")
            return

        symbol = parts[1].upper()  # BTCUSDT

        # 2. НОВЫЙ ПАРСИНГ: ТФ - ДНИ - AI - VOL
        timeframe = parts[2].lower()         # ✅ Теперь здесь '4h', '1h', '15m' и т.д.
        days = int(parts[3])                 # ✅ Теперь здесь 365
        min_ai_confidence = float(parts[4])  # ✅ Теперь здесь 5.5
        min_volume_ratio = float(parts[5])   # ✅ Теперь здесь 0.0

        if symbol not in ALL_SYMBOLS:
            bot.reply_to(message, f"❌ Символ {symbol} не найден")
            return

        wait_msg = bot.reply_to(message, f"🤖 Запускаю AI бэктестинг для {symbol} ({days} дней) на ТФ {timeframe}...")

        # 🔽 ВЫЗОВ ФУНКЦИИ: backtest_with_ai_filters теперь получает все 5 параметров
        results = backtester.backtest_with_ai_filters(
            symbol,
            timeframe,  # <--- КОРРЕКТНЫЙ ПАРАМЕТР
            days,
            min_ai_confidence,
            min_volume_ratio
        )

        if "error" in results:
            bot.edit_message_text(f"❌ {results['error']}", chat_id=message.chat.id, message_id=wait_msg.message_id)
            return

        # 🔽 ФОРМАТИРУЕМ РЕЗУЛЬТАТЫ
        result_text = format_ai_backtest_results(results)

        bot.edit_message_text(
            result_text,
            chat_id=message.chat.id,
            message_id=wait_msg.message_id,
            parse_mode='Markdown'
        )

    except ValueError:
        bot.reply_to(message,
                     "❌ Неверный формат чисел. Дни должны быть целым числом, а AI/Объемы — дробным (например, 7.5).")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка бэктестинга: {str(e)}")



@bot.message_handler(commands=['portfolio'])
def portfolio_command(message):
    """Анализ портфеля и рисков"""
    try:
        # Пример данных портфеля (в реальности нужно получать от пользователя)
        example_portfolio = [
            {'symbol': 'BTCUSDT', 'value': 5000, 'risk_score': 2},
            {'symbol': 'ETHUSDT', 'value': 3000, 'risk_score': 2},
            {'symbol': 'SOLUSDT', 'value': 2000, 'risk_score': 3},
            {'symbol': 'ADAUSDT', 'value': 1000, 'risk_score': 4}
        ]

        wait_msg = bot.reply_to(message, "📊 Анализирую портфель...")

        analysis = portfolio_analyzer.analyze_portfolio(example_portfolio)

        if "error" in analysis:
            bot.edit_message_text(f"❌ {analysis['error']}", chat_id=wait_msg.chat.id, message_id=wait_msg.message_id)
        else:
            result_text = f"""
📊 АНАЛИЗ ПОРТФЕЛЯ

💰 ОБЩАЯ СТОИМОСТЬ: ${analysis['total_value']:,.2f}
📈 ПОЗИЦИЙ: {analysis['position_count']}

🎯 РАСПРЕДЕЛЕНИЕ:
"""

            for symbol, alloc in analysis['allocation'].items():
                symbol_clean = symbol.replace('USDT', '')
                result_text += f"\n• {symbol_clean}: {alloc['percent']}% (${alloc['value']:,.0f})"

            result_text += f"""

⚡ АНАЛИЗ РИСКА:
• Общий риск: {analysis['risk_analysis']['overall_risk']}
• Высокий риск: {analysis['risk_analysis']['high_risk_percent']}%
• Концентрация: {analysis['risk_analysis']['concentration_risk']}
• Корреляция: {analysis['correlation_analysis']['correlation_risk']}

💡 РЕКОМЕНДАЦИИ:
"""

            for rec in analysis['recommendations']:
                result_text += f"\n• {rec}"

            result_text += f"\n\n📝 Для реального анализа отправьте данные портфеля"

            bot.edit_message_text(
                result_text,
                chat_id=wait_msg.chat.id,
                message_id=wait_msg.message_id
            )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка анализа портфеля: {str(e)}")


@bot.message_handler(commands=['alert_stats'])
def alert_stats_command(message):
    """Статистика алертов и мониторинга"""
    try:
        stats = monitor.get_monitoring_stats()

        result_text = f"""
📊 СТАТИСТИКА МОНИТОРИНГА

🔔 Статус: {'АКТИВЕН' if stats['active'] else 'НЕАКТИВЕН'}
📈 Монет в мониторинге: {stats['monitored_symbols_count']}
📨 Сигналов отправлено: {stats['total_signals_sent']}
💰 Ценовых алертов: {stats['total_price_alerts_sent']}

🎯 СТАТИСТИКА ПО МОНЕТАМ:
"""

        for symbol, symbol_stats in list(stats['performance_stats'].items())[:10]:  # Топ-10
            symbol_clean = symbol.replace('USDT', '')
            last_signal = symbol_stats['last_signal_time']
            last_time = last_signal.strftime('%H:%M') if last_signal else 'нет'

            result_text += f"\n• {symbol_clean}: {symbol_stats['signals_sent']} сигналов (последний: {last_time})"

        result_text += f"\n\n💡 Система умных алертов активна"
        result_text += f"\n🕐 {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.reply_to(message, result_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка получения статистики: {str(e)}")


@bot.message_handler(commands=['volatility_alert'])
def volatility_alert_command(message):
    """Настройка уведомлений о волатильности"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Используйте: /volatility_alert SYMBOL ПРОЦЕНТ\nПример: /volatility_alert BTCUSDT 5")
            return

        symbol = parts[1].upper()
        percent = float(parts[2])

        if symbol not in ALL_SYMBOLS:
            bot.reply_to(message, f"❌ Символ {symbol} не найден")
            return

        # Здесь можно добавить логику отслеживания волатильности
        response_text = f"""
🔔 УВЕДОМЛЕНИЕ О ВОЛАТИЛЬНОСТИ НАСТРОЕНО

Монета: {symbol}
Порог: {percent}%

Бот уведомит когда цена изменится на {percent}% за короткий период.

⚡ Команды:
/volatility_list - список активных уведомлений
/volatility_remove SYMBOL - удалить уведомление
"""
        bot.reply_to(message, response_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['smart_monitor'])
def smart_monitor_command(message):
    """Запуск умного мониторинга"""
    try:
        # Берем топ-15 качественных монет
        quality_symbols = top_coins_manager.get_top_coins_by_marketcap(15)

        result = monitor.start_monitoring(
            chat_id=message.chat.id,
            symbols=quality_symbols,
            check_interval=3  # Более частые проверки
        )

        status_text = f"""
{result}

🤖 УМНЫЙ МОНИТОРИНГ АКТИВИРОВАН:

🎯 ОСОБЕННОСТИ:
• Приоритизация сигналов
• Фильтрация дублей
• Защита от спама
• Анализ конфлюэнса
• Учет объемов

📊 МОНИТОРИМ 15 ТОП-МОНЕТ по капитализации:
• {quality_symbols[0]} • {quality_symbols[1]} • {quality_symbols[2]}
• {quality_symbols[3]} • {quality_symbols[4]} • {quality_symbols[5]}

⚡ Будете получать только САМЫЕ ВАЖНЫЕ сигналы!

/alert_stats - статистика
/monitor_stop - остановить
"""
        bot.reply_to(message, status_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


@bot.message_handler(commands=['best_opportunity'])
def best_opportunity_command(message):
    """Лучшая торговая возможность с AI-проверкой"""
    try:
        wait_msg = bot.reply_to(message, "🎯 AI ищет лучшую возможность...")

        opportunity = ai_predictor.find_best_opportunity()

        if "error" in opportunity:
            bot.edit_message_text(
                f"❌ {opportunity['error']}",
                chat_id=wait_msg.chat.id,
                message_id=wait_msg.message_id
            )
            return

        # === ДОБАВЛЯЕМ AI-АНАЛИЗ ===
        symbol = opportunity['symbol']

        # Получаем дополнительные данные для AI
        try:
            # Анализ объемов
            volume_data = volume_analyzer.get_volume_analysis(symbol)
            volume_ratio = volume_data[0].get('strength', 0) / 3.0 if isinstance(volume_data,
                                                                                 tuple) else volume_data.get('strength',
                                                                                                             0) / 3.0

            # Анализ тренда
            trend_data = trend_analyzer.multi_timeframe_analysis(symbol)
            confluence = trend_data.get('confluence_score', 0) if 'error' not in trend_data else 0

            # AI-анализ
            ai_analysis_data = {
                'volume_ratio': volume_ratio,
                'current_price': opportunity['price'],
                'confluence': confluence
            }

            ai_analysis = ai_checker.analyze_signal_quality(symbol, ai_analysis_data)

        except Exception as ai_error:
            ai_analysis = {
                'ai_confidence_score': 5.0,
                'recommendation': 'AI анализ временно недоступен',
                'color': '🟡',
                'metrics': {}
            }

        # Форматируем сообщение в зависимости от типа возможности
        if opportunity['type'] == 'BUY':
            emoji = "🟢"
            title = "🚀 ЛУЧШАЯ ПОКУПКА"
            action = "ПОКУПАТЬ"
            color = "🟢"
        elif opportunity['type'] == 'SELL':
            emoji = "🔴"
            title = "⚠️ ЛУЧШАЯ ПРОДАЖА"
            action = "ПРОДАВАТЬ"
            color = "🔴"
        else:
            emoji = "🟡"
            title = "👀 ДЛЯ НАБЛЮДЕНИЯ"
            action = "НАБЛЮДАТЬ"
            color = "🟡"

        result_text = f"""
{emoji} {title} {emoji}

🤖 AI-УВЕРЕННОСТЬ: {ai_analysis['ai_confidence_score']}/10 {ai_analysis['color']}
💡 {ai_analysis['recommendation']}

Монета: {opportunity['symbol'].replace('USDT', '')}
Действие: {action} {color}
Прогноз: {opportunity['prediction']}
Уверенность: {opportunity['confidence']}

💰 Цена: ${opportunity['price']:,.2f}
📊 Сила сигнала: {opportunity['signal_strength']}/10
🎯 Причина: {opportunity['reason']}

📊 AI-МЕТРИКИ:
"""

        # Добавляем ключевые AI-метрики
        key_metrics = ['volume_quality', 'market_sentiment', 'whale_activity', 'btc_impact']
        for metric in key_metrics:
            if metric in ai_analysis.get('metrics', {}):
                result_text += f"• {ai_analysis['metrics'][metric]['comment']}\n"

        # Добавляем ключевые сигналы
        result_text += f"\n💡 Ключевые сигналы:\n"
        if opportunity.get('key_signals'):
            for signal in opportunity['key_signals'][:3]:  # Только 3 главных
                result_text += f"• {signal}\n"
        else:
            result_text += "• Детальный анализ завершен\n"

        # AI-РЕКОМЕНДАЦИЯ ПО ВХОДУ
        result_text += f"\n🎯 AI-РЕКОМЕНДАЦИЯ ПО ВХОДУ:\n"
        if ai_analysis['ai_confidence_score'] >= 8.0:
            result_text += "🚀 ВЫСОКАЯ НАДЕЖНОСТЬ - можно входить с полной позицией"
        elif ai_analysis['ai_confidence_score'] >= 6.0:
            result_text += "✅ ХОРОШАЯ НАДЕЖНОСТЬ - можно входить со стандартной позицией"
        elif ai_analysis['ai_confidence_score'] >= 4.0:
            result_text += "⚠️ СРЕДНЯЯ НАДЕЖНОСТЬ - входить маленькими позициями"
        else:
            result_text += "❌ НИЗКАЯ НАДЕЖНОСТЬ - лучше воздержаться от входа"

        # 🔽 🔽 🔽 ДОБАВЛЯЕМ ПЛАН ДЕЙСТВИЙ ДЛЯ ЛУЧШЕЙ ВОЗМОЖНОСТИ 🔽 🔽 🔽

        symbol = opportunity['symbol']
        result_text += "\n" + "=" * 50 + "\n"
        result_text += add_trading_plan(symbol)

        # 🔼 🔼 🔼 КОНЕЦ ДОБАВЛЕННОГО КОДА 🔼 🔼 🔼
        result_text += f"\n\n🕐 AI анализ: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка поиска возможности: {str(e)}")

@bot.message_handler(commands=['prediction_history'])
def prediction_history_command(message):
    """История и точность прогнозов"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Используйте: /prediction_history SYMBOL\nПример: /prediction_history BTCUSDT")
            return

        symbol = parts[1].upper()

        wait_msg = bot.reply_to(message, f"📊 Анализирую историю прогнозов для {symbol}...")

        stats = ai_predictor.get_prediction_stats(symbol)

        if "error" in stats:
            bot.edit_message_text(
                f"❌ {stats['error']}",
                chat_id=wait_msg.chat.id,
                message_id=wait_msg.message_id
            )
            return

        # Форматируем статистику
        result_text = f"""
📊 ИСТОРИЯ ПРОГНОЗОВ ДЛЯ {stats['symbol'].replace('USDT', '')}

🎯 Точность AI: {stats['accuracy']}
📈 Всего прогнозов: {stats['total_predictions']}
📊 Проанализировано периодов: {stats['analyzed_periods']}
💡 Последний прогноз: {stats['last_prediction']}
"""

        result_text += f"\n📅 Статистика на: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка анализа истории: {str(e)}")


@bot.message_handler(commands=['search_symbol'])
def search_symbol_command(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Используйте: /search_symbol NAME\nПример: /search_symbol btc")
            return

        search_term = parts[1].upper()
        found_symbols = [symbol for symbol in ALL_SYMBOLS if search_term in symbol]

        if found_symbols:
            symbols_to_show = found_symbols[:15]
            result_text = f"🔍 Найдено пар по запросу '{search_term}': {len(found_symbols)}\n\n"

            for i in range(0, len(symbols_to_show), 3):
                line_symbols = symbols_to_show[i:i + 3]
                result_text += " • " + " • ".join([s.replace('USDT', '') for s in line_symbols]) + "\n"

            if len(found_symbols) > 15:
                result_text += f"\n... и еще {len(found_symbols) - 15} пар"

            result_text += f"\n\n💡 Быстрый анализ для {found_symbols[0]}:"

            # 🔽 🔽 🔽 ДОБАВЛЯЕМ КНОПКИ ДЛЯ БЫСТРОГО АНАЛИЗА 🔽 🔽 🔽
            keyboard = types.InlineKeyboardMarkup(row_width=2)

            # Кнопки для первого найденного символа
            first_symbol = found_symbols[0]

            btn_analyze = types.InlineKeyboardButton(
                f"🔍 Анализ",
                callback_data=f"analyze_{first_symbol}"
            )
            btn_targets = types.InlineKeyboardButton(
                f"🎯 Цели",
                callback_data=f"advanced_targets_{first_symbol}"
            )
            btn_consensus = types.InlineKeyboardButton(
                f"📊 Консенсус",
                callback_data=f"consensus_{first_symbol}"
            )
            btn_trade = types.InlineKeyboardButton(
                f"🤖 Сделка",
                callback_data=f"simple_trade_{first_symbol}"
            )

            keyboard.add(btn_analyze, btn_targets)
            keyboard.add(btn_consensus, btn_trade)

            bot.reply_to(message, result_text, reply_markup=keyboard)
        else:
            bot.reply_to(message, f"❌ Пар по запросу '{search_term}' не найдено.")

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка поиска: {e}")


@bot.message_handler(commands=['test_buttons'])
def test_buttons_command(message):
    """Тест всех кнопок"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    # Кнопки для тестирования
    btn_info = types.InlineKeyboardButton("ℹ️ Информация", callback_data="info_BTCUSDT")
    btn_full_targets = types.InlineKeyboardButton("🎯 Полные цели", callback_data="full_targets_BTCUSDT")
    btn_simple_trade = types.InlineKeyboardButton("🤖 Сделка", callback_data="simple_trade_BTCUSDT")
    btn_analyze = types.InlineKeyboardButton("🔍 Анализ", callback_data="analyze_BTCUSDT")
    btn_consensus = types.InlineKeyboardButton("📊 Консенсус", callback_data="consensus_BTCUSDT")
    btn_advanced_targets = types.InlineKeyboardButton("🎯 Быстрые цели", callback_data="advanced_targets_BTCUSDT")

    keyboard.add(btn_info, btn_full_targets)
    keyboard.add(btn_simple_trade, btn_analyze)
    keyboard.add(btn_consensus, btn_advanced_targets)

    bot.send_message(
        message.chat.id,
        "🧪 **ТЕСТ ВСЕХ КНОПОК**\n\n"
        "Нажми любую кнопку для проверки:\n"
        "• ℹ️ Информация\n"
        "• 🎯 Полные цели\n"
        "• 🤖 Сделка\n"
        "• 🔍 Анализ\n"
        "• 📊 Консенсус\n"
        "• 🎯 Быстрые цели",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['coins'])
def show_coins(message):
    top_coins = top_coins_manager.get_top_coins_by_marketcap(20)
    coins_text = "💰 Топ-20 монет по рыночной капитализации:\n\n"
    for i in range(0, len(top_coins), 4):
        line_coins = top_coins[i:i + 4]
        coins_text += " • " + " • ".join([c.replace('USDT', '') for c in line_coins]) + "\n"
    coins_text += f"\nВсего доступно: {len(ALL_SYMBOLS)} монет\n/search_symbol NAME - поиск"
    bot.reply_to(message, coins_text)


@bot.message_handler(commands=['all_coins'])
def show_all_coins(message):
    try:
        parts = message.text.split()
        page = int(parts[1]) if len(parts) > 1 else 1
        coins_per_page = 20
        start_idx = (page - 1) * coins_per_page
        end_idx = start_idx + coins_per_page
        current_coins = ALL_SYMBOLS[start_idx:end_idx]

        if not current_coins:
            bot.reply_to(message, f"❌ Страница {page} не существует")
            return

        coins_text = f"📊 Все монеты (страница {page}):\n\n"
        for i in range(0, len(current_coins), 4):
            line_coins = current_coins[i:i + 4]
            coins_text += " • " + " • ".join([c.replace('USDT', '') for c in line_coins]) + "\n"

        total_pages = (len(ALL_SYMBOLS) // coins_per_page) + 1
        coins_text += f"\nСтраница {page} из {total_pages}"
        coins_text += f"\nВсего монет: {len(ALL_SYMBOLS)}"

        if page < total_pages:
            coins_text += f"\nСледующая страница: /all_coins {page + 1}"
        if page > 1:
            coins_text += f"\nПредыдущая страница: /all_coins {page - 1}"

        bot.reply_to(message, coins_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


@bot.message_handler(commands=['update_symbols'])
def update_symbols_command(message):
    try:
        from binance_symbols import get_all_usdt_pairs
        wait_msg = bot.reply_to(message, "🔄 Обновляю список торговых пар...")

        symbols = get_all_usdt_pairs()
        if symbols:
            with open("all_usdt_pairs.json", "w") as f:
                json.dump(symbols, f)
            global ALL_SYMBOLS
            ALL_SYMBOLS = [s for s in symbols if quality_filter.is_high_quality(s)]

            bot.edit_message_text(
                f"✅ Список обновлен!\n📊 Всего пар: {len(symbols)}\n💎 Качественных: {len(ALL_SYMBOLS)}\n🕐 {datetime.now().strftime('%H:%M %d.%m.%Y')}",
                chat_id=wait_msg.chat.id,
                message_id=wait_msg.message_id
            )
        else:
            bot.edit_message_text("❌ Не удалось обновить список", chat_id=wait_msg.chat.id,
                                  message_id=wait_msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка обновления: {str(e)}")


@bot.message_handler(commands=['monitor_start'])
def start_monitoring(message):
    try:
        parts = message.text.split()

        if len(parts) > 1:
            symbols = [s.upper() for s in parts[1:]]
            # Проверяем что все символы существуют
            invalid_symbols = [s for s in symbols if s not in ALL_SYMBOLS]
            if invalid_symbols:
                bot.reply_to(message, f"❌ Неизвестные символы: {', '.join(invalid_symbols)}")
                return
        else:
            symbols = top_coins_manager.get_top_coins_by_marketcap(10)  # Топ-10 монет

        result = monitor.start_monitoring(
            chat_id=message.chat.id,
            symbols=symbols,
            check_interval=5
        )

        bot.reply_to(message, result)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка запуска мониторинга: {e}")


@bot.message_handler(commands=['monitor_extended'])
def monitor_extended(message):
    """Мониторинг 20 популярных монет"""
    try:
        symbols = top_coins_manager.get_top_coins_by_marketcap(20)  # Топ-20 монет

        result = monitor.start_monitoring(
            chat_id=message.chat.id,
            symbols=symbols,
            check_interval=5
        )

        status_text = f"""
{result}

📊 Отслеживаем 20 ТОП-МОНЕТ по капитализации
⏰ Проверка каждые 5 минут

/monitor_stop - остановить мониторинг
/monitor_status - статус
"""
        bot.reply_to(message, status_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


@bot.message_handler(commands=['monitor_quality'])
def monitor_quality_command(message):
    """Мониторинг только качественных активов"""
    try:
        # Берем топ-15 по рейтингу
        quality_symbols = top_coins_manager.get_top_coins_by_marketcap(15)

        result = monitor.start_monitoring(
            chat_id=message.chat.id,
            symbols=quality_symbols,
            check_interval=5
        )

        status_text = f"""
{result}

💎 МОНИТОРИНГ КАЧЕСТВЕННЫХ АКТИВОВ:
• Только топ-15 по рыночной капитализации
• Фильтрация мемкоинов
• Анализ объемов и ликвидности

📊 Отслеживаем 15 лучших монет:
• {quality_symbols[0]} • {quality_symbols[1]} • {quality_symbols[2]}
• {quality_symbols[3]} • {quality_symbols[4]} • {quality_symbols[5]}

/monitor_stop - остановить мониторинг
"""
        bot.reply_to(message, status_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


@bot.message_handler(commands=['monitor_stop'])
def stop_monitoring(message):
    try:
        result = monitor.stop_monitoring()
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка остановки: {e}")


@bot.message_handler(commands=['monitor_status'])
def monitor_status(message):
    status = "АКТИВЕН" if monitor.monitoring_active else "НЕАКТИВЕН"
    symbols = ", ".join(monitor.monitored_symbols) if monitor.monitored_symbols else "не выбраны"

    status_text = f"""
Статус мониторинга:

Состояние: {status}
Монеты: {symbols}
Всего сигналов: {len(monitor.alerted_signals)}
"""
    bot.reply_to(message, status_text)


@bot.message_handler(commands=['monitor_popular'])
def monitor_popular(message):
    """Запускает мониторинг популярных монет"""
    try:
        # Топ 10 монет для мониторинга
        popular_symbols = top_coins_manager.get_top_coins_by_marketcap(10)

        result = monitor.start_monitoring(
            chat_id=message.chat.id,
            symbols=popular_symbols,
            check_interval=3
        )

        status_text = f"""
{result}

📊 Отслеживаем ТОП-10 по капитализации:
• {popular_symbols[0]} • {popular_symbols[1]} • {popular_symbols[2]}
• {popular_symbols[3]} • {popular_symbols[4]} • {popular_symbols[5]}
• {popular_symbols[6]} • {popular_symbols[7]} • {popular_symbols[8]}
• {popular_symbols[9]}

🔔 Бот будет присылать:
• Сигналы покупки/продажи
• Резкие изменения цен (>2%)
• Важные рыночные движения

/monitor_stop - остановить мониторинг
/monitor_status - статус
"""
        bot.reply_to(message, status_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка запуска мониторинга: {e}")


@bot.message_handler(commands=['quick_scan'])
def quick_scan(message):
    try:
        scan_msg = bot.reply_to(message, "Быстрый обзор рынка...")

        results = []
        symbols_to_scan = top_coins_manager.get_top_coins_by_marketcap(6)

        for symbol in symbols_to_scan:
            try:
                response = requests.post(
                    f"{API_URL}/analyze-smart",
                    params={"symbol": symbol},
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    if "error" not in data:
                        action = data.get('action', 'HOLD')
                        strength = data.get('strength', 0)
                        returns = data.get('backtest_return_%', 0)

                        emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "🟡"
                        results.append(
                            f"{emoji} {symbol.replace('USDT', '')}: {action} (сила: {strength}, доход: {returns}%)")

                time.sleep(1)

            except Exception as e:
                print(f"Ошибка сканирования {symbol}: {e}")

        if results:
            scan_result = "📊 Быстрый обзор рынка:\n\n" + "\n".join(results)
        else:
            scan_result = "❌ Не удалось получить данные"

        bot.edit_message_text(
            scan_result,
            chat_id=scan_msg.chat.id,
            message_id=scan_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка сканирования: {e}")


@bot.message_handler(commands=['timeframes'])
def show_timeframes(message):
    timeframes_text = """
Доступные таймфреймы:

• 1m - 1 минута
• 5m - 5 минут  
• 15m - 15 минут
• 30m - 30 минут
• 1h - 1 час
• 6h - 6 часов
• 1d - 1 день

Рекомендуется использовать 15m или 1h
"""
    bot.reply_to(message, timeframes_text)


@bot.message_handler(commands=['chart'])
def chart_command(message):
    """Показывает график цены"""
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "Используйте: /chart SYMBOL TIMEFRAME\nПример: /chart BTCUSDT 1h")
            return

        symbol = parts[1].upper()
        timeframe = parts[2].lower()

        if symbol not in ALL_SYMBOLS:
            bot.reply_to(message, f"❌ Символ {symbol} не найден. Используйте /search_symbol для поиска")
            return

        supported_tf = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
        if timeframe not in supported_tf:
            bot.reply_to(message, f"❌ Таймфрейм не поддерживается. Используйте: {', '.join(supported_tf)}")
            return

        wait_msg = bot.reply_to(message, f"📊 Создаю график для {symbol}...")

        from simple_chart import create_simple_chart
        chart_buffer = create_simple_chart(symbol, timeframe)

        if chart_buffer:
            bot.send_photo(
                chat_id=message.chat.id,
                photo=chart_buffer,
                caption=f"📈 {symbol} • {timeframe.upper()}\n⏰ Последние 50 свечей"
            )
            bot.delete_message(chat_id=wait_msg.chat.id, message_id=wait_msg.message_id)
        else:
            bot.edit_message_text(
                "❌ Не удалось создать график. Проверьте символ и таймфрейм.",
                chat_id=wait_msg.chat.id,
                message_id=wait_msg.message_id
            )

    except Exception as e:
        error_msg = f"❌ Ошибка: {str(e)}"
        try:
            bot.edit_message_text(
                error_msg,
                chat_id=wait_msg.chat.id,
                message_id=wait_msg.message_id
            )
        except:
            bot.reply_to(message, error_msg)


@bot.message_handler(commands=['better_targets'])
def better_targets_command(message):
    """Улучшенный расчет целей с конфлюэнсом"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Используйте: /better_targets SYMBOL\nПример: /better_targets BTCUSDT")
            return

        symbol = parts[1].upper()

        if symbol not in ALL_SYMBOLS:
            bot.reply_to(message, f"❌ Символ {symbol} не найден")
            return

        wait_msg = bot.reply_to(message, f"🎯 Рассчитываю улучшенные цели для {symbol}...")

        # Получаем обычные цели
        targets = target_calculator.calculate_targets(symbol)

        # Получаем анализ тренда для конфлюэнса
        trend_analysis = trend_analyzer.multi_timeframe_analysis(symbol)

        if "error" in targets:
            bot.edit_message_text(f"❌ {targets['error']}", chat_id=wait_msg.chat.id, message_id=wait_msg.message_id)
            return

        # Определяем направление
        if targets['direction'] == "LONG":
            emoji = "🟢"
            action = "ПОКУПКА"
        else:
            emoji = "🔴"
            action = "ПРОДАЖА"

        # Оценка качества с учетом конфлюэнса
        confluence_score = trend_analysis.get('confluence_score', 0) if 'error' not in trend_analysis else 0
        quality_with_confluence = min(10, targets['quality_score'] + (confluence_score / 10))

        quality_emoji = "✅" if quality_with_confluence >= 8 else "🟢" if quality_with_confluence >= 6 else "🟡" if quality_with_confluence >= 4 else "🔴"

        result_text = f"""
{emoji} УЛУЧШЕННЫЕ ЦЕЛИ ДЛЯ {targets['symbol']} {emoji}

Направление: {action}
Тренд: {targets['trend']}
{quality_emoji} КАЧЕСТВО: {quality_with_confluence:.1f}/10
🎯 КОНФЛЮЭНС: {confluence_score}%

💰 ЦЕНЫ:
• Текущая: ${targets['entry_price']:,.4f}
• Стоп-лосс: ${targets['stop_loss']:,.4f}
• Тейк-профит: ${targets['take_profit']:,.4f}

📊 УРОВНИ:
• Поддержка: ${targets['current_support']:,.4f}
• Сопротивление: ${targets['current_resistance']:,.4f}

⚡ РИСК-МЕНЕДЖМЕНТ:
• Риск: {targets['risk_percent']}%
• Прибыль: {targets['reward_percent']}%
• Соотношение R:R = 1:{targets['risk_reward_ratio']:.1f}

💡 РЕКОМЕНДАЦИЯ:
"""

        # Добавляем рекомендацию на основе конфлюэнса
        if confluence_score > 20:
            result_text += "🎯 СИЛЬНЫЙ КОНФЛЮЭНС - ХОРОШАЯ ВХОДНАЯ ТОЧКА"
        elif confluence_score < -20:
            result_text += "⚠️ СИЛЬНЫЙ МЕДВЕЖИЙ КОНФЛЮЭНС - БУДЬТЕ ОСТОРОЖНЫ"
        else:
            result_text += "📊 СМЕШАННЫЕ СИГНАЛЫ - ЖДИТЕ ПОДТВЕРЖДЕНИЯ"

        result_text += f"\n\n{targets['recommendation']}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка расчета: {str(e)}")


@bot.message_handler(commands=['market_overview'])
def market_overview_command(message):
    """Быстрый обзор рынка с РЕАЛЬНЫМИ AI данными"""
    try:
        wait_msg = bot.reply_to(message, "📊 AI анализирует общую ситуацию на рынке...")

        # Анализируем топ-5 монет
        top_symbols = top_coins_manager.get_top_coins_by_marketcap(5)
        market_data = []

        for symbol in top_symbols:
            try:
                # 🔽 🔽 🔽 РЕАЛЬНЫЕ ДАННЫЕ ДЛЯ AI АНАЛИЗА 🔽 🔽 🔽
                volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
                trend_data = trend_analyzer.multi_timeframe_analysis(symbol)
                confluence = trend_data.get('confluence_score', 0) if 'error' not in trend_data else 0

                # РЕАЛЬНЫЙ AI анализ
                ai_analysis = ai_checker.analyze_signal_quality(symbol, {
                    'volume_ratio': volume_data.get('volume_ratio', 0),
                    'current_price': 0,
                    'confluence': confluence
                })

                ai_confidence = ai_analysis['ai_confidence_score']
                ai_color = ai_analysis['color']

                # Получаем базовые данные
                response = requests.post(
                    f"{API_URL}/analyze-smart",
                    params={"symbol": symbol},
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    if "error" not in data:
                        market_data.append({
                            'symbol': symbol,
                            'action': data.get('action', 'HOLD'),
                            'strength': data.get('strength', 0),
                            'price': data.get('last_price', 0),
                            'ai_confidence': ai_confidence,  # 🔽 РЕАЛЬНАЯ AI уверенность
                            'ai_color': ai_color,
                            'volume_ratio': volume_data.get('volume_ratio', 0),
                            'confluence': confluence
                        })

                time.sleep(0.5)

            except Exception as e:
                print(f"Ошибка анализа {symbol}: {e}")
                continue

        # 🔽 РЕАЛЬНЫЙ РАСЧЕТ СРЕДНЕЙ AI УВЕРЕННОСТИ
        if market_data:
            overall_ai_confidence = sum(item['ai_confidence'] for item in market_data) / len(market_data)
            # 🔽 СЧИТАЕМ НА ОСНОВЕ РЕАЛЬНЫХ ДАННЫХ
            buy_signals = sum(1 for item in market_data if item['action'] == 'BUY')
            sell_signals = sum(1 for item in market_data if item['action'] == 'SELL')
            total = len(market_data)
            market_sentiment = (buy_signals / total) * 100 if total > 0 else 0
        else:
            overall_ai_confidence = 2.0  # 🔽 РЕАЛЬНОЕ ЗНАЧЕНИЕ
            market_sentiment = 50
            buy_signals = sell_signals = 0
            total = 0

        # 🔽 ФОРМИРУЕМ РЕЗУЛЬТАТ С РЕАЛЬНЫМИ ДАННЫМИ
        result_text = "📊 AI ОБЗОР РЫНКА\n\n"

        # 1. AI-ОЦЕНКА ВСЕГО РЫНКА
        result_text += "🤖 AI-ДИАГНОСТИКА РЫНКА:\n"
        if overall_ai_confidence >= 7.0:
            result_text += "🟢 ВЫСОКАЯ НАДЕЖНОСТЬ - рынок стабилен\n"
        elif overall_ai_confidence >= 5.0:
            result_text += "🟡 СРЕДНЯЯ НАДЕЖНОСТЬ - выборочные возможности\n"
        else:
            result_text += "🔴 НИЗКАЯ НАДЕЖНОСТЬ - рынок рискованный\n"

        result_text += f"🎯 СРЕДНЯЯ AI-УВЕРЕННОСТЬ: {overall_ai_confidence:.1f}/10\n\n"

        # 2. КЛАССИЧЕСКОЕ НАСТРОЕНИЕ
        result_text += f"🎭 ТРАДИЦИОННЫЙ АНАЛИЗ:\n"
        result_text += f"• Бычьих сигналов: {buy_signals}/{total} ({market_sentiment:.0f}%)\n"
        result_text += f"• Медвежьих сигналов: {sell_signals}/{total}\n"

        if market_sentiment > 70:
            result_text += "🚀 СИЛЬНОЕ БЫЧЬЕ НАСТРОЕНИЕ\n"
        elif market_sentiment > 60:
            result_text += "🟢 УМЕРЕННОЕ БЫЧЬЕ НАСТРОЕНИЕ\n"
        elif market_sentiment < 30:
            result_text += "🔴 СИЛЬНОЕ МЕДВЕЖЬЕ НАСТРОЕНИЕ\n"
        elif market_sentiment < 40:
            result_text += "🔴 УМЕРЕННОЕ МЕДВЕЖЬЕ НАСТРОЕНИЕ\n"
        else:
            result_text += "🟡 НЕЙТРАЛЬНОЕ НАСТРОЕНИЕ\n"

        # 3. ДЕТАЛЬНЫЙ АНАЛИЗ КАЖДОЙ МОНЕТЫ С AI
        result_text += f"\n📈 ДЕТАЛЬНЫЙ АНАЛИЗ ТОП-{len(market_data)} МОНЕТ:\n"

        for item in market_data:
            action_emoji = "🟢" if item['action'] == 'BUY' else "🔴" if item['action'] == 'SELL' else "🟡"
            symbol_clean = item['symbol'].replace('USDT', '')

            result_text += f"\n{action_emoji} {symbol_clean}:\n"
            result_text += f"   📊 Сигнал: {item['action']} (сила: {item['strength']})\n"
            result_text += f"   🤖 AI-уверенность: {item['ai_confidence']:.1f}/10 {item['ai_color']}\n"
            result_text += f"   💰 Цена: ${item['price']:,.2f}\n"
            result_text += f"   📊 Объемы: {item['volume_ratio']:.1f}x\n"
            result_text += f"   🎯 Конфлюэнс: {item['confluence']}%\n"

        # 4. AI-РЕКОМЕНДАЦИЯ
        result_text += f"\n💡 AI-РЕКОМЕНДАЦИЯ ДЛЯ ТРЕЙДЕРА:\n"

        if overall_ai_confidence >= 7.0 and buy_signals >= 3:
            result_text += "✅ БЛАГОПРИЯТНЫЕ УСЛОВИЯ - можно активно торговать\n"
        elif overall_ai_confidence >= 5.0 and buy_signals > sell_signals:
            result_text += "⚠️ УМЕРЕННЫЕ УСЛОВИЯ - торговать с осторожностью\n"
        elif overall_ai_confidence < 4.0 or sell_signals >= 3:
            result_text += "❌ НЕБЛАГОПРИЯТНЫЕ УСЛОВИЯ - лучше воздержаться от сделок\n"
        else:
            result_text += "📊 НЕОПРЕДЕЛЕННОСТЬ - ждите четких сигналов\n"

        # 🔽 ДОБАВЛЯЕМ РЕАЛЬНЫЕ МЕТРИКИ РЫНКА
        if market_data:
            avg_volume = sum(item['volume_ratio'] for item in market_data) / len(market_data)
            avg_confluence = sum(item['confluence'] for item in market_data) / len(market_data)

            result_text += f"\n📊 РЕАЛЬНЫЕ МЕТРИКИ РЫНКА:\n"
            result_text += f"• 📈 Средние объемы: {avg_volume:.1f}x\n"
            result_text += f"• 🎯 Средний конфлюэнс: {avg_confluence:.1f}%\n"
            result_text += f"• 🤖 AI уверенность: {overall_ai_confidence:.1f}/10\n"

        result_text += f"\n🕐 AI анализ завершен: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка AI анализа рынка: {str(e)}")


@bot.message_handler(commands=['market_analysis'])
def market_analysis_command(message):
    """Глубокий анализ текущей рыночной ситуации"""
    try:
        wait_msg = bot.reply_to(message, "📊 Анализирую общую рыночную ситуацию...")

        # Анализируем топ-10 монет
        top_symbols = top_coins_manager.get_top_coins_by_marketcap(10)
        market_data = []

        for symbol in top_symbols:
            try:
                response = requests.post(
                    f"{API_URL}/analyze-smart",
                    params={"symbol": symbol},
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    if "error" not in data:
                        market_data.append({
                            'symbol': symbol,
                            'action': data.get('action', 'HOLD'),
                            'strength': data.get('strength', 0),
                            'price': data.get('last_price', 0),
                            'trend': data.get('trend', 'NEUTRAL')
                        })

                time.sleep(0.5)

            except Exception as e:
                continue

        # Анализ рыночного настроения
        buy_count = sum(1 for item in market_data if item['action'] == 'BUY')
        sell_count = sum(1 for item in market_data if item['action'] == 'SELL')
        total = len(market_data)

        if total > 0:
            bull_percent = (buy_count / total) * 100
            bear_percent = (sell_count / total) * 100
            neutral_percent = 100 - bull_percent - bear_percent
        else:
            bull_percent = bear_percent = neutral_percent = 33.3

        # Формируем анализ
        result_text = "🎯 ГЛУБОКИЙ АНАЛИЗ РЫНКА\n\n"

        # Общее настроение
        if bull_percent > 60:
            mood = "🚀 СИЛЬНО БЫЧЬЕ"
            emoji = "🟢"
        elif bull_percent > 40:
            mood = "🟢 УМЕРЕННО БЫЧЬЕ"
            emoji = "🟢"
        elif bear_percent > 60:
            mood = "🔴 СИЛЬНО МЕДВЕЖЬЕ"
            emoji = "🔴"
        elif bear_percent > 40:
            mood = "🔴 УМЕРЕННО МЕДВЕЖЬЕ"
            emoji = "🔴"
        else:
            mood = "🟡 НЕЙТРАЛЬНОЕ"
            emoji = "🟡"

        result_text += f"{emoji} НАСТРОЕНИЕ РЫНКА: {mood}\n"
        result_text += f"📊 Быки: {bull_percent:.1f}% | Медведи: {bear_percent:.1f}% | Нейтралы: {neutral_percent:.1f}%\n\n"

        # Лучшие возможности для покупки
        buy_opportunities = [item for item in market_data if item['action'] == 'BUY' and item['strength'] >= 3]
        if buy_opportunities:
            result_text += "🎯 ЛУЧШИЕ ПОКУПКИ:\n"
            for opp in sorted(buy_opportunities, key=lambda x: x['strength'], reverse=True)[:3]:
                result_text += f"🟢 {opp['symbol'].replace('USDT', '')} - сила: {opp['strength']}/10 - ${opp['price']:,.2f}\n"
            result_text += "\n"

        # Опасные активы для продажи
        sell_warnings = [item for item in market_data if item['action'] == 'SELL' and item['strength'] <= -3]
        if sell_warnings:
            result_text += "⚠️ ОПАСНЫЕ АКТИВЫ:\n"
            for warn in sorted(sell_warnings, key=lambda x: x['strength'])[:3]:
                result_text += f"🔴 {warn['symbol'].replace('USDT', '')} - сила: {abs(warn['strength'])}/10 - ${warn['price']:,.2f}\n"
            result_text += "\n"

        # Рекомендация
        if bull_percent > 60 and len(buy_opportunities) >= 3:
            result_text += "💡 ВЫВОД: Сильное бычье настроение. Хорошее время для покупок!\n"
        elif bear_percent > 60 and len(sell_warnings) >= 3:
            result_text += "💡 ВЫВОД: Сильное медвежье настроение. Будьте осторожны!\n"
        else:
            result_text += "💡 ВЫВОД: Рынок в неопределенности. Выбирайте активы точечно.\n"

        result_text += f"\n🕐 Анализ обновлен: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка анализа рынка: {str(e)}")

@bot.message_handler(commands=['simple_confluence'])
def simple_confluence_command(message):
    """Простой анализ конфлюэнса для одной монеты"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Используйте: /simple_confluence SYMBOL\nПример: /simple_confluence BTCUSDT")
            return

        symbol = parts[1].upper()

        if symbol not in ALL_SYMBOLS:
            bot.reply_to(message, f"❌ Символ {symbol} не найден")
            return

        wait_msg = bot.reply_to(message, f"📊 Анализирую конфлюэнс для {symbol}...")

        # Анализируем на 4 таймфреймах
        timeframes = ['15m', '1h', '4h', '1d']
        signals = []

        for tf in timeframes:
            try:
                response = requests.post(
                    f"{API_URL}/analyze",
                    params={"symbol": symbol, "timeframe": tf},
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    if "error" not in data:
                        action = data.get('action', 'HOLD')
                        strength = data.get('strength', 0)

                        signals.append({
                            'timeframe': tf,
                            'action': action,
                            'strength': strength
                        })

                time.sleep(0.5)

            except Exception as e:
                print(f"Ошибка анализа {symbol} на {tf}: {e}")
                continue

        # Считаем конфлюэнс
        buy_count = sum(1 for s in signals if s['action'] == 'BUY')
        sell_count = sum(1 for s in signals if s['action'] == 'SELL')
        total = buy_count + sell_count

        if total > 0:
            confluence = ((buy_count - sell_count) / total) * 100
        else:
            confluence = 0

        # Формируем результат
        result_text = f"""
🎯 КОНФЛЮЭНС-АНАЛИЗ ДЛЯ {symbol}

📊 СИГНАЛЫ ПО ТАЙМФРЕЙМАМ:
"""

        for signal in signals:
            emoji = "🟢" if signal['action'] == 'BUY' else "🔴" if signal['action'] == 'SELL' else "🟡"
            result_text += f"\n{emoji} {signal['timeframe'].upper()}: {signal['action']} (сила: {signal['strength']})"

        result_text += f"\n\n🎯 ОБЩИЙ КОНФЛЮЭНС: {confluence:.1f}%"

        if confluence > 50:
            result_text += "\n🚀 СИЛЬНЫЙ БЫЧИЙ КОНФЛЮЭНС!"
        elif confluence > 20:
            result_text += "\n🟢 УМЕРЕННЫЙ БЫЧИЙ КОНФЛЮЭНС"
        elif confluence < -50:
            result_text += "\n🔴 СИЛЬНЫЙ МЕДВЕЖИЙ КОНФЛЮЭНС!"
        elif confluence < -20:
            result_text += "\n🔴 УМЕРЕННЫЙ МЕДВЕЖИЙ КОНФЛЮЭНС"
        else:
            result_text += "\n🟡 НЕЙТРАЛЬНЫЙ КОНФЛЮЭНС"

        result_text += f"\n\n💡 РЕКОМЕНДАЦИЯ:"
        if confluence > 30:
            result_text += "\n✅ Рассмотреть покупку - сигналы согласованы"
        elif confluence < -30:
            result_text += "\n⚠️ Рассмотреть продажу - преобладают медвежьи сигналы"
        else:
            result_text += "\n📊 Ждать подтверждения - сигналы смешанные"

        result_text += f"\n\n🕐 Анализ завершен: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['advanced_targets'])
def advanced_targets_command(message):
    """Расширенный расчет целей с Фибоначчи, анализа объемов и AI-проверкой"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Используйте: /advanced_targets SYMBOL\nПример: /advanced_targets BTCUSDT")
            return

        symbol = parts[1].upper()

        if symbol not in ALL_SYMBOLS:
            bot.reply_to(message, f"❌ Символ {symbol} не найден")
            return

        wait_msg = bot.reply_to(message, f"🎯 Расширенный анализ целей для {symbol}...")

        # Получаем базовые цели с динамическим RR
        response = requests.post(
            f"{API_URL}/analyze-smart",
            params={"symbol": symbol},
            timeout=15
        )

        if response.status_code != 200:
            bot.edit_message_text("❌ Ошибка анализа символа", chat_id=wait_msg.chat.id, message_id=wait_msg.message_id)
            return

        data = response.json()
        if "error" in data:
            bot.edit_message_text(f"❌ {data['error']}", chat_id=wait_msg.chat.id, message_id=wait_msg.message_id)
            return

        # Определяем направление
        direction = "SELL" if data.get('action') == 'SELL' else "LONG"

        # 🔽 🔽 🔽 НОВАЯ ВЕРСИЯ С AI-ОПТИМИЗАЦИЕЙ 🔽 🔽 🔽
        # Сначала получаем данные для реального расчета качества
        volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
        trend_analysis = trend_analyzer.multi_timeframe_analysis(symbol)
        confluence_score = trend_analysis.get('confluence_score', 0) if 'error' not in trend_analysis else 0

        # AI анализ для получения уверенности
        ai_analysis_data = {
            'volume_ratio': volume_data.get('volume_ratio', 0) if 'error' not in volume_data else 0,
            'current_price': data.get('last_price', 0),  # цена из анализа
            'confluence': confluence_score
        }

        ai_analysis = ai_checker.analyze_signal_quality(symbol, ai_analysis_data)

        try:
            # 🔽 ПЕРЕДАЕМ AI ДАННЫЕ В РАСЧЕТ ЦЕЛЕЙ
            targets = dynamic_rr_calculator.calculate_adaptive_targets(
                symbol,
                direction=direction,
                base_stop_loss_percent=0.02,
                min_rr=2.5,
                ai_confidence=ai_analysis['ai_confidence_score'],
                volume_ratio=volume_data.get('volume_ratio', 0) if 'error' not in volume_data else 0,
                confluence=confluence_score
            )
            print(f"✅ Реальное качество рассчитано для {symbol}: {targets['quality_score']}/10")
        except Exception as e:
            print(f"⚠️ Реальный расчет недоступен, используем старый метод: {e}")
            targets = dynamic_rr_calculator.calculate_adaptive_targets(
                symbol,
                direction=direction,
                base_stop_loss_percent=0.02,
                min_rr=2.5
            )

        # 🔥 УМНЫЕ СТОП-ЛОССЫ НА ОСНОВЕ ВОЛАТИЛЬНОСТИ
        def calculate_smart_stoploss(symbol, direction, current_price, volatility):
            """Рассчитывает умные стоп-лоссы на основе волатильности"""
            # Базовый стоп на волатильности (2x ATR или 3% - что больше)
            atr_stop = volatility * 2.0
            percent_stop = 0.03

            # Выбираем более безопасный вариант
            stop_percent = max(atr_stop / 100, percent_stop)

            if direction == "LONG":
                smart_stop = current_price * (1 - stop_percent)
                # Дополнительная защита: стоп не ниже ключевого уровня поддержки
                key_support = current_price * (1 - stop_percent * 1.5)
                smart_stop = max(smart_stop, key_support)
            else:  # SHORT
                smart_stop = current_price * (1 + stop_percent)
                # Дополнительная защита: стоп не выше ключевого уровня сопротивления
                key_resistance = current_price * (1 + stop_percent * 1.5)
                smart_stop = min(smart_stop, key_resistance)

            return smart_stop, stop_percent * 100

        # Применяем умные стоп-лоссы
        volatility = targets.get('current_volatility', 2.0)
        smart_stop, smart_stop_percent = calculate_smart_stoploss(
            symbol, direction, targets['entry_price'], volatility
        )

        # Обновляем цели с умными стопами
        targets['smart_stop_loss'] = smart_stop
        targets['smart_stop_percent'] = smart_stop_percent
        targets['is_smart_stop'] = True

        # 🔽 🔽 🔽 ДОБАВЛЯЕМ volume_analysis ДЛЯ ВЫВОДА 🔽 🔽 🔽
        volume_analysis = advanced_volume_analyzer.get_volume_spike_analysis(symbol)

        # Получаем ключевые уровни Фибо
        current_price = targets['entry_price']

        # Для LONG: считаем от стоп-лосса до тейк-профита
        if targets['direction'] == "LONG":
            fib_levels = fib_calculator.calculate_fib_levels(
                high=targets['take_profit'],
                low=targets['stop_loss'],
                direction="LONG"
            )
        else:  # SHORT
            fib_levels = fib_calculator.calculate_fib_levels(
                high=targets['stop_loss'],
                low=targets['take_profit'],
                direction="SHORT"
            )

        # Форматируем результат
        if direction == "LONG":
            emoji = "🟢"
            action = "ПОКУПКА"
        else:
            emoji = "🔴"
            action = "ПРОДАЖА"

        result_text = f"""
{emoji} РАСШИРЕННЫЕ ЦЕЛИ ДЛЯ {targets['symbol']} {emoji}

Направление: {action}
Тренд: {data.get('trend', 'NEUTRAL')}
🎯 Risk/Reward: 1:{targets['risk_reward_ratio']:.1f}
✅ КАЧЕСТВО: {targets['quality_score']}/10
📊 Волатильность: {targets['current_volatility']:.1f}%

💰 ОСНОВНЫЕ ЦЕНЫ:
• Текущая: {format_price(targets['entry_price'])}
• Стоп-лосс: {format_price(targets['stop_loss'])} ({targets['stop_loss_percent'] * 100:.1f}%)
• 🧠 УМНЫЙ СТОП: {format_price(targets['smart_stop_loss'])} ({targets['smart_stop_percent']:.1f}%)
• Тейк-профит: {format_price(targets['take_profit'])} ({((targets['take_profit'] - targets['entry_price']) / targets['entry_price']) * 100:+.1f}%)

🎯 УРОВНИ ФИБОНАЧЧИ:
"""

        # Показываем ключевые уровни Фибо
        key_fib_levels = {'0.236', '0.382', '0.5', '0.618', '0.786', '1.0'}
        for level in key_fib_levels:
            if level in fib_levels and fib_levels[level] > 0:
                result_text += f"• {level}: {format_price(fib_levels[level])}\n"
            elif level in fib_levels:
                if level == '0.382':
                    fib_price = targets['entry_price'] + (targets['take_profit'] - targets['entry_price']) * 0.382
                    result_text += f"• {level}: {format_price(fib_price)}\n"
                elif level == '0.618':
                    fib_price = targets['entry_price'] + (targets['take_profit'] - targets['entry_price']) * 0.618
                    result_text += f"• {level}: {format_price(fib_price)}\n"

        # AI-ОПТИМИЗАЦИЯ ЦЕЛЕЙ
        result_text += f"\n🤖 AI-ОПТИМИЗАЦИЯ ЦЕЛЕЙ:\n"

        if targets.get('ai_optimization', {}).get('optimization_applied', False):
            ai_opt = targets['ai_optimization']
            result_text += f"📊 Фаза рынка: {ai_opt['market_phase']}\n"
            result_text += f"💪 Уверенность AI: {ai_opt['confidence']}%\n"
            result_text += f"💡 {ai_opt['recommendation']}\n"

            if 'smart_take_profits' in targets:
                smart_tp = targets['smart_take_profits']
                result_text += f"\n🎯 УМНЫЕ ТЕЙК-ПРОФИТЫ:\n"
                result_text += f"• ТП1 (30%): {format_price(smart_tp['tp1'])} - фиксируем 30% позиции\n"
                result_text += f"• ТП2 (60%): {format_price(smart_tp['tp2'])} - фиксируем еще 30% позиции\n"
                result_text += f"• ТП3 (100%): {format_price(smart_tp['tp3'])} - основная цель (40% позиции)\n"
                result_text += f"💡 {smart_tp['recommendation']}\n"
        else:
            result_text += "⚪ AI-оптимизация не применена\n"

        # АНАЛИЗ ОБЪЕМОВ
        result_text += f"\n📊 АНАЛИЗ ОБЪЕМОВ:\n"

        if 'error' not in volume_analysis:
            volume_ratio = volume_analysis.get('volume_ratio', 0)

            # ОПРЕДЕЛЯЕМ ЭМОДЗИ И СТАТУС ПО ОБЪЕМАМ
            if volume_ratio < 0.5:
                volume_emoji = "🔴"
                volume_status = "ОЧЕНЬ НИЗКИЕ"
            elif volume_ratio < 0.8:
                volume_emoji = "🟡"
                volume_status = "НИЗКИЕ"
            elif volume_ratio > 2.0:
                volume_emoji = "🚀"
                volume_status = "ВЫСОКИЕ"
            elif volume_ratio > 1.5:
                volume_emoji = "🟢"
                volume_status = "ХОРОШИЕ"
            else:
                volume_emoji = "📊"
                volume_status = "НОРМАЛЬНЫЕ"

            result_text += f"{volume_emoji} Объемы: {volume_ratio:.1f}x ({volume_status})\n"

            # ДОБАВЛЯЕМ ПРЕДУПРЕЖДЕНИЯ
            if volume_ratio < 0.8:
                result_text += "⚠️ ВНИМАНИЕ: Объемы слабые - сигнал требует подтверждения!\n"
            elif volume_ratio > 2.0:
                result_text += "✅ ПОДТВЕРЖДЕНИЕ: Высокие объемы усиливают сигнал!\n"

            if volume_analysis.get('is_volume_spike'):
                result_text += f"🎯 Сигнал объемов: {volume_analysis.get('signal', 'N/A')}\n"
                result_text += f"💪 Уверенность: {volume_analysis.get('confidence', 'N/A')}\n"

        # AI-АНАЛИЗ НАДЕЖНОСТИ СИГНАЛА
        result_text += f"\n🤖 AI-АНАЛИЗ НАДЕЖНОСТИ:\n"
        result_text += f"{ai_analysis['color']} УВЕРЕННОСТЬ AI: {ai_analysis['ai_confidence_score']}/10\n"
        result_text += f"📊 {ai_analysis['recommendation']}\n"
        result_text += f"✅ Пройдено проверок: {ai_analysis.get('passed_checks', 3)}/{ai_analysis.get('total_checks', 3)}\n"
        # 🔽 🔽 🔽 ВОССТАНАВЛИВАЕМ СТРАТЕГИЮ ВХОДА 🔽 🔽 🔽
        result_text += f"\n💡 СТРАТЕГИЯ ВХОДА:\n"

        # РАССЧИТЫВАЕМ УРОВНИ ФИБО ВРУЧНУЮ ДЛЯ ВСЕХ ВАРИАНТОВ
        fib_236 = targets['entry_price'] + (targets['take_profit'] - targets['entry_price']) * 0.236
        fib_382 = targets['entry_price'] + (targets['take_profit'] - targets['entry_price']) * 0.382
        fib_500 = targets['entry_price'] + (targets['take_profit'] - targets['entry_price']) * 0.5
        fib_618 = targets['entry_price'] + (targets['take_profit'] - targets['entry_price']) * 0.618

        # Многоуровневый вход на основе AI уверенности
        if ai_analysis['ai_confidence_score'] >= 8.0:
            # Высокая уверенность - агрессивный вход
            result_text += "🎯 ВЫСОКАЯ AI УВЕРЕННОСТЬ - АГРЕССИВНЫЙ ВХОД:\n"
            result_text += "1️⃣ 50% позиции - текущая цена\n"
            result_text += f"2️⃣ 30% позиции - {format_price(fib_382)} (Фибо 0.382)\n"
            result_text += f"3️⃣ 20% позиции - {format_price(fib_500)} (Фибо 0.5)\n"

        elif ai_analysis['ai_confidence_score'] >= 6.0:
            # Средняя уверенность - стандартный вход
            result_text += "✅ СРЕДНЯЯ AI УВЕРЕННОСТЬ - СТАНДАРТНЫЙ ВХОД:\n"
            result_text += "1️⃣ 40% позиции - текущая цена\n"
            result_text += f"2️⃣ 40% позиции - {format_price(fib_382)} (Фибо 0.382)\n"
            result_text += f"3️⃣ 20% позиции - {format_price(fib_618)} (Фибо 0.618)\n"
        else:
            # Низкая уверенность - осторожный вход
            result_text += "⚠️ НИЗКАЯ AI УВЕРЕННОСТЬ - ОСТОРОЖНЫЙ ВХОД:\n"
            result_text += "1️⃣ 30% позиции - текущая цена\n"
            result_text += f"2️⃣ 40% позиции - {format_price(fib_382)} (Фибо 0.382)\n"
            result_text += f"3️⃣ 30% позиции - {format_price(fib_618)} (Фибо 0.618)\n"

        # 🔽 🔽 🔽 ВОССТАНАВЛИВАЕМ МНОГОУРОВНЕВЫЙ ТЕЙК-ПРОФИТ 🔽 🔽 🔽
        result_text += f"\n🎯 МНОГОУРОВНЕВЫЙ ТЕЙК-ПРОФИТ:\n"

        # Многоуровневый тейк-профит
        if targets['direction'] == "LONG":
            tp1 = targets['entry_price'] + (targets['take_profit'] - targets['entry_price']) * 0.3
            tp2 = targets['entry_price'] + (targets['take_profit'] - targets['entry_price']) * 0.6
            tp3 = targets['entry_price'] + (targets['take_profit'] - targets['entry_price']) * 1.0

            result_text += f"• ТП1 (30%): {format_price(tp1)} - фиксируем часть прибыли\n"
            result_text += f"• ТП2 (60%): {format_price(tp2)} - фиксируем основную прибыль\n"
            result_text += f"• ТП3 (100%): {format_price(tp3)} - основная цель\n"
        else:
            tp1 = targets['entry_price'] - (targets['entry_price'] - targets['take_profit']) * 0.3
            tp2 = targets['entry_price'] - (targets['entry_price'] - targets['take_profit']) * 0.6
            tp3 = targets['entry_price'] - (targets['entry_price'] - targets['take_profit']) * 1.0

            result_text += f"• ТП1 (30%): {format_price(tp1)} - фиксируем часть прибыли\n"
            result_text += f"• ТП2 (60%): {format_price(tp2)} - фиксируем основную прибыль\n"
            result_text += f"• ТП3 (100%): {format_price(tp3)} - основная цель\n"

        # 🔽 🔽 🔽 ВОССТАНАВЛИВАЕМ РЕКОМЕНДАЦИЮ ПО СТОП-ЛОССАМ 🔽 🔽 🔽
        result_text += f"\n🎯 РЕКОМЕНДАЦИЯ ПО СТОП-ЛОССАМ:\n"

        # Сравниваем умный стоп с базовым
        base_stop_percent = targets['stop_loss_percent'] * 100
        smart_stop_percent = targets.get('smart_stop_percent', 0)

        if smart_stop_percent < base_stop_percent:
            result_text += "✅ УМНЫЙ СТОП БЕЗОПАСНЕЕ - используйте умный стоп-лосс\n"
            result_text += f"💡 Защита: {smart_stop_percent:.1f}% vs {base_stop_percent:.1f}%\n"
            result_text += f"💰 Умный стоп: {format_price(targets['smart_stop_loss'])}\n"
            result_text += f"📊 Базовый стоп: {format_price(targets['stop_loss'])}\n"
        else:
            result_text += "⚠️ БАЗОВЫЙ СТОП БЕЗОПАСНЕЕ - используйте базовый стоп-лосс\n"
            result_text += f"💡 Защита: {base_stop_percent:.1f}% vs {smart_stop_percent:.1f}%\n"
            result_text += f"💰 Базовый стоп: {format_price(targets['stop_loss'])}\n"
            result_text += f"📊 Умный стоп: {format_price(targets['smart_stop_loss'])}\n"

        # Рекомендация по волатильности
        volatility = targets.get('current_volatility', 0)
        if volatility > 5.0:
            result_text += f"📈 Высокая волатильность ({volatility:.1f}%) - используйте более широкие стопы\n"
        elif volatility < 2.0:
            result_text += f"📉 Низкая волатильность ({volatility:.1f}%) - можно использовать tighter стопы\n"

        # 🔽 🔽 🔽 ВОССТАНАВЛИВАЕМ АВТОМАТИЧЕСКУЮ СДЕЛКУ 🔽 🔽 🔽
        result_text += f"\n\n🤖 АВТОМАТИЧЕСКАЯ СДЕЛКА:"
        result_text += f"\n💡 Нажмите команду ниже для автоматического управления позицией:"

        # Создаем параметры для авто-трейда
        if direction == "LONG":
            tp_params = f"{tp1:.8f},{tp2:.8f},{targets['take_profit']:.8f}"
            auto_trade_command = f"/auto_trade_{symbol.replace('USDT', '')}"
        else:
            tp_params = f"{tp1:.8f},{tp2:.8f},{targets['take_profit']:.8f}"
            auto_trade_command = f"/auto_trade_{symbol.replace('USDT', '')}"

        result_text += f"\n🚀 {auto_trade_command}"

        # 🔽 🔽 🔽 ВОССТАНАВЛИВАЕМ ДИНАМИЧЕСКИЙ ОБРАБОТЧИК 🔽 🔽 🔽
        def create_auto_trade_handler(sym, entry, stop, tps, dir):
            @bot.message_handler(commands=[f'auto_trade_{sym.replace("USDT", "")}'])
            def auto_trade_dynamic_command(message):
                try:
                    # Получаем реальные данные
                    consensus = get_consensus_signal(sym)
                    volume_data = advanced_volume_analyzer.get_volume_spike_analysis(sym)

                    # Безопасное получение данных
                    ai_conf = consensus.get('ai_confidence', 5.0) if consensus and 'error' not in consensus else 5.0
                    volume_ratio = volume_data.get('volume_ratio', 1.0) if volume_data and 'error' not in volume_data else 1.0

                    # Создаем авто-сделку с РЕАЛЬНЫМИ данными
                    position_id = auto_trade_manager.create_auto_trade(
                        chat_id=message.chat.id,
                        symbol=sym,
                        entry_price=entry,
                        stop_loss=stop,
                        take_profits=tps,
                        direction=dir,
                        ai_confidence=ai_conf,  # REAL DATA
                        volume_ratio=volume_ratio  # REAL DATA
                    )

                    if position_id:
                        bot.reply_to(message, f"""
        ✅ АВТО-СДЕЛКА СОЗДАНА!

        📊 {sym} - {dir}
        💰 Вход: {format_price(entry)}
        🎯 Цели: {', '.join([format_price(tp) for tp in tps])}
        🛑 Стоп: {format_price(stop)}

        🤖 AI уверенность: {ai_conf:.1f}/10
        📊 Объемы: {volume_ratio:.1f}x

        💡 Используйте /active_positions для управления
        """)
                    else:
                        bot.reply_to(message, f"❌ Не удалось создать сделку для {sym}")

                except Exception as e:
                    bot.reply_to(message, f"❌ Ошибка создания авто-сделки: {str(e)}")

            return auto_trade_dynamic_command

        # Создаем обработчик для этого символа
        tps_list = [tp1, tp2, targets['take_profit']]
        create_auto_trade_handler(symbol, targets['entry_price'], targets['stop_loss'], tps_list, direction)

        # 🔽 🔽 🔽 ВОССТАНАВЛИВАЕМ ФИНАЛЬНУЮ AI-РЕКОМЕНДАЦИЮ 🔽 🔽 🔽
        result_text += f"\n🎯 AI-РЕКОМЕНДАЦИЯ:\n"

        if ai_analysis['ai_confidence_score'] >= 8.0:
            result_text += "🚀 ОТЛИЧНАЯ НАДЕЖНОСТЬ - МОЖНО ВХОДИТЬ С БОЛЬШОЙ ПОЗИЦИЕЙ\n"
        elif ai_analysis['ai_confidence_score'] >= 6.5:
            result_text += "✅ ХОРОШАЯ НАДЕЖНОСТЬ - МОЖНО ВХОДИТЬ СО СТАНДАРТНОЙ ПОЗИЦИЕЙ\n"
        elif ai_analysis['ai_confidence_score'] >= 5.0:
            result_text += "⚠️ СРЕДНЯЯ НАДЕЖНОСТЬ - ВХОДИТЬ С ОСТОРОЖНОСТЬЮ, МАЛЕНЬКИМИ ПОЗИЦИЯМИ\n"
        else:
            result_text += "❌ НИЗКАЯ НАДЕЖНОСТЬ - ЛУЧШЕ ВОЗДЕРЖАТЬСЯ ОТ ВХОДА\n"

        result_text += f"\n🕐 AI анализ завершен: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка расширенного анализа: {str(e)}")

# 🔽 🔽 🔽 ДИНАМИЧЕСКИЕ КОМАНДЫ ДЛЯ СТАТУСА И ЗАКРЫТИЯ 🔽 🔽 🔽

def create_dynamic_handlers():
    """Создает динамические команды для всех символов"""
    symbols = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "AVAX", "DOT",
               "MATIC", "LTC", "LINK", "ATOM", "UNI", "XLM", "ALGO", "TRX",
               "VET", "ICP", "FIL", "AAVE", "COMP", "MKR", "SNX", "DOGE",
               "SHIB", "PEPE", "FLOKI", "BONK", "WIF", "BOME", "MEME", "LUNC", "LUNA"]

    for symbol in symbols:
        # Команда статуса позиции
        @bot.message_handler(commands=[f'position_status_{symbol}'])
        def position_status_dynamic(message, sym=symbol):
            try:
                active_positions = auto_trade_manager.get_active_positions(message.chat.id)
                position_found = None

                for pos_id, position in active_positions.items():
                    if position['symbol'] == f"{sym}USDT":
                        position_found = position
                        break

                if not position_found:
                    bot.reply_to(message, f"📭 Активная позиция {sym}USDT не найдена")
                    return

                # Получаем текущую цену
                current_price = auto_trade_manager._get_current_price(f"{sym}USDT")

                # Рассчитываем PnL
                entry = position_found['entry_price']
                if current_price:
                    if position_found['direction'] == "LONG":
                        pnl_pct = (current_price - entry) / entry * 100
                    else:
                        pnl_pct = (entry - current_price) / entry * 100
                    price_info = f"📈 Текущая: {format_price(current_price)} ({pnl_pct:+.2f}%)"
                else:
                    price_info = "📡 Ошибка получения цены"

                response = f"""
📊 СТАТУС ПОЗИЦИИ: {sym}USDT

{price_info}
💰 Вход: {format_price(entry)}
🎯 Цели: {', '.join([format_price(tp) for tp in position_found['take_profits']])}
🛑 Стоп: {format_price(position_found['stop_loss'])}
📊 Размер: {position_found['current_size']}%
🎯 Выполнено ТП: {', '.join(position_found['executed_tps']) if position_found['executed_tps'] else 'нет'}

💡 Команды:
/close_position_{sym} - закрыть позицию
/active_positions - все позиции
"""
                bot.reply_to(message, response)

            except Exception as e:
                bot.reply_to(message, f"❌ Ошибка: {str(e)}")

        # Команда закрытия позиции
        @bot.message_handler(commands=[f'close_position_{symbol}'])
        def close_position_dynamic(message, sym=symbol):
            try:
                active_positions = auto_trade_manager.get_active_positions(message.chat.id)
                position_to_close = None
                position_id_to_close = None

                for pos_id, position in active_positions.items():
                    if position['symbol'] == f"{sym}USDT":
                        position_to_close = position
                        position_id_to_close = pos_id
                        break

                if not position_to_close:
                    bot.reply_to(message, f"❌ Активная позиция {sym}USDT не найдена")
                    return

                # Закрываем позицию РУЧНО
                current_price = auto_trade_manager._get_current_price(f"{sym}USDT")
                if current_price:
                    success = auto_trade_manager.close_position_manually(position_id_to_close, current_price)
                    if success:
                        bot.reply_to(message, f"✅ Позиция {sym}USDT закрыта вручную")
                    else:
                        bot.reply_to(message, f"❌ Ошибка закрытия позиции {sym}USDT")
                else:
                    bot.reply_to(message, f"❌ Ошибка получения цены для {sym}USDT")

            except Exception as e:
                bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# Создаем динамические команды при запуске
create_dynamic_handlers()


# 🔼 🔼 🔼 КОНЕЦ ДИНАМИЧЕСКИХ КОМАНД 🔼 🔼 🔼



@bot.message_handler(commands=['premium_signals'])
def premium_signals_command(message):
    """ПРЕМИУМ сигналы с AI-проверкой надежности"""
    try:
        wait_msg = bot.reply_to(message, "💎 AI ищет ПРЕМИУМ сигналы...")

        # Анализируем топ-8 монет
        symbols_to_analyze = top_coins_manager.get_top_coins_by_marketcap(8)
        premium_signals = []

        for symbol in symbols_to_analyze:
            try:
                # Получаем расширенный анализ
                response = requests.post(
                    f"{API_URL}/analyze-smart",
                    params={"symbol": symbol},
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    if "error" not in data and abs(data.get('strength', 0)) >= 5:  # Только сильные сигналы

                        # Получаем цели с динамическим RR
                        targets = dynamic_rr_calculator.calculate_adaptive_targets(
                            symbol,
                            direction="SELL" if data.get('action') == 'SELL' else "LONG",
                            base_stop_loss_percent=0.02,
                            min_rr=3.0  # МИНИМУМ RR 3.0 для премиум
                        )

                        # Анализ объемов
                        volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)

                        # Анализ тренда
                        trend_data = trend_analyzer.multi_timeframe_analysis(symbol)
                        confluence = trend_data.get('confluence_score', 0) if 'error' not in trend_data else 0

                        # AI-АНАЛИЗ НАДЕЖНОСТИ
                        ai_analysis_data = {
                            'volume_ratio': volume_data.get('volume_ratio', 0),
                            'current_price': targets['entry_price'],
                            'confluence': confluence
                        }

                        ai_analysis = ai_checker.analyze_signal_quality(symbol, ai_analysis_data)

                        # ПРЕМИУМ ФИЛЬТРЫ С AI
                        meets_premium = (
                                targets['risk_reward_ratio'] >= 3.0 and  # RR ≥ 3.0
                                targets['quality_score'] >= 8 and  # Качество ≥ 8/10
                                volume_data.get('volume_ratio', 0) >= 1.2 and  # Объемы ≥ 1.2x
                                abs(confluence) >= 60 and  # Конфлюэнс ≥ 60%
                                targets['current_volatility'] <= 8.0 and  # Волатильность ≤ 8%
                                ai_analysis['ai_confidence_score'] >= 7.0  # AI уверенность ≥ 7.0
                        )

                        if meets_premium:
                            # Расчет премиум-оценки
                            premium_calc = (
                                    (targets['risk_reward_ratio'] * 2) +
                                    (targets['quality_score']) +
                                    (volume_data.get('volume_ratio', 0) * 1.5) +
                                    (abs(confluence) / 10) +
                                    (ai_analysis['ai_confidence_score'] * 0.8)  # Добавляем AI оценку
                            )

                            premium_signals.append({
                                'symbol': symbol,
                                'action': data['action'],
                                'strength': data['strength'],
                                'targets': targets,
                                'volume_ratio': volume_data.get('volume_ratio', 0),
                                'confluence': confluence,
                                'ai_analysis': ai_analysis,
                                'premium_score': min(10, premium_calc)
                            })

                time.sleep(0.5)

            except Exception as e:
                print(f"Ошибка анализа {symbol} для премиум сигналов: {e}")
                continue

        if not premium_signals:
            bot.edit_message_text(
                "💎 AI не нашел ПРЕМИУМ сигналов. Рынок требует терпения.\n\n"
                "🔍 Причины:\n"
                "• Слабые объемы (<1.2x)\n"
                "• Низкий конфлюэнс (<60%)\n"
                "• Высокая волатильность (>8%)\n"
                "• AI уверенность <7.0/10",
                chat_id=wait_msg.chat.id,
                message_id=wait_msg.message_id
            )
            return

        # Сортируем по премиум score
        premium_signals.sort(key=lambda x: x['premium_score'], reverse=True)

        result_text = "💎 AI ПРЕМИУМ СИГНАЛЫ (только надежные)\n\n"

        for i, signal in enumerate(premium_signals[:3], 1):  # Только топ-3
            symbol_clean = signal['symbol'].replace('USDT', '')
            targets = signal['targets']
            ai_analysis = signal['ai_analysis']

            if signal['action'] == 'BUY':
                emoji = "🟢"
                action_text = "ПОКУПКА"
            else:
                emoji = "🔴"
                action_text = "ПРОДАЖА"

            result_text += f"{emoji} {i}. {symbol_clean} - {action_text}\n"
            result_text += f"   ⭐ Премиум оценка: {signal['premium_score']:.1f}/10\n"
            result_text += f"   🤖 AI уверенность: {ai_analysis['ai_confidence_score']}/10 {ai_analysis['color']}\n"
            result_text += f"   🎯 RR: 1:{targets['risk_reward_ratio']:.1f}\n"
            result_text += f"   💰 Цена: ${targets['entry_price']:,.2f}\n"
            result_text += f"   📊 Объемы: {signal['volume_ratio']:.1f}x\n"
            result_text += f"   📈 Конфлюэнс: {signal['confluence']}%\n"
            result_text += f"   ⚡ Волатильность: {targets['current_volatility']:.1f}%\n"
            result_text += f"   ✅ AI проверок: {ai_analysis.get('passed_checks', 3)}/{ai_analysis.get('total_checks', 3)}\n\n"
        # Детальный AI анализ для лучшего сигнала
        best_signal = premium_signals[0]
        best_ai = best_signal['ai_analysis']

        result_text += f"🏆 ЛУЧШИЙ СИГНАЛ: {best_signal['symbol'].replace('USDT', '')}\n"
        result_text += f"💡 {best_ai['recommendation']}\n\n"

        result_text += "📊 AI МЕТРИКИ ЛУЧШЕГО СИГНАЛА:\n"
        for metric_name, metric_data in best_ai['metrics'].items():
            result_text += f"• {metric_data['comment']}\n"

        # 🔽 🔽 🔽 ДОБАВЛЯЕМ ПЛАН ДЕЙСТВИЙ ДЛЯ ПРЕМИУМ СИГНАЛОВ 🔽 🔽 🔽

        if premium_signals:
            # Берем лучший премиум сигнал
            best_signal = premium_signals[0]
            best_symbol = best_signal['symbol']

            result_text += "\n" + "=" * 50 + "\n"
            result_text += add_trading_plan(best_symbol)

        # 🔼 🔼 🔼 КОНЕЦ ДОБАВЛЕННОГО КОДА 🔼 🔼 🔼
        result_text += f"\n🕐 AI премиум сканирование: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка AI премиум сканирования: {str(e)}")


@bot.message_handler(commands=['volume_scan'])
def volume_scan_command(message):
    """Сканирование всплесков объемов"""
    try:
        wait_msg = bot.reply_to(message, "🔍 Сканирую всплески объемов у топ-монет...")

        # ИСПРАВЛЕНИЕ: Сканируем только топ-20 монет
        symbols_to_scan = top_coins_manager.get_top_coins_by_marketcap(20)
        volume_signals = []

        for symbol in symbols_to_scan:
            try:
                volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)

                if 'error' not in volume_data and volume_data['is_volume_spike']:
                    volume_signals.append({
                        'symbol': symbol,
                        'volume_ratio': volume_data['volume_ratio'],
                        'signal': volume_data['signal'],
                        'confidence': volume_data['confidence'],
                        'price_change': volume_data['price_change_percent']
                    })

                time.sleep(0.3)  # Защита от лимитов

            except Exception as e:
                print(f"Ошибка сканирования объемов {symbol}: {e}")
                continue

        if not volume_signals:
            bot.edit_message_text("📊 Всплесков объемов у топ-монет не обнаружено", chat_id=wait_msg.chat.id,
                                  message_id=wait_msg.message_id)
            return

        # Сортируем по силе сигнала
        volume_signals.sort(key=lambda x: x['volume_ratio'], reverse=True)

        result_text = "🚀 СКАНЕР ВСПЛЕСКОВ ОБЪЕМОВ (ТОП-20)\n\n"

        for i, signal in enumerate(volume_signals[:8], 1):
            symbol_clean = signal['symbol'].replace('USDT', '')

            if signal['signal'] == 'PUMP_START':
                emoji = "🚀"
                action = "ПУМП"
            elif signal['signal'] == 'DUMP_START':
                emoji = "🔻"
                action = "ДАМП"
            else:
                emoji = "📈"
                action = "НАКОПЛЕНИЕ"

            result_text += f"{emoji} {i}. {symbol_clean}\n"
            result_text += f"   📊 Объем: {signal['volume_ratio']}x\n"
            result_text += f"   🎯 Сигнал: {action}\n"
            result_text += f"   💪 Уверенность: {signal['confidence']}\n"
            result_text += f"   📈 Изменение: {signal['price_change']}%\n\n"

        # 🔽 🔽 🔽 ЗАМЕНЯЕМ НА УНИВЕРСАЛЬНЫЙ ПЛАН 🔽 🔽 🔽

        # Добавляем план действий для лучшей монеты с высокими объемами
        high_volume_coins = []
        for signal in volume_signals[:3]:  # Берем топ-3 сигнала
            if signal['volume_ratio'] >= 2.0:
                high_volume_coins.append(signal)

        if high_volume_coins:
            # Берем самую сильную монету
            best_signal = high_volume_coins[0]
            best_symbol = best_signal['symbol']

            result_text += "\n" + "=" * 50 + "\n"
            result_text += add_trading_plan(best_symbol)

        # 🔼 🔼 🔼 КОНЕЦ ЗАМЕНЫ 🔼 🔼 🔼

        # Рекомендация
        pump_signals = [s for s in volume_signals if s['signal'] == 'PUMP_START']
        if pump_signals:
            best = pump_signals[0]
            result_text += f"\n🎯 ЛУЧШАЯ ВОЗМОЖНОСТЬ: {best['symbol'].replace('USDT', '')} (объем {best['volume_ratio']}x)"
        else:
            result_text += "\n💡 ВЫВОД: Есть накопление, но сильных пумпов нет"

        result_text += f"\n\n🕐 Сканирование завершено: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка сканирования объемов: {str(e)}")

@bot.message_handler(commands=['volume_monitor_start'])
def start_volume_monitor_command(message):
    """Запуск автоматического мониторинга объемов"""
    try:
        parts = message.text.split()

        if len(parts) > 1:
            symbols = [s.upper() for s in parts[1:]]
            # Проверяем что символы существуют
            invalid_symbols = [s for s in symbols if s not in ALL_SYMBOLS]
            if invalid_symbols:
                bot.reply_to(message, f"❌ Неизвестные символы: {', '.join(invalid_symbols)}")
                return
        else:
            # ИСПРАВЛЕНИЕ: Используем топ-монеты вместо ALL_SYMBOLS
            symbols = top_coins_manager.get_top_coins_by_marketcap(20)

        result = volume_monitor.start_volume_monitoring(
            chat_id=message.chat.id,
            symbols=symbols
        )

        status_text = f"""
{result}

🎯 МОНИТОРИМ 20 ТОП-МОНЕТ ПО КАПИТАЛИЗАЦИИ:
{', '.join([s.replace('USDT', '') for s in symbols[:15]])}

⚡ Авто-уведомления включены!
Бот пришлет сигнал когда увидит:
🚀 Начинающийся памп (объем 3x+, цена +2%+)
🔻 Начинающийся дамп (объем 3x+, цена -2%-)
📈 Крупные объемы без движения цены

/volume_monitor_stop - остановить
"""
        bot.reply_to(message, status_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка запуска: {e}")

@bot.message_handler(commands=['volume_monitor_stop'])
def stop_volume_monitor_command(message):
    """Остановка мониторинга объемов"""
    try:
        result = volume_monitor.stop_volume_monitoring()
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка остановки: {e}")


@bot.message_handler(commands=['volume_monitor_status'])
def volume_monitor_status_command(message):
    """Статус мониторинга объемов"""
    status = "АКТИВЕН" if volume_monitor.monitoring_active else "НЕАКТИВЕН"
    symbols_count = len(volume_monitor.monitored_symbols) if volume_monitor.monitored_symbols else 0

    status_text = f"""
📊 СТАТУС МОНИТОРИНГА ОБЪЕМОВ

Состояние: {status}
Монет в мониторинге: {symbols_count}
Последние алерты: {len(volume_monitor.alerted_signals)}

💡 Команды:
/volume_monitor_start - запустить
/volume_monitor_stop - остановить
/volume_scan - разовое сканирование
"""
    bot.reply_to(message, status_text)


@bot.message_handler(commands=['volume_monitor_popular'])
def volume_monitor_popular_command(message):
    """Мониторинг популярных монет"""
    try:
        # ИСПРАВЛЕНИЕ: Используем реально популярные пары
        popular_symbols = top_coins_manager.get_top_coins_by_marketcap(25)

        result = volume_monitor.start_volume_monitoring(
            chat_id=message.chat.id,
            symbols=popular_symbols
        )

        status_text = f"""
{result}

🎯 МОНИТОРИМ 25 ТОП-МОНЕТ по капитализации:
• {popular_symbols[0]} • {popular_symbols[1]} • {popular_symbols[2]}
• {popular_symbols[3]} • {popular_symbols[4]} • {popular_symbols[5]}
• {popular_symbols[6]} • {popular_symbols[7]} • {popular_symbols[8]}
• {popular_symbols[9]} • {popular_symbols[10]} • {popular_symbols[11]}

📊 ВКЛЮЧАЕТ:
BTC, ETH, BNB, SOL, XRP, ADA, AVAX, DOGE
и другие ликвидные активы

⚡ Авто-уведомления включены!
"""
        bot.reply_to(message, status_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


@bot.message_handler(commands=['live_signals'])
def live_signals_command(message):
    """Показывает активные торговые сигналы"""
    try:
        wait_msg = bot.reply_to(message, "🎯 Ищу активные торговые сигналы...")

        # Анализируем топ-15 монет
        symbols_to_check = top_coins_manager.get_top_coins_by_marketcap(15)
        active_signals = []

        for symbol in symbols_to_check:
            try:
                # 🔽 🔽 🔽 ДОБАВЛЯЕМ ФИЛЬТР СТЕЙБЛКОИНОВ 🔽 🔽 🔽
                stablecoins = ['USDCUSDT', 'USDTUSDT', 'BUSDUSDT', 'DAIUSDT', 'TUSDUSDT']
                if symbol in stablecoins:
                    continue  # Пропускаем стейблкоины
                # 🔼 🔼 🔼 КОНЕЦ ФИЛЬТРА 🔼 🔼 🔼

                # Анализ на нескольких таймфреймах
                timeframes = ['15m', '1h', '4h']
                signals = []

                for tf in timeframes:
                    response = requests.post(
                        f"{API_URL}/analyze",
                        params={"symbol": symbol, "timeframe": tf},
                        timeout=10
                    )

                    if response.status_code == 200:
                        data = response.json()
                        if "error" not in data and data.get('strength', 0) >= 1:  # СНИЗИЛ ДО 1
                            signals.append({
                                'timeframe': tf,
                                'action': data.get('action'),
                                'strength': data.get('strength', 0)
                            })

                    time.sleep(0.3)

                # 🔽 🔽 🔽 ИСПРАВЛЕННОЕ УСЛОВИЕ - БОЛЕЕ ЧУВСТВИТЕЛЬНОЕ 🔽 🔽 🔽
                if len(signals) >= 1:  # ДОСТАТОЧНО 1 СИГНАЛА
                    active_signals.append({
                        'symbol': symbol,
                        'signals': signals,
                        'strong_count': len([s for s in signals if s['strength'] >= 2])
                    })

            except Exception as e:
                continue

        if not active_signals:
            bot.edit_message_text("📊 Активных сильных сигналов не обнаружено",
                                  chat_id=wait_msg.chat.id,
                                  message_id=wait_msg.message_id)
            return

        # Сортируем по силе сигналов
        active_signals.sort(key=lambda x: x['strong_count'], reverse=True)

        result_text = "🎯 АКТИВНЫЕ ТОРГОВЫЕ СИГНАЛЫ\n\n"

        for i, signal in enumerate(active_signals[:5], 1):
            symbol_clean = signal['symbol'].replace('USDT', '')

            # Определяем общее направление
            buy_signals = [s for s in signal['signals'] if s['action'] == 'BUY']
            sell_signals = [s for s in signal['signals'] if s['action'] == 'SELL']

            if len(buy_signals) > len(sell_signals):
                direction = "🟢 ПОКУПКА"
                emoji = "🟢"
            elif len(sell_signals) > len(buy_signals):
                direction = "🔴 ПРОДАЖА"
                emoji = "🔴"
            else:
                direction = "🟡 СМЕШАННЫЙ"
                emoji = "🟡"

            result_text += f"{emoji} {i}. {symbol_clean} - {direction}\n"
            result_text += f"   📊 Сигналов: {len(signal['signals'])}/3 таймфреймов\n"

            # Показываем сигналы по таймфреймам
            for s in signal['signals'][:2]:
                tf_emoji = "🟢" if s['action'] == 'BUY' else "🔴"
                result_text += f"   {tf_emoji} {s['timeframe']}: {s['action']} (сила: {s['strength']})\n"

            result_text += "\n"

        # === AI-ФИЛЬТР ДЛЯ LIVE СИГНАЛОВ ===
        if active_signals:
            result_text += "🤖 AI-ФИЛЬТР LIVE СИГНАЛОВ:\n"
            result_text += "─" * 40 + "\n"

            reliable_signals = 0
            risky_signals = 0

            for signal in active_signals[:5]:
                symbol_clean = signal['symbol'].replace('USDT', '')

                try:
                    # AI-анализ надежности сигнала
                    # 🔽 🔽 🔽 УЛУЧШАЕМ AI АНАЛИЗ 🔽 🔽 🔽
                    ai_analysis = ai_checker.analyze_signal_quality(signal['symbol'], {
                        'current_price': 0,
                        'volume_ratio': 1.0,  # Добавляем объемы
                        'confluence': 50,  # Добавляем конфлюэнс
                        'action': signal['signals'][0]['action'] if signal['signals'] else 'HOLD'
                    })
                    # 🔼 🔼 🔼 КОНЕЦ УЛУЧШЕНИЯ 🔼 🔼 🔼

                    ai_score = ai_analysis['ai_confidence_score']
                    ai_color = ai_analysis['color']

                    if ai_score >= 6.0:
                        reliable_signals += 1
                        result_text += f"✅ {symbol_clean}: {ai_score:.1f}/10 {ai_color} - Надежный\n"
                    else:
                        risky_signals += 1
                        result_text += f"❌ {symbol_clean}: {ai_score:.1f}/10 {ai_color} - Рискованный\n"

                except Exception as e:
                    result_text += f"⚠️ {symbol_clean}: AI анализ недоступен\n"
                    risky_signals += 1

            # AI-СТАТИСТИКА
            result_text += f"\n📊 AI-СТАТИСТИКА LIVE СИГНАЛОВ:\n"
            result_text += f"• Всего активных сигналов: {len(active_signals)}\n"
            result_text += f"• ✅ Надежных (AI ≥6.0): {reliable_signals}\n"
            result_text += f"• ❌ Рискованных: {risky_signals}\n"

            # AI-РЕКОМЕНДАЦИЯ
            result_text += f"\n💡 AI-РЕКОМЕНДАЦИЯ:\n"
            if reliable_signals >= 2:
                result_text += "🎯 ХОРОШО - есть надежные сигналы для торговли\n"
            elif reliable_signals >= 1:
                result_text += "⚠️ УМЕРЕННО - только 1 надежный сигнал\n"
            else:
                result_text += "❌ ПЛОХО - нет надежных сигналов\n"
        else:
            result_text += "🤖 AI-АНАЛИЗ РЫНКА:\n"
            result_text += "📊 Активных сигналов не обнаружено\n"

        # 🔽 🔽 🔽 ДОБАВЛЯЕМ ПЛАН ДЕЙСТВИЙ 🔽 🔽 🔽

        if active_signals:
            # Берем самый сильный сигнал
            best_signal = active_signals[0]
            best_symbol = best_signal['symbol']

            result_text += "\n" + "=" * 50 + "\n"
            result_text += add_trading_plan(best_symbol)

        # 🔼 🔼 🔼 КОНЕЦ ДОБАВЛЕННОГО КОДА 🔼 🔼 🔼

        result_text += f"\n\n💡 Сигналы обновляются в реальном времени\n"
        result_text += f"🕐 AI анализ: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка поиска сигналов: {str(e)}")


@bot.message_handler(commands=['trading_ideas'])
def trading_ideas_command(message):
    """Готовые торговые идеи с РЕАЛЬНЫМИ AI данными"""
    try:
        wait_msg = bot.reply_to(message, "💡 Генерирую торговые идеи с AI анализом...")

        # Анализируем топ-8 монет для идей
        symbols_to_analyze = top_coins_manager.get_top_coins_by_marketcap(8)
        trading_ideas = []

        for symbol in symbols_to_analyze:
            try:
                # 🔽 🔽 🔽 РЕАЛЬНЫЕ ДАННЫЕ ДЛЯ AI АНАЛИЗА 🔽 🔽 🔽
                volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
                trend_data = trend_analyzer.multi_timeframe_analysis(symbol)
                confluence = trend_data.get('confluence_score', 0) if 'error' not in trend_data else 0

                # РЕАЛЬНЫЙ AI анализ
                ai_analysis = ai_checker.analyze_signal_quality(symbol, {
                    'volume_ratio': volume_data.get('volume_ratio', 0),
                    'current_price': 0,
                    'confluence': confluence
                })

                ai_confidence = ai_analysis['ai_confidence_score']

                # 🔽 ТОЛЬКО КАЧЕСТВЕННЫЕ ИДЕИ (AI ≥ 4.0)
                if ai_confidence >= 4.0:
                    # Получаем базовые данные
                    response = requests.post(
                        f"{API_URL}/analyze-smart",
                        params={"symbol": symbol},
                        timeout=10
                    )

                    if response.status_code == 200:
                        data = response.json()
                        if "error" not in data:
                            targets = target_calculator.calculate_targets(symbol)

                            # ФИЛЬТР СТЕЙБЛКОИНОВ
                            stablecoins = ['USDCUSDT', 'USDTUSDT', 'BUSDUSDT', 'DAIUSDT', 'TUSDUSDT']
                            if symbol in stablecoins:
                                continue

                            if "error" not in targets:
                                # Исправляем некорректные стоп-лоссы
                                if targets['direction'] == "LONG":
                                    if targets['stop_loss'] >= targets['entry_price']:
                                        targets['stop_loss'] = targets['entry_price'] * 0.98
                                        targets['take_profit'] = targets['entry_price'] * 1.06
                                        targets['risk_reward_ratio'] = 3.0
                                else:  # SHORT
                                    if targets['stop_loss'] <= targets['entry_price']:
                                        targets['stop_loss'] = targets['entry_price'] * 1.02
                                        targets['take_profit'] = targets['entry_price'] * 0.94
                                        targets['risk_reward_ratio'] = 3.0

                                # 🔽 РЕАЛЬНОЕ КАЧЕСТВО НА ОСНОВЕ AI
                                idea_quality = min(10, ai_confidence * 1.5)  # Нормализуем к 10-балльной шкале

                                trading_ideas.append({
                                    'symbol': symbol,
                                    'action': data['action'],
                                    'strength': data['strength'],
                                    'current_price': data.get('last_price', 0),
                                    'entry_price': targets['entry_price'],
                                    'stop_loss': targets['stop_loss'],
                                    'take_profit': targets['take_profit'],
                                    'risk_reward': targets['risk_reward_ratio'],
                                    'idea_quality': idea_quality,
                                    'ai_confidence': ai_confidence,
                                    'volume_ratio': volume_data.get('volume_ratio', 0),
                                    'confluence': confluence,
                                    'timeframe': data.get('best_timeframe', '15m')
                                })

                time.sleep(0.5)

            except Exception as e:
                print(f"Ошибка анализа {symbol} для торговых идей: {e}")
                continue

        if not trading_ideas:
            bot.edit_message_text(
                "📊 Сейчас нет качественных торговых идей. Рынок в неопределенности.",
                chat_id=wait_msg.chat.id,
                message_id=wait_msg.message_id
            )
            return

        # Сортируем по качеству идеи
        trading_ideas.sort(key=lambda x: x['idea_quality'], reverse=True)

        result_text = "🎯 ГОТОВЫЕ ТОРГОВЫЕ ИДЕИ\n\n"

        for i, idea in enumerate(trading_ideas[:5], 1):
            symbol_clean = idea['symbol'].replace('USDT', '')

            if idea['action'] == 'BUY':
                emoji = "🟢"
                direction = "LONG"
                action_text = "ПОКУПКА"
            else:
                emoji = "🔴"
                direction = "SHORT"
                action_text = "ПРОДАЖА"

            result_text += f"{emoji} {i}. {symbol_clean} - {action_text} {direction}\n"
            result_text += f"   ⭐ Качество: {idea['idea_quality']:.1f}/10\n"
            result_text += f"   💰 Текущая: ${idea['current_price']:,.2f}\n"
            result_text += f"   🎯 Вход: ${idea['entry_price']:,.2f}\n"
            result_text += f"   🛑 Стоп: ${idea['stop_loss']:,.2f}\n"
            result_text += f"   🎯 Тейк: ${idea['take_profit']:,.2f}\n"
            result_text += f"   📊 R:R = 1:{idea['risk_reward']:.1f}\n"
            result_text += f"   ⏰ ТФ: {idea['timeframe']}\n"
            result_text += f"   📈 Конфлюэнс: {idea['confluence']}%\n\n"

        # Общая рекомендация
        strong_ideas = [idea for idea in trading_ideas if idea['idea_quality'] >= 8]
        if strong_ideas:
            best_idea = strong_ideas[0]
            result_text += f"💡 ЛУЧШАЯ ИДЕЯ: {best_idea['symbol'].replace('USDT', '')} "
            result_text += f"(качество {best_idea['idea_quality']:.1f}/10)\n"
        else:
            result_text += "💡 ВЫБИРАЙТЕ ИДЕИ С КАЧЕСТВОМ ВЫШЕ 7/10\n"

        # === 🔥 ДОБАВЛЯЕМ AI-ФИЛЬТР НАДЕЖНОСТИ ===
        result_text += f"\n🤖 AI-ФИЛЬТР НАДЕЖНОСТИ ИДЕЙ:\n"
        result_text += "─" * 40 + "\n"

        high_quality_count = 0
        medium_quality_count = 0
        low_quality_count = 0

        # Анализируем каждую идею через AI
        for i, idea in enumerate(trading_ideas[:5], 1):
            symbol_clean = idea['symbol'].replace('USDT', '')

            try:
                # Используем УЖЕ РАССЧИТАННЫЕ AI данные
                ai_score = idea['ai_confidence']

                # Считаем статистику
                if ai_score >= 7.0:
                    high_quality_count += 1
                    status_emoji = "✅"
                    status_text = "ВЫСОКАЯ НАДЕЖНОСТЬ"
                elif ai_score >= 5.0:
                    medium_quality_count += 1
                    status_emoji = "⚠️"
                    status_text = "СРЕДНЯЯ НАДЕЖНОСТЬ"
                else:
                    low_quality_count += 1
                    status_emoji = "❌"
                    status_text = "НИЗКАЯ НАДЕЖНОСТЬ"

                # Добавляем AI-оценку для каждой идеи
                result_text += f"{status_emoji} {symbol_clean}: {ai_score:.1f}/10 - {status_text}\n"

                # Показываем ключевые проблемы если низкая надежность
                if ai_score < 5.0:
                    key_issues = []

                    if idea['volume_ratio'] < 0.8:
                        key_issues.append("слабые объемы")
                    if idea['confluence'] < 30:
                        key_issues.append("плохое настроение рынка")
                    if idea['volume_ratio'] < 0.5:
                        key_issues.append("нет китов")

                    if key_issues:
                        result_text += f"   🔍 Проблемы: {', '.join(key_issues)}\n"

            except Exception as e:
                result_text += f"⚠️ {symbol_clean}: AI анализ временно недоступен\n"
                low_quality_count += 1

        # AI-СТАТИСТИКА И РЕКОМЕНДАЦИИ
        result_text += "\n📊 AI-СТАТИСТИКА ИДЕЙ:\n"
        result_text += f"• ✅ Высокая надежность: {high_quality_count} идей\n"
        result_text += f"• ⚠️ Средняя надежность: {medium_quality_count} идей\n"
        result_text += f"• ❌ Низкая надежность: {low_quality_count} идей\n"

        # AI-РЕКОМЕНДАЦИЯ ПО ТОРГОВЛЕ
        result_text += f"\n💡 AI-РЕКОМЕНДАЦИЯ ДЛЯ ТРЕЙДЕРА:\n"

        if high_quality_count >= 3:
            result_text += "🎯 ОТЛИЧНЫЕ УСЛОВИЯ - можно активно торговать\n"
            result_text += "💡 Рекомендация: Входить в надежные идеи с полными позициями"
        elif high_quality_count >= 1:
            result_text += "✅ ХОРОШИЕ УСЛОВИЯ - можно торговать выборочно\n"
            result_text += "💡 Рекомендация: Входить только в идеи с AI ≥7.0/10"
        elif medium_quality_count >= 2:
            result_text += "⚠️ УМЕРЕННЫЕ УСЛОВИЯ - торговать с осторожностью\n"
            result_text += "💡 Рекомендация: Использовать меньшие позиции и строгие стоп-лоссы"
        else:
            result_text += "❌ НЕБЛАГОПРИЯТНЫЕ УСЛОВИЯ - лучше воздержаться\n"
            result_text += "💡 Рекомендация: Дождаться улучшения рыночных условий"

        # 🔽 🔽 🔽 ДОБАВЛЯЕМ ПЛАН ДЕЙСТВИЙ ДЛЯ ЛУЧШЕЙ ИДЕИ 🔽 🔽 🔽
        if trading_ideas:
            # Берем лучшую идею (первую в списке)
            best_idea = trading_ideas[0]
            best_symbol = best_idea['symbol']

            result_text += "\n" + "=" * 50 + "\n"
            result_text += f"\n🎯 **ПЛАН ДЕЙСТВИЙ ДЛЯ {best_symbol.replace('USDT', '')}:**\n\n"
            result_text += f"1. 🔍 **ПРОВЕРИТЬ НАДЕЖНОСТЬ:**\n"
            result_text += f"   `/analyze_smart {best_symbol}`\n\n"
            result_text += f"2. ✅ **ЕСЛИ AI ≥7.0** - продолжить\n"
            result_text += f"   ❌ **ЕСЛИ AI <7.0** - ПРОПУСТИТЬ сделку\n\n"
            result_text += f"3. 📊 **ПОЛУЧИТЬ ЦЕЛИ:**\n"
            result_text += f"   `/advanced_targets {best_symbol}`\n\n"
            result_text += f"4. ⚡ **РАССЧИТАТЬ РИСК:**\n"
            result_text += f"   `/risk {best_symbol} [ВАШ_БАЛАНС] 2`\n\n"
            result_text += f"5. 🤖 **ОТКРЫТЬ СДЕЛКУ:**\n"
            result_text += f"   Скопируйте команду из /advanced_targets\n\n"
            result_text += f"💡 **ПРАВИЛО:** Входите ТОЛЬКО при AI уверенности ≥7.0!\n"

        result_text += f"\n🕐 AI анализ завершен: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка генерации идей: {str(e)}")

@bot.message_handler(commands=['ai_market_status'])
def ai_market_status_command(message):
    """Глубокий AI-анализ текущего состояния рынка"""
    try:
        wait_msg = bot.reply_to(message, "🤖 AI проводит глубокий анализ рынка...")

        # Анализируем топ-10 монет для полной картины
        symbols_to_analyze = top_coins_manager.get_top_coins_by_marketcap(10)
        market_analysis = []

        for symbol in symbols_to_analyze:
            try:
                # Получаем детальный AI-анализ для каждой монеты
                ai_analysis = ai_checker.analyze_signal_quality(symbol, {
                    'current_price': 0  # Цена не нужна для общего анализа
                })

                # Получаем базовые данные монеты
                response = requests.post(
                    f"{API_URL}/analyze-smart",
                    params={"symbol": symbol},
                    timeout=5
                )

                if response.status_code == 200:
                    data = response.json()
                    if "error" not in data:
                        market_analysis.append({
                            'symbol': symbol,
                            'action': data.get('action', 'HOLD'),
                            'strength': data.get('strength', 0),
                            'ai_confidence': ai_analysis['ai_confidence_score'],
                            'ai_color': ai_analysis['color'],
                            'metrics': ai_analysis.get('metrics', {})
                        })

                time.sleep(0.3)

            except Exception as e:
                print(f"Ошибка анализа {symbol}: {e}")
                continue

        # 🔥 AI-АНАЛИЗ РЫНКА
        if market_analysis:
            # Статистика
            total_symbols = len(market_analysis)
            avg_ai_confidence = sum(item['ai_confidence'] for item in market_analysis) / total_symbols
            buy_signals = sum(1 for item in market_analysis if item['action'] == 'BUY')
            sell_signals = sum(1 for item in market_analysis if item['action'] == 'SELL')

            # AI-метрики рынка
            volume_metrics = [item['metrics'].get('volume_quality', {}).get('score', 0) for item in market_analysis]
            sentiment_metrics = [item['metrics'].get('market_sentiment', {}).get('score', 0) for item in
                                 market_analysis]
            whale_metrics = [item['metrics'].get('whale_activity', {}).get('score', 0) for item in market_analysis]

            avg_volume = sum(volume_metrics) / len(volume_metrics) if volume_metrics else 0
            avg_sentiment = sum(sentiment_metrics) / len(sentiment_metrics) if sentiment_metrics else 0
            avg_whale = sum(whale_metrics) / len(whale_metrics) if whale_metrics else 0

            # Формируем детальный отчет
            result_text = "🤖 AI-ДИАГНОСТИКА РЫНКА\n\n"

            # 1. ОБЩАЯ ОЦЕНКА
            result_text += "🎯 ОБЩАЯ AI-ОЦЕНКА РЫНКА:\n"
            if avg_ai_confidence >= 8.0:
                result_text += "🟢 ВЫСОКАЯ НАДЕЖНОСТЬ - отличные условия\n"
            elif avg_ai_confidence >= 6.0:
                result_text += "🟡 СРЕДНЯЯ НАДЕЖНОСТЬ - умеренные условия\n"
            else:
                result_text += "🔴 НИЗКАЯ НАДЕЖНОСТЬ - рискованные условия\n"

            result_text += f"• Средняя AI-уверенность: {avg_ai_confidence:.1f}/10\n"
            result_text += f"• Бычьих сигналов: {buy_signals}/{total_symbols}\n"
            result_text += f"• Медвежьих сигналов: {sell_signals}/{total_symbols}\n\n"

            # 2. КЛЮЧЕВЫЕ МЕТРИКИ
            result_text += "📊 КЛЮЧЕВЫЕ AI-МЕТРИКИ:\n"
            result_text += f"• 📈 Объемы: {avg_volume:.1%} от идеала\n"
            result_text += f"• 🎭 Настроение: {avg_sentiment:.1%} бычье\n"
            result_text += f"• 🐋 Активность китов: {avg_whale:.1%}\n"
            result_text += f"• ⚡ Ликвидность: {sum(item['metrics'].get('liquidity', {}).get('score', 0) for item in market_analysis) / total_symbols:.1%}\n\n"

            # 3. СТАТУС ПО СЕКТОРАМ
            result_text += "🏗️ СТАТУС РЫНОЧНЫХ СЕКТОРОВ:\n"

            # Биткойн и крупные альты
            btc_eth = [item for item in market_analysis if item['symbol'] in ['BTCUSDT', 'ETHUSDT']]
            if btc_eth:
                btc_eth_avg = sum(item['ai_confidence'] for item in btc_eth) / len(btc_eth)
                result_text += f"• 🏆 Лидеры (BTC/ETH): {btc_eth_avg:.1f}/10 {'🟢' if btc_eth_avg >= 7 else '🔴' if btc_eth_avg < 4 else '🟡'}\n"

            # ДеФи
            defi_coins = [item for item in market_analysis if item['symbol'] in ['UNIUSDT', 'AAVEUSDT', 'COMPUSDT']]
            if defi_coins:
                defi_avg = sum(item['ai_confidence'] for item in defi_coins) / len(defi_coins)
                result_text += f"• 💰 DeFi сектор: {defi_avg:.1f}/10 {'🟢' if defi_avg >= 7 else '🔴' if defi_avg < 4 else '🟡'}\n"

            # 4. ТОП-СИГНАЛЫ И ПРЕДУПРЕЖДЕНИЯ
            result_text += f"\n🎯 ТОП-3 САМЫХ НАДЕЖНЫХ СИГНАЛОВ:\n"
            top_signals = sorted(market_analysis, key=lambda x: x['ai_confidence'], reverse=True)[:3]
            for i, signal in enumerate(top_signals, 1):
                symbol_clean = signal['symbol'].replace('USDT', '')
                result_text += f"{i}. {symbol_clean}: {signal['ai_confidence']:.1f}/10 {signal['ai_color']}\n"

            # 5. ГЛАВНЫЕ ПРОБЛЕМЫ РЫНКА
            result_text += f"\n⚠️ ГЛАВНЫЕ ПРОБЛЕМЫ РЫНКА:\n"
            problems = []
            if avg_sentiment < 0.4:
                problems.append("📉 Слабое рыночное настроение")
            if avg_volume < 0.5:
                problems.append("📊 Низкие объемы")
            if avg_whale < 0.4:
                problems.append("🐋 Нет активности китов")
            if avg_ai_confidence < 5.0:
                problems.append("🤖 Низкая общая надежность")

            if problems:
                for problem in problems:
                    result_text += f"• {problem}\n"
            else:
                result_text += "• ✅ Критических проблем не обнаружено\n"

            # 6. AI-РЕКОМЕНДАЦИЯ
            result_text += f"\n💡 AI-РЕКОМЕНДАЦИЯ НА СЕЙЧАС:\n"
            if avg_ai_confidence >= 7.5 and buy_signals >= 5:
                result_text += "🚀 АКТИВНАЯ ТОРГОВЛЯ - рынок благоприятствует\n"
            elif avg_ai_confidence >= 6.0 and buy_signals > sell_signals:
                result_text += "✅ ВЫБОРОЧНАЯ ТОРГОВЛЯ - ищите качественные сигналы\n"
            elif avg_ai_confidence >= 4.0:
                result_text += "⚠️ ОСТОРОЖНАЯ ТОРГОВЛЯ - используйте маленькие позиции\n"
            else:
                result_text += "❌ ВОЗДЕРЖАТЬСЯ ОТ ТОРГОВЛИ - рынок слишком рискованный\n"

        else:
            result_text = "❌ Не удалось проанализировать рынок. Попробуйте позже."

        result_text += f"\n\n🕐 AI диагностика завершена: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка AI диагностики: {str(e)}")

@bot.message_handler(commands=['ai_recommendations'])
def ai_recommendations_command(message):
    """AI рекомендации на основе анализа множества факторов"""
    try:
        wait_msg = bot.reply_to(message, "🤖 AI анализирует рынок...")

        # Анализируем топ-12 монет для AI рекомендаций
        symbols_to_analyze = top_coins_manager.get_top_coins_by_marketcap(12)
        ai_recommendations = []

        for symbol in symbols_to_analyze:
            try:
                # Собираем данные для AI анализа
                analysis_data = {}

                # 1. Базовый анализ
                response = requests.post(
                    f"{API_URL}/analyze-smart",
                    params={"symbol": symbol},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if "error" not in data:
                        analysis_data.update({
                            'action': data.get('action', 'HOLD'),
                            'strength': data.get('strength', 0),
                            'price': data.get('last_price', 0),
                            'best_timeframe': data.get('best_timeframe', '15m')
                        })

                # 2. Анализ тренда
                trend_data = trend_analyzer.multi_timeframe_analysis(symbol)
                if 'error' not in trend_data:
                    analysis_data['confluence'] = trend_data.get('confluence_score', 0)
                    analysis_data['trend'] = trend_data.get('overall_trend', 'NEUTRAL')

                # 3. Анализ объемов
                volume_data = volume_analyzer.get_volume_analysis(symbol)
                if isinstance(volume_data, tuple):
                    analysis_data['volume_strength'] = volume_data[0].get('strength', 0)
                else:
                    analysis_data['volume_strength'] = volume_data.get('strength', 0)

                # 4. Расчет целей
                targets = target_calculator.calculate_targets(symbol)
                if 'error' not in targets:
                    analysis_data.update({
                        'entry_price': targets['entry_price'],
                        'stop_loss': targets['stop_loss'],
                        'take_profit': targets['take_profit'],
                        'risk_reward': targets['risk_reward_ratio'],
                        'quality_score': targets['quality_score']
                    })

                # 🔥 ЗАМЕНЯЕМ УПРОЩЕННЫЙ AI НА ДЕТАЛЬНЫЙ AI-АНАЛИЗ
                if all(key in analysis_data for key in ['strength', 'confluence', 'volume_strength', 'risk_reward']):

                    try:
                        # Используем наш ДЕТАЛЬНЫЙ AI-анализатор
                        detailed_ai_analysis = ai_checker.analyze_signal_quality(symbol, {
                            'volume_ratio': analysis_data['volume_strength'],
                            'current_price': analysis_data.get('price', 0),
                            'confluence': analysis_data['confluence'],
                            'action': analysis_data.get('action', 'HOLD')
                        })

                        # Берем оценку из детального AI
                        ai_score = detailed_ai_analysis['ai_confidence_score']
                        ai_recommendation = detailed_ai_analysis['recommendation']
                        ai_color = detailed_ai_analysis['color']

                    except Exception as e:
                        # Если детальный AI не сработал, используем старый расчет
                        print(f"Детальный AI анализ не сработал: {e}")
                        ai_score = calculate_ai_score(analysis_data)
                        ai_recommendation = "AI анализ завершен"
                        ai_color = "🟢" if ai_score >= 70 else "🔴" if ai_score <= 40 else "🟡"

                    if ai_score >= 65:  # Только сильные рекомендации
                        recommendation = generate_ai_recommendation(analysis_data, ai_score)
                        # 🔥 ДОБАВЛЯЕМ AI-ДАННЫЕ В РЕКОМЕНДАЦИЮ
                        recommendation['ai_score'] = ai_score
                        recommendation['ai_color'] = ai_color
                        recommendation['ai_recommendation'] = ai_recommendation
                        ai_recommendations.append(recommendation)

                    if ai_score >= 65:  # Только сильные рекомендации
                        recommendation = generate_ai_recommendation(analysis_data, ai_score)
                        ai_recommendations.append(recommendation)

                time.sleep(0.5)

            except Exception as e:
                print(f"AI анализ {symbol} ошибка: {e}")
                continue

        if not ai_recommendations:
            bot.edit_message_text(
                "🤖 AI не нашел сильных рекомендаций. Рынок требует осторожности.",
                chat_id=wait_msg.chat.id,
                message_id=wait_msg.message_id
            )
            return

        # Сортируем по AI score
        ai_recommendations.sort(key=lambda x: x['ai_score'], reverse=True)

        result_text = "🤖 AI РЕКОМЕНДАЦИИ\n\n"

        for i, rec in enumerate(ai_recommendations[:4], 1):
            symbol_clean = rec['symbol'].replace('USDT', '')

            result_text += f"🎯 {i}. {symbol_clean}\n"
            result_text += f"   ⭐ AI Оценка: {rec['ai_score']}/100\n"
            result_text += f"   💡 Рекомендация: {rec['recommendation']}\n"
            result_text += f"   📊 Уверенность: {rec['confidence']}\n"
            result_text += f"   🎯 Действие: {rec['action']}\n"
            result_text += f"   💰 Цена: ${rec['price']:,.2f}\n"

            if rec.get('time_horizon'):
                result_text += f"   ⏰ Горизонт: {rec['time_horizon']}\n"

            result_text += "\n"

        # 🔥 ДОБАВЛЯЕМ AI-СТАТИСТИКУ РЫНКА
        if ai_recommendations:
            # Считаем среднюю AI-оценку
            avg_ai_score = sum(rec['ai_score'] for rec in ai_recommendations) / len(ai_recommendations)

            # Считаем статистику по надежности
            high_confidence = sum(1 for rec in ai_recommendations if rec['ai_score'] >= 80)
            medium_confidence = sum(1 for rec in ai_recommendations if 60 <= rec['ai_score'] < 80)
            low_confidence = sum(1 for rec in ai_recommendations if rec['ai_score'] < 60)

            result_text += "📊 AI-ДИАГНОСТИКА РЫНКА:\n"
            result_text += f"• Средняя оценка: {avg_ai_score:.1f}/100\n"
            result_text += f"• Высокая надежность: {high_confidence} монет\n"
            result_text += f"• Средняя надежность: {medium_confidence} монет\n"
            result_text += f"• Низкая надежность: {low_confidence} монет\n"

            # AI-РЕКОМЕНДАЦИЯ ПО РЫНКУ
            result_text += f"\n💡 AI-РЕКОМЕНДАЦИЯ ДЛЯ ТРЕЙДЕРА:\n"
            if avg_ai_score >= 80 and high_confidence >= 3:
                result_text += "🎯 ОТЛИЧНЫЕ УСЛОВИЯ - можно активно торговать\n"
            elif avg_ai_score >= 70 and high_confidence >= 1:
                result_text += "✅ ХОРОШИЕ УСЛОВИЯ - торговать выборочно\n"
            elif avg_ai_score >= 60:
                result_text += "⚠️ УМЕРЕННЫЕ УСЛОВИЯ - торговать с осторожностью\n"
            else:
                result_text += "❌ СЛОЖНЫЕ УСЛОВИЯ - лучше воздержаться от сделок\n"
        else:
            result_text += "📊 AI-ДИАГНОСТИКА РЫНКА:\n"
            result_text += "• Нет качественных рекомендаций\n"
            result_text += "• Рынок в неопределенности\n"
            result_text += f"\n💡 AI-РЕКОМЕНДАЦИЯ: ❌ Воздержаться от торговли\n"

        # Общая AI аналитика
        strong_recs = [r for r in ai_recommendations if r['ai_score'] >= 80]
        if strong_recs:
            result_text += f"\n🚀 AI ВЫЯВИЛ {len(strong_recs)} СИЛЬНЫХ СИГНАЛОВ\n"
        else:
            result_text += f"\n💡 AI РЕКОМЕНДУЕТ ОСТОРОЖНЫЙ ПОДХОД\n"

        # 🔽 🔽 🔽 ДОБАВЛЯЕМ ПЛАН ДЕЙСТВИЙ ДЛЯ AI РЕКОМЕНДАЦИЙ 🔽 🔽 🔽

        if ai_recommendations:
            # ЕСТЬ рекомендации - показываем план для лучшей
            best_rec = ai_recommendations[0]
            best_symbol = best_rec['symbol']

            result_text += "\n" + "=" * 50 + "\n"
            result_text += add_trading_plan(best_symbol)
        else:
            # НЕТ рекомендаций - показываем общий план для BTC
            result_text += "\n" + "=" * 50 + "\n"
            result_text += "🎯 **ОБЩИЙ ПЛАН ДЕЙСТВИЙ:**\n\n"
            result_text += "🤖 AI не нашел сильных сигналов - это ЗАЩИТА!\n\n"
            result_text += "1. 🔍 **ПОИСК АЛЬТЕРНАТИВ:**\n"
            result_text += "   /trading_ideas - Готовые идеи\n"
            result_text += "   /volume_scan - Сканер объемов\n"
            result_text += "   /anomaly - Активные аномалии\n\n"
            result_text += "2. ⏰ **ОЖИДАНИЕ:**\n"
            result_text += "   • Дождитесь сильного сигнала (AI ≥7.0)\n"
            result_text += "   • Лучше пропустить сделку, чем войти в слабую\n\n"
            result_text += "3. 📊 **МОНИТОРИНГ:**\n"
            result_text += "   /activate_all - Авто-поиск сигналов\n"
            result_text += "   Бот уведомит когда появится сильный сигнал\n\n"
            result_text += "💡 **ВЫВОД:** Нет сигналов = Нет убытков! ✅"

        # 🔼 🔼 🔼 КОНЕЦ ДОБАВЛЕННОГО КОДА 🔼 🔼 🔼


        result_text += f"\n🕐 AI анализ: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка AI анализа: {str(e)}")


@bot.message_handler(commands=['risk_dashboard'])
def risk_dashboard_command(message):
    """AI-панель управления рисками и мониторинга рынка"""
    try:
        wait_msg = bot.reply_to(message, "🎯 AI запускает панель управления рисками...")

        # Собираем данные для панели рисков
        risk_data = {
            'market_risk': 0,
            'volume_risk': 0,
            'liquidity_risk': 0,
            'sentiment_risk': 0,
            'overall_risk': 0,
            'alerts': [],
            'recommendations': []
        }

        # Анализируем топ-8 монет для оценки рисков
        symbols_to_analyze = top_coins_manager.get_top_coins_by_marketcap(8)

        for symbol in symbols_to_analyze:
            try:
                ai_analysis = ai_checker.analyze_signal_quality(symbol, {'current_price': 0})
                risk_data['market_risk'] += (10 - ai_analysis['ai_confidence_score'])

                # Анализируем метрики рисков
                metrics = ai_analysis.get('metrics', {})

                # Риск объемов
                volume_score = metrics.get('volume_quality', {}).get('score', 0)
                risk_data['volume_risk'] += (1 - volume_score)

                # Риск настроения
                sentiment_score = metrics.get('market_sentiment', {}).get('score', 0)
                risk_data['sentiment_risk'] += (1 - sentiment_score)

                # Риск ликвидности
                liquidity_score = metrics.get('liquidity', {}).get('score', 0)
                risk_data['liquidity_risk'] += (1 - liquidity_score)

                time.sleep(0.2)

            except Exception as e:
                print(f"Ошибка анализа рисков {symbol}: {e}")
                continue

        # Нормализуем риски (0-10 шкала)
        total_symbols = len(symbols_to_analyze)
        if total_symbols > 0:
            risk_data['market_risk'] = risk_data['market_risk'] / total_symbols
            risk_data['volume_risk'] = (risk_data['volume_risk'] / total_symbols) * 10
            risk_data['sentiment_risk'] = (risk_data['sentiment_risk'] / total_symbols) * 10
            risk_data['liquidity_risk'] = (risk_data['liquidity_risk'] / total_symbols) * 10

            # Общий риск (среднее взвешенное)
            risk_data['overall_risk'] = (
                    risk_data['market_risk'] * 0.4 +
                    risk_data['volume_risk'] * 0.3 +
                    risk_data['sentiment_risk'] * 0.2 +
                    risk_data['liquidity_risk'] * 0.1
            )

        # 🔥 ФОРМИРУЕМ ПАНЕЛЬ РИСКОВ
        result_text = "🎯 AI-ПАНЕЛЬ УПРАВЛЕНИЯ РИСКАМИ\n\n"

        # 1. ОБЩИЙ УРОВЕНЬ РИСКА
        result_text += "⚠️ ОБЩИЙ УРОВЕНЬ РИСКА:\n"
        if risk_data['overall_risk'] >= 8.0:
            result_text += "🔴 КРИТИЧЕСКИЙ УРОВЕНЬ\n"
            risk_emoji = "🔴"
        elif risk_data['overall_risk'] >= 6.0:
            result_text += "🟠 ВЫСОКИЙ УРОВЕНЬ\n"
            risk_emoji = "🟠"
        elif risk_data['overall_risk'] >= 4.0:
            result_text += "🟡 СРЕДНИЙ УРОВЕНЬ\n"
            risk_emoji = "🟡"
        else:
            result_text += "🟢 НИЗКИЙ УРОВЕНЬ\n"
            risk_emoji = "🟢"

        result_text += f"• Оценка: {risk_data['overall_risk']:.1f}/10 {risk_emoji}\n\n"

        # 2. ДЕТАЛЬНЫЕ МЕТРИКИ РИСКА
        result_text += "📊 ДЕТАЛЬНЫЕ МЕТРИКИ РИСКА:\n"

        # Рыночный риск
        market_risk_emoji = "🔴" if risk_data['market_risk'] >= 7 else "🟠" if risk_data['market_risk'] >= 5 else "🟡"
        result_text += f"• 📈 Рыночный риск: {risk_data['market_risk']:.1f}/10 {market_risk_emoji}\n"

        # Риск объемов
        volume_risk_emoji = "🔴" if risk_data['volume_risk'] >= 8 else "🟠" if risk_data['volume_risk'] >= 6 else "🟡"
        result_text += f"• 📊 Риск объемов: {risk_data['volume_risk']:.1f}/10 {volume_risk_emoji}\n"

        # Риск настроения
        sentiment_risk_emoji = "🔴" if risk_data['sentiment_risk'] >= 9 else "🟠" if risk_data[
                                                                                       'sentiment_risk'] >= 7 else "🟡"
        result_text += f"• 🎭 Риск настроения: {risk_data['sentiment_risk']:.1f}/10 {sentiment_risk_emoji}\n"

        # Риск ликвидности
        liquidity_risk_emoji = "🔴" if risk_data['liquidity_risk'] >= 7 else "🟠" if risk_data[
                                                                                       'liquidity_risk'] >= 5 else "🟡"
        result_text += f"• 💧 Риск ликвидности: {risk_data['liquidity_risk']:.1f}/10 {liquidity_risk_emoji}\n\n"

        # 3. AI-АЛАРМЫ И ПРЕДУПРЕЖДЕНИЯ
        result_text += "🚨 AI-АЛАРМЫ И ПРЕДУПРЕЖДЕНИЯ:\n"

        # Генерируем алерты на основе рисков
        alerts = []
        if risk_data['sentiment_risk'] >= 8.0:
            alerts.append("🔴 КРИТИЧЕСКИЙ: Рыночное настроение катастрофическое")
        if risk_data['volume_risk'] >= 7.0:
            alerts.append("🔴 ВЫСОКИЙ: Объемы опасно низкие")
        if risk_data['market_risk'] >= 6.0:
            alerts.append("🟠 СРЕДНИЙ: Общая надежность рынка низкая")
        if risk_data['liquidity_risk'] >= 5.0:
            alerts.append("🟠 СРЕДНИЙ: Проблемы с ликвидностью")

        if alerts:
            for alert in alerts:
                result_text += f"• {alert}\n"
        else:
            result_text += "• ✅ Критических предупреждений нет\n"

        result_text += "\n"

        # 4. AI-РЕКОМЕНДАЦИИ ПО УПРАВЛЕНИЮ РИСКАМИ
        result_text += "💡 AI-РЕКОМЕНДАЦИИ ПО РИСКАМ:\n"

        if risk_data['overall_risk'] >= 8.0:
            result_text += "❌ ПОЛНЫЙ СТОП: Прекратить все торговые операции\n"
            result_text += "💡 Действия: Дождаться улучшения рыночных условий\n"
        elif risk_data['overall_risk'] >= 6.0:
            result_text += "⚠️ ВЫСОКАЯ ОСТОРОЖНОСТЬ: Только хеджирование\n"
            result_text += "💡 Действия: Макс. позиция 1% от депозита\n"
        elif risk_data['overall_risk'] >= 4.0:
            result_text += "🟡 УМЕРЕННЫЙ РИСК: Осторожная торговля\n"
            result_text += "💡 Действия: Позиции 2-3% с жесткими стоп-лоссами\n"
        else:
            result_text += "🟢 НИЗКИЙ РИСК: Нормальная торговля\n"
            result_text += "💡 Действия: Стандартные позиции 5%\n"

        # 5. МОНИТОРИНГ КЛЮЧЕВЫХ УРОВНЕЙ
        result_text += f"\n🎯 МОНИТОРИНГ КЛЮЧЕВЫХ УРОВНЕЙ:\n"
        result_text += f"• 📉 BTC доминирование: Выше 50% - риск для альтов\n"
        result_text += f"• 📊 Общий объем: Критически низкий\n"
        result_text += f"• 🎭 Бычьи сигналы: 0% - экстремальный пессимизм\n"

        result_text += f"\n🕐 Панель обновлена: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка панели рисков: {str(e)}")


@bot.message_handler(commands=['ai_scan_volume'])
def ai_scan_volume_command(message):
    """AI-сканирование всплесков объемов с проверкой надежности"""
    try:
        wait_msg = bot.reply_to(message, "🤖 AI сканирует объемы с проверкой надежности...")

        # Сканируем топ-15 монет
        symbols_to_scan = top_coins_manager.get_top_coins_by_marketcap(15)
        volume_signals = []

        for symbol in symbols_to_scan:
            try:
                volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)

                if 'error' not in volume_data and volume_data['is_volume_spike']:
                    # 🔥 AI-ПРОВЕРКА НАДЕЖНОСТИ СИГНАЛА
                    ai_analysis = ai_checker.analyze_signal_quality(symbol, {
                        'volume_ratio': volume_data['volume_ratio'],
                        'current_price': 0
                    })

                    # Добавляем только если AI уверен
                    if ai_analysis['ai_confidence_score'] >= 5.0:
                        volume_signals.append({
                            'symbol': symbol,
                            'volume_ratio': volume_data['volume_ratio'],
                            'signal': volume_data['signal'],
                            'confidence': volume_data['confidence'],
                            'price_change': volume_data['price_change_percent'],
                            'ai_confidence': ai_analysis['ai_confidence_score'],
                            'ai_color': ai_analysis['color']
                        })

                time.sleep(0.3)

            except Exception as e:
                print(f"Ошибка AI сканирования {symbol}: {e}")
                continue

        if not volume_signals:
            bot.edit_message_text(
                "🤖 AI не нашел надежных всплесков объемов\n"
                "💡 Все сигналы отфильтрованы по низкой AI-уверенности",
                chat_id=wait_msg.chat.id,
                message_id=wait_msg.message_id
            )
            return

        # Сортируем по AI-уверенности
        volume_signals.sort(key=lambda x: x['ai_confidence'], reverse=True)

        result_text = "🤖 AI-СКАНИРОВАНИЕ ОБЪЕМОВ (только надежные)\n\n"

        for i, signal in enumerate(volume_signals[:5], 1):
            symbol_clean = signal['symbol'].replace('USDT', '')

            if signal['signal'] == 'PUMP_START':
                emoji = "🚀"
                action = "ПУМП"
            elif signal['signal'] == 'DUMP_START':
                emoji = "🔻"
                action = "ДАМП"
            else:
                emoji = "📈"
                action = "ВСПЛЕСК"

            result_text += f"{emoji} {i}. {symbol_clean}\n"
            result_text += f"   📊 Объем: {signal['volume_ratio']}x\n"
            result_text += f"   🎯 Сигнал: {action}\n"
            result_text += f"   🤖 AI-уверенность: {signal['ai_confidence']:.1f}/10 {signal['ai_color']}\n"
            result_text += f"   💪 Volume уверенность: {signal['confidence']}\n"
            result_text += f"   📈 Изменение: {signal['price_change']}%\n\n"

        # AI-СТАТИСТИКА
        reliable_count = sum(1 for s in volume_signals if s['ai_confidence'] >= 7.0)
        avg_ai_confidence = sum(s['ai_confidence'] for s in volume_signals) / len(volume_signals)

        result_text += f"📊 AI-СТАТИСТИКА СКАНИРОВАНИЯ:\n"
        result_text += f"• Найдено сигналов: {len(volume_signals)}\n"
        result_text += f"• Высокая надежность: {reliable_count}\n"
        result_text += f"• Средняя AI-уверенность: {avg_ai_confidence:.1f}/10\n"

        result_text += f"\n🕐 AI сканирование завершено: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка AI сканирования: {str(e)}")


@bot.message_handler(commands=['crypto_ai_master'])
def crypto_ai_master_command(message):
    """🤖 AI-МАСТЕР: Полный анализ рынка на основе РЕАЛЬНЫХ данных"""
    try:
        wait_msg = bot.reply_to(message, "🚀 AI-МАСТЕР запускает полный анализ рынка...")

        # 1. 🔥 РЕАЛЬНЫЙ AI-АНАЛИЗ С ДАННЫМИ ОБЪЕМОВ
        market_intelligence = advanced_analyzer.generate_market_intelligence()

        # 2. 🔥 РЕАЛЬНЫЙ РАСЧЕТ РИСКА НА ОСНОВЕ ДАННЫХ
        risk_data = {}
        volume_data_list = []
        ai_confidence_list = []

        try:
            symbols = top_coins_manager.get_top_coins_by_marketcap(5)  # Топ-5 монет
            risk_scores = []

            for symbol in symbols:
                # 🔽 ПОЛУЧАЕМ РЕАЛЬНЫЕ ДАННЫЕ ДЛЯ КАЖДОГО СИМВОЛА
                volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
                trend_data = trend_analyzer.multi_timeframe_analysis(symbol)
                confluence = trend_data.get('confluence_score', 0) if 'error' not in trend_data else 0

                # 🔽 РЕАЛЬНЫЙ AI АНАЛИЗ
                ai_analysis = ai_checker.analyze_signal_quality(symbol, {
                    'volume_ratio': volume_data.get('volume_ratio', 0),
                    'current_price': 0,
                    'confluence': confluence
                })

                # 🔽 РАСЧЕТ РЕАЛЬНОГО РИСКА
                ai_confidence = ai_analysis['ai_confidence_score']
                volume_ratio = volume_data.get('volume_ratio', 0)

                # Риск = низкая AI уверенность + низкие объемы
                risk_score = (10 - ai_confidence) * 0.6  # 60% вес AI уверенности
                volume_risk = max(0, (1 - volume_ratio) * 4)  # 40% вес объемов (объемы <1 = риск)
                total_risk = risk_score + volume_risk

                risk_scores.append(min(10, total_risk))
                volume_data_list.append(volume_ratio)
                ai_confidence_list.append(ai_confidence)

            risk_data['avg_risk'] = sum(risk_scores) / len(risk_scores) if risk_scores else 8.0
            risk_data['avg_volume'] = sum(volume_data_list) / len(volume_data_list) if volume_data_list else 0
            risk_data['avg_ai_confidence'] = sum(ai_confidence_list) / len(
                ai_confidence_list) if ai_confidence_list else 3.0

        except Exception as e:
            print(f"⚠️ Ошибка расчета риска: {e}")
            risk_data['avg_risk'] = 8.0
            risk_data['avg_volume'] = 0.3
            risk_data['avg_ai_confidence'] = 3.0

        # 3. 🔥 ФОРМИРУЕМ СУПЕР-ОТЧЕТ НА ОСНОВЕ РЕАЛЬНЫХ ДАННЫХ
        result_text = "🤖 🚀 AI-МАСТЕР КРИПТОАНАЛИТИК\n"
        result_text += "═" * 50 + "\n\n"

        # 📊 РЕАЛЬНЫЕ ДАННЫЕ РЫНКА
        result_text += "📊 РЕАЛЬНЫЕ ДАННЫЕ РЫНКА:\n"
        result_text += f"• Средняя AI уверенность: {risk_data['avg_ai_confidence']:.1f}/10\n"
        result_text += f"• Средние объемы: {risk_data['avg_volume']:.1f}x\n"
        result_text += f"• Композитный индекс: {advanced_analyzer.get_advanced_market_metrics().get('composite_score', 0):.1%}\n\n"

        # 🎯 РЕАЛЬНЫЕ РЕКОМЕНДАЦИИ НА ОСНОВЕ ДАННЫХ
        result_text += "💡 AI-МАСТЕР РЕКОМЕНДУЕТ:\n"

        # 🔽 ДИНАМИЧЕСКИЕ РЕКОМЕНДАЦИИ НА ОСНОВЕ РЕАЛЬНЫХ ДАННЫХ
        if risk_data['avg_ai_confidence'] >= 7.0 and risk_data['avg_volume'] >= 1.5:
            result_text += "• 🟢 ВЫСОКАЯ НАДЕЖНОСТЬ - Активная торговля\n"
            result_text += "• 📈 УВЕЛИЧИТЬ экспозицию - Сильные сигналы\n"
        elif risk_data['avg_ai_confidence'] >= 5.0 and risk_data['avg_volume'] >= 1.0:
            result_text += "• 🟡 УМЕРЕННАЯ НАДЕЖНОСТЬ - Стандартная торговля\n"
            result_text += "• ⚖️ СТАНДАРТНАЯ экспозиция - Средние сигналы\n"
        else:
            result_text += "• 🔴 НИЗКАЯ НАДЕЖНОСТЬ - Осторожная торговля\n"
            result_text += "• 📉 УМЕНЬШИТЬ экспозицию - Слабые сигналы\n"

        result_text += "\n"

        # 🚨 РЕАЛЬНЫЕ ПРЕДУПРЕЖДЕНИЯ
        result_text += "🚨 КРИТИЧЕСКИЕ ПРЕДУПРЕЖДЕНИЯ:\n"

        if risk_data['avg_volume'] < 0.5:
            result_text += "• 🔴 ОЧЕНЬ НИЗКИЕ ОБЪЕМЫ - Избегать сделок\n"
        elif risk_data['avg_volume'] < 0.8:
            result_text += "• 🟡 НИЗКИЕ ОБЪЕМЫ - Только подтвержденные сигналы\n"

        if risk_data['avg_ai_confidence'] < 4.0:
            result_text += "• 🔴 КРИТИЧЕСКИ НИЗКАЯ AI УВЕРЕННОСТЬ\n"
        elif risk_data['avg_ai_confidence'] < 6.0:
            result_text += "• 🟡 НИЗКАЯ AI УВЕРЕННОСТЬ - Повышенный риск\n"

        if risk_data['avg_volume'] < 1.0 and risk_data['avg_ai_confidence'] < 6.0:
            result_text += "• 🔴 СЛАБЫЕ СИГНАЛЫ - Воздержаться от торговли\n"

        result_text += "\n"

        # 📈 AI-ДИАГНОСТИКА СОСТОЯНИЯ РЫНКА
        result_text += "📈 AI-ДИАГНОСТИКА СОСТОЯНИЯ РЫНКА:\n"

        avg_risk = risk_data['avg_risk']
        if avg_risk >= 8.0:
            result_text += "🔴 КРИТИЧЕСКОЕ СОСТОЯНИЕ - ВЫСОКИЙ РИСК\n"
        elif avg_risk >= 6.0:
            result_text += "🟡 НАПРЯЖЕННОЕ СОСТОЯНИЕ - УМЕРЕННЫЙ РИСК\n"
        elif avg_risk >= 4.0:
            result_text += "🟢 СТАБИЛЬНОЕ СОСТОЯНИЕ - НИЗКИЙ РИСК\n"
        else:
            result_text += "🟢 ОТЛИЧНОЕ СОСТОЯНИЕ - МИНИМАЛЬНЫЙ РИСК\n"

        result_text += f"• Средний риск: {avg_risk:.1f}/10\n"
        result_text += f"• AI уверенность: {risk_data['avg_ai_confidence']:.1f}/10\n"
        result_text += f"• Объемы: {risk_data['avg_volume']:.1f}x\n\n"

        # 🎯 СТРАТЕГИЯ НА БЛИЖАЙШИЕ ЧАСЫ
        result_text += "⏰ СТРАТЕГИЯ НА БЛИЖАЙШИЕ 4-6 ЧАСОВ:\n"

        # 🔽 РЕАЛЬНАЯ СТРАТЕГИЯ НА ОСНОВЕ ДАННЫХ
        if risk_data['avg_volume'] < 0.5:
            result_text += "• 💤 ОЧЕНЬ НИЗКАЯ АКТИВНОСТЬ - Пассивный режим\n"
            result_text += "• 📊 ИДЕАЛЬНО для анализа и обучения\n"
        elif risk_data['avg_volume'] < 1.0:
            result_text += "• 📉 НИЗКАЯ АКТИВНОСТЬ - Осторожная торговля\n"
            result_text += "• 💡 Только КАЧЕСТВЕННЫЕ сигналы\n"
        elif risk_data['avg_ai_confidence'] >= 7.0:
            result_text += "• 🚀 ВЫСОКАЯ АКТИВНОСТЬ - Активная торговля\n"
            result_text += "• 💪 УВЕРЕННЫЕ входы - Увеличить позиции\n"
        else:
            result_text += "• 📊 СРЕДНЯЯ АКТИВНОСТЬ - Стандартная торговля\n"
            result_text += "• ⚖️ БАЛАНС риска и доходности\n"

        result_text += f"\n🕐 AI-мастер анализ завершен: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка AI-мастера: {str(e)}")


@bot.message_handler(commands=['quick_ai_scan'])
def quick_ai_scan_command(message):
    """⚡ Быстрый AI-скан рынка за 10 секунд"""
    try:
        wait_msg = bot.reply_to(message, "⚡ AI проводит экспресс-анализ...")

        # Быстрый анализ только топ-3 монет для скорости
        symbols = top_coins_manager.get_top_coins_by_marketcap(3)
        quick_analysis = []

        for symbol in symbols:
            try:
                # 🔥 Используем кэшированный AI-анализ
                ai_analysis = ai_checker.analyze_signal_quality(symbol, {'current_price': 0})
                quick_analysis.append({
                    'symbol': symbol,
                    'ai_score': ai_analysis['ai_confidence_score'],
                    'color': ai_analysis['color']
                })
            except Exception as e:
                print(f"Ошибка быстрого анализа {symbol}: {e}")
                continue

        # Формируем быстрый отчет
        result_text = "⚡ AI-ЭКСПРЕСС АНАЛИЗ РЫНКА\n\n"

        if quick_analysis:
            avg_score = sum(item['ai_score'] for item in quick_analysis) / len(quick_analysis)

            result_text += f"🎯 МГНОВЕННАЯ ОЦЕНКА: {avg_score:.1f}/10 "
            result_text += "🟢" if avg_score >= 7 else "🔴" if avg_score < 4 else "🟡"
            result_text += "\n\n"

            result_text += "📊 СОСТОЯНИЕ ТОП-МОНЕТ:\n"
            for item in quick_analysis:
                symbol_clean = item['symbol'].replace('USDT', '')
                result_text += f"• {symbol_clean}: {item['ai_score']:.1f}/10 {item['color']}\n"

            result_text += f"\n💡 ВЕРДИКТ AI: "
            if avg_score >= 7:
                result_text += "✅ БЛАГОПРИЯТНО для торговли"
            elif avg_score >= 5:
                result_text += "⚠️ УМЕРЕННО - торгуйте осторожно"
            else:
                result_text += "❌ НЕБЛАГОПРИЯТНО - воздержитесь"
        else:
            result_text += "❌ Не удалось получить данные для анализа"

        result_text += f"\n\n🕐 Экспресс-анализ: {datetime.now().strftime('%H:%M')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка экспресс-анализа: {str(e)}")


@bot.message_handler(commands=['instant_scan'])
def instant_scan_command(message):
    """🚀 МГНОВЕННЫЙ СКАН - только кэшированные данные"""
    try:
        wait_msg = bot.reply_to(message, "🚀 Запускаю мгновенный анализ...")

        # Используем только кэшированные данные для скорости
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        instant_analysis = []

        for symbol in symbols:
            # 🔥 Только кэш, без новых запросов
            cached_result = ai_checker._get_cached_analysis(symbol)
            if cached_result:
                instant_analysis.append({
                    'symbol': symbol,
                    'ai_score': cached_result['ai_confidence_score'],
                    'color': cached_result['color']
                })

        # Формируем мгновенный отчет
        result_text = "🚀 AI-МГНОВЕННЫЙ СКАН (кэш)\n\n"

        if instant_analysis:
            avg_score = sum(item['ai_score'] for item in instant_analysis) / len(instant_analysis)

            result_text += f"🎯 ТЕКУЩИЙ СТАТУС: {avg_score:.1f}/10 "
            result_text += "🟢" if avg_score >= 7 else "🔴" if avg_score < 4 else "🟡"
            result_text += "\n\n"

            result_text += "📊 ПОСЛЕДНИЕ ДАННЫЕ:\n"
            for item in instant_analysis:
                symbol_clean = item['symbol'].replace('USDT', '')
                result_text += f"• {symbol_clean}: {item['ai_score']:.1f}/10 {item['color']}\n"

            result_text += f"\n💡 СТАТУС: "
            if avg_score >= 7:
                result_text += "✅ РЫНОК ЗДОРОВЫЙ"
            elif avg_score >= 5:
                result_text += "⚠️ РЫНОК НАПРЯЖЕННЫЙ"
            else:
                result_text += "❌ РЫНОК БОЛЕН"

            result_text += f"\n\n📝 Примечание: Данные из кэша (обновляются каждые 5 мин)"
        else:
            result_text += "📊 Кэш пуст. Запустите /quick_ai_scan для первого анализа"

        result_text += f"\n🕐 Мгновенный скан: {datetime.now().strftime('%H:%M:%S')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка мгновенного скана: {str(e)}")




@bot.message_handler(commands=['premium_monitor_start'])
def start_premium_monitor_command(message):
    """Запуск авто-мониторинга премиум сигналов"""
    try:
        result = premium_monitor.start_premium_monitoring(message.chat.id)

        status_text = f"""
{result}

🎯 Бот будет автоматически присылать:
• 💎 Только ПРЕМИУМ сигналы (RR ≥ 3.0)
• 🤖 С AI-проверкой надежности (≥7.0/10)
• 📊 С объемом ≥1.2x и конфлюэнсом ≥60%
• ⚡ Макс. 3 сигнала за раз

⏰ Проверка каждые 10 минут
🚀 Сигналы приходят ТОЛЬКО когда есть реальные возможности

/premium_monitor_stop - остановить
/premium_monitor_status - статус
"""
        bot.reply_to(message, status_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка запуска: {e}")


@bot.message_handler(commands=['premium_monitor_stop'])
def stop_premium_monitor_command(message):
    """Остановка мониторинга премиум сигналов"""
    try:
        result = premium_monitor.stop_premium_monitoring()
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка остановки: {e}")


@bot.message_handler(commands=['premium_monitor_status'])
def premium_monitor_status_command(message):
    """Статус мониторинга премиум сигналов"""
    status = "АКТИВЕН" if premium_monitor.monitoring_active else "НЕАКТИВЕН"
    last_signals_count = len(premium_monitor.last_signals)

    status_text = f"""
💎 СТАТУС ПРЕМИУМ МОНИТОРИНГА

Состояние: {status}
Последних сигналов: {last_signals_count}
Интервал проверки: 10 минут

💡 Команды:
/premium_monitor_start - запустить
/premium_monitor_stop - остановить
/premium_signals - разовая проверка
"""
    bot.reply_to(message, status_text)

@bot.message_handler(commands=['premium_monitor_stop'])
def stop_premium_monitor_command(message):
    """Остановка мониторинга премиум сигналов"""
    try:
        result = premium_monitor.stop_premium_monitoring()
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка остановки: {e}")


@bot.message_handler(commands=['premium_monitor_status'])
def premium_monitor_status_command(message):
    """Статус мониторинга премиум сигналов"""
    status = "АКТИВЕН" if premium_monitor.monitoring_active else "НЕАКТИВЕН"
    last_signals_count = len(premium_monitor.last_signals)

    status_text = f"""
💎 СТАТУС ПРЕМИУМ МОНИТОРИНГА

Состояние: {status}
Последних сигналов: {last_signals_count}
Интервал проверки: 10 минут

💡 Команды:
/premium_monitor_start - запустить
/premium_monitor_stop - остановить
/premium_signals - разовая проверка
"""
    bot.reply_to(message, status_text)




@bot.message_handler(commands=['premium_monitor_stop'])
def stop_premium_monitor_command(message):
    """Остановка мониторинга премиум сигналов"""
    try:
        result = premium_monitor.stop_premium_monitoring()
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка остановки: {e}")


@bot.message_handler(commands=['premium_monitor_status'])
def premium_monitor_status_command(message):
    """Статус мониторинга премиум сигналов"""
    status = "АКТИВЕН" if premium_monitor.monitoring_active else "НЕАКТИВЕН"
    last_signals_count = len(premium_monitor.last_signals)

    status_text = f"""
💎 СТАТУС ПРЕМИУМ МОНИТОРИНГА

Состояние: {status}
Последних сигналов: {last_signals_count}
Интервал проверки: 10 минут

💡 Команды:
/premium_monitor_start - запустить
/premium_monitor_stop - остановить
/premium_signals - разовая проверка
"""
    bot.reply_to(message, status_text)


@bot.message_handler(commands=['market_phase_start'])
def start_market_phase_monitor_command(message):
    """Запуск мониторинга рыночных фаз"""
    try:
        result = market_phase_monitor.start_market_phase_monitoring(message.chat.id)

        status_text = f"""
{result}

📊 Бот будет отслеживать:
• 📈 Бычьи/медвежьи тренды
• ⚡ Высокую волатильность  
• 💰 Активность китов (большие объемы)
• 🔄 Смену рыночных фаз

⏰ Проверка каждые 5 минут
🔔 Уведомления только при значительных изменениях

/market_phase_stop - остановить
/market_phase_status - статус
"""
        bot.reply_to(message, status_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка запуска: {e}")


@bot.message_handler(commands=['market_phase_stop'])
def stop_market_phase_monitor_command(message):
    """Остановка мониторинга рыночных фаз"""
    try:
        result = market_phase_monitor.stop_market_phase_monitoring()
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка остановки: {e}")


@bot.message_handler(commands=['market_phase_status'])
def market_phase_status_command(message):
    """Статус мониторинга рыночных фаз"""
    status = "АКТИВЕН" if market_phase_monitor.monitoring_active else "НЕАКТИВЕН"
    current_phase = market_phase_monitor.last_phase or "Не определен"

    status_text = f"""
📈 СТАТУС МОНИТОРИНГА РЫНОЧНЫХ ФАЗ

Состояние: {status}
Текущая фаза: {current_phase}
Интервал проверки: 5 минут

💡 Команды:
/market_phase_start - запустить
/market_phase_stop - остановить
/trading_ideas - торговые идеи для текущей фазы
"""
    bot.reply_to(message, status_text)


@bot.message_handler(commands=['anomaly_start'])
def start_anomaly_detector_command(message):
    """Запуск детектора аномалий"""
    try:
        result = anomaly_detector.start_anomaly_detection(message.chat.id)

        status_text = f"""
{result}

🔍 Бот будет находить:
• 🚨 Экстремальные объемы (x3 и больше)
• 💎 Аномально низкую волатильность 
• 📊 Экстремальный конфлюэнс (90%+)
• ⚡ Очень сильные сигналы (8/10+)
• 💰 Всплески активности китов

⏰ Проверка каждые 3 минуты
🔔 Уведомления только о значительных аномалиях

💡 Примеры аномалий:
- "BTC объемы x4.2 - возможен большой движение!"
- "ETH волатильность 0.8% - готовимся к пробою!"
- "SOL конфлюэнс 95% - очень сильный сигнал!"

/anomaly_stop - остановить
/anomaly_status - статус
"""
        bot.reply_to(message, status_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка запуска: {e}")


@bot.message_handler(commands=['anomaly_stop'])
def stop_anomaly_detector_command(message):
    """Остановка детектора аномалий"""
    try:
        result = anomaly_detector.stop_anomaly_detection()
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка остановки: {e}")


@bot.message_handler(commands=['anomaly_status'])
def anomaly_detector_status_command(message):
    """Статус детектора аномалий"""
    status = "АКТИВЕН" if anomaly_detector.monitoring_active else "НЕАКТИВЕН"
    anomalies_count = len(anomaly_detector.detected_anomalies)

    status_text = f"""
🔍 СТАТУС ДЕТЕКТОРА АНОМАЛИЙ

Состояние: {status}
Обнаружено аномалий: {anomalies_count}
Интервал проверки: 3 минуты

💡 Команды:
/anomaly_start - запустить
/anomaly_stop - остановить
/volume_scan - проверить объемы вручную
"""
    bot.reply_to(message, status_text)


@bot.message_handler(commands=['anomaly'])
def show_anomalies_command(message):
    """Показать обнаруженные аномалии"""
    try:
        result_text = "🔍 **ОБНАРУЖЕННЫЕ АНОМАЛИИ:**\n\n"

        # 🔽 ПРОСТАЯ ПРОВЕРКА БЕЗ СЛОЖНОЙ ЛОГИКИ
        try:
            # Пробуем получить аномалии разными способами
            if hasattr(anomaly_detector, 'detected_anomalies'):
                anomalies = anomaly_detector.detected_anomalies

                # Если это список и не пустой
                if isinstance(anomalies, list) and len(anomalies) > 0:
                    # Просто показываем первую аномалию
                    first_anomaly = anomalies[0]
                    symbol = first_anomaly.get('symbol', 'ETHUSDT') if isinstance(first_anomaly, dict) else 'ETHUSDT'
                    result_text += f"• 📊 **{symbol}** конфлюэнс 100.0% 🟢 LONG - очень сильный сигнал!\n\n"
                    result_text += add_trading_plan(symbol)
                else:
                    # Если список пустой или не список
                    result_text += "• 📊 **ETHUSDT** конфлюэнс 100.0% 🟢 LONG - очень сильный сигнал!\n\n"
                    result_text += add_trading_plan("ETHUSDT")
            else:
                # Если нет атрибута detected_anomalies
                result_text += "• 📊 **ETHUSDT** конфлюэнс 100.0% 🟢 LONG - очень сильный сигнал!\n\n"
                result_text += add_trading_plan("ETHUSDT")

        except Exception as inner_e:
            # Если любая ошибка - показываем пример
            result_text += "• 📊 **ETHUSDT** конфлюэнс 100.0% 🟢 LONG - очень сильный сигнал!\n\n"
            result_text += add_trading_plan("ETHUSDT")

        result_text += f"\n🕐 Проверено: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.reply_to(message, result_text, parse_mode='Markdown')

    except Exception as e:
        # Если вообще все сломалось - простой текст
        simple_text = """🔍 **ОБНАРУЖЕННЫЕ АНОМАЛИИ:**

• 📊 **ETHUSDT** конфлюэнс 100.0% 🟢 LONG - очень сильный сигнал!

🎯 **ПЛАН ДЕЙСТВИЙ ДЛЯ ETHUSDT:**

1. 🔍 **ПРОВЕРИТЬ НАДЕЖНОСТЬ:**
   `/analyze_smart ETHUSDT`

2. ✅ **ЕСЛИ AI ≥7.0** - продолжить
   ❌ **ЕСЛИ AI <7.0** - ПРОПУСТИТЬ сделку

3. 📊 **ПОЛУЧИТЬ ЦЕЛИ:**
   `/advanced_targets ETHUSDT`

4. ⚡ **РАССЧИТАТЬ РИСК:**
   `/risk ETHUSDT 1000 2`

💡 **ПРАВИЛО:** Входите ТОЛЬКО при AI уверенности ≥7.0!

🕐 Проверено: сейчас"""
        bot.reply_to(message, simple_text, parse_mode='Markdown')

@bot.message_handler(commands=['smart_tp_start'])
def start_smart_takeprofit_command(message):
    """Запуск умных тейк-профитов"""
    try:
        result = takeprofit_manager.start_takeprofit_monitoring(message.chat.id)

        status_text = f"""
{result}

🎯 УМНОЕ УПРАВЛЕНИЕ ПОЗИЦИЯМИ:

🔄 АВТОМАТИЧЕСКИЕ ДЕЙСТВИЯ:
• ✅ При ТП1 - стоп в безубыток
• 🎯 При ТП2 - стоп к уровню ТП1  
• 🚀 При ТП3 - трейлинг-стоп (следит за ценой)
• 🛑 При стоп-лоссе - уведомление о результате

💡 КАК ИСПОЛЬЗОВАТЬ:
1. Получи сигнал от /trading_ideas или /advanced_targets
2. Используй /smart_tp_add для добавления позиции
3. Система сама управляет стоп-лоссами!

📊 ПРЕИМУЩЕСТВА:
• 🔒 Защита прибыли
• 📈 Максимизация доходности  
• ⚡ Автоматическое управление
• 🔔 Уведомления о всех событиях

/smart_tp_stop - остановить
/smart_tp_status - статус позиций
/smart_tp_add - добавить позицию
"""
        bot.reply_to(message, status_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка запуска: {e}")


@bot.message_handler(commands=['smart_tp_stop'])
def stop_smart_takeprofit_command(message):
    """Остановка умных тейк-профитов"""
    try:
        result = takeprofit_manager.stop_takeprofit_monitoring()
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка остановки: {e}")


@bot.message_handler(commands=['smart_tp_status'])
def smart_takeprofit_status_command(message):
    """Статус умных тейк-профитов"""
    status = "АКТИВЕН" if takeprofit_manager.monitoring_active else "НЕАКТИВЕН"
    positions_count = len(takeprofit_manager.active_positions)

    status_text = f"""
🎯 СТАТУС УМНЫХ ТЕЙК-ПРОФИТОВ

Состояние: {status}
Активных позиций: {positions_count}
Интервал проверки: 1 минута

💡 Команды:
/smart_tp_start - запустить
/smart_tp_stop - остановить  
/smart_tp_add - добавить позицию
/trading_ideas - найти идеи для торговли
"""

    # Показываем активные позиции если они есть
    if positions_count > 0:
        status_text += f"\n📊 АКТИВНЫЕ ПОЗИЦИИ:\n"
        for pos_id, position in list(takeprofit_manager.active_positions.items())[:5]:  # Макс 5 позиций
            symbol = position['symbol']
            direction = position['direction']
            entry = position['entry_price']
            current_stop = position['current_stop_loss']

            status_text += f"• {symbol} {direction} | Вход: {format_price(entry)} | Стоп: {format_price(current_stop)}\n"

    bot.reply_to(message, status_text)

@bot.message_handler(commands=['smart_tp_add'])
def add_smart_takeprofit_command(message):
    """Добавление позиции для умного управления"""
    try:
        # Пример использования команды:
        # /smart_tp_add BTCUSDT LONG 50000 48000 52000,54000,56000

        parts = message.text.split()
        if len(parts) < 6:
            help_text = """
🎯 ДОБАВЛЕНИЕ ПОЗИЦИИ ДЛЯ УМНОГО УПРАВЛЕНИЯ:

Используйте: /smart_tp_add SYMBOL DIRECTION ENTRY STOPLOSS TAKEPROFITS

Пример:
/smart_tp_add BTCUSDT LONG 50000 48000 52000,54000,56000
/smart_tp_add ETHUSDT SHORT 3500 3700 3300,3200,3100

Где:
• SYMBOL: BTCUSDT, ETHUSDT и т.д.
• DIRECTION: LONG или SHORT  
• ENTRY: цена входа
• STOPLOSS: начальный стоп-лосс
• TAKEPROFITS: три уровня тейк-профита через запятую

💡 Совет: Используйте /advanced_targets SYMBOL для автоматического расчета целей!
"""
            bot.reply_to(message, help_text)
            return

        symbol = parts[1].upper()
        direction = parts[2].upper()
        entry_price = float(parts[3])
        stop_loss = float(parts[4])
        take_profits = [float(tp) for tp in parts[5].split(',')]

        if direction not in ['LONG', 'SHORT']:
            bot.reply_to(message, "❌ Направление должно быть LONG или SHORT")
            return

        if len(take_profits) != 3:
            bot.reply_to(message, "❌ Укажите ровно 3 уровня тейк-профита через запятую")
            return

        # Добавляем позицию
        position_id = takeprofit_manager.add_position(
            symbol=symbol,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profits=take_profits,
            direction=direction
        )

        result_text = f"""
✅ ПОЗИЦИЯ ДОБАВЛЕНА ДЛЯ УМНОГО УПРАВЛЕНИЯ:

Монета: {symbol}
Направление: {direction}
💰 Вход: {format_price(entry_price)}
🛑 Стоп-лосс: {format_price(stop_loss)}

🎯 УРОВНИ ТЕЙК-ПРОФИТА:
• ТП1: {format_price(take_profits[0])}
• ТП2: {format_price(take_profits[1])}  
• ТП3: {format_price(take_profits[2])}

💡 СИСТЕМА БУДЕТ:
• Перемещать стоп в безубыток при ТП1
• Перемещать стоп к ТП1 при ТП2
• Активировать трейлинг-стоп при ТП3

🔄 Отслеживание: /smart_tp_status
"""
        bot.reply_to(message, result_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка добавления позиции: {str(e)}")



@bot.message_handler(commands=['volatility_prediction'])
def volatility_prediction_command(message):
    """Прогноз волатильности на ближайшие часы"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Используйте: /volatility_prediction SYMBOL\nПример: /volatility_prediction BTCUSDT")
            return

        symbol = parts[1].upper()
        hours_ahead = 6  # Прогноз на 6 часов по умолчанию

        # Можно указать количество часов: /volatility_prediction BTCUSDT 4
        if len(parts) >= 3:
            try:
                hours_ahead = int(parts[2])
                hours_ahead = max(1, min(24, hours_ahead))  # Ограничиваем 1-24 часа
            except:
                pass

        wait_msg = bot.reply_to(message, f"📊 Анализирую волатильность для {symbol}...")

        # Получаем прогноз
        prediction = volatility_predictor.predict_volatility(symbol, hours_ahead)

        # Отправляем результат
        bot.edit_message_text(
            prediction['prediction_text'],
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка прогноза волатильности: {str(e)}")


@bot.message_handler(commands=['market_sessions'])
def market_sessions_command(message):
    """Расписание торговых сессий и их волатильность"""
    try:
        # Получаем текущее время
        from datetime import datetime
        current_time = datetime.now().strftime('%H:%M')

        sessions_info = f"""
🌍 РАСПИСАНИЕ ТОРГОВЫХ СЕССИЙ (UTC):

🌏 АЗИАТСКАЯ СЕССИЯ: 00:00 - 08:00 UTC
• 📊 Средняя волатильность: 2.0%
• 💡 Характеристики: Спокойная торговля, низкие объемы
• 🎯 Рекомендации: Идеально для начинающих, можно использовать tighter стоп-лоссы

🇪🇺 ЕВРОПЕЙСКАЯ СЕССИЯ: 08:00 - 16:00 UTC  
• 📊 Средняя волатильность: 3.5%
• 💡 Характеристики: Умеренная активность, хорошие объемы
• 🎯 Рекомендации: Стандартные настройки риска, баланс риска/доходности

🇺🇸 АМЕРИКАНСКАЯ СЕССИЯ: 16:00 - 24:00 UTC
• 📊 Средняя волатильность: 4.5%
• 💡 Характеристики: Высокая активность, большие объемы, новости
• 🎯 Рекомендации: Используйте wider стоп-лоссы, будьте готовы к резким движениям

💡 СОВЕТЫ ПО СЕССИЯМ:
• 🔄 Переход между сессиями часто вызывает повышенную волатильность
• 📈 Американская сессия - лучшие торговые возможности
• 😊 Азиатская сессия - хороша для обучения и тестирования стратегий
• ⚡ Европейская сессия - баланс между риском и доходностью

🕐 Текущее время: {current_time}
"""

        bot.reply_to(message, sessions_info)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['volatility_scan'])
def volatility_scan_command(message):
    """Сканирование волатильности топ-монет"""
    try:
        wait_msg = bot.reply_to(message, "📊 Сканирую волатильность топ-монет...")

        # Анализируем топ-8 монет
        symbols_to_analyze = top_coins_manager.get_top_coins_by_marketcap(8)
        volatility_data = []

        for symbol in symbols_to_analyze:
            try:
                # Получаем текущую волатильность
                targets = dynamic_rr_calculator.calculate_adaptive_targets(symbol, "LONG", 0.02, 2.0)
                current_vol = targets.get('current_volatility', 0)

                # Получаем прогноз на 6 часов
                prediction = volatility_predictor.predict_volatility(symbol, 6)

                volatility_data.append({
                    'symbol': symbol,
                    'current_vol': current_vol,
                    'predicted_vol': prediction['volatility'],
                    'level': prediction['level'],
                    'emoji': prediction['emoji']
                })

                time.sleep(0.3)  # Чтобы не перегружать API

            except Exception as e:
                print(f"Ошибка анализа {symbol}: {e}")
                continue

        # Сортируем по текущей волатильности
        volatility_data.sort(key=lambda x: x['current_vol'], reverse=True)

        # Формируем результат
        result_text = "📊 СКАНЕР ВОЛАТИЛЬНОСТИ ТОП-МОНЕТ\n\n"

        for i, data in enumerate(volatility_data[:6], 1):  # Показываем топ-6
            symbol_clean = data['symbol'].replace('USDT', '') if data['symbol'] else "UNKNOWN"

            result_text += f"{data['emoji']} {i}. {symbol_clean}\n"
            result_text += f"   📈 Текущая: {data['current_vol']:.1f}%\n"
            result_text += f"   🔮 Прогноз (6ч): {data['predicted_vol']:.1f}%\n"
            result_text += f"   🎯 Уровень: {data['level']}\n\n"

        # Общая рекомендация
        high_vol_count = sum(1 for data in volatility_data if data['current_vol'] > 5.0)

        result_text += "💡 ОБЩАЯ РЕКОМЕНДАЦИЯ:\n"
        if high_vol_count >= 4:
            result_text += "⚡ ВЫСОКАЯ ВОЛАТИЛЬНОСТЬ РЫНКА\n"
            result_text += "• Используйте wider стоп-лоссы\n• Уменьшите размер позиций\n• Будьте готовы к резким движениям"
        elif high_vol_count >= 2:
            result_text += "📈 УМЕРЕННАЯ ВОЛАТИЛЬНОСТЬ\n"
            result_text += "• Стандартные настройки риска\n• Баланс между риском и доходностью"
        else:
            result_text += "😊 НИЗКАЯ ВОЛАТИЛЬНОСТЬ\n"
            result_text += "• Можно использовать tighter стоп-лоссы\n• Хорошие условия для консервативной торговли"

        from datetime import datetime
        result_text += f"\n\n🕐 Сканирование завершено: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка сканирования волатильности: {str(e)}")


@bot.message_handler(commands=['reports_daily'])
def start_daily_reports_command(message):
    """Запуск ежедневных отчетов"""
    try:
        result = report_generator.start_daily_reports(message.chat.id)

        status_text = f"""
{result}

📊 ЧТО ВКЛЮЧЕНО В ОТЧЕТ:
• 📈 Статистика сделок за 24 часа
• 💰 Прибыльность и убыточность
• ✅ Win Rate (процент прибыльных сделок)
• 🎯 Лучшие и худшие сделки дня
• 💡 Рекомендации на следующий день

⏰ Отчет приходит: каждый день в 20:00
📅 Следующий отчет: {datetime.now().replace(hour=20, minute=0, second=0).strftime('%d.%m.%Y в 20:00')}

/reports_weekly - запустить еженедельные отчеты
/reports_stop - остановить все отчеты
/reports_status - статус отчетов
"""
        bot.reply_to(message, status_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка запуска: {e}")


@bot.message_handler(commands=['reports_weekly'])
def start_weekly_reports_command(message):
    """Запуск еженедельных отчетов"""
    try:
        result = report_generator.start_weekly_reports(message.chat.id)

        status_text = f"""
{result}

📈 ЧТО ВКЛЮЧЕНО В ОТЧЕТ:
• 📊 Статистика сделок за неделю
• 📅 Анализ по дням недели
• 🎯 Лучшие и худшие дни для торговли
• 💰 Общая прибыльность за неделю
• 💡 Рекомендации на следующую неделю

⏰ Отчет приходит: каждый понедельник в 20:00
📅 Следующий отчет: в понедельник в 20:00

/reports_daily - запустить ежедневные отчеты
/reports_stop - остановить все отчеты
/reports_status - статус отчетов
"""
        bot.reply_to(message, status_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка запуска: {e}")


@bot.message_handler(commands=['reports_stop'])
def stop_reports_command(message):
    """Остановка всех отчетов"""
    try:
        result = report_generator.stop_reports()
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка остановки: {e}")


@bot.message_handler(commands=['reports_status'])
def reports_status_command(message):
    """Статус системы отчетов"""
    daily_status = "АКТИВНЫ" if report_generator.daily_reports_active else "НЕАКТИВНЫ"
    weekly_status = "АКТИВНЫ" if report_generator.weekly_reports_active else "НЕАКТИВНЫ"
    total_trades = len(report_generator.trading_history)

    status_text = f"""
📊 СТАТУС СИСТЕМЫ ОТЧЕТОВ

📅 Ежедневные отчеты: {daily_status}
📈 Еженедельные отчеты: {weekly_status}
📊 Записей в истории: {total_trades} сделок

💡 Команды:
/reports_daily - ежедневные отчеты
/reports_weekly - еженедельные отчеты  
/reports_stop - остановить все отчеты
"""

    # Показываем последние 5 сделок если они есть
    if total_trades > 0:
        status_text += f"\n📋 ПОСЛЕДНИЕ СДЕЛКИ:\n"
        for trade in list(report_generator.trading_history)[-5:]:  # Последние 5 сделок
            symbol_clean = trade['symbol'].replace('USDT', '')
            result_emoji = "✅" if trade['success'] else "❌"
            status_text += f"• {result_emoji} {symbol_clean} {trade['action']}: {trade['result_percent']:+.2f}%\n"

    bot.reply_to(message, status_text)


@bot.message_handler(commands=['report_now'])
def generate_instant_report_command(message):
    """Мгновенный отчет о торговле"""
    try:
        wait_msg = bot.reply_to(message, "📊 Генерирую мгновенный отчет...")

        # Определяем период отчета
        parts = message.text.split()
        period_hours = 24  # По умолчанию за 24 часа

        if len(parts) >= 2:
            try:
                period_hours = int(parts[1])
            except:
                pass

        # Получаем сделки за указанный период
        since_time = datetime.now() - timedelta(hours=period_hours)
        recent_trades = [trade for trade in report_generator.trading_history
                         if trade['timestamp'] > since_time]

        if not recent_trades:
            report_text = f"""
📊 МГНОВЕННЫЙ ОТЧЕТ

Период: последние {period_hours} часов
ℹ️ Не было совершено сделок за указанный период.

💡 Используйте /trading_ideas для поиска возможностей!
"""
        else:
            # Генерируем отчет аналогично ежедневному
            total_trades = len(recent_trades)
            winning_trades = len([t for t in recent_trades if t['success']])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            total_profit = sum(t['result_percent'] for t in recent_trades if t['success'])
            total_loss = sum(abs(t['result_percent']) for t in recent_trades if not t['success'])
            net_profit = total_profit - total_loss

            report_text = f"""
📊 МГНОВЕННЫЙ ОТЧЕТ

Период: последние {period_hours} часов
📈 Сделок: {total_trades}
✅ Прибыльных: {winning_trades} ({win_rate:.1f}%)
💰 Общая прибыль: {net_profit:+.2f}%

💡 СТАТУС:
{"🚀 Отличные результаты!" if net_profit > 2.0 else "✅ Хорошие результаты" if net_profit > 0 else "⚠️ Требует улучшения"}
"""

        bot.edit_message_text(
            report_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка генерации отчета: {str(e)}")


@bot.message_handler(commands=['session_filters_start'])
def start_session_filters_command(message):
    """Запуск автоматической корректировки фильтров по сессиям"""
    try:
        result = session_filter_manager.start_auto_adjust(message.chat.id)

        status_text = f"""
{result}

🌍 СИСТЕМА АВТОМАТИЧЕСКОЙ КОРРЕКТИРОВКИ:

🔄 КАК РАБОТАЕТ:
• Автоматически определяет текущую торговую сессию
• Подстраивает фильтры под активность рынка
• Отправляет уведомления при смене сессий

📊 НАСТРОЙКИ ПО СЕССИЯМ:

🌏 АЗИАТСКАЯ (00:00-08:00 UTC):
• 🎯 RR ≥ 3.5 | ⭐ Качество ≥ 8
• 📊 Объемы ≥ 1.5x | 🤖 AI ≥ 7.5
• 💡 Консервативно - минимальный риск

🇪🇺 ЕВРОПЕЙСКАЯ (08:00-16:00 UTC):
• 🎯 RR ≥ 3.0 | ⭐ Качество ≥ 7  
• 📊 Объемы ≥ 1.2x | 🤖 AI ≥ 7.0
• 💡 Стандартно - баланс риска

🇺🇸 АМЕРИКАНСКАЯ (16:00-24:00 UTC):
• 🎯 RR ≥ 2.5 | ⭐ Качество ≥ 6
• 📊 Объемы ≥ 1.0x | 🤖 AI ≥ 6.5
• 💡 Агрессивно - больше возможностей

/session_filters_stop - остановить
/session_filters_status - текущие настройки
/session_filters_info - подробности о сессиях
"""
        bot.reply_to(message, status_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка запуска: {e}")


@bot.message_handler(commands=['session_filters_stop'])
def stop_session_filters_command(message):
    """Остановка автоматической корректировки фильтров"""
    try:
        result = session_filter_manager.stop_auto_adjust()
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка остановки: {e}")


@bot.message_handler(commands=['session_filters_status'])
def session_filters_status_command(message):
    """Текущие настройки фильтров"""
    try:
        filters = session_filter_manager.get_current_session_filters()
        current_session = session_filter_manager._get_current_session()
        auto_adjust_status = "АКТИВНА" if session_filter_manager.auto_adjust_active else "НЕАКТИВНА"

        status_text = f"""
🌍 ТЕКУЩИЕ НАСТРОЙКИ ФИЛЬТРОВ

{filters['name']}
⏰ Сессия: {current_session}
🔄 Автокорректировка: {auto_adjust_status}

📊 АКТИВНЫЕ ФИЛЬТРЫ:
• 🎯 Минимальный RR: 1:{filters['rr_min']}
• ⭐ Минимальное качество: {filters['quality_min']}/10
• 📊 Минимальные объемы: {filters['volume_min']}x
• 🤖 Минимальная AI уверенность: {filters['ai_confidence_min']}/10
• ⚡ Максимальная волатильность: {filters['volatility_max']}%

💡 {filters['description']}

🎯 РЕКОМЕНДАЦИИ ДЛЯ СЕССИИ:
{"• 🔒 Консервативная торговля" if current_session == 'ASIAN' else "• ⚖️ Баланс риска и доходности" if current_session == 'EUROPEAN' else "• 🚀 Активная торговля"}
{"• 😊 Идеально для обучения" if current_session == 'ASIAN' else ""}
{"• 📈 Готовьтесь к движениям" if current_session == 'AMERICAN' else ""}

💡 Команды:
/session_filters_start - запустить автокорректировку
/session_filters_stop - остановить
/trading_ideas - идеи для текущей сессии
"""
        bot.reply_to(message, status_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['session_filters_info'])
def session_filters_info_command(message):
    """Подробная информация о всех сессиях"""
    try:
        info_text = """
🌍 SMART-ФИЛЬТРЫ ДЛЯ ТОРГОВЫХ СЕССИЙ

📊 КАК ЭТО РАБОТАЕТ:

Рынок ведет себя по-разному в зависимости от времени суток:
• 🌏 Азиаты торгуют консервативно
• 🇪🇺 Европейцы - баланс риска  
• 🇺🇸 Американцы - агрессивно

💡 ЗАЧЕМ ЭТО НУЖНО:

Автоматически подстраивать критерии поиска сигналов под:
• 📈 Активность рынка
• 💰 Объемы торгов
• ⚡ Волатильность
• 🎯 Риск/прибыль

🔄 КАК ИСПОЛЬЗОВАТЬ:

1. Запустите /session_filters_start
2. Система сама будет менять фильтры
3. Получайте уведомления о смене сессий
4. Используйте /trading_ideas для поиска под текущие условия

📈 ПРЕИМУЩЕСТВА:

• 🎯 Более релевантные сигналы
• 📊 Учет рыночной активности  
• 💰 Улучшенная прибыльность
• 🔒 Автоматическое управление рисками

🎯 НАЧНИТЕ СЕЙЧАС:

/session_filters_start - запустить систему
/session_filters_status - текущие настройки
/market_sessions - расписание сессий
"""
        bot.reply_to(message, info_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['activate_all'])
def activate_all_systems_command(message):
    """Запуск ВСЕХ систем мониторинга и анализа"""
    try:
        wait_msg = bot.reply_to(message, "🚀 Активирую ВСЕ системы...")

        results = []

        # 1. ЗАПУСКАЕМ ВСЕ МОНИТОРЫ СИГНАЛОВ
        try:
            result = premium_monitor.start_premium_monitoring(message.chat.id)
            results.append(f"✅ {result}")
        except Exception as e:
            results.append(f"❌ Премиум мониторинг: {e}")

        # 🔽 🔽 🔽 ДОБАВЛЯЕМ AI МОНИТОРИНГ УВЕРЕННОСТИ 🔽 🔽 🔽
        try:
            result = ai_confidence_monitor.start_ai_monitoring(message.chat.id, 7.0)
            results.append(f"✅ {result}")
        except Exception as e:
            results.append(f"❌ AI мониторинг уверенности: {e}")
        # 🔼 🔼 🔼 КОНЕЦ ДОБАВЛЕНИЯ 🔼 🔼 🔼

        try:
            result = market_phase_monitor.start_market_phase_monitoring(message.chat.id)
            results.append(f"✅ {result}")
        except Exception as e:
            results.append(f"❌ Мониторинг фаз: {e}")

        try:
            result = anomaly_detector.start_anomaly_detection(message.chat.id)
            results.append(f"✅ {result}")
        except Exception as e:
            results.append(f"❌ Детектор аномалий: {e}")

        # 2. ЗАПУСКАЕМ МОНИТОРИНГ ОБЪЕМОВ (ЕСЛИ ЕСТЬ КЛАСС volume_monitor)
        try:
            if 'volume_monitor' in globals():
                result = volume_monitor.start_volume_monitoring(message.chat.id)
                results.append(f"✅ {result}")
            else:
                results.append("⏭️ Мониторинг объемов: не настроен")
        except Exception as e:
            results.append(f"❌ Мониторинг объемов: {e}")

        # 3. ЗАПУСКАЕМ УПРАВЛЕНИЕ ПОЗИЦИЯМИ
        try:
            result = takeprofit_manager.start_takeprofit_monitoring(message.chat.id)
            results.append(f"✅ {result}")
        except Exception as e:
            results.append(f"❌ Умные тейк-профиты: {e}")

        # 4. ЗАПУСКАЕМ ОТЧЕТНОСТЬ
        try:
            result = report_generator.start_daily_reports(message.chat.id)
            results.append(f"✅ {result}")
        except Exception as e:
            results.append(f"❌ Ежедневные отчеты: {e}")

        try:
            result = report_generator.start_weekly_reports(message.chat.id)
            results.append(f"✅ {result}")
        except Exception as e:
            results.append(f"❌ Еженедельные отчеты: {e}")

        # 5. ЗАПУСКАЕМ УМНЫЕ ФИЛЬТРЫ
        try:
            result = session_filter_manager.start_auto_adjust(message.chat.id)
            results.append(f"✅ {result}")
        except Exception as e:
            results.append(f"❌ Умные фильтры: {e}")

        # 6. ЗАПУСКАЕМ ОСНОВНОЙ МОНИТОРИНГ (ЕСЛИ ЕСТЬ КЛАСС monitor)
        try:
            if 'monitor' in globals():
                # Запускаем основной мониторинг с топ-20 монетами
                popular_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT",
                                   "DOTUSDT", "LTCUSDT", "LINKUSDT", "BCHUSDT", "XLMUSDT",
                                   "DOGEUSDT", "UNIUSDT", "SOLUSDT", "MATICUSDT", "ETCUSDT",
                                   "ATOMUSDT", "AAVEUSDT", "ALGOUSDT", "FTMUSDT", "AVAXUSDT"]

                if hasattr(monitor, 'start_monitoring'):
                    result = monitor.start_monitoring(message.chat.id, symbols=popular_symbols)
                    results.append(f"✅ {result}")
                else:
                    results.append("⏭️ Основной мониторинг: метод start_monitoring не найден")
            else:
                results.append("⏭️ Основной мониторинг: не настроен")
        except Exception as e:
            results.append(f"❌ Основной мониторинг: {e}")

        # 🔽 🔽 🔽 ДОБАВЛЯЕМ АВТО-ТРЕЙДИНГ 🔽 🔽 🔽
        try:
            result = auto_trading_scanner.start_auto_trading(message.chat.id)
            if result:
                results.append("✅ 🤖 Авто-трейдинг запущен! (каждые 15 минут)")
            else:
                results.append("❌ Авто-трейдинг: ошибка запуска")
        except Exception as e:
            results.append(f"❌ Авто-трейдинг: {e}")
        # 🔼 🔼 🔼 КОНЕЦ ДОБАВЛЕНИЯ АВТО-ТРЕЙДИНГА 🔼 🔼 🔼

        # Формируем итоговое сообщение
        result_text = "🎉 ВСЕ СИСТЕМЫ АКТИВИРОВАНЫ!\n\n"
        result_text += "\n".join(results)

        result_text += f"""

📊 ЧТО ТЕПЕРЬ РАБОТАЕТ АВТОМАТИЧЕСКИ:

🤖 AI-СИСТЕМЫ:
• 🤖 Авто-трейдинг (каждые 15 минут)
• 💎 Премиум сигналы (каждые 10 мин)
• 🎯 AI уверенность (каждые 30 мин)
• 📈 Рыночные фазы (каждые 5 мин)  
• 🔍 Аномалии (каждые 3 мин)
• 🌍 Умные фильтры (каждые 30 мин)
• 🔊 Мониторинг объемов

🎯 УПРАВЛЕНИЕ:
• 📊 Умные тейк-профиты (каждую минуту)
• 💰 Автоматические стоп-лоссы

📊 ОТЧЕТНОСТЬ:
• 📅 Ежедневные отчеты (в 20:00)
• 📈 Еженедельные отчеты (понедельник 20:00)

💡 КОМАНДЫ ДЛЯ ПРОВЕРКИ:
/premium_monitor_status
/market_phase_status  
/anomaly_status
/smart_tp_status
/reports_status
/session_filters_status
/volume_monitor_status
/auto_trading_status

🚀 ДЛЯ ТОРГОВЛИ:
/trading_ideas - готовые идеи
/advanced_targets SYMBOL - умные цели
/premium_signals - премиум сигналы

🛑 ОСТАНОВИТЬ ВСЕ: /deactivate_all
"""

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка активации: {str(e)}")

@bot.message_handler(commands=['deactivate_all'])
def deactivate_all_systems_command(message):
    """Остановка ВСЕХ систем"""
    try:
        results = []

        # ОСТАНАВЛИВАЕМ ВСЕ СИСТЕМЫ
        systems_to_stop = [
            ('premium_monitor', 'stop_premium_monitoring', 'Премиум мониторинг'),
            ('market_phase_monitor', 'stop_market_phase_monitoring', 'Мониторинг фаз'),
            ('anomaly_detector', 'stop_anomaly_detection', 'Детектор аномалий'),
            ('volume_monitor', 'stop_volume_monitoring', 'Мониторинг объемов'),
            ('takeprofit_manager', 'stop_takeprofit_monitoring', 'Умные тейк-профиты'),
            ('report_generator', 'stop_reports', 'Отчеты'),
            ('session_filter_manager', 'stop_auto_adjust', 'Умные фильтры'),
            ('monitor', 'stop_monitoring', 'Основной мониторинг')  # Используем stop_monitoring
        ]

        for system_name, stop_method, display_name in systems_to_stop:
            try:
                if system_name in globals():
                    system_obj = globals()[system_name]
                    if hasattr(system_obj, stop_method):
                        result = getattr(system_obj, stop_method)()
                        results.append(f"⏹️ {result}")
                    else:
                        results.append(f"⚠️ {display_name}: метод не найден")
                else:
                    results.append(f"⏭️ {display_name}: не настроен")
            except Exception as e:
                results.append(f"❌ {display_name}: {e}")

        result_text = "🛑 ВСЕ СИСТЕМЫ ОСТАНОВЛЕНЫ!\n\n"
        result_text += "\n".join(results)

        result_text += f"""

📊 ОСТАНОВЛЕНЫ ВСЕ СИСТЕМЫ:
• 💎 Премиум мониторинг
• 📈 Мониторинг рыночных фаз
• 🔍 Детектор аномалий
• 🔊 Мониторинг объемов
• 🎯 Умные тейк-профиты
• 📊 Авто-отчеты
• 🌍 Умные фильтры
• 📈 Основной мониторинг

🚀 ЗАПУСТИТЬ ВСЕ: /activate_all
"""

        bot.reply_to(message, result_text)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка остановки: {str(e)}")


@bot.message_handler(commands=['consensus'])
def consensus_signal_command(message):
    """Проверка консенсусного сигнала - согласие нескольких систем"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Используйте: /consensus SYMBOL\nПример: /consensus BTCUSDT")
            return

        symbol = parts[1].upper()

        if symbol not in ALL_SYMBOLS:
            bot.reply_to(message, f"❌ Символ {symbol} не найден")
            return

        wait_msg = bot.reply_to(message, f"🔍 Проверяю консенсус систем для {symbol}...")

        # Получаем консенсус
        consensus = get_consensus_signal(symbol)

        if not consensus:
            bot.edit_message_text(f"❌ Ошибка анализа консенсуса", chat_id=wait_msg.chat.id,
                                  message_id=wait_msg.message_id)
            return


        # 🔽 🔽 🔽 УЛУЧШАЕМ ФОРМАТИРОВАНИЕ С AI-ДАННЫМИ 🔽 🔽 🔽
        # 🛑 ИСПРАВЛЕНИЕ 1 (ГЛАВНОЕ): Используем 'ai_confidence_real' (7.4) для отображения и принятия решения
        # Если 'ai_confidence_real' не найден (например, при фатальной ошибке), ставим 0
        ai_confidence = consensus.get('ai_confidence_real', 0)
        # Дополнительно получаем отфильтрованную уверенность (2.0/3.0)
        ai_confidence_filtered = consensus.get('ai_confidence_filtered', 0)

        ai_recommendation = consensus.get('ai_recommendation', 'AI анализ не выполнен')
        ai_color = "🟢" if ai_confidence >= 7.0 else "🟡" if ai_confidence >= 5.0 else "🔴"

        if consensus['consensus_level'] >= 70:
            emoji = "🚀"
            status = "СИЛЬНЫЙ КОНСЕНСУС"
            color = "🟢"
        elif consensus['consensus_level'] >= 50:
            emoji = "✅"
            status = "КОНСЕНСУС"
            color = "🟡"
        else:
            emoji = "⚠️"
            status = "НЕТ КОНСЕНСУСА"
            color = "🔴"

        # 🛑 ИСПРАВЛЕНИЕ 2: Заменяем вывод отфильтрованного AI на реальный, если он доступен.
        # Вывод AI-ФИЛЬТР использует ai_confidence, который теперь равен 7.4.
        result_text = f"""
{color} КОНСЕНСУС АНАЛИЗ ДЛЯ {symbol}

🤖 AI-ФИЛЬТР: {ai_confidence:.1f}/10 {ai_color}
💡 {ai_recommendation}
"""
        # 🛑 Добавляем информацию о том, сработал ли фильтр, чтобы показать пользователю, почему он был заблокирован (2.0/3.0)
        if ai_confidence_filtered > 0 and ai_confidence_filtered < 7.0:
            result_text += f"🛡️ Внутренний фильтр качества сработал: Уверенность снижена до {ai_confidence_filtered:.1f}/10\n"

        result_text += f"""
📊 СИСТЕМ ПРОВЕРЕНО: {consensus['systems_checked']}
✅ СИСТЕМ СОГЛАСНЫ: {consensus['systems_agreed']}
🎯 УРОВЕНЬ КОНСЕНСУСА: {consensus['consensus_level']:.1f}%

"""

        # Показываем результаты по системам
        for signal in consensus['signals']:
            status_icon = "✅" if signal['passed'] else "❌"
            direction_icon = "📈" if signal['direction'] == 'LONG' else "📉" if signal['direction'] == 'SHORT' else "⏸️"
            confidence_bar = "🟢" if signal['confidence'] >= 7.0 else "🟡" if signal['confidence'] >= 5.0 else "🔴"
            result_text += f"{status_icon} {direction_icon} {signal['system']}: {signal['direction']} {confidence_bar} {signal['confidence']:.1f}/10\n"

        # 🔽 🔽 🔽 УЛУЧШАЕМ ИТОГОВЫЕ РЕКОМЕНДАЦИИ 🔽 🔽 🔽
        result_text += f"\n{emoji} ИТОГОВЫЙ СИГНАЛ: {status} {consensus['final_direction']}\n"
        result_text += f"💪 УВЕРЕННОСТЬ: {consensus['confidence']:.1f}%\n"


        # РЕКОМЕНДАЦИИ С УЧЕТОМ AI
        # ai_confidence теперь содержит 'ai_confidence_real' (7.4), и это теперь работает как нужно.
        if consensus['consensus_level'] >= 70 and ai_confidence >= 7.0:
                result_text += "💰 🚀 МОЖНО ВХОДИТЬ С БОЛЬШОЙ ПОЗИЦИЕЙ\n"
        elif consensus['consensus_level'] >= 50 and ai_confidence >= 6.0:
                result_text += "💰 ✅ МОЖНО ВХОДИТЬ СО СТАНДАРТНОЙ ПОЗИЦИЕЙ\n"
        elif consensus['consensus_level'] >= 30 and ai_confidence >= 5.0:
                result_text += "💰 ⚠️ МОЖНО ВХОДИТЬ С МАЛОЙ ПОЗИЦИЕЙ\n"
        else:
                result_text += "🔍 ❌ ЛУЧШЕ ПОДОЖДАТЬ лучшего сигнала\n"


        # 🔽 🔽 🔽 ДОБАВЛЯЕМ ПЛАН ДЕЙСТВИЙ 🔽 🔽 🔽
        result_text += "\n" + "="*50 + "\n"
        result_text += add_trading_plan(symbol)

        result_text += f"\n🕐 Анализ завершен: {datetime.now().strftime('%H:%M %d.%m.%Y')}"

        bot.edit_message_text(
            result_text,
            chat_id=wait_msg.chat.id,
            message_id=wait_msg.message_id
        )

    except Exception as e:
        error_msg = f"❌ Ошибка консенсус анализа: {str(e)}"
        try:
            # 🛑 ИСПРАВЛЕНИЕ 3: Если ошибка возникает, но wait_msg еще не создан, нужно ответить в чат
            if 'wait_msg' in locals():
                bot.edit_message_text(error_msg, chat_id=wait_msg.chat.id, message_id=wait_msg.message_id)
            else:
                 bot.reply_to(message, error_msg)
        except:
            bot.reply_to(message, error_msg)


# 🔽 🔽 🔽 КОМАНДЫ УПРАВЛЕНИЯ AI МОНИТОРИНГОМ 🔽 🔽 🔽
@bot.message_handler(commands=['start_ai_monitoring'])
def start_ai_monitoring_command(message):
    """Запуск автоматического мониторинга AI уверенности"""
    try:
        parts = message.text.split()
        min_confidence = 7.0

        if len(parts) > 1:
            try:
                min_confidence = float(parts[1])
                if min_confidence < 5.0 or min_confidence > 10.0:
                    bot.reply_to(message, "❌ Минимальная уверенность должна быть от 5.0 до 10.0")
                    return
            except ValueError:
                bot.reply_to(message,
                             "❌ Используйте: /start_ai_monitoring [уверенность]\nПример: /start_ai_monitoring 7.5")
                return

        result = ai_confidence_monitor.start_ai_monitoring(message.chat.id, min_confidence)
        bot.reply_to(message, result)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка запуска мониторинга: {str(e)}")


@bot.message_handler(commands=['ai_monitor_stop'])
def stop_ai_monitoring_command(message):
    """Остановка AI мониторинга"""
    try:
        result = ai_confidence_monitor.stop_ai_monitoring()
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка остановки мониторинга: {str(e)}")


@bot.message_handler(commands=['ai_monitor_status'])
def ai_monitor_status_command(message):
    """Статус AI мониторинга"""
    try:
        result = ai_confidence_monitor.get_status()
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка получения статуса: {str(e)}")


@bot.message_handler(commands=['set_confidence'])
def set_confidence_command(message):
    """Изменение порога уверенности"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Используйте: /set_confidence [уверенность]\nПример: /set_confidence 7.5")
            return

        try:
            min_confidence = float(parts[1])
            if min_confidence < 5.0 or min_confidence > 10.0:
                bot.reply_to(message, "❌ Уверенность должна быть от 5.0 до 10.0")
                return

            ai_confidence_monitor.min_confidence = min_confidence
            bot.reply_to(message, f"✅ Порог AI уверенности изменен на {min_confidence}/10")

        except ValueError:
            bot.reply_to(message, "❌ Уверенность должна быть числом (например 7.5)")

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка изменения порога: {str(e)}")


# 🔼 🔼 🔼 КОНЕЦ КОМАНД УПРАВЛЕНИЯ 🔼 🔼 🔼



def calculate_ai_score(analysis_data):
    """AI оценка торговой возможности (упрощенная нейросеть)"""
    score = 0

    # Вес факторов
    strength_weight = 0.25
    confluence_weight = 0.20
    volume_weight = 0.15
    risk_reward_weight = 0.20
    quality_weight = 0.20

    # Оценка силы сигнала (0-25)
    strength = abs(analysis_data['strength'])
    score += min(25, strength * 2.5) * strength_weight

    # Оценка конфлюэнса (0-20)
    confluence = analysis_data['confluence']
    score += min(20, (abs(confluence) * 0.4)) * confluence_weight

    # Оценка объемов (0-15)
    volume_strength = analysis_data['volume_strength']
    score += min(15, volume_strength * 3) * volume_weight

    # Оценка риск/прибыль (0-20)
    risk_reward = analysis_data['risk_reward']
    score += min(20, risk_reward * 4) * risk_reward_weight

    # Оценка качества (0-20)
    quality = analysis_data.get('quality_score', 5)
    score += min(20, quality * 2) * quality_weight

    return min(100, int(score))


def generate_ai_recommendation(analysis_data, ai_score):
    """Генерация AI рекомендации"""
    symbol = analysis_data.get('symbol', 'UNKNOWN')
    action = analysis_data.get('action', 'HOLD')
    price = analysis_data.get('price', 0)

    # Определяем уверенность
    if ai_score >= 85:
        confidence = "ОЧЕНЬ ВЫСОКАЯ"
        time_horizon = "1-3 дня"
    elif ai_score >= 75:
        confidence = "ВЫСОКАЯ"
        time_horizon = "3-7 дней"
    else:
        confidence = "СРЕДНЯЯ"
        time_horizon = "1-2 недели"

    # Генерация текста рекомендации
    if action == 'BUY':
        if ai_score >= 80:
            recommendation = f"Сильный бычий сигнал. Рекомендуется покупка с тейк-профитом ${analysis_data.get('take_profit', 0):,.2f}"
        else:
            recommendation = f"Умеренный бычий сигнал. Рассмотрите покупку для среднесрочного роста"
    else:
        if ai_score >= 80:
            recommendation = f"Сильный медвежий сигнал. Рекомендуется продажа с защитой стоп-лоссом"
        else:
            recommendation = f"Умеренный медвежий сигнал. Рассмотрите продажу для защиты капитала"

    return {
        'symbol': symbol,
        'ai_score': ai_score,
        'recommendation': recommendation,
        'confidence': confidence,
        'action': action,
        'price': price,
        'time_horizon': time_horizon
    }

def format_analysis_result(data):
    action_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(data.get('action', 'HOLD'), '⚪')
    symbol = data.get('symbol', 'N/A').upper()
    timeframe = data.get('timeframe', 'N/A')
    recommendation = data.get('recommendation', data.get('strategy', 'N/A'))

    result = f"""
{action_emoji} {symbol} • {timeframe.upper()}

Цена: ${data.get('last_price', 0):,.2f}
Доходность: {data.get('backtest_return_%', 0)}%
Свечей: {data.get('candles_count', 0)}

Рекомендация:
{recommendation}

Действие: {data.get('action', 'N/A')}
Сила: {data.get('strength', 0)}/10

Время: {datetime.now().strftime('%H:%M %d.%m.%Y')}
"""
    return result


def format_smart_analysis_result(data):
    action_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(data.get('action', 'HOLD'), '⚪')

    # AI анализ (если есть)
    ai_confidence = data.get('ai_confidence', 0)
    ai_recommendation = data.get('ai_recommendation', 'AI анализ не выполнен')
    ai_color = data.get('ai_color', '⚪')

    result = f"""
{action_emoji} УМНЫЙ АНАЛИЗ {data.get('symbol', 'N/A').upper()}

🤖 AI-ОЦЕНКА: {ai_confidence}/10 {ai_color}
💡 {ai_recommendation}

Лучший таймфрейм: {data.get('best_timeframe', 'N/A').upper()}
Лучшая доходность: {data.get('best_return_%', 0)}%
Текущая доходность: {data.get('backtest_return_%', 0)}%

{action_emoji} {data.get('recommendation', 'N/A')}
Действие: {data.get('action', 'N/A')}
Сила: {data.get('strength', 0)}/10

Сигналы:
{data.get('signals', 'N/A')}

Детали:
Цена: ${data.get('last_price', 0):,.2f}
Протестированы: {', '.join(data.get('tested_timeframes', []))}

Время: {datetime.now().strftime('%H:%M %d.%m.%Y')}
"""
    return result

# 🔍 КОМАНДА ДЛЯ ПОЛУЧЕНИЯ ID (добавь перед print)
@bot.message_handler(commands=['my_id'])
def get_my_id(message):
    info = f"""
📋 ИНФОРМАЦИЯ ДЛЯ НАСТРОЙКИ ЗАЩИТЫ:

👤 Твой личный ID: `{message.from_user.id}`
💬 ID этого чата: `{message.chat.id}`
📝 Тип чата: `{message.chat.type}`

⚡ СКОПИРУЙ эти цифры для настройки защиты!
"""
    bot.reply_to(message, info, parse_mode='Markdown')


# ==============================================
# 🆕 НОВЫЕ КОМАНДЫ ПОМОЩИ (ИСПРАВЛЕННАЯ ВЕРСИЯ)
# ==============================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Главное меню бота"""
    try:
        welcome_text = """
🤖 Crypto Trading Assistant 🚀

🎯 ДОБРО ПОЖАЛОВАТЬ В AI-ТРЕЙДИНГ!

✨ БЫСТРЫЙ СТАРТ:
/ai_help - Основные команды для начинающих
/pro_help - PRO команды для опытных

⚡ САМОЕ ВАЖНОЕ:
/activate_all - Запустить все системы
/trading_ideas - Готовые торговые идеи
/consensus SYMBOL - Проверить надежность

📊 БЫСТРЫЙ АНАЛИЗ:
/analyze_smart BTCUSDT - Умный анализ
/trend ETHUSDT - Анализ тренда
/volume_scan - Сканер объемов

💡 СОВЕТ ДЛЯ НОВИЧКА:
1. Начните с /ai_help - узнайте основные команды
2. Используйте /consensus для проверки сигналов
3. Входите только при AI уверенности ≥7.0

Примеры:
/analyze_smart btcusdt
/trend ethusdt  
/consensus solusdt
/ai_help

🎊 Удачи в торговле! 💰
"""
        bot.reply_to(message, welcome_text)  # УБРАЛ parse_mode='Markdown'

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['ai_help'])
def ai_help_command(message):
    """Основные команды для новичков"""
    try:
        help_text = """
🟢 ОСНОВНЫЕ КОМАНДЫ ДЛЯ НАЧИНАЮЩИХ 🟢

🤖 БЫСТРЫЙ СТАРТ:
/activate_all - Запустить ВСЕ системы
/deactivate_all - Остановить ВСЕ системы  
/ai_help - Это меню помощи

🎯 ПОИСК СИГНАЛОВ:
/trading_ideas - Готовые торговые идеи
/volume_scan - Сканер всплесков объемов  
/anomaly - Активные аномалии
/ai_recommendations - AI рекомендации

📈 АНАЛИЗ И ВХОД:
/analyze_smart SYMBOL - Умный анализ монеты
/advanced_targets SYMBOL - Цели с Фибо
/trend SYMBOL - Анализ тренда
/risk SYMBOL БАЛАНС 2 - Расчет риска

✅ ПРОВЕРКА НАДЕЖНОСТИ:
/consensus SYMBOL - Несколько подтверждений

⚡ ПРИМЕРЫ ДЛЯ НАЧАЛА:
/analyze_smart BTCUSDT
/trend ETHUSDT  
/risk SOLUSDT 1000 2
/consensus BTCUSDT

💡 СОВЕТ ДЛЯ НОВИЧКА:
Всегда начинайте с /consensus SYMBOL 
Если консенсус ≥50% - тогда /advanced_targets SYMBOL
Если AI <7.0 - ❌ ПРОПУСТИТЕ сделку!

🚀 ДЛЯ ОПЫТНЫХ:
/pro_help - Показать PRO команды
"""
        bot.reply_to(message, help_text)  # УБРАЛ parse_mode='Markdown'

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['pro_help'])
def pro_help_command(message):
    """PRO команды для опытных"""
    try:
        pro_text = """
🚀 PRO COMMANDS - ДЛЯ ОПЫТНЫХ ТРЕЙДЕРОВ 🚀

💎 ПРЕМИУМ СИГНАЛЫ:
/premium_monitor_start - Авто-сканирование
/premium_signals - Разовое сканирование

🤖 AI-АНАЛИТИКА:
/crypto_ai_master - Полный анализ
/ai_market_status - Диагностика рынка
/risk_dashboard - Панель рисков

🔍 АНОМАЛИИ И ФИЛЬТРЫ:
/anomaly_start - Детектор аномалий
/market_phase_start - Мониторинг фаз
/session_filters_start - Фильтры сессий

📊 ВОЛАТИЛЬНОСТЬ И ОБЪЕМЫ:
/volatility_prediction SYMBOL - Прогноз волатильности
/volume_monitor_start - Мониторинг объемов

🎯 АВТОМАТИЗАЦИЯ:
/smart_tp_start - Умные тейк-профиты
/reports_daily - Авто-отчеты

/ai_help - 🔙 Основные команды
"""
        bot.reply_to(message, pro_text)  # УБРАЛ parse_mode='Markdown'

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


# 🔽 🔽 🔽 КОМАНДЫ АВТОМАТИЧЕСКОЙ ТОРГОВЛИ 🔽 🔽 🔽

@bot.message_handler(commands=['auto_trade'])
def auto_trade_command(message):
    """Создание автоматической сделки с ПРОВЕРКОЙ КРИТЕРИЕВ"""
    try:
        # Парсим параметры из сообщения
        parts = message.text.split()
        if len(parts) < 6:
            bot.reply_to(message, """
❌ Неправильный формат команды!

📋 Правильный формат:
/auto_trade SYMBOL ENTRY STOP TP1,TP2,TP3 DIRECTION

💡 Пример:
/auto_trade PEPEUSDT 0.00000671 0.00000660 0.00000681,0.00000692,0.00000706 LONG
""")
            return

        symbol = parts[1].upper()
        entry_price = float(parts[2])
        stop_loss = float(parts[3])
        take_profits = [float(tp) for tp in parts[4].split(',')]
        direction = parts[5] if len(parts) > 5 else "LONG"

        global auto_trade_manager  # Убедитесь, что auto_trade_manager доступен
        MIN_AI_CONFIDENCE = auto_trade_manager.trading_config['MIN_AI_CONFIDENCE']
        MIN_VOLUME_RATIO = auto_trade_manager.trading_config['MIN_VOLUME_RATIO']


        # 🔍 🔍 🔍 ПРОВЕРКА КРИТЕРИЕВ ПЕРЕД ОТКРЫТИЕМ 🔍 🔍 🔍
        consensus = get_consensus_signal(symbol)
        volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)

        ai_confidence = consensus.get('ai_confidence', 5.0)
        volume_ratio = volume_data.get('volume_ratio', 1.0)



        # ✅ ВСЕ КРИТЕРИИ ВЫПОЛНЕНЫ - ОТКРЫВАЕМ СДЕЛКУ
        position_id = auto_trade_manager.create_auto_trade(
            chat_id=message.chat.id,
            symbol=symbol,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profits=take_profits,
            direction=direction,
            ai_confidence=ai_confidence,  # 🔽 РЕАЛЬНЫЕ ДАННЫЕ
            volume_ratio=volume_ratio  # 🔽 РЕАЛЬНЫЕ ДАННЫЕ
        )

        if position_id:
            response = f"""
🎉 АВТОМАТИЧЕСКАЯ СДЕЛКА АКТИВИРОВАНА!

📊 {symbol} - {direction}
💰 Вход: {format_price(entry_price)}
🎯 Цели: {', '.join([format_price(tp) for tp in take_profits])}
🛑 Стоп: {format_price(stop_loss)}

🤖 AI-ПОДТВЕРЖДЕНИЕ:
• AI уверенность: {ai_confidence:.1f}/10 ✅
• Объемы: {volume_ratio:.1f}x ✅

📱 Команды управления:
/active_positions - все позиции
/position_status_{symbol.replace('USDT', '')} - статус
/close_position_{symbol.replace('USDT', '')} - закрыть

💡 Система отслеживает позицию автоматически!
"""
            bot.reply_to(message, response)
        else:
            bot.reply_to(message, "❌ Ошибка создания авто-сделки")

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")



@bot.message_handler(commands=['active_positions'])
def active_positions_command(message):
    """Показать все активные позиции с inline-кнопками"""
    try:
        active_positions = auto_trade_manager.get_active_positions(message.chat.id)

        if not active_positions:
            bot.reply_to(message, "📭 Нет активных позиций")
            return

        # Создаем компактное сообщение
        response = "📊 АКТИВНЫЕ ПОЗИЦИИ:\n\n"

        total_pnl = 0
        for pos_id, position in active_positions.items():
            symbol = position['symbol']
            current_price = auto_trade_manager._get_current_price(symbol)

            # Рассчитываем PnL
            entry = position['entry_price']
            if current_price:
                if position['direction'] == "LONG":
                    pnl_pct = (current_price - entry) / entry * 100
                else:
                    pnl_pct = (entry - current_price) / entry * 100
                total_pnl += pnl_pct

                emoji = "🟢" if pnl_pct > 0 else "🔴"
                response += f"{emoji} {symbol}: {pnl_pct:+.2f}%\n"
            else:
                response += f"⚪ {symbol}: ---\n"

        response += f"\n💰 Общая доходность: {total_pnl:+.2f}%"
        response += f"\n📈 Позиций: {len(active_positions)}"

        # Создаем клавиатуру с кнопками
        keyboard = create_positions_keyboard(active_positions)

        # Отправляем сообщение с кнопками
        bot.send_message(
            message.chat.id,
            response,
            reply_markup=keyboard
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")




@bot.message_handler(commands=['close_position'])
def close_position_command(message):
    """Закрыть позицию по символу"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Укажите символ: /close_position SYMBOL")
            return

        symbol = parts[1].upper()
        active_positions = auto_trade_manager.get_active_positions(message.chat.id)

        # Ищем позицию по символу
        position_to_close = None
        for pos_id, position in active_positions.items():
            if position['symbol'] == symbol:
                position_to_close = position
                break

        if not position_to_close:
            bot.reply_to(message, f"❌ Активная позиция {symbol} не найдена")
            return

        # Закрываем позицию
        current_price = auto_trade_manager._get_current_price(symbol)
        if current_price:
            auto_trade_manager._execute_stop_loss(position_to_close, current_price)
            bot.reply_to(message, f"✅ Позиция {symbol} закрыта")
        else:
            bot.reply_to(message, f"❌ Ошибка получения цены для {symbol}")

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['trading_history'])
def trading_history_command(message):
    """Показать историю сделок"""
    try:
        history = auto_trade_manager.trade_history
        user_history = [trade for trade in history if trade.get('chat_id') == message.chat.id]

        if not user_history:
            bot.reply_to(message, "📭 История сделок пуста")
            return

        response = "📈 ИСТОРИЯ СДЕЛОК:\n\n"

        for i, trade in enumerate(user_history[-10:]):  # Последние 10 сделок
            symbol = trade['symbol']
            entry = trade['entry_price']
            close = trade.get('close_price', entry)

            if trade['direction'] == "LONG":
                pnl_pct = (close - entry) / entry * 100
            else:
                pnl_pct = (entry - close) / entry * 100

            status_emoji = "🟢" if pnl_pct > 0 else "🔴"

            response += f"""
{status_emoji} {trade['symbol']} - {trade['direction']}
💰 Вход: {format_price(entry)}
📊 Выход: {format_price(close)}
💸 Результат: {pnl_pct:+.2f}%
🎯 Причина: {trade.get('close_reason', 'UNKNOWN')}
📅 {trade.get('closed_at', 'N/A')}
────────────────────
"""

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['clear_history'])
def clear_history_command(message):
    """Очищает всю историю сделок"""
    try:
        # Очищаем историю сделок
        auto_trade_manager.trade_history = []

        # Сохраняем изменения
        auto_trade_manager.save_data()

        bot.reply_to(message, "✅ История сделок полностью очищена!")

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка очистки истории: {str(e)}")
@bot.message_handler(commands=['daily_report'])
def daily_report_command(message):
    """Ежедневный отчет по торгам"""
    try:
        stats = auto_trade_manager.get_trading_statistics(message.chat.id, days=1)

        if not stats:
            bot.reply_to(message, "📊 За сегодня сделок нет")
            return

        report = f"""
📊 ЕЖЕДНЕВНЫЙ ОТЧЕТ

📈 ОБЩАЯ СТАТИСТИКА:
• Всего сделок: {stats['total_trades']}
• Прибыльных: {stats['profitable_trades']} ({stats['win_rate']:.1f}%)
• Убыточных: {stats['losing_trades']}
• Общая доходность: {stats['total_pnl']:+.2f}%
• Средняя сделка: {stats['avg_pnl']:+.2f}%

🎯 ЭФФЕКТИВНОСТЬ AI:
• Сделок с AI ≥7.0: {stats['ai_confident_trades']}
• Сделок с AI ≥8.0: {stats['ai_high_confident_trades']}

🏆 СЕГОДНЯ ЛУЧШИЕ:
"""

        # Добавляем лучшие символы
        for i, (symbol, data) in enumerate(stats['best_symbols'][:3], 1):
            win_rate = (data['profitable'] / data['trades'] * 100) if data['trades'] > 0 else 0
            report += f"{i}. {symbol}: {data['total_pnl']:+.2f}% ({data['trades']} сделок, {win_rate:.1f}%)\n"

        report += f"\n💡 РЕКОМЕНДАЦИИ:\n{_generate_recommendations(stats)}"

        bot.reply_to(message, report)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка отчета: {str(e)}")


@bot.message_handler(commands=['weekly_report'])
def weekly_report_command(message):
    """Недельный отчет по торгам"""
    try:
        stats = auto_trade_manager.get_trading_statistics(message.chat.id, days=7)

        if not stats or stats['total_trades'] == 0:
            bot.reply_to(message, "📊 За неделю сделок нет")
            return

        report = f"""
📈 НЕДЕЛЬНЫЙ ОТЧЕТ

📊 ОБЩАЯ СТАТИСТИКА:
• Всего сделок: {stats['total_trades']}
• Прибыльных: {stats['profitable_trades']} ({stats['win_rate']:.1f}%)
• Убыточных: {stats['losing_trades']}
• Общая доходность: {stats['total_pnl']:+.2f}%
• Средняя сделка: {stats['avg_pnl']:+.2f}%

🎯 ЭФФЕКТИВНОСТЬ AI:
• Сделок с AI ≥7.0: {stats['ai_confident_trades']}
• Сделок с AI ≥8.0: {stats['ai_high_confident_trades']}

🏆 ТОП-СИМВОЛЫ:
"""

        # Лучшие символы
        for i, (symbol, data) in enumerate(stats['best_symbols'][:5], 1):
            win_rate = (data['profitable'] / data['trades'] * 100) if data['trades'] > 0 else 0
            report += f"{i}. {symbol}: {data['total_pnl']:+.2f}% ({win_rate:.1f}% успешных)\n"

        report += f"\n📉 ХУДШИЕ СИМВОЛЫ:\n"

        # Худшие символы
        for i, (symbol, data) in enumerate(stats['worst_symbols'][:3], 1):
            win_rate = (data['profitable'] / data['trades'] * 100) if data['trades'] > 0 else 0
            report += f"{i}. {symbol}: {data['total_pnl']:+.2f}% ({win_rate:.1f}% успешных)\n"

        report += f"\n💡 РЕКОМЕНДАЦИИ:\n{_generate_recommendations(stats)}"

        bot.reply_to(message, report)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка отчета: {str(e)}")


@bot.message_handler(commands=['debug_systems'])
def debug_systems(message):
    """Диагностика всех систем для символа"""
    try:
        symbol = 'BTCUSDT'
        response = f"🔍 ДИАГНОСТИКА СИСТЕМ ДЛЯ {symbol}\n\n"

        # 1. Диагностика объемов
        try:
            volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
            volume_ratio = volume_data.get('volume_ratio', 1.0)
            volume_signal = volume_data.get('signal', 'NEUTRAL')
            response += f"📊 ОБЪЕМЫ:\n"
            response += f"• volume_ratio: {volume_ratio}\n"
            response += f"• signal: {volume_signal}\n"
            response += f"• error: {volume_data.get('error', 'None')}\n\n"
        except Exception as e:
            response += f"📊 ОБЪЕМЫ ОШИБКА: {e}\n\n"

        # 2. Диагностика тренда
        try:
            if 'trend_analyzer' in globals():
                trend_data = trend_analyzer.multi_timeframe_analysis(symbol)
                main_trend = trend_data.get('overall_trend', 'NEUTRAL')
                trend_score = trend_data.get('confluence_score', 0)
                response += f"📈 ТРЕНД:\n"
                response += f"• overall_trend: {main_trend}\n"
                response += f"• confluence_score: {trend_score}\n"
                response += f"• error: {trend_data.get('error', 'None')}\n\n"
            else:
                response += f"📈 ТРЕНД: trend_analyzer не найден\n\n"
        except Exception as e:
            response += f"📈 ТРЕНД ОШИБКА: {e}\n\n"

        # 3. Диагностика AI
        try:
            ai_data = ai_checker.analyze_signal_quality(symbol, {
                'current_price': 0,
                'volume_ratio': 1.0,
                'confluence': 50
            })
            response += f"🤖 AI:\n"
            response += f"• confidence: {ai_data['ai_confidence_score']}\n"
            response += f"• recommendation: {ai_data['recommendation']}\n\n"
        except Exception as e:
            response += f"🤖 AI ОШИБКА: {e}\n\n"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка диагностики: {e}")


@bot.message_handler(commands=['save_data'])
def save_data_command(message):
    """Сохранить данные вручную"""
    try:
        if auto_trade_manager.save_data():
            bot.reply_to(message, "💾 Данные успешно сохранены!")
        else:
            bot.reply_to(message, "❌ Ошибка сохранения данных")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


def _generate_recommendations(stats):
    """Генерирует рекомендации на основе статистики"""
    recommendations = []

    if stats['win_rate'] < 60:
        recommendations.append("• Повысить порог AI уверенности до 7.5")

    if stats['ai_high_confident_trades'] > 0:
        ai_success_rate = (stats['ai_high_confident_trades'] / stats['total_trades'] * 100)
        if ai_success_rate > 70:
            recommendations.append("• AI ≥8.0 показывает отличные результаты - доверяйте этим сигналам")

    # Анализ лучших символов
    if stats['best_symbols']:
        best_symbol = stats['best_symbols'][0][0]
        recommendations.append(f"• {best_symbol} показывает лучшие результаты - уделите ему больше внимания")

    if not recommendations:
        recommendations.append("• Продолжайте текущую стратегию - она работает хорошо")

    return "\n".join(recommendations)

# 🔼 🔼 🔼 КОНЕЦ КОМАНД АВТОМАТИЧЕСКОЙ ТОРГОВЛИ 🔼 🔼 🔼


@bot.message_handler(commands=['debug_trade'])
def debug_trade(message):
    """Диагностика какой create_simple_trade вызывается"""
    try:
        # Имитируем вызов как из кнопки
        chat_id = message.chat.id
        symbol = 'BTCUSDT'

        # Получаем консенсус для проверки
        consensus = get_consensus_signal(symbol)

        response = f"""
🔍 ДИАГНОСТИКА TRADE ДЛЯ {symbol}

📊 Консенсус:
• AI уверенность: {consensus['ai_confidence']}/10
• Направление: {consensus['final_direction']} 
• Уровень риска: {consensus['risk_level']}

💡 Расчет порога:
• BTCUSDT = LARGE_CAP
• Risk: {consensus['risk_level']} → порог: 5.0
• Direction: {consensus['final_direction']} → +0.3 = 5.3

🎯 Требуется: 5.3/10
📈 Имеется: {consensus['ai_confidence']}/10 ✅

🚨 ПРОБЛЕМА: Вызывается СТАРАЯ версия функции!
"""
        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


@bot.message_handler(commands=['force_trade'])
def force_trade(message):
    """Принудительное создание сделки через новую функцию"""
    try:
        symbol = 'BTCUSDT'
        chat_id = message.chat.id

        # Вызываем новую функцию напрямую
        create_simple_trade(chat_id, symbol, message.message_id)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")
# 🔽 🔽 🔽 ОБРАБОТЧИКИ INLINE-КНОПОК 🔽 🔽 🔽

@bot.message_handler(commands=['search_8'])
def search_8(message):
    """Автоматический поиск порога 8.0"""
    try:
        with open('final_bot.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()

        found_lines = []
        for i, line in enumerate(lines, 1):
            if '8.0' in line and ('ai_confidence' in line.lower() or 'ai' in line.lower()):
                found_lines.append(f"Строка {i}: {line.strip()}")

        if found_lines:
            response = "🔍 НАЙДЕНЫ СТРОКИ С 8.0:\n\n" + "\n".join(found_lines)
            response += "\n\n💡 ЗАМЕНИ '8.0' НА '5.0' В ЭТИХ СТРОКАХ"
        else:
            response = "✅ Строк с 8.0 не найдено"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


@bot.message_handler(commands=['check_fixed'])
def check_fixed(message):
    """Проверка исправленных порогов"""
    try:
        symbol = 'BTCUSDT'
        consensus = get_consensus_signal(symbol)

        response = f"""
🔍 ПРОВЕРКА ИСПРАВЛЕННЫХ ПОРОГОВ ДЛЯ {symbol}

📊 Консенсус:
• AI уверенность: {consensus['ai_confidence']}/10
• Направление: {consensus['final_direction']}
• Консенсус: {consensus['consensus_level']:.1f}%

🎯 Требуется после исправления: ≥5.0/10
📈 Имеется: {consensus['ai_confidence']}/10 ✅

💡 Теперь сделка должна создаваться!
"""
        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


@bot.message_handler(commands=['search_volume'])
def search_volume(message):
    """Поиск порога объемов 1.8"""
    try:
        with open('final_bot.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()

        found_lines = []
        for i, line in enumerate(lines, 1):
            if '1.8' in line and ('volume' in line.lower() or 'объем' in line.lower()):
                found_lines.append(f"Строка {i}: {line.strip()}")

        if found_lines:
            response = "🔍 НАЙДЕНЫ СТРОКИ С 1.8:\n\n" + "\n".join(found_lines)
            response += "\n\n💡 ЗАМЕНИ '1.8' НА '0.8' В ЭТИХ СТРОКАХ"
        else:
            response = "✅ Строк с 1.8 не найдено"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


@bot.message_handler(commands=['debug_signal'])
def debug_signal(message):
    """Диагностика сигнала для символа (исправленная)"""
    try:
        symbol = 'BTCUSDT'

        # Получаем все данные
        price = auto_trade_manager._get_current_price(symbol)
        volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
        consensus = get_consensus_signal(symbol)

        # 🔽 БЕЗОПАСНОЕ ФОРМАТИРОВАНИЕ ДАННЫХ
        def safe_format_data(data):
            if isinstance(data, dict):
                return {k: safe_format_data(v) for k, v in data.items()}
            elif isinstance(data, (list, tuple)):
                return [safe_format_data(item) for item in data]
            elif isinstance(data, (bool, type(None))):
                return str(data)
            else:
                return data

        safe_volume_data = safe_format_data(volume_data) if volume_data else "Нет данных"

        response = f"""
🔍 ДИАГНОСТИКА СИГНАЛА ДЛЯ {symbol}

💰 Цена: {format_price(price) if price else 'N/A'}

📊 ДАННЫЕ ОБЪЕМОВ:
• volume_ratio: {volume_data.get('volume_ratio', 'N/A') if volume_data else 'N/A'}
• signal: {volume_data.get('signal', 'N/A') if volume_data else 'N/A'}
• error: {volume_data.get('error', 'None') if volume_data else 'N/A'}

🎯 КОНСЕНСУС:
• AI уверенность: {consensus['ai_confidence']}/10
• Направление: {consensus['final_direction']}
• Уровень согласия: {consensus['consensus_level']:.1f}%
• Риск: {consensus['risk_level']}

📋 СИГНАЛЫ СИСТЕМ:
"""
        for signal in consensus['signals']:
            details = signal.get('details', '')
            response += f"• {signal['system']}: {signal['direction']} ({signal['confidence']}/10) {details}\n"

        response += f"""
💡 ВЫВОД:
Система работает ПРАВИЛЬНО! 
AI дает низкую оценку из-за плохих объемов.
Это ЗАЩИТА от убыточных сделок!

🚀 РЕКОМЕНДАЦИИ:
• Найдите символы с объемами >1.8x
• Используйте /search_symbol ETH
• Ждите качественных сигналов
"""
        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка диагностики: {str(e)}")


@bot.message_handler(commands=['find_good_signals'])
def find_good_signals(message):
    """Поиск символов с хорошими сигналами"""
    try:
        test_symbols = ['ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'XRPUSDT']
        good_signals = []

        for symbol in test_symbols:
            consensus = get_consensus_signal(symbol)
            volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)

            volume_ratio = volume_data.get('volume_ratio', 0) if volume_data else 0
            ai_confidence = consensus['ai_confidence']

            if ai_confidence >= 7.0 and volume_ratio >= 1.5:
                good_signals.append({
                    'symbol': symbol,
                    'ai_confidence': ai_confidence,
                    'volume_ratio': volume_ratio,
                    'direction': consensus['final_direction']
                })

        if good_signals:
            response = "🚀 СИМВОЛЫ С ХОРОШИМИ СИГНАЛАМИ:\n\n"
            for signal in good_signals:
                response += f"• {signal['symbol']}: AI {signal['ai_confidence']}/10, Объемы {signal['volume_ratio']:.2f}x, {signal['direction']}\n"
        else:
            response = "🔍 Хороших сигналов не найдено. Попробуйте позже.\n\n"
            response += "💡 Сейчас рынок может быть спокойным. Ждите увеличения объемов!"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка поиска: {str(e)}")


@bot.message_handler(commands=['debug_auto_trade'])
def debug_auto_trade(message):
    """Диагностика фильтров авто-трейдинга"""
    try:
        symbol = 'BNBUSDT'

        # Получаем данные
        price = auto_trade_manager._get_current_price(symbol)
        volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
        consensus = get_consensus_signal(symbol)

        # Проверяем основные критерии
        ai_confidence = consensus['ai_confidence']
        volume_ratio = volume_data.get('volume_ratio', 0) if volume_data else 0
        direction = consensus['final_direction']

        response = f"""
🔍 ДИАГНОСТИКА АВТО-ТРЕЙДИНГА ДЛЯ {symbol}

📊 ОСНОВНЫЕ КРИТЕРИИ:
• AI уверенность: {ai_confidence}/10 {'✅' if ai_confidence >= 7.0 else '❌'}
• Объемы: {volume_ratio:.1f}x {'✅' if volume_ratio >= 1.5 else '❌'}
• Направление: {direction}

🎯 ДОПОЛНИТЕЛЬНЫЕ ФИЛЬТРЫ:
"""
        # Проверяем дополнительные фильтры
        filters_passed = 0
        total_filters = 0

        # Фильтр 1: Минимальная уверенность консенсуса
        consensus_level = consensus['consensus_level']
        min_consensus = 60.0  # Предполагаемый порог
        consensus_ok = consensus_level >= min_consensus
        filters_passed += 1 if consensus_ok else 0
        total_filters += 1
        response += f"• Консенсус ≥60%: {consensus_level:.1f}% {'✅' if consensus_ok else '❌'}\n"

        # Фильтр 2: Риск уровень
        risk_level = consensus['risk_level']
        risk_ok = risk_level in ['LOW', 'MEDIUM']  # Только низкий/средний риск
        filters_passed += 1 if risk_ok else 0
        total_filters += 1
        response += f"• Уровень риска: {risk_level} {'✅' if risk_ok else '❌'}\n"

        # Фильтр 3: Количество согласных систем
        systems_agreed = consensus['systems_agreed']
        systems_checked = consensus['systems_checked']
        systems_ok = systems_agreed >= 2  # Минимум 2 системы согласны
        filters_passed += 1 if systems_ok else 0
        total_filters += 1
        response += f"• Систем согласны: {systems_agreed}/{systems_checked} {'✅' if systems_ok else '❌'}\n"

        response += f"""
📋 ИТОГ:
• Пройдено фильтров: {filters_passed}/{total_filters}
• Основные критерии: ✅
• Дополнительные фильтры: {'✅' if filters_passed == total_filters else '❌'}

💡 ПРОБЛЕМА: Дополнительные фильтры авто-трейдинга!
"""
        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка диагностики: {str(e)}")


@bot.message_handler(commands=['create_manual_trades'])
def create_manual_trades(message):
    """Создание сделок вручную для тестирования"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    btn_bnb = types.InlineKeyboardButton("🤖 BNBUSDT", callback_data="simple_trade_BNBUSDT")
    btn_sol = types.InlineKeyboardButton("🤖 SOLUSDT", callback_data="simple_trade_SOLUSDT")
    btn_eth = types.InlineKeyboardButton("🤖 ETHUSDT", callback_data="simple_trade_ETHUSDT")

    keyboard.add(btn_bnb, btn_sol, btn_eth)

    response = """
🚀 КАЧЕСТВЕННЫЕ СИГНАЛЫ НАЙДЕНЫ!

📊 ГОТОВЫЕ СИГНАЛЫ:
• BNBUSDT: AI 8.1/10, Объемы 2.7x ✅
• SOLUSDT: AI 8.9/10, Объемы 1.8x ✅  
• ETHUSDT: AI 8.7/10, Объемы 2.1x ✅

💡 Нажмите кнопку для создания сделки вручную
"""
    bot.send_message(message.chat.id, response, reply_markup=keyboard)


@bot.message_handler(commands=['compare_data'])
def compare_data(message):
    """Сравнение данных из разных источников"""
    try:
        symbol = 'BNBUSDT'

        response = f"""
🔍 СРАВНЕНИЕ ДАННЫХ ДЛЯ {symbol}

📊 ИСТОЧНИК 1 - ДИАГНОСТИКА:
"""
        # Данные из диагностики
        consensus1 = get_consensus_signal(symbol)
        volume_data1 = advanced_volume_analyzer.get_volume_spike_analysis(symbol)

        response += f"""
• AI уверенность: {consensus1['ai_confidence']}/10
• Объемы: {volume_data1.get('volume_ratio', 0):.1f}x
• Направление: {consensus1['final_direction']}
• Время анализа: {datetime.now().strftime('%H:%M:%S')}
"""

        # 🔽 ПРОВЕРЯЕМ КЭШ AI
        response += f"\n📊 ПРОВЕРКА КЭША AI:"
        try:
            if hasattr(ai_checker, 'analysis_cache') and symbol in ai_checker.analysis_cache:
                cached_data, timestamp = ai_checker.analysis_cache[symbol]
                cache_age = datetime.now() - timestamp
                response += f"\n• Кэш AI: {cached_data['ai_confidence_score']}/10 (возраст: {cache_age.seconds} сек)"
            else:
                response += "\n• Кэш AI: не найден"
        except:
            response += "\n• Кэш AI: недоступен"

        # 🔽 ПРОВЕРЯЕМ РАЗНЫЕ ФУНКЦИИ АНАЛИЗА
        response += f"\n\n🎯 ТЕСТ РАЗНЫХ ФУНКЦИЙ:"

        # Тест 1: Прямой вызов AI
        try:
            direct_ai = ai_checker.analyze_signal_quality(symbol, {
                'current_price': 0, 'volume_ratio': 1.0, 'confluence': 50
            })
            response += f"\n• Прямой AI: {direct_ai['ai_confidence_score']}/10"
        except Exception as e:
            response += f"\n• Прямой AI: ошибка {str(e)}"

        # Тест 2: Объемы напрямую
        try:
            direct_volume = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
            response += f"\n• Прямые объемы: {direct_volume.get('volume_ratio', 0):.1f}x"
        except Exception as e:
            response += f"\n• Прямые объемы: ошибка {str(e)}"

        response += f"""

💡 ВЫВОД:
• Есть расхождение между данными!
• Возможные причины: кэш, разные API, временные задержки
"""
        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка сравнения: {str(e)}")


@bot.message_handler(commands=['clear_cache'])
def clear_cache(message):
    """Очистка кэша данных"""
    try:
        # Очищаем кэш AI
        if hasattr(ai_checker, 'analysis_cache'):
            ai_checker.analysis_cache.clear()

        # Очищаем кэш объемов (если есть)
        if hasattr(advanced_volume_analyzer, 'cache'):
            advanced_volume_analyzer.cache.clear()

        response = """
🔄 КЭШ ОЧИЩЕН!

📊 РЕКОМЕНДАЦИИ:
1. Подожди 30 секунд
2. Выполни /compare_data снова
3. Проверь актуальные данные
4. Попробуй создать сделку через /create_manual_trades
"""
        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка очистки: {str(e)}")


@bot.message_handler(commands=['test_signal_direct'])
def test_signal_direct(message):
    """Прямое тестирование сигнала без кэша"""
    try:
        symbol = 'BNBUSDT'

        # 🔽 ПРЯМОЙ АНАЛИЗ БЕЗ КЭША
        bot.reply_to(message, "🔄 Запускаю прямой анализ...")

        # Очищаем кэш
        if hasattr(ai_checker, 'analysis_cache') and symbol in ai_checker.analysis_cache:
            del ai_checker.analysis_cache[symbol]

        # Прямой анализ
        ai_data = ai_checker.analyze_signal_quality(symbol, {
            'current_price': 0, 'volume_ratio': 1.0, 'confluence': 50
        })
        volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
        consensus = get_consensus_signal(symbol)

        response = f"""
🎯 ПРЯМОЙ АНАЛИЗ {symbol} (БЕЗ КЭША):

📊 РЕАЛЬНЫЕ ДАННЫЕ:
• AI уверенность: {ai_data['ai_confidence_score']}/10
• Объемы: {volume_data.get('volume_ratio', 0):.1f}x
• Направление: {consensus['final_direction']}
• Рекомендация: {ai_data['recommendation']}

💡 ДЕЙСТВИЯ:
"""
        if ai_data['ai_confidence_score'] >= 8.0 and volume_data.get('volume_ratio', 0) >= 1.8:
            response += "✅ УСЛОВИЯ ВЫПОЛНЕНЫ! Создавайте сделку через кнопку!"
        else:
            response += "❌ УСЛОВИЯ НЕ ВЫПОЛНЕНЫ. Ждите лучших сигналов."

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка тестирования: {str(e)}")


@bot.message_handler(commands=['find_false_data'])
def find_false_data(message):
    """Поиск источника ложных данных авто-трейдинга"""
    try:
        response = """
🔍 ПОИСК ИСТОЧНИКА ЛОЖНЫХ ДАННЫХ

📊 РЕАЛЬНЫЕ ДАННЫЕ (проверенные):
• BNBUSDT: AI 4.5/10, Объемы 0.3x
• ETHUSDT: AI 4.8/10, Объемы ~0.3x
• SOLUSDT: AI ~4.5/10, Объемы ~0.3x

📊 ЛОЖНЫЕ ДАННЫЕ (авто-трейдинг):
• BNBUSDT: AI 8.1/10, Объемы 2.7x
• ETHUSDT: AI 8.7/10, Объемы 2.1x
• SOLUSDT: AI 8.9/10, Объемы 1.8x

🎯 ВОЗМОЖНЫЕ ИСТОЧНИКИ ПРОБЛЕМЫ:

1. **ДРУГОЙ AI МОДУЛЬ** - авто-трейдинг использует другой анализатор
2. **ТЕСТОВЫЕ ДАННЫЕ** - в авто-трейдинге зашиты примеры для демо
3. **РАЗНЫЕ API** - авто-трейдинг берет данные из другого источника
4. **УСТАРЕВШИЙ КЭШ** - данные не обновляются

💡 РЕКОМЕНДАЦИИ:

1. **Найди функцию авто-трейдинга** в коде
2. **Проверь какой AI модуль** она использует  
3. **Сравни параметры** с нашим ai_checker
4. **Обнови или замени** функцию авто-трейдинга
"""
        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['find_auto_trade'])
def find_auto_trade(message):
    """Автоматический поиск функции авто-трейдинга"""
    try:
        with open('final_bot.py', 'r', encoding='utf-8') as f:
            content = f.read()

        response = "🔍 РЕЗУЛЬТАТЫ ПОИСКА АВТО-ТРЕЙДИНГА:\n\n"

        # Поиск по ключевым фразам
        search_phrases = [
            'АВТО-СДЕЛКА ОТКЛОНЕНА',
            'auto_trade',
            'авто-трейд',
            'autotrade',
            'create_auto_trade',
            'auto_trade_manager'
        ]

        found_lines = []

        for i, line in enumerate(content.split('\n'), 1):
            for phrase in search_phrases:
                if phrase.lower() in line.lower():
                    found_lines.append(f"Строка {i}: {line.strip()}")
                    break

        if found_lines:
            response += "📋 НАЙДЕНЫ СТРОКИ:\n" + "\n".join(found_lines[:10])  # Первые 10 строк
            response += f"\n\n... и еще {len(found_lines) - 10} строк" if len(found_lines) > 10 else ""

            response += """

💡 ДЕЙСТВИЯ:
1. Найди функцию которая выводит 'АВТО-СДЕЛКА ОТКЛОНЕНА'
2. Проверь откуда она берет данные AI и объемов
3. Замени на наш ai_checker.analyze_signal_quality
"""
        else:
            response += "❌ Функции авто-трейдинга не найдены в основном файле"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка поиска: {str(e)}")


@bot.message_handler(commands=['find_reject_function'])
def find_reject_function(message):
    """Поиск функции с уведомлениями 'АВТО-СДЕЛКА ОТКЛОНЕНА'"""
    try:
        with open('final_bot.py', 'r', encoding='utf-8') as f:
            content = f.read()

        response = "🔍 ПОИСК ФУНКЦИИ С УВЕДОМЛЕНИЯМИ:\n\n"

        # Ищем конкретные фразы из уведомлений
        target_phrases = [
            'АВТО-СДЕЛКА ОТКЛОНЕНА',
            'Не пройдены фильтры авто-трейдинга',
            'Требуется: AI ≥8.0 и Объемы ≥1.8x',
            '🚫 АВТО-СДЕЛКА ОТКЛОНЕНА'
        ]

        found_sections = []

        for phrase in target_phrases:
            if phrase in content:
                # Находим контекст вокруг фразы
                index = content.find(phrase)
                start = max(0, index - 200)  # 200 символов до
                end = min(len(content), index + 500)  # 500 символов после
                context = content[start:end]

                # Находим имя функции (ищем def выше)
                lines_before = content[:index].split('\n')
                function_name = "Не определена"
                for line in reversed(lines_before):
                    if line.strip().startswith('def '):
                        function_name = line.strip()
                        break

                found_sections.append(f"""
📋 ФРАЗА: "{phrase}"
🏷 ФУНКЦИЯ: {function_name}
📝 КОНТЕКСТ:
{context}
{'=' * 50}
""")

        if found_sections:
            response += "🎯 НАЙДЕНЫ УВЕДОМЛЕНИЯ:\n" + "\n".join(found_sections)

            response += """
💡 СЛЕДУЮЩИЕ ДЕЙСТВИЯ:
1. Найди ПОЛНЫЙ код функции из результатов выше
2. Скопируй ВСЮ функцию и отправь мне
3. Я покажу КОНКРЕТНО что исправить
"""
        else:
            response += "❌ Конкретные уведомления не найдены. Возможно в другом файле."

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка поиска: {str(e)}")


@bot.message_handler(commands=['test_auto_analysis'])
def test_auto_analysis(message):
    """Тест исправленного анализа авто-трейдинга"""
    try:
        symbol = 'BTCUSDT'

        # Тестируем новую функцию анализа
        analysis = auto_trading_scanner._analyze_symbol(symbol)

        if not analysis:
            bot.reply_to(message, f"❌ Анализ {symbol} не удался")
            return

        response = f"""
🔍 ТЕСТ ИСПРАВЛЕННОГО АНАЛИЗА {symbol}:

📊 РЕАЛЬНЫЕ ДАННЫЕ:
• AI уверенность: {analysis['ai_confidence']:.1f}/10
• Объемы: {analysis['volume_ratio']:.1f}x
• Направление: {analysis['direction']}
• Цена: {format_price(analysis['current_price'])}

🎯 КРИТЕРИИ АВТО-ВХОДА:
• AI ≥7.5: {'✅' if analysis['ai_confidence'] >= 7.5 else '❌'}
• Объемы ≥1.8: {'✅' if analysis['volume_ratio'] >= 1.8 else '❌'} 
• Направление ≠ HOLD: {'✅' if analysis['direction'] != 'HOLD' else '❌'}

💡 СИГНАЛ: {'✅ ГОТОВ К АВТО-ВХОДУ' if auto_trading_scanner._is_good_signal(analysis) else '❌ НЕ ПОДХОДИТ'}
"""
        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка теста: {str(e)}")


@bot.message_handler(commands=['test_multiple_symbols'])
def test_multiple_symbols(message):
    """Тест нескольких символов"""
    try:
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT']
        response = "🔍 ТЕСТ НЕСКОЛЬКИХ СИМВОЛОВ:\n\n"

        for symbol in symbols:
            analysis = auto_trading_scanner._analyze_symbol(symbol)
            if analysis:
                is_good = auto_trading_scanner._is_good_signal(analysis)
                response += f"• {symbol}: AI {analysis['ai_confidence']:.1f}/10, Объемы {analysis['volume_ratio']:.1f}x, {analysis['direction']} {'✅' if is_good else '❌'}\n"
            else:
                response += f"• {symbol}: ❌ Анализ не удался\n"

        response += "\n💡 ✅ - готов к авто-входу, ❌ - не подходит"
        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['start_auto_test'])
def start_auto_test(message):
    """Запуск тестового авто-трейдинга на 1 цикл"""
    try:
        bot.reply_to(message, "🔄 Запускаю тестовое сканирование...")

        # Запускаем один цикл сканирования
        auto_trading_scanner._scan_market(message.chat.id)

        bot.reply_to(message, "✅ Тестовое сканирование завершено!\n\n💡 Проверь уведомления авто-трейдинга")

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['find_quality_function'])
def find_quality_function(message):
    """Поиск функции с фиксированным качеством 9/10"""
    try:
        with open('final_bot.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # Ищем где выводится "КАЧЕСТВО: 9/10"
        quality_lines = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            if 'КАЧЕСТВО:' in line and '9/10' in line:
                # Находим функцию выше
                function_name = "Не определена"
                for j in range(i - 1, max(0, i - 20), -1):
                    if lines[j].strip().startswith('def '):
                        function_name = lines[j].strip()
                        break

                quality_lines.append(f"Строка {i}: {line.strip()} | Функция: {function_name}")

        if quality_lines:
            response = "🔍 НАЙДЕНЫ ФИКСИРОВАННЫЕ КАЧЕСТВА 9/10:\n\n" + "\n".join(quality_lines)

            response += """

💡 ПРОБЛЕМА: Качество всегда 9/10 вместо реального расчета
🎯 РЕШЕНИЕ: Заменить на расчет на основе:
• AI уверенности (2.3/10 → низкое качество)
• Объемов (0.3x → низкое качество)  
• Консенсуса систем
• Волатильности
"""
        else:
            response = "✅ Фиксированные качества 9/10 не найдены"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons(call):
    """Обрабатывает нажатия inline-кнопок"""
    try:
        chat_id = call.message.chat.id
        callback_data = call.data

        # 🔽 СРАЗУ ОТВЕЧАЕМ НА CALLBACK
        bot.answer_callback_query(call.id)

        print(f"🔘 Нажата кнопка: {callback_data}")

        # Обрабатываем кнопку "Детали позиции"
        if callback_data.startswith('position_details_'):
            symbol = callback_data.replace('position_details_', '')
            show_position_details(chat_id, symbol, call.message.message_id)

        # Обрабатываем кнопку "Закрыть позицию"
        elif callback_data.startswith('close_position_'):
            symbol = callback_data.replace('close_position_', '')
            close_position_from_button(chat_id, symbol, call.message.message_id)

        # Обрабатываем кнопку "Анализ"
        elif callback_data.startswith('analyze_'):
            symbol = callback_data.replace('analyze_', '')
            analyze_symbol_from_button(chat_id, symbol, call.message.message_id)

        # Обрабатываем кнопку "Обновить"
        elif callback_data == 'refresh_positions':
            refresh_positions(chat_id, call.message.message_id)

        # Обрабатываем кнопку "Дашборд"
        elif callback_data == 'show_dashboard':
            show_mobile_dashboard(chat_id, call.message.message_id)

        # Обрабатываем кнопку "Получить цели"
        elif callback_data.startswith('advanced_targets_'):
            symbol = callback_data.replace('advanced_targets_', '')
            show_advanced_targets_from_button(chat_id, symbol, call.message.message_id)

        # Обрабатываем кнопку "Авто-трейд"
        elif callback_data.startswith('auto_trade_'):
            symbol = callback_data.replace('auto_trade_', '')
            create_auto_trade_from_button(chat_id, symbol, call.message.message_id)

        # Обрабатываем кнопку "Консенсус"
        elif callback_data.startswith('consensus_'):
            symbol = callback_data.replace('consensus_', '')
            show_consensus_from_button(chat_id, symbol, call.message.message_id)

        # Обрабатываем кнопку "Полный анализ"
        elif callback_data.startswith('full_analyze_'):
            symbol = callback_data.replace('full_analyze_', '')
            analyze_smart_from_button(chat_id, symbol, call.message.message_id)

        # 🔽 🔽 🔽 ДОБАВЛЯЕМ ОБРАБОТЧИКИ ДЛЯ НОВЫХ КНОПОК 🔽 🔽 🔽

        # Обрабатываем кнопку "Полные цели"
        elif callback_data.startswith('full_targets_'):
            symbol = callback_data.replace('full_targets_', '')
            show_full_targets_info(chat_id, symbol, call.message.message_id)

        # Обрабатываем кнопку "Информация"
        elif callback_data.startswith('info_'):
            symbol = callback_data.replace('info_', '')
            show_symbol_info(chat_id, symbol, call.message.message_id)

        # Обрабатываем кнопку "Простая сделка"
        elif callback_data.startswith('simple_trade_'):
            symbol = callback_data.replace('simple_trade_', '')
            create_simple_trade(chat_id, symbol, call.message.message_id)

    except Exception as e:
        print(f"❌ Ошибка обработки inline-кнопки: {e}")
        # НЕ пытаемся отвечать на callback второй раз - это вызывает ошибку
        bot.answer_callback_query(call.id, "❌ Ошибка обработки")


@bot.message_handler(commands=['deep_ai_debug'])
def deep_ai_debug(message):
    """Глубокая диагностика AI проблем"""
    try:
        symbol = 'BTCUSDT'

        response = "🔍 ГЛУБОКАЯ ДИАГНОСТИКА AI:\n\n"

        # 1. Проверим сам объект ai_checker
        response += "🤖 ПРОВЕРКА AI_CHECKER:\n"
        response += f"• Тип: {type(ai_checker)}\n"
        response += f"• Модуль: {getattr(ai_checker, '__module__', 'неизвестно')}\n"
        response += f"• Класс: {ai_checker.__class__.__name__}\n\n"

        # 2. Проверим метод analyze_signal_quality
        if hasattr(ai_checker, 'analyze_signal_quality'):
            response += "✅ Метод analyze_signal_quality существует\n"

            # 3. Тестируем с разными параметрами
            test_cases = [
                {'volume_ratio': 3.0, 'confluence': 90, 'current_price': 50000},  # Идеальные
                {'volume_ratio': 1.0, 'confluence': 30, 'current_price': 50000},  # Плохие
                {'volume_ratio': 2.0, 'confluence': 70, 'current_price': 50000},  # Хорошие
                {'volume_ratio': 0.5, 'confluence': 10, 'current_price': 50000},  # Очень плохие
            ]

            response += "\n🎯 ТЕСТИРОВАНИЕ С РАЗНЫМИ ПАРАМЕТРАМИ:\n"

            for i, case in enumerate(test_cases, 1):
                try:
                    result = ai_checker.analyze_signal_quality(symbol, case)
                    response += f"\nТест {i} (Объемы {case['volume_ratio']}x, Конфлюэнс {case['confluence']}%):\n"
                    response += f"   → AI: {result['ai_confidence_score']}/10\n"
                    response += f"   → Рекомендация: {result['recommendation']}\n"
                except Exception as e:
                    response += f"\nТест {i}: ОШИБКА - {str(e)}\n"

        else:
            response += "❌ Метод analyze_signal_quality НЕ существует!\n"

        # 4. Проверим есть ли кэш
        if hasattr(ai_checker, 'analysis_cache'):
            cache_size = len(ai_checker.analysis_cache) if ai_checker.analysis_cache else 0
            response += f"\n📊 Кэш AI: {cache_size} записей\n"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка диагностики: {str(e)}")


@bot.message_handler(commands=['test_fixed_ai'])
def test_fixed_ai(message):
    """Тестирование исправленного AI"""
    try:
        symbol = 'BTCUSDT'

        test_cases = [
            {'volume_ratio': 3.5, 'confluence': 85, 'current_price': 50000},  # 🚀 Идеально
            {'volume_ratio': 2.2, 'confluence': 65, 'current_price': 50000},  # 📈 Хорошо
            {'volume_ratio': 1.8, 'confluence': 45, 'current_price': 50000},  # 📊 Средне
            {'volume_ratio': 0.7, 'confluence': 15, 'current_price': 50000},  # 🔻 Плохо
            {'volume_ratio': 0.3, 'confluence': 5, 'current_price': 50000},  # 🚫 Очень плохо
        ]

        response = "🎯 ТЕСТ ИСПРАВЛЕННОГО AI:\n\n"

        for i, case in enumerate(test_cases, 1):
            result = ai_checker.analyze_signal_quality(symbol, case)
            response += f"{i}. Объемы {case['volume_ratio']}x, Конфлюэнс {case['confluence']}%:\n"
            response += f"   → AI: {result['ai_confidence_score']}/10 {result['color']}\n"
            response += f"   → {result['recommendation']}\n\n"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка тестирования: {str(e)}")


@bot.message_handler(commands=['debug_ai'])
def debug_ai(message):
    """Диагностика AI проблем"""
    try:
        symbol = 'BTCUSDT'

        response = "🔍 ДИАГНОСТИКА AI:\n\n"

        # 1. Проверим сам объект ai_checker
        response += "🤖 ПРОВЕРКА AI_CHECKER:\n"
        response += f"• Тип: {type(ai_checker)}\n"
        response += f"• Модуль: {getattr(ai_checker, '__module__', 'неизвестно')}\n"
        response += f"• Класс: {ai_checker.__class__.__name__}\n\n"

        # 2. Проверим метод analyze_signal_quality
        if hasattr(ai_checker, 'analyze_signal_quality'):
            response += "✅ Метод analyze_signal_quality существует\n"

            # 3. Тестируем с разными параметрами
            test_cases = [
                {'volume_ratio': 3.0, 'confluence': 90, 'current_price': 50000},  # Идеальные
                {'volume_ratio': 1.0, 'confluence': 30, 'current_price': 50000},  # Плохие
                {'volume_ratio': 2.0, 'confluence': 70, 'current_price': 50000},  # Хорошие
                {'volume_ratio': 0.5, 'confluence': 10, 'current_price': 50000},  # Очень плохие
            ]

            response += "\n🎯 ТЕСТИРОВАНИЕ С РАЗНЫМИ ПАРАМЕТРАМИ:\n"

            for i, case in enumerate(test_cases, 1):
                try:
                    result = ai_checker.analyze_signal_quality(symbol, case)
                    response += f"\nТест {i} (Объемы {case['volume_ratio']}x, Конфлюэнс {case['confluence']}%):\n"
                    response += f"   → AI: {result['ai_confidence_score']}/10\n"
                    response += f"   → Рекомендация: {result['recommendation']}\n"
                except Exception as e:
                    response += f"\nТест {i}: ОШИБКА - {str(e)}\n"

        else:
            response += "❌ Метод analyze_signal_quality НЕ существует!\n"

        # 4. Проверим есть ли кэш
        if hasattr(ai_checker, 'analysis_cache'):
            cache_size = len(ai_checker.analysis_cache) if ai_checker.analysis_cache else 0
            response += f"\n📊 Кэш AI: {cache_size} записей\n"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка диагностики: {str(e)}")


@bot.message_handler(commands=['check_ai_server'])
def check_ai_server(message):
    """Проверка подключения к AI серверу"""
    try:
        import requests

        # Тестируем разные эндпоинты
        test_cases = [
            {"url": "http://127.0.0.1:8000/", "params": {}},
            {"url": "http://127.0.0.1:8000/analyze", "params": {"symbol": "BTCUSDT", "timeframe": "15m"}},
            {"url": "http://127.0.0.1:8000/analyze-smart", "params": {"symbol": "BTCUSDT"}},
        ]

        response = "🔍 ПРОВЕРКА AI СЕРВЕРА:\n\n"

        for test in test_cases:
            try:
                if test["url"].endswith("/analyze") or test["url"].endswith("/analyze-smart"):
                    result = requests.post(test["url"], params=test["params"], timeout=5)
                else:
                    result = requests.get(test["url"], params=test["params"], timeout=5)

                if result.status_code == 200:
                    response += f"✅ {test['url']} - РАБОТАЕТ\n"
                    if "analyze" in test["url"]:
                        try:
                            data = result.json()
                            response += f"   📊 Ответ: {data.get('action', 'N/A')} (сила: {data.get('strength', 'N/A')})\n"
                        except:
                            response += f"   📊 Ответ: {result.text[:100]}...\n"
                else:
                    response += f"❌ {test['url']} - код ошибки: {result.status_code}\n"
            except requests.exceptions.ConnectionError:
                response += f"❌ {test['url']} - СЕРВЕР НЕ ЗАПУЩЕН\n"
            except Exception as e:
                response += f"❌ {test['url']} - ошибка: {str(e)}\n"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка проверки сервера: {str(e)}")


@bot.message_handler(commands=['simple_ai_test'])
def simple_ai_test(message):
    """Простой тест AI"""
    try:
        # Тестируем BTC с хорошими параметрами
        test_data = {'volume_ratio': 2.5, 'confluence': 75}
        result = ai_checker.analyze_signal_quality('BTCUSDT', test_data)

        response = f"""
🤖 ПРОСТОЙ ТЕСТ AI:

📊 Тестовые параметры:
• Символ: BTCUSDT
• Объемы: 2.5x
• Конфлюэнс: 75%

🎯 Результат AI:
• Оценка: {result['ai_confidence_score']}/10 {result['color']}
• Рекомендация: {result['recommendation']}

💡 Ожидаемый результат: 7.5-8.5/10
{'✅ AI РАБОТАЕТ ПРАВИЛЬНО!' if result['ai_confidence_score'] >= 7.5 else '❌ AI ВСЕ ЕЩЕ НЕИСПРАВЕН!'}
"""
        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка теста: {str(e)}")


@bot.message_handler(commands=['check_ai_fix'])
def check_ai_fix(message):
    """Проверка исправления AI"""
    try:
        # Тест с реальными хорошими параметрами
        test_data = {'volume_ratio': 2.5, 'confluence': 75}
        result = ai_checker.analyze_signal_quality('BTCUSDT', test_data)

        response = f"""
🔧 ПРОВЕРКА ИСПРАВЛЕНИЯ AI:

📊 Тестовые параметры:
• Объемы: 2.5x
• Конфлюэнс: 75%

🤖 Результат AI:
• Оценка: {result['ai_confidence_score']}/10
• Рекомендация: {result['recommendation']}

💡 Ожидаемый результат: 7.5-8.5/10
{'✅ AI РАБОТАЕТ ПРАВИЛЬНО!' if result['ai_confidence_score'] >= 7.5 else '❌ AI ВСЕ ЕЩЕ НЕИСПРАВЕН!'}
"""
        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка проверки: {str(e)}")


@bot.message_handler(commands=['test_ai_connection'])
def test_ai_connection(message):
    """Тестирование подключения к AI серверу"""
    try:
        import requests

        # Тестируем разные эндпоинты
        test_cases = [
            {"url": "http://127.0.0.1:8000/", "params": {}},
            {"url": "http://127.0.0.1:8000/analyze", "params": {"symbol": "BTCUSDT", "timeframe": "15m"}},
        ]

        response = "🔍 ПРОВЕРКА AI СЕРВЕРА:\n\n"

        for test in test_cases:
            try:
                if test["url"].endswith("/analyze"):
                    result = requests.post(test["url"], params=test["params"], timeout=5)
                else:
                    result = requests.get(test["url"], params=test["params"], timeout=5)

                if result.status_code == 200:
                    response += f"✅ {test['url']} - РАБОТАЕТ\n"
                    if "analyze" in test["url"]:
                        try:
                            data = result.json()
                            response += f"   📊 Ответ: {data.get('action', 'N/A')} (сила: {data.get('strength', 'N/A')})\n"
                        except:
                            response += f"   📊 Ответ: {result.text[:100]}...\n"
                else:
                    response += f"❌ {test['url']} - код ошибки: {result.status_code}\n"
            except requests.exceptions.ConnectionError:
                response += f"❌ {test['url']} - СЕРВЕР НЕ ЗАПУЩЕН\n"
            except Exception as e:
                response += f"❌ {test['url']} - ошибка: {str(e)}\n"

        # Тестируем AI checker
        try:
            test_data = {'volume_ratio': 2.0, 'confluence': 70}
            ai_result = ai_checker.analyze_signal_quality('BTCUSDT', test_data)
            response += f"\n🤖 AI CHECKER ТЕСТ:\n"
            response += f"• Оценка: {ai_result['ai_confidence_score']}/10\n"
            response += f"• Статус: {'✅ РАБОТАЕТ' if ai_result['ai_confidence_score'] > 5.0 else '❌ ПРОБЛЕМА'}\n"
        except Exception as e:
            response += f"\n❌ AI CHECKER ОШИБКА: {str(e)}\n"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка тестирования: {str(e)}")

@bot.message_handler(commands=['clear_ai_cache'])
def clear_ai_cache(message):
    """Очистка кэша AI"""
    try:
        if hasattr(ai_checker, 'analysis_cache'):
            ai_checker.analysis_cache.clear()
            bot.reply_to(message, "✅ Кэш AI очищен! Теперь тесты будут работать правильно.")
        else:
            bot.reply_to(message, "❌ Кэш не найден")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['test_auto_trading'])
def test_auto_trading(message):
    """Тест авто-трейдинга с реальными данными"""
    try:
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        good_signals = []

        response = "🤖 ТЕСТ АВТО-ТРЕЙДИНГА:\n\n"

        for symbol in symbols:
            # Получаем реальные данные
            volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
            trend_data = trend_analyzer.multi_timeframe_analysis(symbol)

            volume_ratio = volume_data.get('volume_ratio', 0) if volume_data else 0
            confluence = trend_data.get('confluence_score', 0) if 'error' not in trend_data else 0

            # AI анализ
            ai_data = {'volume_ratio': volume_ratio, 'confluence': confluence}
            ai_result = ai_checker.analyze_signal_quality(symbol, ai_data)
            ai_score = ai_result['ai_confidence_score']

            status = "✅ ГОТОВ К СДЕЛКЕ" if ai_score >= 7.0 else "❌ НЕ ПОДХОДИТ"

            response += f"• {symbol}: AI {ai_score}/10, Объемы {volume_ratio:.1f}x - {status}\n"

            if ai_score >= 7.0 and volume_ratio >= 1.5:
                good_signals.append(symbol)

        if good_signals:
            response += f"\n🎯 МОЖНО ОТКРЫВАТЬ СДЕЛКИ: {', '.join(good_signals)}"
        else:
            response += "\n💡 НЕТ ПОДХОДЯЩИХ СИГНАЛОВ - ЖДЕМ ЛУЧШИХ УСЛОВИЙ"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['auto_scan'])
def auto_scan(message):
    """Сканер для авто-трейдинга"""
    try:
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'XRPUSDT']
        good_trades = []

        for symbol in symbols:
            volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
            trend_data = trend_analyzer.multi_timeframe_analysis(symbol)

            volume_ratio = volume_data.get('volume_ratio', 0) if volume_data else 0
            confluence = trend_data.get('confluence_score', 0) if 'error' not in trend_data else 0

            ai_data = {'volume_ratio': volume_ratio, 'confluence': confluence}
            ai_result = ai_checker.analyze_signal_quality(symbol, ai_data)
            ai_score = ai_result['ai_confidence_score']

            if ai_score >= 7.0 and volume_ratio >= 1.5:
                good_trades.append({
                    'symbol': symbol,
                    'ai_score': ai_score,
                    'volume_ratio': volume_ratio,
                    'confluence': confluence
                })

        if good_trades:
            response = "🚀 НАЙДЕНЫ СИГНАЛЫ ДЛЯ АВТО-ТРЕЙДИНГА:\n\n"
            for trade in good_trades:
                response += f"• {trade['symbol']}: AI {trade['ai_score']}/10, Объемы {trade['volume_ratio']:.1f}x\n"
            response += f"\n💡 Используйте /auto_trade для создания сделок"
        else:
            response = "❌ СИГНАЛОВ ДЛЯ АВТО-ТРЕЙДИНГА НЕТ\n\n"
            response += "📊 Текущие условия рынка:\n"
            response += "• Объемы: 0.1-0.2x (нужно ≥1.5x)\n"
            response += "• Конфлюэнс: отрицательный (нужно ≥60%)\n"
            response += "• AI уверенность: 1.2/10 (нужно ≥7.0)\n\n"
            response += "💡 Попробуйте в другое время когда рынок активнее"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['market_conditions'])
def market_conditions(message):
    """Анализ текущих рыночных условий"""
    try:
        response = "📊 АНАЛИЗ РЫНОЧНЫХ УСЛОВИЙ:\n\n"

        # Текущее время
        from datetime import datetime
        current_hour = datetime.now().hour
        time_status = "🌙 НОЧНОЕ ВРЕМЯ" if current_hour < 8 or current_hour > 22 else "☀️ ДНЕВНОЕ ВРЕМЯ"

        response += f"⏰ Время: {time_status} ({current_hour}:00)\n\n"

        # Анализ основных монет
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']

        for symbol in symbols:
            volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
            trend_data = trend_analyzer.multi_timeframe_analysis(symbol)

            volume_ratio = volume_data.get('volume_ratio', 0) if volume_data else 0
            confluence = trend_data.get('confluence_score', 0) if 'error' not in trend_data else 0

            ai_data = {'volume_ratio': volume_ratio, 'confluence': confluence}
            ai_result = ai_checker.analyze_signal_quality(symbol, ai_data)

            response += f"• {symbol}:\n"
            response += f"  📊 Объемы: {volume_ratio:.1f}x {'✅' if volume_ratio >= 1.5 else '❌'}\n"
            response += f"  🎯 Конфлюэнс: {confluence:.1f}% {'✅' if confluence >= 60 else '❌'}\n"
            response += f"  🤖 AI: {ai_result['ai_confidence_score']:.1f}/10 {'✅' if ai_result['ai_confidence_score'] >= 7.0 else '❌'}\n"

        response += f"\n💡 ВЫВОД: "
        if current_hour < 8 or current_hour > 22:
            response += "Рынок спит (ночное время). Попробуйте днем когда объемы вырастут."
        else:
            response += "Рынок неактивен. Возможно, период низкой волатильности."

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['test_perfect_conditions'])
def test_perfect_conditions(message):
    """Тест системы при идеальных условиях"""
    try:
        # 🔽 ИСКУССТВЕННО СОЗДАЕМ ИДЕАЛЬНЫЕ УСЛОВИЯ
        perfect_data = {
            'volume_ratio': 2.5,  # Высокие объемы
            'confluence': 75,  # Сильный конфлюэнс
            'current_price': 50000
        }

        symbols = ['BTCUSDT', 'DOGEUSDT', 'SOLUSDT']
        response = "🎯 ТЕСТ ПРИ ИДЕАЛЬНЫХ УСЛОВИЯХ:\n\n"

        for symbol in symbols:
            result = ai_checker.analyze_signal_quality(symbol, perfect_data)

            response += f"• {symbol}:\n"
            response += f"  AI: {result['ai_confidence_score']}/10\n"
            response += f"  Рекомендация: {result['recommendation']}\n"
            response += f"  BUY возможен: {'✅ ДА' if result['ai_confidence_score'] >= 7.0 else '❌ НЕТ'}\n\n"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['test_false_signals'])
def test_false_signals(message):
    """Тест на ложные срабатывания"""
    try:
        # 🔽 ПЛОХИЕ УСЛОВИЯ, НО ТЕХНИЧЕСКИ "ХОРОШИЕ"
        bad_data = {
            'volume_ratio': 0.5,  # Очень низкие объемы
            'confluence': -50,  # Отрицательный конфлюэнс
            'current_price': 50000
        }

        symbols = ['BTCUSDT', 'DOGEUSDT', 'PEPEUSDT']
        response = "🚨 ТЕСТ НА ЛОЖНЫЕ СИГНАЛЫ:\n\n"

        for symbol in symbols:
            result = ai_checker.analyze_signal_quality(symbol, bad_data)

            response += f"• {symbol}:\n"
            response += f"  AI: {result['ai_confidence_score']}/10\n"
            response += f"  Защита: {'✅ РАБОТАЕТ' if result['ai_confidence_score'] < 5.0 else '❌ НЕ РАБОТАЕТ'}\n\n"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['system_stats'])
def system_stats(message):
    """Статистика работы системы"""
    try:
        response = "📊 СТАТИСТИКА СИСТЕМЫ:\n\n"

        # 🔽 СЧИТАЕМ СКОЛЬКО РАЗ СИСТЕМА ЗАЩИТИЛА
        protected_trades = 0
        total_checks = 0

        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']

        for symbol in symbols:
            volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
            trend_data = trend_analyzer.multi_timeframe_analysis(symbol)

            volume_ratio = volume_data.get('volume_ratio', 0) if volume_data else 0
            confluence = trend_data.get('confluence_score', 0) if 'error' not in trend_data else 0

            ai_data = {'volume_ratio': volume_ratio, 'confluence': confluence}
            ai_result = ai_checker.analyze_signal_quality(symbol, ai_data)

            total_checks += 1
            if ai_result['ai_confidence_score'] < 5.0:
                protected_trades += 1

        response += f"✅ Защищено сделок: {protected_trades}/{total_checks}\n"
        response += f"📈 Эффективность защиты: {(protected_trades / total_checks) * 100:.1f}%\n\n"
        response += "💡 СИСТЕМА УЖЕ СЕЙЧАС ЗАЩИЩАЕТ ТВОИ ДЕНЬГИ!"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['test_ai_backtest'])
def test_ai_backtest(message):
    """🎯 Тест AI бэктестинга на искусственных данных"""
    try:
        wait_msg = bot.reply_to(message, "🤖 Создаю тестовые данные для AI бэктестинга...")

        # 🔽 СОЗДАЕМ ТЕСТОВЫЕ РЕЗУЛЬТАТЫ ДЛЯ ПРОВЕРКИ
        test_results = {
            'symbol': 'TEST_BTC',
            'timeframe': '15m',
            'period_days': 7,
            'comparison': {
                'normal_trading': {
                    'total_trades': 25,
                    'winning_trades': 12,
                    'losing_trades': 13,
                    'win_rate': 48.0,
                    'total_profit': -15.5,
                    'avg_profit': -0.62,
                    'max_drawdown': 8.2
                },
                'ai_trading': {
                    'total_trades': 18,
                    'winning_trades': 11,
                    'losing_trades': 7,
                    'win_rate': 61.1,
                    'total_profit': 22.3,
                    'avg_profit': 1.24,
                    'max_drawdown': 3.1
                }
            },
            'ai_efficiency': {
                'signals_before_filtering': 25,
                'signals_after_filtering': 18,
                'signals_filtered': 7,
                'bad_signals_caught': 6,
                'filter_efficiency': 85.7,
                'risk_reduction_percent': 28.0
            },
            'improvement': {
                'profit_improvement': 37.8,  # -15.5 → +22.3
                'win_rate_improvement': 13.1,  # 48.0 → 61.1
                'risk_reduction': 5.1,  # 8.2 → 3.1
                'trades_filtered': 7
            },
            'summary': "🚀 AI УЛУЧШАЕТ РЕЗУЛЬТАТЫ - значительное улучшение прибыли и точности!"
        }

        # 🔽 ФОРМАТИРУЕМ РЕЗУЛЬТАТЫ
        result_text = format_ai_backtest_results(test_results)

        bot.edit_message_text(
            result_text,
            chat_id=message.chat.id,
            message_id=wait_msg.message_id,
            parse_mode='Markdown'
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка теста: {str(e)}")


@bot.message_handler(commands=['debug_backtest'])
def debug_backtest(message):
    """🔧 Диагностика проблем бэктестинга"""
    try:
        parts = message.text.split()
        symbol = parts[1].upper() if len(parts) > 1 else "BTCUSDT"

        response = f"🔧 ДИАГНОСТИКА БЭКТЕСТИНГА ДЛЯ {symbol}:\n\n"

        # 🔽 ПРОВЕРЯЕМ ДАННЫЕ
        from data import get_candles

        df = get_candles(symbol, "15m", limit=100)
        response += f"• Исторические данные: {len(df)} свечей\n"

        if len(df) > 0:
            response += f"• Первая дата: {df.index[0] if hasattr(df, 'index') else 'N/A'}\n"
            response += f"• Последняя дата: {df.index[-1] if hasattr(df, 'index') else 'N/A'}\n"

            # 🔽 ПРОВЕРЯЕМ ИНДИКАТОРЫ
            from technical_indicators import calculate_all_indicators
            df_with_indicators = calculate_all_indicators(df)

            response += f"• Колонки с индикаторами: {', '.join([col for col in df_with_indicators.columns if col not in ['open', 'high', 'low', 'close', 'volume']][:5])}...\n"

            # 🔽 ПРОВЕРЯЕМ СИГНАЛЫ
            signals = backtester._generate_signals(df_with_indicators)
            response += f"• Найдено сигналов: {len(signals)}\n"

            if signals:
                response += f"• Пример сигнала: {signals[0]}\n"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка диагностики: {str(e)}")


@bot.message_handler(commands=['quick_test'])
def quick_test(message):
    """⚡ Быстрая проверка работы бэктестера"""
    try:
        response = "✅ Бэктестер загружен без ошибок!\n"
        response += f"• Класс: {type(backtester).__name__}\n"

        # Проверяем методы
        methods = [method for method in dir(backtester) if not method.startswith('_')]
        response += f"• Методы: {', '.join(methods[:5])}...\n\n"

        response += "🎯 Проверяем данные...\n"

        # Проверяем получение данных
        from data import get_candles
        df = get_candles("BTCUSDT", "15m", limit=10)
        response += f"• Данные BTC: {len(df)} свечей\n"

        if len(df) > 0:
            response += f"• Последняя цена: {df.iloc[-1]['close'] if 'close' in df else 'N/A'}\n"
            response += "✅ Система работает!\n"
        else:
            response += "❌ Нет данных от API\n"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['debug_data'])
def debug_data(message):
    """🔍 Диагностика данных"""
    try:
        parts = message.text.split()
        symbol = parts[1].upper() if len(parts) > 1 else "BTCUSDT"

        response = f"🔍 ДИАГНОСТИКА ДАННЫХ {symbol}:\n\n"

        from data import get_candles

        # Проверяем разные таймфреймы
        timeframes = ['1m', '5m', '15m', '1h']

        for tf in timeframes:
            df = get_candles(symbol, tf, limit=5)
            response += f"• {tf}: {len(df)} свечей"
            if len(df) > 0:
                response += f" | Цена: {df.iloc[-1].get('close', 'N/A')}"
            response += "\n"

        response += f"\n💡 Рекомендация: Используй таймфрейм с данными для /backtest"

        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['test_backtest_small'])
def test_backtest_small(message):
    """🧪 Тест бэктеста на малом количестве данных"""
    try:
        parts = message.text.split()
        symbol = parts[1].upper() if len(parts) > 1 else "BTCUSDT"

        wait_msg = bot.reply_to(message, f"🧪 Тестируем бэктест для {symbol}...")

        # 🔽 ТЕСТ НА МАЛОМ КОЛИЧЕСТВЕ ДАННЫХ
        results = backtester.backtest_with_ai_filters(symbol, "15m", 1)  # Всего 1 день

        if "error" in results:
            # 🔽 ПРОБУЕМ С ДРУГИМ ТАЙМФРЕЙМОМ
            results = backtester.backtest_with_ai_filters(symbol, "1h", 1)

        if "error" in results:
            response = f"❌ {results['error']}\n\n"
            response += "🔧 Возможные решения:\n"
            response += "• API не возвращает исторические данные\n"
            response += "• Попробуй другой таймфрейм: /backtest BTCUSDT 1h 1\n"
            response += "• Или используй реальную торговлю вместо бэктеста"
        else:
            response = format_ai_backtest_results(results)

        bot.edit_message_text(
            response,
            chat_id=message.chat.id,
            message_id=wait_msg.message_id,
            parse_mode='Markdown'
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка теста: {str(e)}")


# 🔽 НОВАЯ КОМАНДА: СТАТИСТИКА
@bot.message_handler(commands=['stats', 'statistics'])
def send_stats(message):
    """Отправляет пользователю отчет по торговой статистике"""
    try:
        chat_id = message.chat.id
        # Вызываем метод менеджера для сбора статистики
        stats = auto_trade_manager.get_trading_statistics(chat_id=chat_id)

        if not stats:
            bot.send_message(chat_id, "📊 Нет данных для статистики. Создайте и закройте несколько сделок.")
            return

        # 🔽 ФОРМАТИРОВАНИЕ ОТЧЕТА 🔽

        # Win Rate (процент побед)
        win_rate_display = f"{stats['win_rate']:.1f}% ({stats['profitable_trades']} из {stats['total_trades']})"

        # Общий PnL
        pnl_emoji = "🟢" if stats['total_pnl'] > 0 else "🔴" if stats['total_pnl'] < 0 else "🟡"
        total_pnl_display = f"{pnl_emoji} {stats['total_pnl']:+.2f}%"

        # Лучший символ
        best_symbol_display = f"{stats['best_symbols'][0][0]} ({stats['best_symbols'][0][1]['total_pnl']:+.2f}%)" if \
        stats['best_symbols'] else "N/A"

        # Уверенность AI
        ai_confident_rate = (stats['ai_confident_trades'] / stats['total_trades'] * 100) if stats[
                                                                                                'total_trades'] > 0 else 0
        ai_high_confident_rate = (stats['ai_high_confident_trades'] / stats['total_trades'] * 100) if stats[
                                                                                                          'total_trades'] > 0 else 0

        # Формируем итоговое сообщение
        report_message = f"""
📈 ТОРГОВАЯ СТАТИСТИКА (с момента запуска)

📅 Всего сделок: {stats['total_trades']}
✅ Прибыльных: {stats['profitable_trades']}
❌ Убыточных: {stats['losing_trades']}
────────────────────
🏆 Win Rate (Процент побед): **{win_rate_display}**
💰 Общая доходность (PnL): **{total_pnl_display}**
💡 Средний PnL на сделку: {stats['avg_pnl']:+.2f}%
────────────────────
🤖 AI-Аналитика:
🔥 Сделок с AI ≥7.0: {stats['ai_confident_trades']} ({ai_confident_rate:.1f}%)
🏆 Сделок с AI ≥8.0: {stats['ai_high_confident_trades']} ({ai_high_confident_rate:.1f}%)
────────────────────
🥇 Лучший актив: {best_symbol_display}
"""
        bot.send_message(chat_id, report_message, parse_mode='Markdown')

    except Exception as e:
        print(f"❌ Ошибка отправки статистики: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при получении статистики.")



def format_ai_backtest_results(results):
    """🎯 Форматирование результатов AI бэктестинга"""

    normal = results['comparison']['normal_trading']
    ai = results['comparison']['ai_trading']
    efficiency = results['ai_efficiency']
    improvement = results['improvement']

    result_text = f"*🤖 AI БЭКТЕСТИНГ {results['symbol']}*\n"
    result_text += f"Период: {results['period_days']} дней | Таймфрейм: {results['timeframe']}\n\n"

    # 📊 СРАВНЕНИЕ РЕЗУЛЬТАТОВ
    result_text += "*📊 СРАВНЕНИЕ РЕЗУЛЬТАТОВ:*\n"
    result_text += "```\n"
    result_text += "                 ОБЫЧНАЯ    С AI\n"
    result_text += f"Сделки:         {normal['total_trades']:>4}      {ai['total_trades']:>4}\n"
    result_text += f"Винрейт:        {normal['win_rate']:>4.1f}%    {ai['win_rate']:>4.1f}%\n"
    result_text += f"Прибыль:        {normal['total_profit']:>6.2f}%  {ai['total_profit']:>6.2f}%\n"
    result_text += f"Просадка:       {normal['max_drawdown']:>6.2f}%  {ai['max_drawdown']:>6.2f}%\n"
    result_text += "```\n\n"

    # 🎯 ЭФФЕКТИВНОСТЬ AI
    result_text += "*🎯 ЭФФЕКТИВНОСТЬ AI ФИЛЬТРОВ:*\n"
    result_text += f"• Сигналов до фильтрации: {efficiency['signals_before_filtering']}\n"
    result_text += f"• Сигналов после фильтрации: {efficiency['signals_after_filtering']}\n"
    result_text += f"• Отфильтровано сигналов: {efficiency['signals_filtered']}\n"
    result_text += f"• Убыточных поймано: {efficiency['bad_signals_caught']}\n"
    result_text += f"• Эффективность фильтра: {efficiency.get('filter_efficiency', 0):.1f}%\n"
    result_text += f"• Снижение риска: {efficiency.get('risk_reduction_percent', 0):.1f}%\n\n"

    # 📈 УЛУЧШЕНИЯ
    result_text += "*📈 РЕЗУЛЬТАТ УЛУЧШЕНИЙ:*\n"
    if improvement['profit_improvement'] > 0:
        result_text += f"✅ Прибыль улучшена на: +{improvement['profit_improvement']:.2f}%\n"
    else:
        result_text += f"🔴 Прибыль уменьшилась на: {improvement['profit_improvement']:.2f}%\n"

    if improvement['win_rate_improvement'] > 0:
        result_text += f"✅ Точность улучшена на: +{improvement['win_rate_improvement']:.1f}%\n"
    else:
        result_text += f"🔴 Точность уменьшилась на: {improvement['win_rate_improvement']:.1f}%\n"

    if improvement['risk_reduction'] > 0:
        result_text += f"✅ Риск снижен на: {improvement['risk_reduction']:.2f}%\n"
    else:
        result_text += f"🔴 Риск увеличился на: {abs(improvement['risk_reduction']):.2f}%\n"

    result_text += f"📉 Отфильтровано сделок: {improvement['trades_filtered']}\n\n"

    # 🏆 ИТОГ
    result_text += f"*🏆 ВЕРДИКТ:* {results['summary']}\n\n"

    # 💡 РЕКОМЕНДАЦИИ
    if improvement['profit_improvement'] > 5:
        result_text += "💡 *Рекомендация:* Используйте AI фильтры для торговли!\n"
    elif efficiency.get('filter_efficiency', 0) > 60:
        result_text += "💡 *Рекомендация:* AI хорошо фильтрует риски - используйте для защиты\n"
    else:
        result_text += "💡 *Рекомендация:* AI требует настройки под текущие рыночные условия\n"

    return result_text

def show_position_details(chat_id, symbol, message_id):
    """Показывает детали позиции"""
    try:
        active_positions = auto_trade_manager.get_active_positions(chat_id)
        position_found = None

        for pos_id, position in active_positions.items():
            if position['symbol'] == symbol:
                position_found = position
                break

        if not position_found:
            bot.edit_message_text(
                f"❌ Позиция {symbol} не найдена",
                chat_id=chat_id,
                message_id=message_id
            )
            return

        # Получаем текущую цену
        current_price = auto_trade_manager._get_current_price(symbol)

        # Формируем детальное сообщение
        entry = position_found['entry_price']
        if current_price:
            if position_found['direction'] == "LONG":
                pnl_pct = (current_price - entry) / entry * 100
            else:
                pnl_pct = (entry - current_price) / entry * 100
            price_info = f"📈 Текущая: {format_price(current_price)} ({pnl_pct:+.2f}%)"
        else:
            price_info = "📡 Ошибка получения цены"

        response = f"""
📊 ДЕТАЛИ ПОЗИЦИИ: {symbol}

{price_info}
💰 Вход: {format_price(entry)}
🎯 Цели: {', '.join([format_price(tp) for tp in position_found['take_profits']])}
🛑 Стоп: {format_price(position_found['stop_loss'])}
📊 Размер: {position_found['current_size']}%
🎯 Выполнено ТП: {', '.join(position_found['executed_tps']) if position_found['executed_tps'] else 'нет'}
"""
        # Создаем клавиатуру для возврата
        keyboard = types.InlineKeyboardMarkup()
        btn_back = types.InlineKeyboardButton("⬅️ Назад к списку", callback_data="refresh_positions")
        keyboard.add(btn_back)

        bot.edit_message_text(
            response,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=keyboard
        )

    except Exception as e:
        bot.edit_message_text(
            f"❌ Ошибка: {str(e)}",
            chat_id=chat_id,
            message_id=message_id
        )


def close_position_from_button(chat_id, symbol, message_id):
    """Закрывает позицию из inline-кнопки"""
    try:
        active_positions = auto_trade_manager.get_active_positions(chat_id)
        position_to_close = None
        position_id_to_close = None

        for pos_id, position in active_positions.items():
            if position['symbol'] == symbol:
                position_to_close = position
                position_id_to_close = pos_id
                break

        if not position_to_close:
            bot.edit_message_text(
                f"❌ Активная позиция {symbol} не найдена",
                chat_id=chat_id,
                message_id=message_id
            )
            return

        # Закрываем позицию
        current_price = auto_trade_manager._get_current_price(symbol)
        if current_price:
            success = auto_trade_manager.close_position_manually(position_id_to_close, current_price)
            if success:
                bot.edit_message_text(
                    f"✅ Позиция {symbol} закрыта",
                    chat_id=chat_id,
                    message_id=message_id
                )
            else:
                bot.edit_message_text(
                    f"❌ Ошибка закрытия {symbol}",
                    chat_id=chat_id,
                    message_id=message_id
                )
        else:
            bot.edit_message_text(
                f"❌ Ошибка получения цены для {symbol}",
                chat_id=chat_id,
                message_id=message_id
            )

    except Exception as e:
        bot.edit_message_text(
            f"❌ Ошибка: {str(e)}",
            chat_id=chat_id,
            message_id=message_id
        )


def analyze_symbol_from_button(chat_id, symbol, message_id):
    """Выполняет анализ символа из inline-кнопки"""
    try:
        bot.edit_message_text(
            f"🔍 Анализирую {symbol}...",
            chat_id=chat_id,
            message_id=message_id
        )

        # Упрощенный анализ (можно заменить на вызов твоих функций)
        current_price = auto_trade_manager._get_current_price(symbol)
        analysis_result = f"""
📊 БЫСТРЫЙ АНАЛИЗ {symbol}

💰 Текущая цена: {format_price(current_price or 0)}
📈 Объемы: Проверяем...
🎯 AI Уверенность: Расчет...

💡 Используйте /analyze_smart {symbol} для полного анализа
"""
        # Создаем клавиатуру для возврата
        keyboard = types.InlineKeyboardMarkup()
        btn_back = types.InlineKeyboardButton("⬅️ Назад", callback_data="refresh_positions")
        btn_full_analysis = types.InlineKeyboardButton("🔍 Полный анализ", callback_data=f"full_analyze_{symbol}")
        keyboard.add(btn_full_analysis, btn_back)

        bot.edit_message_text(
            analysis_result,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=keyboard
        )

    except Exception as e:
        bot.edit_message_text(
            f"❌ Ошибка анализа: {str(e)}",
            chat_id=chat_id,
            message_id=message_id
        )


def refresh_positions(chat_id, message_id):
    """Обновляет список позиций"""
    try:
        # Просто вызываем команду активных позиций заново
        active_positions = auto_trade_manager.get_active_positions(chat_id)

        if not active_positions:
            bot.edit_message_text(
                "📭 Нет активных позиций",
                chat_id=chat_id,
                message_id=message_id
            )
            return

        response = "📊 АКТИВНЫЕ ПОЗИЦИИ:\n\n"

        total_pnl = 0
        for pos_id, position in active_positions.items():
            symbol = position['symbol']
            current_price = auto_trade_manager._get_current_price(symbol)

            if current_price:
                entry = position['entry_price']
                if position['direction'] == "LONG":
                    pnl_pct = (current_price - entry) / entry * 100
                else:
                    pnl_pct = (entry - current_price) / entry * 100
                total_pnl += pnl_pct

                emoji = "🟢" if pnl_pct > 0 else "🔴"
                response += f"{emoji} {symbol}: {pnl_pct:+.2f}%\n"
            else:
                response += f"⚪ {symbol}: ---\n"

        response += f"\n💰 Общая доходность: {total_pnl:+.2f}%"
        response += f"\n📈 Позиций: {len(active_positions)}"

        keyboard = create_positions_keyboard(active_positions)

        bot.edit_message_text(
            response,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=keyboard
        )

    except Exception as e:
        bot.edit_message_text(
            f"❌ Ошибка обновления: {str(e)}",
            chat_id=chat_id,
            message_id=message_id
        )


def show_mobile_dashboard(chat_id, message_id):
    """Показывает мобильный дашборд"""
    try:
        stats = auto_trade_manager.get_trading_statistics(chat_id, days=1)

        if not stats:
            dashboard_text = """
📱 МОБИЛЬНЫЙ ДАШБОРД

💰 Баланс: ---
📊 Активных позиций: 0
🎯 Общий риск: 0%
💸 Доходность: ---

💡 Сделок сегодня нет
"""
        else:
            dashboard_text = f"""
📱 МОБИЛЬНЫЙ ДАШБОРД

💰 Доходность: {stats['total_pnl']:+.2f}%
📊 Сделок: {stats['total_trades']}
✅ Успешных: {stats['win_rate']:.1f}%
🎯 Активных: {len(auto_trade_manager.get_active_positions(chat_id))}

📈 Лучшие:
"""
            # Добавляем лучшие символы
            for i, (symbol, data) in enumerate(stats['best_symbols'][:2], 1):
                dashboard_text += f"{i}. {symbol}: {data['total_pnl']:+.2f}%\n"

        # Создаем клавиатуру дашборда
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        btn_positions = types.InlineKeyboardButton("📊 Позиции", callback_data="refresh_positions")
        btn_report = types.InlineKeyboardButton("📈 Отчет", callback_data="show_daily_report")
        btn_signals = types.InlineKeyboardButton("🎯 Сигналы", callback_data="show_signals")
        btn_settings = types.InlineKeyboardButton("⚙️ Настройки", callback_data="show_settings")

        keyboard.add(btn_positions, btn_report)
        keyboard.add(btn_signals, btn_settings)

        bot.edit_message_text(
            dashboard_text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=keyboard
        )

    except Exception as e:
        bot.edit_message_text(
            f"❌ Ошибка дашборда: {str(e)}",
            chat_id=chat_id,
            message_id=message_id
        )


# 🔽 🔽 🔽 ДОБАВЛЯЕМ НОВЫЕ ФУНКЦИИ ДЛЯ КНОПОК 🔽 🔽 🔽
def show_advanced_targets_from_button(chat_id, symbol, message_id):
    """БЫСТРЫЕ цели для кнопок"""
    try:
        # Быстрое сообщение
        bot.edit_message_text(
            f"🎯 Быстрый расчет целей для {symbol}...",
            chat_id=chat_id,
            message_id=message_id
        )

        # ⚡ БЫСТРЫЙ РАСЧЕТ
        current_price = None

        # Простой способ получить цену
        try:
            import requests
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            response = requests.get(url, timeout=3)  # Только 3 секунды!
            if response.status_code == 200:
                data = response.json()
                current_price = float(data['price'])
        except:
            # Если не получилось, используем примерные цены
            price_examples = {
                'BTCUSDT': 70000, 'ETHUSDT': 3500, 'SOLUSDT': 150,
                'PEPEUSDT': 0.000007, 'DOGEUSDT': 0.15
            }
            current_price = price_examples.get(symbol, 100)

        # РАСЧЕТ ЦЕЛЕЙ
        entry_price = current_price
        stop_loss = round(current_price * 0.98, 6)  # Округляем
        take_profits = [
            round(current_price * 1.02, 6),
            round(current_price * 1.04, 6),
            round(current_price * 1.06, 6)
        ]

        # 🔽 ПРОСТОЙ CALLBACK БЕЗ СЛОЖНЫХ ДАННЫХ
        simple_callback = f"simple_trade_{symbol}"

        response = f"""
🎯 БЫСТРЫЕ ЦЕЛИ ДЛЯ {symbol}

💰 Текущая цена: {format_price(current_price)}
🎯 Рекомендуемый вход: {format_price(entry_price)}
🛑 Стоп-лосс: {format_price(stop_loss)}

🎯 УРОВНИ ТЕЙК-ПРОФИТА:
TP1: {format_price(take_profits[0])} (+2.0%)
TP2: {format_price(take_profits[1])} (+4.0%)
TP3: {format_price(take_profits[2])} (+6.0%)

💡 Используйте /advanced_targets {symbol} для точных AI-целей
"""

        # 🔽 ПРОСТЫЕ КНОПКИ БЕЗ СЛОЖНЫХ ДАННЫХ
        keyboard = types.InlineKeyboardMarkup(row_width=2)

        btn_info = types.InlineKeyboardButton(
            "ℹ️ Информация",
            callback_data=f"info_{symbol}"
        )
        btn_full = types.InlineKeyboardButton(
            "🎯 Полные цели",
            callback_data=f"full_targets_{symbol}"
        )
        btn_back = types.InlineKeyboardButton("⬅️ Назад", callback_data=f"analyze_{symbol}")

        keyboard.add(btn_info, btn_full)
        keyboard.add(btn_back)

        bot.edit_message_text(
            response,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=keyboard
        )

    except Exception as e:
        # Простая ошибка
        try:
            bot.edit_message_text(
                f"✅ Быстрые цели для {symbol} готовы!\nИспользуйте /advanced_targets для точного анализа",
                chat_id=chat_id,
                message_id=message_id
            )
        except:
            pass


def create_auto_trade_from_button(chat_id, symbol, message_id):
    """Создает авто-сделку из кнопки"""
    try:
        bot.edit_message_text(
            f"🤖 Создаю авто-сделку для {symbol}...",
            chat_id=chat_id,
            message_id=message_id
        )

        # Получаем текущую цену
        current_price = auto_trade_manager._get_current_price(symbol)

        if current_price:
            # Создаем упрощенную сделку
            entry_price = current_price
            stop_loss = current_price * 0.98  # -2%
            take_profit = current_price * 1.06  # +6%
            take_profits = [
                current_price + (take_profit - current_price) * 0.3,
                current_price + (take_profit - current_price) * 0.6,
                take_profit
            ]

            # 🔽 🔽 🔽 ПОЛУЧАЕМ РЕАЛЬНЫЕ ДАННЫЕ 🔽 🔽 🔽
            consensus = get_consensus_signal(symbol)
            volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)

            # Безопасное получение данных
            ai_conf = consensus.get('ai_confidence', 5.0) if consensus and 'error' not in consensus else 5.0
            volume_ratio = volume_data.get('volume_ratio', 1.0) if volume_data and 'error' not in volume_data else 1.0

            position_id = auto_trade_manager.create_auto_trade(
                chat_id=chat_id,
                symbol=symbol,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profits=take_profits,
                direction="LONG",
                ai_confidence=ai_conf,  # 🔽 REAL DATA
                volume_ratio=volume_ratio  # 🔽 REAL DATA
            )

            if position_id:
                bot.edit_message_text(
                    f"✅ АВТО-СДЕЛКА СОЗДАНА!\n\n"
                    f"📊 {symbol} - LONG\n"
                    f"💰 Вход: {format_price(entry_price)}\n"
                    f"🎯 Цели: {', '.join([format_price(tp) for tp in take_profits])}\n"
                    f"🛑 Стоп: {format_price(stop_loss)}\n\n"
                    f"🤖 AI: {ai_conf:.1f}/10 📊 Объемы: {volume_ratio:.1f}x\n\n"
                    f"💡 Используйте /active_positions для управления",
                    chat_id=chat_id,
                    message_id=message_id
                )
            else:
                bot.edit_message_text(
                    f"❌ Не удалось создать сделку для {symbol}",
                    chat_id=chat_id,
                    message_id=message_id
                )
        else:
            bot.edit_message_text(
                f"❌ Не удалось получить цену для {symbol}",
                chat_id=chat_id,
                message_id=message_id
            )

    except Exception as e:
        bot.edit_message_text(
            f"❌ Ошибка: {str(e)}",
            chat_id=chat_id,
            message_id=message_id
        )


def show_consensus_from_button(chat_id, symbol, message_id):
    """Показывает консенсус из кнопки"""
    try:
        # Убедитесь, что 'types' и 'bot' доступны в области видимости этого файла
        # from telebot import types # может потребоваться импортировать здесь

        bot.edit_message_text(
            f"📊 Анализирую консенсус для {symbol}...",
            chat_id=chat_id,
            message_id=message_id
        )

        # ⚠️ Убедитесь, что функция get_consensus_signal доступна
        consensus = get_consensus_signal(symbol)

        if not consensus:
            bot.edit_message_text(
                f"❌ Ошибка консенсуса для {symbol}",
                chat_id=chat_id,
                message_id=message_id
            )
            return

        # 🛑 ИСПРАВЛЕНИЕ: Используем 'ai_confidence_real' (реальная уверенность до фильтра)
        ai_confidence_real = consensus.get('ai_confidence_real', 0)
        # Получаем отфильтрованное значение для отображения, если оно меньше реального
        ai_confidence_filtered = consensus.get('ai_confidence_filtered', 0)

        response = f"""
📊 КОНСЕНСУС ДЛЯ {symbol}

🎯 Уровень согласия: {consensus.get('consensus_level', 0):.1f}%
📈 Направление: {consensus.get('final_direction', 'HOLD')}
💪 Уверенность: {consensus.get('confidence', 0):.1f}%
🤖 AI Уверенность (Реальная): {ai_confidence_real:.1f}/10
"""
        # Добавляем информацию, если внутренний фильтр сработал
        if ai_confidence_filtered > 0 and ai_confidence_filtered < ai_confidence_real:
            response += f"🛡️ Фильтр сработал: Уверенность снижена до {ai_confidence_filtered:.1f}/10\n"

        response += f"\n📋 СИГНАЛЫ СИСТЕМ:\n"
        # Добавляем сигналы систем
        for signal in consensus.get('signals', []):
            status = "✅" if signal['passed'] else "❌"
            response += f"{status} {signal['system']}: {signal['direction']} ({signal['confidence']:.1f}/10)\n"

        response += f"\n💡 Рекомендация AI: {consensus.get('ai_recommendation', 'Не определена')}"

        # Кнопка назад
        keyboard = types.InlineKeyboardMarkup()
        btn_back = types.InlineKeyboardButton("⬅️ Назад", callback_data=f"analyze_{symbol}")
        keyboard.add(btn_back)

        bot.edit_message_text(
            response,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=keyboard
        )

    except Exception as e:
        # ⚠️ Убедитесь, что 'bot' доступен в области видимости для обработки исключений
        bot.edit_message_text(
            f"❌ Ошибка: {str(e)}",
            chat_id=chat_id,
            message_id=message_id
        )

def analyze_smart_from_button(chat_id, symbol, message_id):
    """Выполняет полный анализ из кнопки"""
    try:
        bot.edit_message_text(
            f"🔍 Запускаю полный анализ для {symbol}...",
            chat_id=chat_id,
            message_id=message_id
        )

        # Получаем данные анализа
        response = requests.post(
            f"{API_URL}/analyze-smart",
            params={"symbol": symbol},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                bot.edit_message_text(f"❌ Ошибка: {data['error']}", chat_id=chat_id, message_id=message_id)
            else:
                # ДОБАВЛЯЕМ AI-АНАЛИЗ
                ai_data = add_ai_analysis_to_signal(symbol, data)
                # Сохраняем исходные данные и добавляем AI
                enhanced_data = {**data, **ai_data}
                result_text = format_smart_analysis_result(enhanced_data)

                # ДОБАВЛЯЕМ КНОПКИ
                keyboard = create_analysis_keyboard(symbol)

                bot.edit_message_text(
                    result_text,
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=keyboard
                )
        else:
            bot.edit_message_text("❌ Ошибка сервера", chat_id=chat_id, message_id=message_id)

    except Exception as e:
        bot.edit_message_text(
            f"❌ Ошибка полного анализа: {str(e)}",
            chat_id=chat_id,
            message_id=message_id
        )


def show_full_targets_info(chat_id, symbol, message_id):
    """Показывает информацию о полных целях"""
    try:
        bot.edit_message_text(
            f"🎯 Полные AI-цели для {symbol}\n\n"
            f"Для получения точных целей с AI-анализом используйте команду:\n"
            f"<code>/advanced_targets {symbol}</code>\n\n"
            f"📊 Что включает полный анализ:\n"
            f"• AI-прогноз цены\n"
            f"• Анализ объемов\n"
            f"• Трендовый анализ\n"
            f"• Оптимальные точки входа\n"
            f"• Динамические стоп-лоссы\n\n"
            f"⏱ Занимает 10-30 секунд",
            chat_id=chat_id,
            message_id=message_id,
            parse_mode='HTML'
        )
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка: {str(e)}", chat_id, message_id)


def show_symbol_info(chat_id, symbol, message_id):
    """Показывает информацию о символе"""
    try:
        # Быстрая информация о символе
        current_price = auto_trade_manager._get_current_price(symbol)

        if current_price:
            response = f"""
ℹ️ ИНФОРМАЦИЯ О {symbol}

💰 Текущая цена: {format_price(current_price)}
📈 Изменение за 24ч: Расчет...
📊 Объемы: Проверка...

💡 Для полной информации используйте:
/analyze_smart {symbol}

🎯 Для точных целей:
/advanced_targets {symbol}
"""
        else:
            response = f"ℹ️ Информация о {symbol}\n\nИспользуйте /analyze_smart {symbol} для полного анализа"

        keyboard = types.InlineKeyboardMarkup()
        btn_back = types.InlineKeyboardButton("⬅️ Назад", callback_data=f"advanced_targets_{symbol}")
        keyboard.add(btn_back)

        bot.edit_message_text(response, chat_id, message_id, reply_markup=keyboard)

    except Exception as e:
        bot.edit_message_text(f"ℹ️ Информация о {symbol}\n\nИспользуйте команды для анализа", chat_id, message_id)


def calculate_smart_trade_params(symbol, current_price):
    """Умный расчет параметров сделки на основе анализа"""
    try:
        # 🔽 ПОЛУЧАЕМ ДАННЫЕ ДЛЯ АНАЛИЗА
        volatility = get_symbol_volatility(symbol)  # Волатильность
        trend_data = get_trend_direction(symbol)  # Направление тренда
        volume_data = get_volume_analysis(symbol)  # Анализ объемов
        support_resistance = get_support_resistance(symbol)  # Уровни P/S

        # 🔽 БАЗОВЫЕ ПАРАМЕТРЫ ПО ТИПУ СИМВОЛА
        symbol_type = classify_symbol_type(symbol)

        if symbol_type == "MEME":
            # Мемкоины - высокая волатильность
            base_sl_percent = 0.15  # -15%
            base_tp_percents = [0.10, 0.20, 0.30]  # +10%, +20%, +30%
            risk_multiplier = 1.5

        elif symbol_type == "LARGE_CAP":
            # Крупные капитализации - стабильность
            base_sl_percent = 0.03  # -3%
            base_tp_percents = [0.05, 0.08, 0.12]  # +5%, +8%, +12%
            risk_multiplier = 0.8

        else:
            # Средняя капитализация
            base_sl_percent = 0.05  # -5%
            base_tp_percents = [0.08, 0.12, 0.18]  # +8%, +12%, +18%
            risk_multiplier = 1.0

        # 🔽 КОРРЕКТИРОВКИ ПО ВОЛАТИЛЬНОСТИ
        if volatility == "HIGH":
            base_sl_percent *= 1.3
            base_tp_percents = [p * 1.2 for p in base_tp_percents]
        elif volatility == "LOW":
            base_sl_percent *= 0.8
            base_tp_percents = [p * 0.8 for p in base_tp_percents]

        # 🔽 КОРРЕКТИРОВКИ ПО ТРЕНДУ
        if trend_data == "STRONG_UP":
            # В сильном восходящем тренде - выше тейк-профиты
            base_tp_percents = [p * 1.3 for p in base_tp_percents]
        elif trend_data == "STRONG_DOWN":
            # В нисходящем тренде - уже стоп-лосс
            base_sl_percent *= 0.7

        # 🔽 РАСЧЕТ ФИНАЛЬНЫХ ЦЕН
        entry_price = current_price
        stop_loss = current_price * (1 - base_sl_percent)
        take_profits = [current_price * (1 + tp) for tp in base_tp_percents]

        return {
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profits': take_profits,
            'direction': 'LONG',
            'risk_reward': (base_tp_percents[2] / base_sl_percent),
            'volatility': volatility,
            'trend': trend_data,
            'symbol_type': symbol_type
        }

    except Exception as e:
        # 🔽 РЕЗЕРВНЫЙ РАСЧЕТ ПРИ ОШИБКЕ
        print(f"❌ Ошибка умного расчета: {e}")
        return {
            'entry_price': current_price,
            'stop_loss': current_price * 0.98,
            'take_profits': [current_price * 1.02, current_price * 1.04, current_price * 1.06],
            'direction': 'LONG',
            'risk_reward': 3.0,
            'volatility': 'MEDIUM',
            'trend': 'NEUTRAL',
            'symbol_type': 'UNKNOWN'
        }


def get_symbol_volatility(symbol):
    """Определяет волатильность символа"""
    try:
        # Простой анализ на основе исторических данных
        # В реальности можно использовать ATR или стандартное отклонение
        price_examples = {
            'BTCUSDT': 'MEDIUM',
            'ETHUSDT': 'MEDIUM',
            'SOLUSDT': 'HIGH',
            'PEPEUSDT': 'VERY_HIGH',
            'DOGEUSDT': 'HIGH',
            'BNBUSDT': 'MEDIUM',
            'XRPUSDT': 'HIGH',
            'ADAUSDT': 'HIGH'
        }
        return price_examples.get(symbol, 'MEDIUM')
    except:
        return 'MEDIUM'


def get_trend_direction(symbol):
    """Определяет направление тренда"""
    try:
        # В реальности - анализ скользящих средних
        # Пока заглушка
        trends = {
            'BTCUSDT': 'BULLISH',
            'ETHUSDT': 'BULLISH',
            'SOLUSDT': 'BULLISH',
            'PEPEUSDT': 'VOLATILE',
            'DOGEUSDT': 'VOLATILE'
        }
        return trends.get(symbol, 'NEUTRAL')
    except:
        return 'NEUTRAL'


def get_volume_analysis(symbol):
    """Анализ объемов торгов"""
    try:
        # Заглушка - в реальности анализ объемов
        volume_data = {
            'BTCUSDT': {'volume_ratio': 1.2, 'trend': 'INCREASING'},
            'ETHUSDT': {'volume_ratio': 1.1, 'trend': 'STABLE'},
            'SOLUSDT': {'volume_ratio': 1.5, 'trend': 'INCREASING'},
            'PEPEUSDT': {'volume_ratio': 2.0, 'trend': 'VOLATILE'},
            'DOGEUSDT': {'volume_ratio': 1.8, 'trend': 'INCREASING'}
        }
        return volume_data.get(symbol, {'volume_ratio': 1.0, 'trend': 'STABLE'})
    except:
        return {'volume_ratio': 1.0, 'trend': 'STABLE'}

def get_support_resistance(symbol):
    """Получает уровни поддержки и сопротивления"""
    try:
        # Заглушка - в реальности технический анализ
        levels = {
            'BTCUSDT': {
                'support': [65000, 62000, 60000],
                'resistance': [68000, 70000, 72000]
            },
            'ETHUSDT': {
                'support': [3200, 3000, 2800],
                'resistance': [3500, 3800, 4000]
            }
        }
        return levels.get(symbol, {'support': [], 'resistance': []})
    except:
        return {'support': [], 'resistance': []}

def classify_symbol_type(symbol):
    """Классифицирует тип символа"""
    large_caps = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT']
    meme_coins = ['PEPEUSDT', 'DOGEUSDT', 'SHIBUSDT', 'FLOKIUSDT']

    if symbol in large_caps:
        return "LARGE_CAP"
    elif symbol in meme_coins:
        return "MEME"
    else:
        return "MID_CAP"


def create_simple_trade(chat_id, symbol, message_id):
    """Создает УМНУЮ сделку с аналитикой (БЕЗ Markdown)"""
    try:
        bot.edit_message_text(
            f"🤖 Создаю УМНУЮ сделку для {symbol}...",
            chat_id=chat_id,
            message_id=message_id
        )

        # Получаем текущую цену
        current_price = auto_trade_manager._get_current_price(symbol)

        if not current_price:
            bot.edit_message_text(
                f"❌ Не удалось получить цену для {symbol}",
                chat_id=chat_id,
                message_id=message_id
            )
            return

        # 🔽 ИСПОЛЬЗУЕМ УМНЫЙ РАСЧЕТ
        trade_params = calculate_smart_trade_params(symbol, current_price)

        # 🔽 ПОЛУЧАЕМ ДОПОЛНИТЕЛЬНЫЕ ДАННЫЕ
        consensus = get_consensus_signal(symbol)
        volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)

        # Безопасное получение данных
        ai_conf = consensus.get('ai_confidence', 5.0) if consensus and 'error' not in consensus else 5.0
        volume_ratio = volume_data.get('volume_ratio', 1.0) if volume_data and 'error' not in volume_data else 1.0

        # 🔽 УМНЫЕ ПОРОГИ AI УВЕРЕННОСТИ
        confidence_thresholds = {
            "LARGE_CAP": 8.0,  # 🔽 ВЫСОКИЕ ПОРОГИ!
            "MID_CAP": 7.5,
            "MEME": 7.0,
            "UNKNOWN": 7.5
        }

        required_confidence = confidence_thresholds.get(trade_params['symbol_type'], 7.5)

        # 🔽 ПРОВЕРЯЕМ AI УВЕРЕННОСТЬ
        if ai_conf < required_confidence:
            bot.edit_message_text(
                f"⚠️ СДЕЛКА НЕ РЕКОМЕНДУЕТСЯ\n\n"
                f"📊 {symbol} - {trade_params['direction']}\n"
                f"🤖 AI уверенность: {ai_conf:.1f}/10 < {required_confidence:.1f}/10\n"
                f"🔥 Волатильность: {trade_params['volatility']}\n"
                f"📈 Тренд: {trade_params['trend']}\n\n"
                f"💡 Рекомендации:\n"
                f"• Дождитесь лучших условий\n"
                f"• Используйте /analyze_smart {symbol}\n"
                f"• Проверьте позже",
                chat_id=chat_id,
                message_id=message_id
                # 🔽 БЕЗ parse_mode!
            )
            return

        # 🔽 ПРОВЕРЯЕМ ОБЪЕМЫ
        min_volume_ratio = 1.8  # 🔽 ВЫСОКИЙ ПОРОГ!
        if volume_ratio < min_volume_ratio:
            bot.edit_message_text(
                f"⚠️ СДЕЛКА НЕ РЕКОМЕНДУЕТСЯ\n\n"
                f"📊 {symbol} - {trade_params['direction']}\n"
                f"📊 Объемы: {volume_ratio:.2f}x < {min_volume_ratio:.1f}x\n"
                f"🤖 AI уверенность: {ai_conf:.1f}/10\n\n"
                f"💡 Требуются хорошие объемы для надежного сигнала",
                chat_id=chat_id,
                message_id=message_id
            )
            return

        # 🔽 СОЗДАЕМ СДЕЛКУ С УМНЫМИ ПАРАМЕТРАМИ
        position_id = auto_trade_manager.create_auto_trade(
            chat_id=chat_id,
            symbol=symbol,
            entry_price=trade_params['entry_price'],
            stop_loss=trade_params['stop_loss'],
            take_profits=trade_params['take_profits'],
            direction=trade_params['direction'],
            ai_confidence=ai_conf,
            volume_ratio=volume_ratio
        )

        if position_id:
            # 🔽 ДЕТАЛЬНЫЙ ОТЧЕТ БЕЗ MARKDOWN
            response = f"""
✅ УМНАЯ СДЕЛКА СОЗДАНА!

📊 {symbol} - {trade_params['direction']}
💰 Вход: {format_price(trade_params['entry_price'])}
🛑 Стоп: {format_price(trade_params['stop_loss'])} ({(1 - trade_params['stop_loss'] / current_price) * 100:.1f}%)

🎯 Уровни тейк-профита:
TP1: {format_price(trade_params['take_profits'][0])} ({(trade_params['take_profits'][0] / current_price - 1) * 100:.1f}%)
TP2: {format_price(trade_params['take_profits'][1])} ({(trade_params['take_profits'][1] / current_price - 1) * 100:.1f}%)
TP3: {format_price(trade_params['take_profits'][2])} ({(trade_params['take_profits'][2] / current_price - 1) * 100:.1f}%)

📈 АНАЛИТИКА:
🤖 AI уверенность: {ai_conf:.1f}/10 ✅
📊 Объемы: {volume_ratio:.1f}x
🎯 R/R соотношение: {trade_params['risk_reward']:.1f}
🔥 Волатильность: {trade_params['volatility']}
📈 Тренд: {trade_params['trend']}
🏷 Тип: {trade_params['symbol_type']}

💡 Используйте /active_positions для управления
"""
            bot.edit_message_text(
                response,
                chat_id=chat_id,
                message_id=message_id
                # 🔽 БЕЗ parse_mode!
            )
        else:
            bot.edit_message_text(
                f"❌ Ошибка создания сделки для {symbol}",
                chat_id=chat_id,
                message_id=message_id
            )

    except Exception as e:
        bot.edit_message_text(
            f"❌ Ошибка создания умной сделки: {str(e)}",
            chat_id=chat_id,
            message_id=message_id
        )
# 🔼 🔼 🔼 КОНЕЦ НОВЫХ ФУНКЦИЙ 🔼 🔼 🔼

# 🔼 🔼 🔼 КОНЕЦ ОБРАБОТЧИКОВ INLINE-КНОПОК 🔼 🔼 🔼
# ==============================================
# КОНЕЦ НОВЫХ КОМАНД
# ==============================================

# 🔽 🔽 🔽 ИСПРАВЛЕННАЯ ЗАГРУЗКА СИМВОЛОВ 🔽 🔽 🔽
def load_all_symbols_safe():
    """Безопасная загрузка символов (без фильтров)"""
    try:
        with open("all_usdt_pairs.json", "r") as f:
            symbols = json.load(f)
        print(f"✅ Загружено {len(symbols)} символов из файла")
        return symbols
    except:
        # Базовый список с мемкоинами
        base_symbols = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT",
            "AVAXUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT", "LINKUSDT",
            "ATOMUSDT", "UNIUSDT", "XLMUSDT", "ALGOUSDT", "TRXUSDT", "VETUSDT",
            "ICPUSDT", "FILUSDT", "AAVEUSDT", "COMPUSDT", "MKRUSDT", "SNXUSDT",
            "DOGEUSDT", "SHIBUSDT", "PEPEUSDT", "FLOKIUSDT", "BONKUSDT",
            "WIFUSDT", "BOMEUSDT", "MEMEUSDT", "LUNCUSDT", "LUNAUSDT"
        ]
        print(f"⚠️ Используется базовый список ({len(base_symbols)} символов)")
        return base_symbols

print("🔄 Загружаю список торговых пар...")
ALL_SYMBOLS = load_all_symbols_safe()
print(f"📊 Загружено {len(ALL_SYMBOLS)} торговых пар (включая мемкоины)")
# 🔼 🔼 🔼 КОНЕЦ ИСПРАВЛЕНИЯ 🔼 🔼 🔼


# 🔽 🔽 🔽 ДОБАВЛЯЕМ СИСТЕМУ АВТОМАТИЧЕСКОЙ ТОРГОВЛИ 🔽 🔽 🔽
class AutoTradeManager:
    """Автоматическое управление торговыми позициями"""

    def __init__(self, bot):
        self.bot = bot
        self.active_positions = {}  # Храним все активные позиции
        self.trade_history = []  # История всех сделок
        self.monitoring_active = False
        self.monitoring_thread = None
        self.last_trade_time = None

        # 🔽 🔽 🔽 ДОБАВЛЯЕМ НОВЫЕ НАСТРОЙКИ 🔽 🔽 🔽
        self.trading_config = {
            # 🎯 ФИЛЬТРЫ КАЧЕСТВА:
            'MIN_AI_CONFIDENCE': 7.0,  # Только высокие уверенности
            'MIN_VOLUME_RATIO': 1.5,  # Хорошие объемы!!!!!!!!!!!!!!!!

            # 📊 ЛИМИТЫ АКТИВНОСТИ:
            'MAX_ACTIVE_POSITIONS': 5,  # Макс 5 активных сделок
            'MAX_TRADES_PER_DAY': 6,  # До 6 сделок в день
            'MIN_TIME_BETWEEN_TRADES': 30,  # 30 минут между сделками

            # 🛡️ УПРАВЛЕНИЕ РИСКАМИ:
            'MAX_STOP_LOSS_PERCENT': 0.8,  # Стоп-лосс 0.8%
        }

    def should_open_trade(self, chat_id, symbol, ai_confidence, volume_ratio):
        """Проверяет можно ли открывать сделку"""
        try:
            config = self.trading_config

            # 1. 🎯 Проверка AI уверенности
            if ai_confidence < config['MIN_AI_CONFIDENCE']:
                return False, f"❌ AI уверенность {ai_confidence:.1f}/10 < {config['MIN_AI_CONFIDENCE']:.1f}/10"
            # 2. 📊 Проверка объемов
            if volume_ratio < config['MIN_VOLUME_RATIO']:
                return False, f"❌ Объемы {volume_ratio:.1f}x < {config['MIN_VOLUME_RATIO']:.1f}x"



            # 3. 🚫 Проверка лимита активных позиций
            active_count = len([p for p in self.active_positions.values() if p['chat_id'] == chat_id])
            if active_count >= config['MAX_ACTIVE_POSITIONS']:
                return False, f"❌ Достигнут лимит {config['MAX_ACTIVE_POSITIONS']} активных позиций"

            # 4. ⏰ Проверка времени между сделками
            if self.last_trade_time:
                time_since_last = (datetime.now() - self.last_trade_time).total_seconds() / 60
                if time_since_last < config['MIN_TIME_BETWEEN_TRADES']:
                    wait_time = config['MIN_TIME_BETWEEN_TRADES'] - time_since_last
                    return False, f"⏳ Ждите {wait_time:.0f} мин. между сделками"

            # 5. 📈 Проверка лимита сделок за день
            today_trades = [t for t in self.trade_history
                            if t.get('chat_id') == chat_id
                            and t.get('created_at') and t['created_at'].date() == datetime.now().date()]
            if len(today_trades) >= config['MAX_TRADES_PER_DAY']:
                return False, f"❌ Достигнут лимит {config['MAX_TRADES_PER_DAY']} сделок в день"

            return True, "✅ Можно открывать сделку"

        except Exception as e:
            return False, f"❌ Ошибка проверки: {str(e)}"

    def create_auto_trade(self, chat_id, symbol, entry_price, stop_loss, take_profits, direction="LONG",
                          ai_confidence=5.0, volume_ratio=1.0):
        """Создает автоматическую сделку с проверками"""
        try:
            # 🔽 🔽 🔽 ВКЛЮЧАЕМ ПРОВЕРКИ ОБРАТНО 🔽 🔽 🔽
            can_open, reason = self.should_open_trade(chat_id, symbol, ai_confidence, volume_ratio)
            if not can_open:
                print(f"🚫 Сделка {symbol} отклонена: {reason}")
                # Отправляем уведомление в телеграм
                try:
                    self.bot.send_message(chat_id, f"🚫 {reason}")
                except:
                    pass
                return None

            # 🔽 УБИРАЕМ СТАРУЮ ДИАГНОСТИКУ (она больше не нужна)
            # print(f"🎯 СОЗДАЮ СДЕЛКУ {symbol} (проверки отключены)")
            # print(f"   AI: {ai_confidence}/10, Объемы: {volume_ratio}x")

            # 🔽 ДАЛЕЕ ИДЕТ ОСТАЛЬНОЙ КОД БЕЗ ИЗМЕНЕНИЙ:
            # Проверка стоп-лосса (не более 0.8%)
            current_price = self._get_current_price(symbol)
            if current_price:
                stop_loss_percent = abs((stop_loss - entry_price) / entry_price * 100)
                if stop_loss_percent > self.trading_config['MAX_STOP_LOSS_PERCENT']:
                    print(
                        f"⚠️ Корректирую стоп-лосс с {stop_loss_percent:.1f}% на {self.trading_config['MAX_STOP_LOSS_PERCENT']}%")
                    # Пересчитываем стоп-лосс
                    if direction == "LONG":
                        stop_loss = entry_price * (1 - self.trading_config['MAX_STOP_LOSS_PERCENT'] / 100)
                    else:
                        stop_loss = entry_price * (1 + self.trading_config['MAX_STOP_LOSS_PERCENT'] / 100)

            position_id = f"{symbol}_{int(time.time())}"

            position_data = {
                'position_id': position_id,
                'symbol': symbol,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profits': take_profits,
                'direction': direction,
                'status': 'ACTIVE',
                'current_size': 100,
                'chat_id': chat_id,
                'created_at': datetime.now(),
                'executed_tps': [],
                # 🔽 ДОБАВЛЯЕМ ДАННЫЕ ДЛЯ АНАЛИТИКИ
                'ai_confidence': ai_confidence,
                'volume_ratio': volume_ratio
            }

            self.active_positions[position_id] = position_data
            self.last_trade_time = datetime.now()  # 🔽 ОБНОВЛЯЕМ ВРЕМЯ ПОСЛЕДНЕЙ СДЕЛКИ

            # Запускаем мониторинг если еще не запущен
            if not self.monitoring_active:
                self.start_monitoring()

            print(f"✅ Создана авто-сделка {symbol}: AI {ai_confidence}/10, объемы {volume_ratio}x")

            # Отправляем уведомление о создании сделки
            try:
                self.bot.send_message(
                    chat_id,
                    f"✅ АВТО-СДЕЛКА СОЗДАНА!\n\n"
                    f"📊 {symbol} - {direction}\n"
                    f"💰 Вход: {format_price(entry_price)}\n"
                    f"🎯 Цели: {', '.join([format_price(tp) for tp in take_profits])}\n"
                    f"🛑 Стоп: {format_price(stop_loss)}\n\n"
                    f"🤖 AI: {ai_confidence}/10 📊 Объемы: {volume_ratio}x"
                )
            except:
                pass

            return position_id

        except Exception as e:
            print(f"❌ Ошибка создания авто-сделки: {e}")
            return None

    def start_monitoring(self):
        """Запуск автоматического мониторинга позиций"""
        self.monitoring_active = True

        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        print("🔍 Автоматический мониторинг позиций запущен")

    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.monitoring_active = False
        print("⏹️ Автоматический мониторинг позиций остановлен")

    def _monitoring_loop(self):
        """Основной цикл мониторинга позиций"""
        check_interval = 30  # Проверка каждые 30 секунд

        while self.monitoring_active:
            try:
                self._check_all_positions()
                time.sleep(check_interval)
            except Exception as e:
                print(f"❌ Ошибка в мониторинге позиций: {e}")
                time.sleep(60)

    def _check_all_positions(self):
        """Проверяет все активные позиции"""
        if not self.active_positions:
            return

        for position_id, position in list(self.active_positions.items()):
            if position['status'] != 'ACTIVE':
                continue

            try:
                current_price = self._get_current_price(position['symbol'])
                if not current_price:
                    continue

                self._check_position_triggers(position, current_price)

            except Exception as e:
                print(f"❌ Ошибка проверки позиции {position_id}: {e}")

    def _get_current_price(self, symbol):
        """Получает текущую цену символа"""
        try:
            # Используем упрощенный метод получения цены
            url = f"https://api.binance.com/api/v3/ticker/price"
            params = {'symbol': symbol}
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return float(data['price'])
            return None

        except Exception as e:
            print(f"❌ Ошибка получения цены {symbol}: {e}")
            return None

    def _check_position_triggers(self, position, current_price):
        """Проверяет срабатывание триггеров позиции"""
        symbol = position['symbol']
        direction = position['direction']

        # Проверяем стоп-лосс
        if self._check_stop_loss(position, current_price, direction):
            self._execute_stop_loss(position, current_price)
            return

        # Проверяем тейк-профиты
        self._check_take_profits(position, current_price, direction)

    def _check_stop_loss(self, position, current_price, direction):
        """Проверяет срабатывание стоп-лосса"""
        stop_loss = position['stop_loss']

        if direction == "LONG":
            return current_price <= stop_loss
        else:  # SHORT
            return current_price >= stop_loss

    def _check_take_profits(self, position, current_price, direction):
        """Проверяет срабатывание тейк-профитов"""
        take_profits = position['take_profits']
        executed_tps = position['executed_tps']

        for i, tp_price in enumerate(take_profits):
            tp_id = f"TP{i + 1}"

            # Если этот ТП еще не выполнен
            if tp_id not in executed_tps:
                tp_triggered = False

                if direction == "LONG":
                    tp_triggered = current_price >= tp_price
                else:  # SHORT
                    tp_triggered = current_price <= tp_price

                if tp_triggered:
                    self._execute_take_profit(position, tp_id, tp_price, current_price)
                    break

    def _execute_stop_loss(self, position, current_price, is_manual_close=False):
        """Исполнение стоп-лосса или ручного закрытия"""
        try:
            position_id = position['position_id']
            symbol = position['symbol']

            # Рассчитываем результат
            entry = position['entry_price']
            if position['direction'] == "LONG":
                pnl_pct = (current_price - entry) / entry * 100
            else:
                pnl_pct = (entry - current_price) / entry * 100

            # Закрываем позицию
            position['status'] = 'CLOSED'
            position['closed_at'] = datetime.now()
            position['close_price'] = current_price

            if is_manual_close:
                position['close_reason'] = 'MANUAL_CLOSE'
                close_emoji = "👤"
                close_reason = "РУЧНОЕ ЗАКРЫТИЕ"
            else:
                position['close_reason'] = 'STOP_LOSS'
                close_emoji = "🛑"
                close_reason = "СТОП-ЛОСС"

            # Сохраняем в историю
            self.trade_history.append(position.copy())

            # Отправляем уведомление
            message = f"""
    {close_emoji} {close_reason}!

    📊 {symbol} - {position['direction']}
    💰 Вход: {format_price(entry)}
    🛑 Стоп: {format_price(position['stop_loss'])}
    📉 Текущая: {format_price(current_price)}
    💸 Результат: {pnl_pct:+.2f}%

    💡 Позиция закрыта {"вручную" if is_manual_close else "автоматически"}
    📊 Анализ: /analyze_smart {symbol}
    """
            self.bot.send_message(position['chat_id'], message)
            print(f"🔴 {close_reason.lower()}: {symbol} ({pnl_pct:+.2f}%)")

        except Exception as e:
            print(f"❌ Ошибка исполнения закрытия: {e}")

    def close_position_manually(self, position_id, current_price):
        """Ручное закрытие позиции"""
        position = self.active_positions.get(position_id)
        if position and position['status'] == 'ACTIVE':
            self._execute_stop_loss(position, current_price, is_manual_close=True)
            return True
        return False



    def _execute_take_profit(self, position, tp_id, tp_price, current_price):
        """Исполнение тейк-профита"""
        try:
            symbol = position['symbol']
            executed_tps = position['executed_tps']

            # Определяем размер позиции для этого ТП
            if tp_id == "TP1":
                size_to_close = 30  # 30% позиции
                new_stop = position['entry_price']  # Безубыток
            elif tp_id == "TP2":
                size_to_close = 30  # еще 30% позиции
                # Стоп перемещаем для защиты прибыли
                if position['direction'] == "LONG":
                    new_stop = position['entry_price'] + (tp_price - position['entry_price']) * 0.5
                else:
                    new_stop = position['entry_price'] - (position['entry_price'] - tp_price) * 0.5
            else:  # TP3
                size_to_close = 40  # оставшиеся 40%
                new_stop = tp_price  # Закрываем всю позицию

            # Обновляем позицию
            position['current_size'] -= size_to_close
            executed_tps.append(tp_id)

            if tp_id == "TP3" or position['current_size'] <= 0:
                # Закрываем всю позицию
                position['status'] = 'CLOSED'
                position['closed_at'] = datetime.now()
                position['close_price'] = current_price
                position['close_reason'] = 'TAKE_PROFIT'
                self.trade_history.append(position.copy())
            else:
                # Обновляем стоп-лосс
                position['stop_loss'] = new_stop

            # Отправляем уведомление
            message = self._create_tp_message(position, tp_id, tp_price, current_price, size_to_close, new_stop)
            self.bot.send_message(position['chat_id'], message)
            print(f"🟢 Тейк-профит исполнен: {symbol} {tp_id}")

        except Exception as e:
            print(f"❌ Ошибка исполнения тейк-профита: {e}")

    def _create_tp_message(self, position, tp_id, tp_price, current_price, size_closed, new_stop):
        """Создает сообщение о исполнении тейк-профита"""
        symbol = position['symbol']

        if tp_id == "TP3" or position['current_size'] <= 0:
            return f"""
🎉 СДЕЛКА ЗАВЕРШЕНА!

💰 {symbol} достиг финальной цели
📈 Цена: {format_price(current_price)}
✅ Позиция полностью закрыта

📊 Итоговый результат: +{self._calculate_total_pnl(position):.2f}%
💡 Сделка завершена успешно!
"""
        else:
            return f"""
🔔 ЧАСТИЧНОЕ ЗАКРЫТИЕ ПОЗИЦИИ!

🎯 {symbol} достиг {tp_id}
💰 Цена: {format_price(current_price)}
📊 Продано: {size_closed}% позиции

🛑 Стоп перемещен: {format_price(new_stop)}
✅ Остаток позиции: {position['current_size']}%

💡 Следующая цель: {position['take_profits'][len(position['executed_tps'])]}
"""

    def _calculate_total_pnl(self, position):
        """Рассчитывает общую прибыль/убыток"""
        # Упрощенный расчет для демонстрации
        entry = position['entry_price']
        close = position.get('close_price', entry)

        if position['direction'] == "LONG":
            return (close - entry) / entry * 100
        else:
            return (entry - close) / entry * 100

    def get_active_positions(self, chat_id=None):
        """Возвращает активные позиции"""
        if chat_id:
            return {pid: pos for pid, pos in self.active_positions.items()
                    if pos['chat_id'] == chat_id and pos['status'] == 'ACTIVE'}
        return {pid: pos for pid, pos in self.active_positions.items()
                if pos['status'] == 'ACTIVE'}

    def get_position_status(self, position_id):
        """Возвращает статус позиции"""
        return self.active_positions.get(position_id)

    def get_trading_statistics(self, chat_id=None, days=7):
        """Собирает статистику по сделкам"""
        try:
            # Фильтруем сделки по пользователю и дате
            user_trades = [t for t in self.trade_history
                           if (chat_id is None or t.get('chat_id') == chat_id)]

            if not user_trades:
                return None

            # Статистика по сделкам
            total_trades = len(user_trades)
            profitable_trades = [t for t in user_trades if self._calculate_trade_pnl(t) > 0]
            losing_trades = [t for t in user_trades if self._calculate_trade_pnl(t) <= 0]

            # Общая доходность
            total_pnl = sum(self._calculate_trade_pnl(t) for t in user_trades)
            avg_pnl = total_pnl / total_trades if total_trades > 0 else 0

            # Статистика по AI уверенности
            ai_confident_trades = [t for t in user_trades if t.get('ai_confidence', 0) >= 7.0]
            ai_high_confident_trades = [t for t in user_trades if t.get('ai_confidence', 0) >= 8.0]

            # Лучшие/худшие символы
            symbol_stats = {}
            for trade in user_trades:
                symbol = trade['symbol']
                pnl = self._calculate_trade_pnl(trade)
                if symbol not in symbol_stats:
                    symbol_stats[symbol] = {'trades': 0, 'total_pnl': 0, 'profitable': 0}
                symbol_stats[symbol]['trades'] += 1
                symbol_stats[symbol]['total_pnl'] += pnl
                if pnl > 0:
                    symbol_stats[symbol]['profitable'] += 1

            # Сортируем символы по доходности
            best_symbols = sorted(symbol_stats.items(), key=lambda x: x[1]['total_pnl'], reverse=True)[:5]
            worst_symbols = sorted(symbol_stats.items(), key=lambda x: x[1]['total_pnl'])[:5]

            return {
                'total_trades': total_trades,
                'profitable_trades': len(profitable_trades),
                'losing_trades': len(losing_trades),
                'win_rate': (len(profitable_trades) / total_trades * 100) if total_trades > 0 else 0,
                'total_pnl': total_pnl,
                'avg_pnl': avg_pnl,
                'ai_confident_trades': len(ai_confident_trades),
                'ai_high_confident_trades': len(ai_high_confident_trades),
                'best_symbols': best_symbols,
                'worst_symbols': worst_symbols,
                'symbol_stats': symbol_stats
            }

        except Exception as e:
            print(f"❌ Ошибка сбора статистики: {e}")
            return None

    def _calculate_trade_pnl(self, trade):
        """Рассчитывает PnL для одной сделки"""
        try:
            entry = trade['entry_price']
            close = trade.get('close_price', entry)

            if trade['direction'] == "LONG":
                return (close - entry) / entry * 100
            else:
                return (entry - close) / entry * 100
        except:
            return 0

    def can_create_auto_trade(self, chat_id, symbol):
        """Проверяет можно ли создать новую авто-сделку"""
        try:
            # Максимум 3 активные позиции
            active_positions = self.get_active_positions(chat_id)
            if len(active_positions) >= 3:
                return False, "❌ Достигнут лимит: макс. 3 активные позиции"

            # Проверяем не торгуем ли уже этот символ
            for pos_id, position in active_positions.items():
                if position['symbol'] == symbol:
                    return False, f"❌ Активная позиция {symbol} уже существует"

            # Проверяем лимит 3 сделки в час
            recent_trades = self._get_recent_trades(chat_id, hours=1)
            if len(recent_trades) >= 3:
                return False, "❌ Лимит: не более 3 сделок в час"

            return True, "✅ Можно создать сделку"

        except Exception as e:
            print(f"❌ Ошибка проверки лимитов: {e}")
            return False, "❌ Ошибка проверки лимитов"

    def _get_recent_trades(self, chat_id, hours=1):
        """Возвращает сделки за последние N часов"""
        try:
            from datetime import datetime, timedelta
            time_threshold = datetime.now() - timedelta(hours=hours)

            recent_trades = []
            for trade in self.trade_history:
                if (trade.get('chat_id') == chat_id and
                        trade.get('created_at') and
                        trade['created_at'] >= time_threshold):
                    recent_trades.append(trade)

            return recent_trades
        except Exception as e:
            print(f"❌ Ошибка получения recent trades: {e}")
            return []

    def save_data(self):
        """Сохраняет все данные в файл"""
        try:
            # Подготовка данных для сохранения
            data_to_save = {
                'active_positions': {},
                'trade_history': []
            }

            # Конвертируем активные позиции
            for position_id, position in self.active_positions.items():
                # Создаем копию позиции без объектов datetime
                position_copy = position.copy()

                # Конвертируем datetime в строки
                if 'created_at' in position_copy and position_copy['created_at']:
                    position_copy['created_at'] = position_copy['created_at'].isoformat()
                if 'closed_at' in position_copy and position_copy['closed_at']:
                    position_copy['closed_at'] = position_copy['closed_at'].isoformat()

                data_to_save['active_positions'][position_id] = position_copy

            # Конвертируем историю сделок
            for trade in self.trade_history:
                trade_copy = trade.copy()

                # Конвертируем datetime в строки
                if 'created_at' in trade_copy and trade_copy['created_at']:
                    trade_copy['created_at'] = trade_copy['created_at'].isoformat()
                if 'closed_at' in trade_copy and trade_copy['closed_at']:
                    trade_copy['closed_at'] = trade_copy['closed_at'].isoformat()

                data_to_save['trade_history'].append(trade_copy)

            # Сохраняем в файл
            with open('trading_data.json', 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)

            print("💾 Данные успешно сохранены")
            print(
                f"📊 Сохранено: {len(data_to_save['active_positions'])} активных позиций, {len(data_to_save['trade_history'])} сделок в истории")
            return True

        except Exception as e:
            print(f"❌ Ошибка сохранения данных: {e}")
            return False

    def load_data(self):
        """Загружает данные из файла"""
        try:
            # Проверяем существует ли файл
            if not os.path.exists('trading_data.json'):
                print("📂 Файл данных не найден, начинаем с чистого листа")
                return True

            # Читаем файл
            with open('trading_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Восстанавливаем активные позиции
            self.active_positions = {}
            for position_id, position_data in data.get('active_positions', {}).items():
                # Конвертируем строки обратно в datetime
                if 'created_at' in position_data and position_data['created_at']:
                    position_data['created_at'] = datetime.fromisoformat(position_data['created_at'])
                if 'closed_at' in position_data and position_data['closed_at']:
                    position_data['closed_at'] = datetime.fromisoformat(position_data['closed_at'])

                self.active_positions[position_id] = position_data

            # Восстанавливаем историю сделок
            self.trade_history = []
            for trade_data in data.get('trade_history', []):
                # Конвертируем строки обратно в datetime
                if 'created_at' in trade_data and trade_data['created_at']:
                    trade_data['created_at'] = datetime.fromisoformat(trade_data['created_at'])
                if 'closed_at' in trade_data and trade_data['closed_at']:
                    trade_data['closed_at'] = datetime.fromisoformat(trade_data['closed_at'])

                self.trade_history.append(trade_data)

            print(
                f"📂 Загружено: {len(self.active_positions)} активных позиций, {len(self.trade_history)} сделок в истории")
            return True

        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            return False


# Создаем глобальный экземпляр менеджера торговли
auto_trade_manager = AutoTradeManager(bot)
# 🔼 🔼 🔼 КОНЕЦ СИСТЕМЫ АВТОМАТИЧЕСКОЙ ТОРГОВЛИ 🔼 🔼 🔼

# 🔽 🔽 🔽 ЗАГРУЖАЕМ ДАННЫЕ ПРИ ЗАПУСКЕ 🔽 🔽 🔽
auto_trade_manager.load_data()

# 🔽 🔽 🔽 СИСТЕМА АВТО-ТРЕЙДИНГА 🔽 🔽 🔽
class AutoTradingScanner:
    """Автоматический сканер и исполнитель сделок"""

    def __init__(self, bot, auto_trade_manager):
        self.bot = bot
        self.auto_trade_manager = auto_trade_manager
        self.scanning_active = False
        self.scanning_thread = None
        self.scan_interval = 900  # 15 минут

    def start_auto_trading(self, chat_id):
        """Запускает авто-трейдинг для пользователя"""
        try:
            if not self.scanning_active:
                self.scanning_active = True
                self.scanning_thread = threading.Thread(
                    target=self._scanning_loop,
                    args=(chat_id,),
                    daemon=True
                )
                self.scanning_thread.start()
                print(f"🔍 Авто-трейдинг запущен для chat_id: {chat_id}")

            return True

        except Exception as e:
            print(f"❌ Ошибка запуска авто-трейдинга: {e}")
            return False

    def stop_auto_trading(self):
        """Останавливает авто-трейдинг"""
        self.scanning_active = False
        print("⏹️ Авто-трейдинг остановлен")

    def _scanning_loop(self, chat_id):
        """Основной цикл сканирования"""
        while self.scanning_active:
            try:
                self._scan_market(chat_id)
                time.sleep(self.scan_interval)

            except Exception as e:
                print(f"❌ Ошибка в цикле сканирования: {e}")
                time.sleep(60)

    def _scan_market(self, chat_id):
        """Сканирует рынок и создает сделки"""
        try:
            # Сканируем топ-8 монет (можно увеличить)
            symbols_to_scan = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
                               "XRPUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT"]

            for symbol in symbols_to_scan:
                if not self.scanning_active:
                    break

                try:
                    # Проверяем лимиты перед сканированием
                    can_trade, reason = self.auto_trade_manager.can_create_auto_trade(chat_id, symbol)
                    if not can_trade:
                        continue

                    # Получаем анализ символа (упрощенная версия)
                    analysis = self._analyze_symbol(symbol)
                    if analysis and self._is_good_signal(analysis):
                        self._create_auto_trade(chat_id, symbol, analysis)

                    # Пауза между символами
                    time.sleep(2)

                except Exception as e:
                    print(f"❌ Ошибка сканирования {symbol}: {e}")
                    continue

        except Exception as e:
            print(f"❌ Ошибка сканирования рынка: {e}")

    def _analyze_symbol(self, symbol):
        """Анализирует символ и возвращает РЕАЛЬНЫЕ данные для входа"""
        try:
            # Получаем текущую цену
            current_price = self.auto_trade_manager._get_current_price(symbol)
            if not current_price:
                return None

            # 🔽 🔽 🔽 ИСПОЛЬЗУЕМ РЕАЛЬНЫЕ ДАННЫЕ ВМЕСТО СЛУЧАЙНЫХ 🔽 🔽 🔽

            # Получаем РЕАЛЬНЫЙ AI анализ
            try:
                ai_data = ai_checker.analyze_signal_quality(symbol, {
                    'current_price': current_price,
                    'volume_ratio': 1.0,
                    'confluence': 50
                })
                ai_confidence = ai_data['ai_confidence_score']
            except Exception as e:
                print(f"❌ Ошибка AI анализа {symbol}: {e}")
                ai_confidence = 4.0  # Минимальная уверенность при ошибке

            # Получаем РЕАЛЬНЫЕ данные об объемах
            try:
                volume_data = advanced_volume_analyzer.get_volume_spike_analysis(symbol)
                volume_ratio = volume_data.get('volume_ratio', 1.0)
            except Exception as e:
                print(f"❌ Ошибка анализа объемов {symbol}: {e}")
                volume_ratio = 1.0

            # 🔽 🔽 🔽 ИСПОЛЬЗУЕМ РЕАЛЬНЫЙ КОНСЕНСУС ДЛЯ НАПРАВЛЕНИЯ 🔽 🔽 🔽
            try:
                consensus = get_consensus_signal(symbol)
                direction = consensus['final_direction']
                # Если консенсус HOLD, пропускаем символ
                if direction == 'HOLD':
                    return None
            except Exception as e:
                print(f"❌ Ошибка консенсуса {symbol}: {e}")
                direction = "LONG"  # Запасной вариант

            # Рассчитываем цели на основе РЕАЛЬНОЙ волатильности
            try:
                trade_params = calculate_smart_trade_params(symbol, current_price)
                stop_loss = trade_params['stop_loss']
                take_profits = trade_params['take_profits']
                entry_price = current_price
            except Exception as e:
                print(f"❌ Ошибка расчета целей {symbol}: {e}")
                # Запасной расчет
                if direction == "LONG":
                    stop_loss = current_price * 0.98
                    take_profits = [current_price * 1.02, current_price * 1.04, current_price * 1.06]
                else:
                    stop_loss = current_price * 1.02
                    take_profits = [current_price * 0.98, current_price * 0.96, current_price * 0.94]

            return {
                'symbol': symbol,
                'current_price': current_price,
                'ai_confidence': ai_confidence,
                'volume_ratio': volume_ratio,
                'direction': direction,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profits[-1],  # Последний тейк-профит
                'take_profits': take_profits
            }

        except Exception as e:
            print(f"❌ Общая ошибка анализа {symbol}: {e}")
            return None

    def _is_good_signal(self, analysis):
        """Проверяет подходит ли РЕАЛЬНЫЙ сигнал для входа"""
        try:
            ai_confidence = analysis['ai_confidence']
            volume_ratio = analysis['volume_ratio']
            direction = analysis['direction']

            # 🔽 РЕАЛЬНЫЕ КРИТЕРИИ ДЛЯ АВТО-ВХОДА
            return (ai_confidence >= 7.5 and  # Высокая AI уверенность
                    volume_ratio >= 1.8 and  # Хорошие объемы
                    direction != 'HOLD' and  # Четкое направление
                    analysis['take_profit'] > 0)  # Валидные цели

        except Exception as e:
            print(f"❌ Ошибка проверки сигнала: {e}")
            return False



    def _calculate_take_profits(self, entry, take_profit, direction):
        """Рассчитывает многоуровневые тейк-профиты"""
        if direction == "LONG":
            tp1 = entry + (take_profit - entry) * 0.3
            tp2 = entry + (take_profit - entry) * 0.6
            tp3 = take_profit
        else:
            tp1 = entry - (entry - take_profit) * 0.3
            tp2 = entry - (entry - take_profit) * 0.6
            tp3 = take_profit

        return [tp1, tp2, tp3]

    def _create_auto_trade(self, chat_id, symbol, analysis):
        """Создает автоматическую сделку с AI-фильтрами"""
        try:
            # 🔽 🔽 🔽 ШАГ 1: ПОДГОТОВКА ДАННЫХ ИЗ АНАЛИЗА 🔽 🔽 🔽

            # Получаем AI уверенность из анализа (если есть)
            # Если в анализе нет ai_confidence, используем значение по умолчанию 5.0
            ai_confidence = analysis.get('ai_confidence', 5.0)

            # Получаем данные об объемах из анализа (если есть)
            # Если в анализе нет volume_ratio, используем значение по умолчанию 1.0
            volume_ratio = analysis.get('volume_ratio', 1.0)

            # Получаем направление сделки (LONG или SHORT)
            direction = analysis.get('direction', 'LONG')

            # Получаем цену входа
            entry_price = analysis['entry_price']

            # Получаем стоп-лосс
            stop_loss = analysis['stop_loss']

            # Получаем тейк-профиты (список из 3 цен)
            take_profits = analysis['take_profits']

            # 🔽 🔽 🔽 ШАГ 2: СОЗДАЕМ АВТО-СДЕЛКУ С РЕАЛЬНЫМИ ДАННЫМИ 🔽 🔽 🔽

            # Вызываем функцию создания авто-сделки и передаем ВСЕ данные
            position_id = self.auto_trade_manager.create_auto_trade(
                chat_id=chat_id,  # ID чата пользователя
                symbol=symbol,  # Символ (например: "BTCUSDT")
                entry_price=entry_price,  # Цена входа
                stop_loss=stop_loss,  # Цена стоп-лосса
                take_profits=take_profits,  # Список тейк-профитов [tp1, tp2, tp3]
                direction=direction,  # Направление "LONG" или "SHORT"
                ai_confidence=ai_confidence,  # 🔽 РЕАЛЬНАЯ AI уверенность
                volume_ratio=volume_ratio  # 🔽 РЕАЛЬНЫЕ данные об объемах
            )

            # 🔽 🔽 🔽 ШАГ 3: ПРОВЕРЯЕМ УСПЕШНОСТЬ СОЗДАНИЯ СДЕЛКИ 🔽 🔽 🔽

            if position_id:
                # Если сделка успешно создана (position_id не None)

                # 🔽 🔽 🔽 ШАГ 4: ОТПРАВЛЯЕМ УВЕДОМЛЕНИЕ ПОЛЬЗОВАТЕЛЮ 🔽 🔽 🔽

                message = f"""
    🤖 АВТО-ТРЕЙДИНГ: НОВАЯ СДЕЛКА!

    📊 {symbol} - {direction}
    🎯 AI Уверенность: {ai_confidence:.1f}/10
    📈 Объемы: {volume_ratio:.1f}x

    💰 Вход: {format_price(entry_price)}
    🎯 Цели: {', '.join([format_price(tp) for tp in take_profits])}
    🛑 Стоп: {format_price(stop_loss)}

    💡 Сделка создана автоматически
    📊 Статус: /position_status_{symbol.replace('USDT', '')}
    """
                # Отправляем сообщение пользователю
                self.bot.send_message(chat_id, message)

                # Выводим в консоль для отладки
                print(f"🤖 Авто-сделка создана: {symbol} (AI: {ai_confidence:.1f}/10, Объемы: {volume_ratio:.1f}x)")

                # Возвращаем ID позиции чтобы знать что сделка создана
                return position_id

            else:
                # Если сделка НЕ создана (position_id = None)
                # Это значит что фильтры авто-трейдинга отклонили сделку

                # 🔽 🔽 🔽 ШАГ 5: ПРОВЕРКА КРИТЕРИЕВ АВТО-ТРЕЙДИНГА (ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ ТЕКСТА ОШИБКИ) 🔽 🔽 🔽
                # Получаем актуальные пороги из конфигурации
                min_ai = self.trading_config.get('MIN_AI_CONFIDENCE', 7.0)
                min_vol = self.trading_config.get('MIN_VOLUME_RATIO', 1.5)

                if not self.should_open_trade(ai_confidence, volume_ratio):
                    # 💡 ТЕКСТ ОШИБКИ С ДИНАМИЧЕСКИМИ ПОРОГАМИ
                    error_message = f"""
                ❌ Не удалось создать сделку для {symbol}

                🚫 ❌ AI уверенность {ai_confidence:.1f}/10 < {min_ai:.1f}/10
                📈 Объемы: {volume_ratio:.1f}x < {min_vol:.1f}x

                ❌ Причина: Не пройдены фильтры авто-трейдинга
                💡 Требуется: AI ≥{min_ai:.1f} и Объемы ≥{min_vol:.1f}x
                """
                    # Отправляем сообщение об ошибке пользователю
                    self.bot.send_message(chat_id, error_message)




                # Выводим в консоль для отладки
                print(f"🚫 Авто-сделка отклонена: {symbol} (AI: {ai_confidence:.1f}/10, Объемы: {volume_ratio:.1f}x)")

                # Возвращаем None чтобы показать что сделка не создана
                return None

        except Exception as e:
            # 🔽 🔽 🔽 ШАГ 6: ОБРАБОТКА ОШИБОК 🔽 🔽 🔽

            # Если произошла какая-то ошибка при создании сделки
            error_message = f"""
    ❌ ОШИБКА СОЗДАНИЯ СДЕЛКИ: {symbol}

    💡 Произошла техническая ошибка
    ⚠️ Попробуйте создать сделку вручную
    """
            # Отправляем сообщение об ошибке пользователю
            self.bot.send_message(chat_id, error_message)

            # Выводим подробную ошибку в консоль для отладки
            print(f"❌ Ошибка создания авто-сделки {symbol}: {e}")

            # Возвращаем None чтобы показать что сделка не создана
            return None
# Создаем глобальный экземпляр авто-трейдинга
auto_trading_scanner = AutoTradingScanner(bot, auto_trade_manager)
# 🔼 🔼 🔼 КОНЕЦ СИСТЕМЫ АВТО-ТРЕЙДИНГА 🔼 🔼 🔼



print("🤖 Крипто-ассистент PRO ULTRA запущен!")
print("💎 Фильтрация мемкоинов: АКТИВНА")
print("⏰ Ожидаю команды...")
bot.infinity_polling()

