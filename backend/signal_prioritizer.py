class SignalPrioritizer:
    def __init__(self):
        self.priority_boost = {
            'BTCUSDT': 20,
            'ETHUSDT': 15,
            'BNBUSDT': 10,
            'SOLUSDT': 8,
            'XRPUSDT': 5,
            'ADAUSDT': 5
        }

    def calculate_priority_score(self, symbol_data):
        """Рассчитывает приоритет сигнала"""
        score = 0

        # Бонус за основные активы
        score += self.priority_boost.get(symbol_data['symbol'], 0)

        # Сила сигнала (основной фактор)
        score += abs(symbol_data['strength']) * 3

        # Рейтинг актива
        score += symbol_data.get('asset_rating', 5) * 1.5

        # Уровень доверия
        score += symbol_data.get('confidence_level', 5)

        # Объемы торгов (если есть)
        if symbol_data.get('volume_24h', 0) > 50000000:  # $50M+
            score += 10
        elif symbol_data.get('volume_24h', 0) > 10000000:  # $10M+
            score += 5

        return int(score)

    def get_priority_emoji(self, score):
        """Возвращает эмодзи приоритета"""
        if score >= 40:
            return "🥇 ВЫСОКИЙ ПРИОРИТЕТ"
        elif score >= 25:
            return "🥈 СРЕДНИЙ ПРИОРИТЕТ"
        else:
            return "🥉 НИЗКИЙ ПРИОРИТЕТ"

    def sort_signals(self, signals_list):
        """Сортирует сигналы по приоритету"""
        return sorted(signals_list, key=lambda x: x.get('priority_score', 0), reverse=True)


# Глобальный экземпляр
signal_prioritizer = SignalPrioritizer()