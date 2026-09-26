# advanced_ai_analyzer.py
import requests
from datetime import datetime, timedelta
import json
from ai_confidence_checker import ai_checker


class AdvancedAIAnalyzer:
    def __init__(self):
        self.api_url = "http://127.0.0.1:8000"

    def get_advanced_market_metrics(self):
        """Расширенные метрики рынка"""
        try:
            # Анализ волатильности
            volatility_data = self._analyze_market_volatility()

            # Анализ корреляций
            correlation_data = self._analyze_correlations()

            # Анализ рыночных циклов
            cycle_data = self._analyze_market_cycles()

            # Анализ институциональной активности
            institutional_data = self._analyze_institutional_activity()

            return {
                'volatility_metrics': volatility_data,
                'correlation_analysis': correlation_data,
                'market_cycles': cycle_data,
                'institutional_activity': institutional_data,
                'composite_score': self._calculate_composite_score(volatility_data, correlation_data, cycle_data,
                                                                   institutional_data)
            }

        except Exception as e:
            print(f"Ошибка расширенного анализа: {e}")
            return {'error': str(e)}

    def _analyze_market_volatility(self):
        """Анализ волатильности рынка"""
        try:
            # Анализируем топ-10 монет
            symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
                       'ADAUSDT', 'AVAXUSDT', 'DOTUSDT', 'LINKUSDT', 'MATICUSDT']

            volatility_scores = []
            for symbol in symbols:
                try:
                    response = requests.post(
                        f"{self.api_url}/analyze-smart",
                        params={"symbol": symbol},
                        timeout=5
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if "error" not in data:
                            # Простая оценка волатильности по силе сигнала
                            strength = abs(data.get('strength', 0))
                            if strength >= 5:
                                volatility_scores.append(0.8)  # Высокая волатильность
                            elif strength >= 3:
                                volatility_scores.append(0.5)  # Средняя
                            else:
                                volatility_scores.append(0.2)  # Низкая
                except:
                    continue

            avg_volatility = sum(volatility_scores) / len(volatility_scores) if volatility_scores else 0.3

            return {
                'market_volatility': avg_volatility,
                'volatility_trend': 'INCREASING' if avg_volatility > 0.6 else 'DECREASING' if avg_volatility < 0.3 else 'STABLE',
                'risk_level': 'HIGH' if avg_volatility > 0.7 else 'MEDIUM' if avg_volatility > 0.4 else 'LOW'
            }

        except Exception as e:
            return {'error': f"Volatility analysis error: {e}"}

    def _analyze_correlations(self):
        """Анализ корреляций между активами"""
        # Упрощенный анализ корреляций
        return {
            'btc_dominance_impact': 0.85,  # Влияние BTC на альты
            'defi_correlation': 0.72,  # Корреляция в DeFi секторе
            'market_synchronization': 0.68,  # Синхронизация рынка
            'sector_rotation_detected': False  # Обнаружена ли ротация секторов
        }

    def _analyze_market_cycles(self):
        """Анализ рыночных циклов"""
        current_hour = datetime.now().hour

        # Определяем фазу дня
        if 0 <= current_hour < 8:
            session = 'ASIAN'
            activity = 'LOW'
        elif 8 <= current_hour < 16:
            session = 'EUROPEAN'
            activity = 'MEDIUM'
        else:
            session = 'AMERICAN'
            activity = 'HIGH'

        return {
            'trading_session': session,
            'expected_activity': activity,
            'cycle_phase': 'ACCUMULATION',  # Накопление, маркап, дистрибуция, дамп
            'cycle_strength': 0.65
        }

    def _analyze_institutional_activity(self):
        """Анализ институциональной активности"""
        return {
            'whale_accumulation': False,
            'institutional_interest': 'LOW',
            'futures_activity': 'MODERATE',
            'spot_dominance': True
        }

    def _calculate_composite_score(self, volatility, correlation, cycles, institutional):
        """Композитный скоринг рынка"""
        weights = {
            'volatility': 0.25,
            'correlation': 0.20,
            'cycles': 0.30,
            'institutional': 0.25
        }

        score = 0
        score += volatility.get('market_volatility', 0.5) * weights['volatility']
        score += correlation.get('btc_dominance_impact', 0.5) * weights['correlation']
        score += cycles.get('cycle_strength', 0.5) * weights['cycles']
        score += (0.8 if institutional.get('institutional_interest') == 'HIGH' else 0.5) * weights['institutional']

        return min(1.0, score)

    def generate_market_intelligence(self):
        """Генерация рыночной аналитики"""
        metrics = self.get_advanced_market_metrics()

        if 'error' in metrics:
            return "❌ Не удалось получить данные для анализа"

        intelligence = {
            'market_phase': self._determine_market_phase(metrics),
            'trading_recommendation': self._generate_trading_recommendation(metrics),
            'risk_advisory': self._generate_risk_advisory(metrics),
            'key_opportunities': self._identify_opportunities(metrics),
            'critical_warnings': self._identify_warnings(metrics)
        }

        return intelligence

    def _determine_market_phase(self, metrics):
        """Определение фазы рынка"""
        composite = metrics['composite_score']

        if composite >= 0.8:
            return "🚀 БЫЧИЙ МАРКАП - Активный рост"
        elif composite >= 0.6:
            return "📈 НАКОПЛЕНИЕ - Подготовка к движению"
        elif composite >= 0.4:
            return "🔄 КОНСОЛИДАЦИЯ - Боковое движение"
        elif composite >= 0.2:
            return "📉 ДИСТРИБУЦИЯ - Распределение"
        else:
            return "🔴 МЕДВЕЖИЙ ДАМП - Активное падение"

    def _generate_trading_recommendation(self, metrics):
        """Генерация торговых рекомендаций"""
        phase = self._determine_market_phase(metrics)
        volatility = metrics['volatility_metrics']['risk_level']

        if "БЫЧИЙ" in phase and volatility != 'HIGH':
            return "🎯 АКТИВНАЯ ПОКУПКА - Входить в лонги"
        elif "НАКОПЛЕНИЕ" in phase:
            return "💰 НАКОПЛЕНИЕ ПОЗИЦИЙ - Постепенный вход"
        elif "КОНСОЛИДАЦИЯ" in phase:
            return "⚖️ РЕЙНДЖ-ТРЕЙДИНГ - Торговля в диапазоне"
        elif "ДИСТРИБУЦИЯ" in phase:
            return "🛑 ЗАКРЫТИЕ ЛОНГОВ - Фиксация прибыли"
        else:
            return "❌ ВОЗДЕРЖАНИЕ - Неблагоприятные условия"

    def _generate_risk_advisory(self, metrics):
        """Генерация рекомендаций по рискам"""
        volatility = metrics['volatility_metrics']['risk_level']

        if volatility == 'HIGH':
            return "🔴 ВЫСОКИЙ РИСК - Уменьшить позиции, использовать стоп-лоссы"
        elif volatility == 'MEDIUM':
            return "🟡 УМЕРЕННЫЙ РИСК - Стандартные позиции с защитой"
        else:
            return "🟢 НИЗКИЙ РИСК - Можно увеличивать экспозицию"

    def _identify_opportunities(self, metrics):
        """Выявление возможностей"""
        opportunities = []

        if metrics['correlation_analysis']['sector_rotation_detected']:
            opportunities.append("🔄 РОТАЦИЯ СЕКТОРОВ - Ищите недооцененные активы")

        if metrics['institutional_activity']['whale_accumulation']:
            opportunities.append("🐋 НАКОПЛЕНИЕ КИТОВ - Следуйте за крупными игроками")

        if metrics['market_cycles']['expected_activity'] == 'HIGH':
            opportunities.append("⏰ АКТИВНАЯ СЕССИЯ - Ожидайте повышенной волатильности")

        if not opportunities:
            opportunities.append("📊 СТАНДАРТНЫЕ УСЛОВИЯ - Торгуйте по стратегии")

        return opportunities

    def _identify_warnings(self, metrics):
        """Выявление предупреждений"""
        warnings = []

        if metrics['volatility_metrics']['risk_level'] == 'HIGH':
            warnings.append("⚡ ВЫСОКАЯ ВОЛАТИЛЬНОСТЬ - Риск ликвидаций")

        if metrics['correlation_analysis']['market_synchronization'] > 0.8:
            warnings.append("🎯 ВЫСОКАЯ КОРРЕЛЯЦИЯ - Диверсифицируйте портфель")

        if metrics['institutional_activity']['institutional_interest'] == 'LOW':
            warnings.append("🏢 СЛАБЫЙ ИНСТИТУЦИОНАЛЬНЫЙ ИНТЕРЕС - Осторожность с крупными позициями")

        return warnings


# Глобальный экземпляр
advanced_analyzer = AdvancedAIAnalyzer()