import time
from datetime import datetime, timedelta
from collections import defaultdict


class SmartAlertSystem:
    def __init__(self):
        self.alert_history = defaultdict(list)
        self.alert_cooldown = timedelta(minutes=30)  # Защита от спама
        self.unique_signals = set()

    def should_send_alert(self, symbol, signal_type, strength):
        """Проверяет нужно ли отправлять алерт"""
        alert_key = f"{symbol}_{signal_type}_{strength}"

        # Проверяем был ли уже такой сигнал
        if alert_key in self.unique_signals:
            return False

        # Проверяем кд
        now = datetime.now()
        recent_alerts = [
            alert_time for alert_time in self.alert_history[symbol]
            if now - alert_time < self.alert_cooldown
        ]

        # Максимум 3 алерта за период кд
        if len(recent_alerts) >= 3:
            return False

        # Добавляем в историю
        self.alert_history[symbol].append(now)
        self.unique_signals.add(alert_key)

        # Очищаем старые записи
        self._cleanup_old_alerts()

        return True

    def _cleanup_old_alerts(self):
        """Очистка старых алертов"""
        now = datetime.now()
        cutoff_time = now - timedelta(hours=24)

        for symbol in list(self.alert_history.keys()):
            self.alert_history[symbol] = [
                alert_time for alert_time in self.alert_history[symbol]
                if alert_time > cutoff_time
            ]

            if not self.alert_history[symbol]:
                del self.alert_history[symbol]

    def prioritize_alerts(self, alerts):
        """Приоритизация алертов"""
        prioritized = []

        for alert in alerts:
            score = self._calculate_alert_score(alert)
            alert['priority_score'] = score
            prioritized.append(alert)

        # Сортируем по приоритету
        prioritized.sort(key=lambda x: x['priority_score'], reverse=True)
        return prioritized

    def _calculate_alert_score(self, alert):
        """Расчет приоритета алерта"""
        score = 0

        # Сила сигнала
        score += abs(alert.get('strength', 0)) * 10

        # Качество актива
        score += alert.get('asset_rating', 5) * 2

        # Объемы торгов
        if alert.get('volume_strength', 0) >= 4:
            score += 15
        elif alert.get('volume_strength', 0) >= 2:
            score += 10

        # Конфлюэнс
        if alert.get('confluence_score', 0) > 20:
            score += 20
        elif alert.get('confluence_score', 0) > 10:
            score += 10

        # BTC/ETH получают бонус
        if alert.get('symbol') in ['BTCUSDT', 'ETHUSDT']:
            score += 10

        return score

    def filter_duplicate_alerts(self, alerts):
        """Фильтрация дублирующихся алертов"""
        seen = set()
        unique_alerts = []

        for alert in alerts:
            alert_key = f"{alert['symbol']}_{alert.get('signal_type', '')}_{alert.get('timeframe', '')}"

            if alert_key not in seen:
                seen.add(alert_key)
                unique_alerts.append(alert)

        return unique_alerts

    def generate_alert_summary(self, alerts, max_alerts=5):
        """Генерация сводки алертов"""
        if not alerts:
            return "📊 Нет значимых сигналов для оповещения"

        prioritized = self.prioritize_alerts(alerts)
        filtered = self.filter_duplicate_alerts(prioritized)
        top_alerts = filtered[:max_alerts]

        summary = f"🎯 ТОП-{len(top_alerts)} СИГНАЛОВ:\n\n"

        for i, alert in enumerate(top_alerts, 1):
            symbol_clean = alert['symbol'].replace('USDT', '')
            strength = alert.get('strength', 0)

            if strength > 0:
                emoji = "🟢"
                action = "ПОКУПКА"
            else:
                emoji = "🔴"
                action = "ПРОДАЖА"

            priority = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"

            summary += f"{priority} {emoji} {symbol_clean} - {action}\n"
            summary += f"   💪 Сила: {abs(strength)}/10 | 🏆 Рейтинг: {alert.get('asset_rating', 'N/A')}/10\n"

            if alert.get('volume_strength', 0) >= 3:
                summary += f"   📈 Объемы: усиляют сигнал\n"

            summary += "\n"

        return summary


# Глобальный экземпляр
smart_alerts = SmartAlertSystem()