# test_scanner.py

from datetime import datetime, timedelta
from collections import defaultdict
import threading
import time


# 1. --- MOCK / УПРОЩЕННЫЙ КЛАСС: AutoTradeManager ---
class AutoTradeManager:
    """Упрощенный Менеджер для теста сканера"""

    def __init__(self, bot):
        self.bot = bot
        # Хранилище активных позиций
        self.active_positions = defaultdict(dict)
        # Конфигурация, нужная для проверки лимитов
        self.trading_config = {
            'MAX_ACTIVE_POSITIONS': 5,  # Дефолтное значение
            'SCANNING_ENABLED': True
        }
        self.trade_history = []

    # Пустые методы для предотвращения ошибок в других частях кода
    def _get_current_price(self, symbol):
        return 1.0

    def should_open_trade(self, symbol, direction, config):
        return True, "Passed"


# 2. --- MOCK / УПРОЩЕННЫЙ КЛАСС: AutoTradingScanner ---
class AutoTradingScanner:
    """Упрощенный Сканер для проверки лимитов"""

    def __init__(self, bot, auto_trade_manager):
        self.bot = bot
        self.manager = auto_trade_manager
        self.scanning_active = False  # Флаг для теста 7

    def can_start_scanning(self, chat_id):
        """Проверяет, можно ли начать сканирование для данного пользователя (Тест 7 и 8)"""

        # 1. Проверка на активные позиции

        # Получаем только активные позиции для текущего chat_id
        active_count = sum(
            1 for pos in self.manager.active_positions.values()
            if pos.get('chat_id') == chat_id and pos.get('status') == 'ACTIVE'
        )

        max_limit = self.manager.trading_config.get('MAX_ACTIVE_POSITIONS', 5)

        if active_count >= max_limit:
            reason = f"❌ Достигнут лимит: макс. {max_limit} активные позиции ({active_count}/{max_limit})"
            # 🔽 Отправляем сообщение только при достижении лимита (имитация)
            self.bot.send_message(chat_id, reason)
            return False, reason

        # 2. Проверка, что сканирование еще не запущено (для полноты)
        if self.scanning_active:
            return False, "❌ Сканирование уже активно"

        return True, "✅ Сканирование разрешено"

    def start_scanning(self, chat_id):
        self.scanning_active = True
        return f"✅ Сканирование запущено"

    def stop_scanning(self, chat_id):
        self.scanning_active = False
        return f"⏹️ Сканирование остановлено"


# ----------------------------------------------------------------------
# 3. ТЕСТОВЫЙ КОД (ЗАПУСК)
# ----------------------------------------------------------------------

# Создаем Мок-бота
class MockBot:
    """Мок-бот для имитации отправки сообщений"""

    def send_message(self, chat_id, text):
        print(f"[{chat_id}] [MockBot]: {text}")


# Инициализируем менеджера
mock_bot = MockBot()
atm = AutoTradeManager(mock_bot)

# Инициализируем сканер, передавая ему менеджера
ats = AutoTradingScanner(mock_bot, atm)

# Тестовый chat_id
TEST_CHAT_ID = 123456

# --- ТЕСТ 7: Разрешение по умолчанию ---
print("--- ТЕСТ 7: Разрешение по умолчанию (0 позиций) ---")
can_scan_7, reason_7 = ats.can_start_scanning(TEST_CHAT_ID)
print(f"Результат ТЕСТА 7: {can_scan_7}, Причина: {reason_7}")
print("-" * 40)

# --- ТЕСТ 8: Достижение Лимита Активных Позиций (3/3) ---
print("--- ТЕСТ 8: Достижение Лимита (3 активные позиции) ---")

# ⚠️ Устанавливаем лимит 3 для теста, чтобы проверить блокировку
atm.trading_config['MAX_ACTIVE_POSITIONS'] = 3
# Имитируем 3 активные позиции для этого chat_id
atm.active_positions['pos_btc'] = {'status': 'ACTIVE', 'chat_id': TEST_CHAT_ID, 'symbol': 'BTCUSDT'}
atm.active_positions['pos_eth'] = {'status': 'ACTIVE', 'chat_id': TEST_CHAT_ID, 'symbol': 'ETHUSDT'}
atm.active_positions['pos_bnb'] = {'status': 'ACTIVE', 'chat_id': TEST_CHAT_ID, 'symbol': 'BNBUSDT'}

can_scan_8, reason_8 = ats.can_start_scanning(TEST_CHAT_ID)
print(f"Результат ТЕСТА 8: {can_scan_8}, Причина: {reason_8}")
print("-" * 40)