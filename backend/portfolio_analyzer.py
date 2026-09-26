import numpy as np
import pandas as pd
from datetime import datetime


class PortfolioAnalyzer:
    def __init__(self):
        self.correlation_threshold = 0.7

    def analyze_portfolio(self, positions):
        """Анализ риска портфеля"""
        try:
            if not positions:
                return {"error": "Нет позиций для анализа"}

            total_value = sum(pos['value'] for pos in positions)

            # Анализ распределения
            allocation = self._calculate_allocation(positions, total_value)

            # Анализ риска
            risk_analysis = self._calculate_portfolio_risk(positions, total_value)

            # Анализ корреляции
            correlation_analysis = self._analyze_correlations(positions)

            return {
                'total_value': total_value,
                'position_count': len(positions),
                'allocation': allocation,
                'risk_analysis': risk_analysis,
                'correlation_analysis': correlation_analysis,
                'recommendations': self._generate_recommendations(allocation, risk_analysis, correlation_analysis)
            }

        except Exception as e:
            return {"error": f"Ошибка анализа портфеля: {str(e)}"}

    def _calculate_allocation(self, positions, total_value):
        """Расчет распределения активов"""
        allocation = {}

        for pos in positions:
            symbol = pos['symbol']
            value = pos['value']
            percent = (value / total_value) * 100

            allocation[symbol] = {
                'value': value,
                'percent': round(percent, 2),
                'risk_level': pos.get('risk_level', 'MEDIUM')
            }

        return allocation

    def _calculate_portfolio_risk(self, positions, total_value):
        """Расчет риска портфеля"""
        high_risk_value = sum(pos['value'] for pos in positions if pos.get('risk_score', 3) >= 4)
        medium_risk_value = sum(pos['value'] for pos in positions if pos.get('risk_score', 3) == 3)
        low_risk_value = sum(pos['value'] for pos in positions if pos.get('risk_score', 3) <= 2)

        high_risk_percent = (high_risk_value / total_value) * 100
        medium_risk_percent = (medium_risk_value / total_value) * 100
        low_risk_percent = (low_risk_value / total_value) * 100

        # Общая оценка риска
        if high_risk_percent > 30:
            overall_risk = "🔴 ВЫСОКИЙ"
        elif high_risk_percent > 15:
            overall_risk = "🟡 СРЕДНИЙ"
        else:
            overall_risk = "🟢 НИЗКИЙ"

        return {
            'high_risk_percent': round(high_risk_percent, 1),
            'medium_risk_percent': round(medium_risk_percent, 1),
            'low_risk_percent': round(low_risk_percent, 1),
            'overall_risk': overall_risk,
            'concentration_risk': self._calculate_concentration_risk(positions, total_value)
        }

    def _calculate_concentration_risk(self, positions, total_value):
        """Расчет риска концентрации"""
        if not positions:
            return "НЕТ ДАННЫХ"

        # Риск самой крупной позиции
        largest_position = max(positions, key=lambda x: x['value'])
        largest_percent = (largest_position['value'] / total_value) * 100

        if largest_percent > 50:
            return "🔴 ОЧЕНЬ ВЫСОКИЙ (одна позиция > 50%)"
        elif largest_percent > 30:
            return "🟡 ВЫСОКИЙ (одна позиция > 30%)"
        elif largest_percent > 20:
            return "🟡 УМЕРЕННЫЙ (одна позиция > 20%)"
        else:
            return "🟢 НИЗКИЙ (хорошая диверсификация)"

    def _analyze_correlations(self, positions):
        """Анализ корреляции между активами"""
        # В реальной системе здесь был бы расчет корреляции на исторических данных
        # Сейчас используем упрощенную логику

        symbols = [pos['symbol'] for pos in positions]

        if len(symbols) <= 1:
            return {
                'high_correlation_pairs': [],
                'correlation_risk': "🟢 НИЗКИЙ (мало позиций)"
            }

        # Предполагаем, что BTC и ETH имеют высокую корреляцию
        high_correlation_pairs = []
        if 'BTCUSDT' in symbols and 'ETHUSDT' in symbols:
            high_correlation_pairs.append(('BTCUSDT', 'ETHUSDT'))

        correlation_risk = "🔴 ВЫСОКИЙ" if len(high_correlation_pairs) > 0 else "🟢 НИЗКИЙ"

        return {
            'high_correlation_pairs': high_correlation_pairs,
            'correlation_risk': correlation_risk
        }

    def _generate_recommendations(self, allocation, risk_analysis, correlation_analysis):
        """Генерация рекомендаций по портфелю"""
        recommendations = []

        # Рекомендации по риску
        if risk_analysis['high_risk_percent'] > 30:
            recommendations.append("🔴 СРОЧНО УМЕНЬШИТЕ ВЫСОКОРИСКОВЫЕ АКТИВЫ")
        elif risk_analysis['high_risk_percent'] > 15:
            recommendations.append("🟡 РАССМОТРИТЕ УМЕНЬШЕНИЕ ВЫСОКОРИСКОВЫХ АКТИВОВ")

        # Рекомендации по концентрации
        if "ВЫСОКИЙ" in risk_analysis['concentration_risk']:
            recommendations.append("🎯 ДИВЕРСИФИЦИРУЙТЕ ПОРТФЕЛЬ - уменьшите крупнейшие позиции")

        # Рекомендации по корреляции
        if correlation_analysis['correlation_risk'] == "🔴 ВЫСОКИЙ":
            recommendations.append("📊 ДОБАВЬТЕ НЕКОРРЕЛИРОВАННЫЕ АКТИВЫ")

        if not recommendations:
            recommendations.append("✅ ПОРТФЕЛЬ ОПТИМАЛЬНО СБАЛАНСИРОВАН")

        return recommendations

    def calculate_rebalancing(self, current_allocation, target_allocation):
        """Расчет ребалансировки портфеля"""
        rebalancing = {}

        for symbol, current in current_allocation.items():
            target = target_allocation.get(symbol, {'percent': 0})

            current_percent = current['percent']
            target_percent = target['percent']

            difference = target_percent - current_percent

            if abs(difference) > 2:  # Ребалансируем если разница > 2%
                rebalancing[symbol] = {
                    'current_percent': current_percent,
                    'target_percent': target_percent,
                    'difference': round(difference, 2),
                    'action': 'BUY' if difference > 0 else 'SELL'
                }

        return rebalancing


# Глобальный экземпляр
portfolio_analyzer = PortfolioAnalyzer()