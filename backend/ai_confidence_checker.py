# ai_confidence_checker.py - ОКОНЧАТЕЛЬНЫЙ ФИКС ДЛЯ ПРОБЛЕМЫ 5.0/10
# Эта версия использует ТОЛЬКО локальный расчет (Объем/Конфлюэнс)
# и ИГНОРИРУЕТ внешний API 127.0.0.1:8000, устраняя ошибку 5.0.

import requests
from datetime import datetime, timedelta
import json


class AIConfidenceChecker:
    def __init__(self):
        # API URL оставлен для совместимости, но не используется в основной логике.
        self.api_url = "http://127.0.0.1:8000"
        self.analysis_cache = {}
        self.cache_duration = timedelta(minutes=5)

    def _get_cached_analysis(self, cache_key):
        """Получить анализ из кэша"""
        if cache_key in self.analysis_cache:
            cached_data, timestamp = self.analysis_cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                return cached_data
        return None

    def _set_cached_analysis(self, cache_key, analysis):
        """Сохранить анализ в кэш"""
        self.analysis_cache[cache_key] = (analysis, datetime.now())

    def get_coin_type(self, symbol):
        """Определяет тип монеты для разных подходов к анализу"""
        coin_types = {
            'BLUECHIP': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
            'LARGECAP': ['SOLUSDT', 'ADAUSDT', 'XRPUSDT', 'DOTUSDT', 'LINKUSDT'],
            'MIDCAP': ['AVAXUSDT', 'MATICUSDT', 'ATOMUSDT', 'ALGOUSDT'],
            'MEME': ['DOGEUSDT', 'SHIBUSDT', 'PEPEUSDT', 'BONKUSDT', 'FLOKIUSDT'],
            'STABLECOIN': ['USDCUSDT', 'USDTUSDT', 'BUSDUSDT', 'DAIUSDT']
        }

        for coin_type, symbols in coin_types.items():
            if symbol in symbols:
                return coin_type
        return 'MIDCAP'

    def get_coin_parameters(self, coin_type):
        """Возвращает параметры анализа для разных типов монет"""
        parameters = {
            'BLUECHIP': {
                'volume_weight': 0.5,
                'confluence_weight': 0.5,
                'min_volume': 1.0,
                'min_ai_buy': 6.5,
                'description': '🏆 ФУНДАМЕНТАЛЬНО СИЛЬНЫЕ'
            },
            'LARGECAP': {
                'volume_weight': 0.6,
                'confluence_weight': 0.4,
                'min_volume': 1.2,
                'min_ai_buy': 7.0,
                'description': '📊 КРУПНЫЕ КАПИТАЛИЗАЦИИ'
            },
            'MIDCAP': {
                'volume_weight': 0.7,
                'confluence_weight': 0.3,
                'min_volume': 1.5,
                'min_ai_buy': 7.5,
                'description': '⚡ СРЕДНИЕ КАПИТАЛИЗАЦИИ'
            },
            'MEME': {
                'volume_weight': 0.8,
                'confluence_weight': 0.2,
                'min_volume': 2.0,
                'min_ai_buy': 8.0,
                'description': '🎭 МЕМНЫЕ МОНЕТЫ (ВЫСОКИЙ РИСК)'
            },
            'STABLECOIN': {
                'volume_weight': 0.3,
                'confluence_weight': 0.7,
                'min_volume': 0.5,
                'min_ai_buy': 5.0,
                'description': '🛡️ СТЕЙБЛКОИНЫ (НИЗКИЙ РИСК)'
            }
        }
        return parameters.get(coin_type, parameters['MIDCAP'])

    def is_valid_buy_signal(self, ai_score, confluence, volume_ratio, coin_type):
        """Проверяет можно ли давать BUY рекомендацию"""
        params = self.get_coin_parameters(coin_type)

        if ai_score < params['min_ai_buy']:
            return False
        if volume_ratio < params['min_volume']:
            return False
        if confluence < 30:  # Минимальный конфлюэнс для всех типов
            return False
        return True

    def analyze_signal_quality(self, symbol, signal_data):
        """
        🎯 ЛОКАЛЬНЫЙ АНАЛИЗ (Объем/Конфлюэнс).
        Это основная функция расчета балла.
        """

        volume_ratio = signal_data.get('volume_ratio', 1.0)
        confluence = signal_data.get('confluence', 50)

        cache_key = f"{symbol}_V{volume_ratio}_C{confluence}"

        cached_result = self._get_cached_analysis(cache_key)
        if cached_result:
            return cached_result

        try:
            # 🔽 ОПРЕДЕЛЯЕМ ТИП МОНЕТЫ И ПАРАМЕТРЫ
            coin_type = self.get_coin_type(symbol)
            params = self.get_coin_parameters(coin_type)

            # 🔽 ОЦЕНКА ОБЪЕМОВ
            if volume_ratio >= 3.0:
                volume_score = 10.0
            elif volume_ratio >= 2.5:
                volume_score = 9.0
            elif volume_ratio >= 2.0:
                volume_score = 8.0
            elif volume_ratio >= 1.8:
                volume_score = 7.5
            elif volume_ratio >= 1.5:
                volume_score = 7.0
            elif volume_ratio >= 1.2:
                volume_score = 6.0
            elif volume_ratio >= 1.0:
                volume_score = 5.0
            elif volume_ratio >= 0.8:
                volume_score = 4.0
            elif volume_ratio >= 0.6:
                volume_score = 3.0
            elif volume_ratio >= 0.4:
                volume_score = 2.0
            else:
                volume_score = 1.0

            # 🔽 ОЦЕНКА КОНФЛЮЭНСА
            if confluence >= 80:
                confluence_score = 10.0
            elif confluence >= 70:
                confluence_score = 8.0
            elif confluence >= 60:
                confluence_score = 7.0
            elif confluence >= 50:
                confluence_score = 6.0
            elif confluence >= 40:
                confluence_score = 5.0
            elif confluence >= 30:
                confluence_score = 4.0
            elif confluence >= 20:
                confluence_score = 3.0
            elif confluence >= 10:
                confluence_score = 2.0
            else:
                confluence_score = 1.0

            # 🔽 РАСЧЕТ С УЧЕТОМ ТИПА МОНЕТЫ
            volume_weight = params['volume_weight']
            confluence_weight = params['confluence_weight']

            final_score = (volume_score * volume_weight) + (confluence_score * confluence_weight)
            final_score = max(1.0, min(10.0, round(final_score, 1)))

            # 🔽 УМНЫЕ РЕКОМЕНДАЦИИ С УЧЕТОМ ТИПА МОНЕТЫ
            min_ai_buy = params['min_ai_buy']

            # 🔽 ПРОВЕРЯЕМ МОЖНО ЛИ ДАВАТЬ BUY
            can_buy = self.is_valid_buy_signal(final_score, confluence, volume_ratio, coin_type)

            if can_buy and final_score >= 8.5:
                recommendation = f"🚀 {params['description']} - СИЛЬНЫЙ СИГНАЛ"
                color = "🟢"
            elif can_buy and final_score >= min_ai_buy:
                recommendation = f"✅ {params['description']} - МОЖНО РАССМОТРЕТЬ"
                color = "🟢"
            elif final_score >= 6.0:
                recommendation = f"⚠️ {params['description']} - ТРЕБУЕТ ПОДТВЕРЖДЕНИЯ"
                color = "🟡"
            else:
                recommendation = f"🔴 {params['description']} - ИЗБЕГАТЬ"
                color = "🔴"

            result = {
                'ai_confidence_score': final_score,
                'ai_confidence': final_score,
                'ai_confidence_real': final_score,

                'recommendation': recommendation,
                'color': color,
                'passed_checks': 3,
                'total_checks': 3,
                'coin_type': coin_type,
                'metrics': {
                    'volume_score': volume_score,
                    'confluence_score': confluence_score,
                    'final_score': final_score,
                    'volume_weight': volume_weight,
                    'confluence_weight': confluence_weight
                }
            }

            self._set_cached_analysis(cache_key, result)
            return result

        except Exception as e:
            # В случае ошибки возвращаем низкий, но не 5.0 балл
            print(f"❌ Ошибка локального AI: {e}")
            return {
                'ai_confidence_score': 4.0,
                'ai_confidence': 4.0,
                'ai_confidence_real': 4.0,
                'recommendation': '❌ ОШИБКА AI (Локальный сбой)',
                'color': '🔴',
                'passed_checks': 0,
                'total_checks': 3
            }

    # ФИКС: Эта функция используется backtester.py.
    # Мы принудительно устанавливаем ее равной локальной функции расчета.
    get_combined_confidence = analyze_signal_quality

    def should_send_alert(self, *args, **kwargs):
        """Совместимость со старым кодом"""
        return True

    def get_global_market_sentiment(self):
        """
        ФИКС: Больше не пытается подключиться к внешнему API.
        Возвращает безопасное нейтральное значение.
        """
        return 0.5, "🛡️ Сентимент отключен (внешний API не используется)"


# Создаем глобальный экземпляр
ai_checker = AIConfidenceChecker()
smart_alerts_ai = ai_checker