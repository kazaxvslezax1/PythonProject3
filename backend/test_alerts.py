# test_alerts.py

# 💡 ВАЖНО: Должен быть импортирован класс SmartAlertsAI
from smart_alerts_ai import SmartAlertsAI

# Если у вас нет отдельного ai_confidence_checker.py,
# вам нужно определить MockAI_Checker внутри этого файла.

# ----------------------------------------------------------------------
# 🟢 ТЕСТ 1: УСПЕШНАЯ ГЕНЕРАЦИЯ СВОДКИ (Приоритизация)
# ----------------------------------------------------------------------

print("--- ТЕСТ 1: ГЕНЕРАЦИЯ СВОДКИ ---")

# Инициализируем систему
ai_alerts_manager_1 = SmartAlertsAI()

# 📝 Тестовые данные (сигналы, которые должны пройти фильтр AI >= 6.0)
test_alerts = [
    {'symbol': 'LTCUSDT', 'signal_type': 'LONG', 'strength': 8, 'ai_confidence': 8.5, 'asset_rating': 9}, # Сильный
    {'symbol': 'SOLUSDT', 'signal_type': 'SHORT', 'strength': 7, 'ai_confidence': 6.2, 'asset_rating': 7}, # Средний
    {'symbol': 'ADAUSDT', 'signal_type': 'LONG', 'strength': 4, 'ai_confidence': 5.5, 'asset_rating': 5}, # Слабый
    {'symbol': 'XRPUSDT', 'signal_type': 'SHORT', 'strength': 9, 'ai_confidence': 9.1, 'asset_rating': 8}, # Сильный
]

# 1. Приоритезация (добавляет ai_priority)
# Предполагаем, что ai_alerts_manager умеет приоритизировать
prioritized = ai_alerts_manager_1.prioritize_alerts(test_alerts)

# 2. Фильтрация дубликатов (удаляет дубликаты символов, оставляя самый сильный)
filtered = ai_alerts_manager_1.filter_duplicate_alerts(prioritized)

# 3. Генерация сводки
summary = ai_alerts_manager_1.generate_alert_summary(filtered)

print(summary)
print("-" * 40)


print("--- ТЕСТ 2: ФИЛЬТР AI ---")

# 💡 Нам нужен Мок-объект, который будет возвращать низкий AI-балл
class MockAI_Checker:
    """Мок для ai_checker, который возвращает низкий балл"""
    def analyze_signal_quality(self, symbol, signal_data):
        # Имитируем низкий балл AI, который должен быть отфильтрован (5.8 < 6.0)
        # ✅ Возвращаем 5.8!
        return {'ai_confidence_score': 5.8}

# Инициализируем SmartAlertsAI, передавая ему наш Мок-объект
ai_alerts_manager_2 = SmartAlertsAI(ai_checker=MockAI_Checker()) # ✅ ТЕПЕРЬ МОК ИСПОЛЬЗУЕТСЯ!

# 🚨 Проверяем сигнал со слабой AI-уверенностью
# Если фильтр AI работает, функция должна вернуть False и вывести print в консоль.
result = ai_alerts_manager_2.should_send_alert('DOGEUSDT', 'LONG', 8)

# ✅ Ожидаемый вывод: AI отфильтровал слабый сигнал: DOGEUSDT (5.8/10)
print(f"Результат should_send_alert для DOGEUSDT (AI 5.8): {result}")
print("-" * 40)