import requests
import pandas as pd
from datetime import datetime, timedelta


class QualityFilter:
    def __init__(self):
        self.low_quality_keywords = [
            'BABY', 'ELON', 'FLOKI', 'SHIB', 'PEPE', 'BONK', 'MEME', 'TURBO',
            'AKITA', 'KISHU', 'SAFEMOON', 'DOGE', 'SAMO', 'WIF', 'BOME'
        ]

        self.blacklist = [
            'ACHUSDT', 'BTTUSDT', 'SCUSDT', 'HOTUSDT', 'WINUSDT', 'SXPUSDT',
            'PERLUSDT', 'BEAMUSDT', 'MBLUSDT', 'TVKUSDT', 'SLPUSDT'
        ]

        self.whitelist = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT',
            'AVAXUSDT', 'DOTUSDT', 'MATICUSDT', 'LTCUSDT', 'LINKUSDT', 'ATOMUSDT',
            'UNIUSDT', 'XLMUSDT', 'ALGOUSDT', 'TRXUSDT', 'VETUSDT', 'ICPUSDT',
            'FILUSDT', 'AAVEUSDT', 'COMPUSDT', 'MKRUSDT', 'SNXUSDT', 'CRVUSDT'
        ]

    def is_high_quality(self, symbol):
        """Проверяет является ли актив качественным"""
        # Вайтлист - всегда пропускаем
        if symbol in self.whitelist:
            return True

        # Блеклист - всегда отклоняем
        if symbol in self.blacklist:
            return False

        # Фильтр по ключевым словам мемкоинов
        if any(keyword in symbol for keyword in self.low_quality_keywords):
            return False

        return True

    def get_asset_rating(self, symbol, price, volume_24h=None, market_cap=None):
        """Рассчитывает рейтинг актива от 1 до 10"""
        rating = 5.0  # Средний стартовый рейтинг

        # Бонус за вайтлист
        if symbol in self.whitelist:
            rating += 2.0

        # Штраф за блеклист
        if symbol in self.blacklist:
            rating -= 3.0

        # Оценка по цене
        if price > 10.0:
            rating += 1.5
        elif price > 1.0:
            rating += 1.0
        elif price > 0.1:
            rating += 0.5
        elif price < 0.01:
            rating -= 2.0

        # Оценка по объему (если данные есть)
        if volume_24h:
            if volume_24h > 100000000:  # $100M+
                rating += 2.0
            elif volume_24h > 50000000:  # $50M+
                rating += 1.5
            elif volume_24h > 10000000:  # $10M+
                rating += 1.0
            elif volume_24h < 1000000:  # <$1M
                rating -= 1.5

        # Оценка по капитализации (если данные есть)
        if market_cap:
            if market_cap > 10000000000:  # $10B+
                rating += 2.0
            elif market_cap > 1000000000:  # $1B+
                rating += 1.5
            elif market_cap < 100000000:  # <$100M
                rating -= 1.0

        # Ограничиваем рейтинг от 1 до 10
        return max(1.0, min(10.0, round(rating, 1)))

    def get_risk_score(self, symbol, price, volatility, volume_24h=None):
        """Рассчитывает оценку риска от 1 до 5"""
        risk_score = 0

        # Цена < $0.01 = высокий риск
        if price < 0.01:
            risk_score += 2

        # Цена < $0.10 = средний риск
        elif price < 0.10:
            risk_score += 1

        # Волатильность > 20% = высокий риск
        if volatility > 20:
            risk_score += 2
        elif volatility > 10:
            risk_score += 1

        # Низкие объемы = высокий риск
        if volume_24h and volume_24h < 5000000:  # <$5M
            risk_score += 1

        # Мемкоины = дополнительный риск
        if any(keyword in symbol for keyword in self.low_quality_keywords):
            risk_score += 1

        return min(5, max(1, risk_score))

    def get_confidence_level(self, signal_strength, volume_analysis, risk_score):
        """Рассчитывает уровень доверия к сигналу"""
        base_confidence = abs(signal_strength) * 1.5

        # Корректировка на основе объема
        if "ВЫШЕ СРЕДНЕГО" in volume_analysis:
            base_confidence += 2
        elif "НИЗКИЕ" in volume_analysis:
            base_confidence -= 1

        # Корректировка на основе риска
        base_confidence -= (risk_score - 1)

        confidence = max(1, min(10, round(base_confidence)))

        if confidence >= 8:
            return confidence, "🎯 ВЫСОКАЯ НАДЕЖНОСТЬ"
        elif confidence >= 5:
            return confidence, "🟡 СРЕДНЯЯ НАДЕЖНОСТЬ"
        else:
            return confidence, "🔴 НИЗКАЯ НАДЕЖНОСТЬ"


# Глобальный экземпляр
quality_filter = QualityFilter()