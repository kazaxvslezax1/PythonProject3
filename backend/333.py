# ai_confidence_checker.py - УЛУЧШЕННАЯ ВЕРСИЯ С РАЗНЫМИ ПОДХОДАМИ
import requests
from datetime import datetime, timedelta
import json


class AIConfidenceChecker:
    def __init__(self):
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
        """🎯 УМНЫЙ AI АНАЛИЗ С РАЗНЫМИ ПОДХОДАМИ ДЛЯ РАЗНЫХ МОНЕТ"""

        volume_ratio = signal_data.get('volume_ratio', 1.0)
        confluence = signal_data.get('confluence', 50)

        # 🔥 ИСПРАВЛЕННЫЙ КЛЮЧ КЭША
        cache_key = f"{symbol}_V{volume_ratio}_C{confluence}"
        print(f"🔍 КЭШ КЛЮЧ: {cache_key}")

        # 🔥 ПРОВЕРЯЕМ КЭШ
        cached_result = self._get_cached_analysis(cache_key)
        if cached_result:
            print(f"⚡ Использован кэш: {cache_key} -> {cached_result['ai_confidence_score']}/10")
            return cached_result

        try:
            # 🔽 ОПРЕДЕЛЯЕМ ТИП МОНЕТЫ И ПАРАМЕТРЫ
            coin_type = self.get_coin_type(symbol)
            params = self.get_coin_parameters(coin_type)

            print(f"🎯 ТИП МОНЕТЫ: {symbol} -> {params['description']}")

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
                confluence_score = 8.5
            elif confluence >= 60:
                confluence_score = 7.5
            elif confluence >= 50:
                confluence_score = 6.5
            elif confluence >= 40:
                confluence_score = 5.5
            elif confluence >= 30:
                confluence_score = 4.5
            elif confluence >= 20:
                confluence_score = 3.5
            elif confluence >= 10:
                confluence_score = 2.5
            else:
                confluence_score = 1.5

            # 🔽 РАСЧЕТ С УЧЕТОМ ТИПА МОНЕТЫ
            volume_weight = params['volume_weight']
            confluence_weight = params['confluence_weight']

            final_score = (volume_score * volume_weight) + (confluence_score * confluence_weight)
            final_score = max(1.0, min(10.0, round(final_score, 1)))

            print(
                f"📊 РАСЧЕТ ({coin_type}): V:{volume_score} * {volume_weight} + C:{confluence_score} * {confluence_weight} = {final_score}")

            # 🔽 УМНЫЕ РЕКОМЕНДАЦИИ С УЧЕТОМ ТИПА МОНЕТЫ
            min_ai_buy = params['min_ai_buy']
            min_volume = params['min_volume']

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

            # 🔥 СОХРАНЯЕМ В КЭШ
            self._set_cached_analysis(cache_key, result)
            print(f"🎯 СОХРАНЕНО В КЭШ: {cache_key} -> {final_score}/10 ({recommendation})")
            return result

        except Exception as e:
            print(f"❌ Ошибка AI: {e}")
            return {
                'ai_confidence_score': 4.0,
                'recommendation': '❌ ОШИБКА AI',
                'color': '🔴',
                'passed_checks': 0,
                'total_checks': 3
            }

    def analyze_signal_quality_with_server(self, symbol, signal_data):
        """Пробуем использовать AI сервер если доступен"""
        try:
            local_result = self.analyze_signal_quality(symbol, signal_data)

            if local_result['ai_confidence_score'] >= 7.0:
                try:
                    print(f"🔍 Проверяем AI сервер для {symbol}...")
                    response = requests.post(
                        "http://127.0.0.1:8000/analyze-smart",
                        params={"symbol": symbol},
                        timeout=3
                    )
                    if response.status_code == 200:
                        server_data = response.json()
                        print(f"✅ AI сервер ответил: {server_data}")
                except:
                    print("⚠️ AI сервер недоступен")

            return local_result

        except Exception as e:
            print(f"❌ Ошибка комбинированного анализа: {e}")
            return self.analyze_signal_quality(symbol, signal_data)

    def should_send_alert(self, *args, **kwargs):
        """Совместимость со старым кодом"""
        return True

    def get_global_market_sentiment(self):
        """Анализ общего настроения рынка"""
        try:
            top_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']
            bullish_count = 0
            total_analyzed = 0

            for symbol in top_symbols:
                try:
                    response = requests.post(
                        f"{self.api_url}/analyze-smart",
                        params={"symbol": symbol},
                        timeout=5
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if "error" not in data:
                            if data.get('action') == 'BUY':
                                bullish_count += 1
                            total_analyzed += 1
                except:
                    continue

            sentiment = bullish_count / total_analyzed if total_analyzed > 0 else 0.5
            return sentiment, f"Бычьих сигналов: {bullish_count}/{total_analyzed} ({sentiment:.1%})"

        except Exception as e:
            print(f"Ошибка анализа рынка: {e}")
            return 0.5, "❌ Ошибка анализа рынка"


# Создаем глобальный экземпляр
ai_checker = AIConfidenceChecker()
smart_alerts_ai = ai_checker