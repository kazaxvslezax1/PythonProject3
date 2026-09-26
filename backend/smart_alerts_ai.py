# smart_alerts_ai.py
from datetime import datetime, timedelta
from collections import defaultdict
from ai_confidence_checker import ai_checker


class SmartAlertsAI:
    def __init__(self, ai_checker=ai_checker): # ✅ ИСПРАВЛЕНИЕ 1: Добавляем ai_checker в __init__
        self.ai_checker = ai_checker # ✅ ИСПРАВЛЕНИЕ 2: Сохраняем в переменную экземпляра
        self.alert_history = defaultdict(list)
        self.cooldown_period = timedelta(minutes=10)

    def should_send_alert(self, symbol, signal_type, strength):
        """AI-проверка нужно ли отправлять алерт"""
        try:
            # Проверяем кулдаун
            last_alert = self.alert_history.get(symbol)
            if last_alert and datetime.now() - last_alert[-1] < self.cooldown_period:
                return False

            # AI-анализ надежности сигнала
            ai_analysis = self.ai_checker.analyze_signal_quality(symbol, {
                'current_price': 0,
                'action': signal_type
            })

            # Фильтруем по AI-уверенности
            if ai_analysis['ai_confidence_score'] < 6.0:
                print(f"AI отфильтровал слабый сигнал: {symbol} ({ai_analysis['ai_confidence_score']}/10)")
                return False

            # Фильтруем по силе сигнала
            if abs(strength) < 4:
                return False

            # Записываем в историю
            self.alert_history[symbol].append(datetime.now())

            # Ограничиваем историю (последние 50 алертов)
            if len(self.alert_history[symbol]) > 50:
                self.alert_history[symbol] = self.alert_history[symbol][-50:]

            return True

        except Exception as e:
            print(f"Ошибка AI-фильтра алертов: {e}")
            return True  # В случае ошибки отправляем алерт

    def prioritize_alerts(self, alerts):
        """Приоритизация алертов по AI-оценке"""
        try:
            scored_alerts = []
            for alert in alerts:

                # 🔽 🔽 🔽 ИСПРАВЛЕНИЕ: ПРОВЕРЯЕМ СУЩЕСТВУЮЩУЮ AI-ОЦЕНКУ 🔽 🔽 🔽

                ai_confidence_score = alert.get('ai_confidence')

                # Если AI-оценки нет в словаре (пришла из другого источника), тогда рассчитываем
                if ai_confidence_score is None:
                    symbol = alert['symbol']
                    ai_analysis = ai_checker.analyze_signal_quality(symbol, {
                        'current_price': alert.get('price', 0),
                        'action': alert.get('signal_type', 'HOLD')
                    })
                    ai_confidence_score = ai_analysis['ai_confidence_score']

                # 🔽 🔽 🔽 ДАЛЬНЕЙШИЙ РАСЧЕТ ПРИОРИТЕТА ИСПОЛЬЗУЕТ ai_confidence_score 🔽 🔽 🔽

                # Считаем приоритет (AI уверенность + сила сигнала)
                priority_score = (
                        ai_confidence_score * 0.6 +  # Используем найденный/пересчитанный балл
                        abs(alert.get('strength', 0)) * 0.4
                )

                scored_alerts.append({
                    **alert,
                    'ai_priority': priority_score,
                    'ai_confidence': ai_confidence_score  # Сохраняем финальный балл
                })

            # Сортируем по приоритету
            scored_alerts.sort(key=lambda x: x['ai_priority'], reverse=True)
            return scored_alerts

        except Exception as e:
            print(f"Ошибка приоритизации: {e}")
            return alerts

    def filter_duplicate_alerts(self, alerts):
        """Фильтрация дублирующих алертов"""
        filtered = []
        seen_symbols = set()

        for alert in alerts:
            symbol = alert['symbol']
            if symbol not in seen_symbols:
                filtered.append(alert)
                seen_symbols.add(symbol)

        return filtered

    def generate_alert_summary(self, alerts):
        """Генерация сводки по алертам"""
        if not alerts:
            return "🤖 AI: Важных алертов нет"

        strong_alerts = [a for a in alerts if a.get('ai_confidence', 0) >= 7.0]
        medium_alerts = [a for a in alerts if 5.0 <= a.get('ai_confidence', 0) < 7.0]

        summary = f"🤖 AI-СВОДКА АЛЕРТОВ:\n"
        summary += f"• 🔥 Важных: {len(strong_alerts)}\n"
        summary += f"• ⚠️ Средних: {len(medium_alerts)}\n"
        summary += f"• 📊 Всего: {len(alerts)}\n"

        if strong_alerts:
            top_alert = strong_alerts[0]
            summary += f"\n🎯 ТОП-СИГНАЛ: {top_alert['symbol']} "
            summary += f"(AI: {top_alert.get('ai_confidence', 0):.1f}/10)"

        return summary


# Создаем глобальный экземпляр
smart_alerts_ai = SmartAlertsAI()