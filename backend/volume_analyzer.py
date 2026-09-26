import requests
import pandas as pd
from datetime import datetime, timedelta


class VolumeAnalyzer:
    def __init__(self):
        self.volume_cache = {}
        self.cache_duration = timedelta(minutes=30)

    def get_volume_analysis(self, symbol):
        """Анализирует объемы торгов с улучшенной логикой"""
        try:
            # Используем Binance API для получения данных об объемах
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                current_volume = float(data['volume']) * float(data['lastPrice'])
                price_change = float(data['priceChangePercent'])

                # Анализ объема на свечах
                volume_signal = self._analyze_candle_volumes(symbol)

                # Определяем силу сигнала объема
                volume_strength = self._calculate_volume_strength(current_volume, price_change, volume_signal)

                return {
                    'current_volume': current_volume,
                    'volume_formatted': self.format_volume(current_volume),
                    'price_change_percent': price_change,
                    'signal': volume_signal,
                    'strength': volume_strength,
                    'message': self._generate_volume_message(current_volume, price_change, volume_signal,
                                                             volume_strength)
                }

            return {
                'current_volume': 0,
                'volume_formatted': 'Н/Д',
                'price_change_percent': 0,
                'signal': 'NO_DATA',
                'strength': 0,
                'message': '📊 ДАННЫЕ ОБ ОБЪЕМАХ НЕДОСТУПНЫ'
            }

        except Exception as e:
            return {
                'current_volume': 0,
                'volume_formatted': 'Н/Д',
                'price_change_percent': 0,
                'signal': 'ERROR',
                'strength': 0,
                'message': f'📊 ОШИБКА АНАЛИЗА ОБЪЕМОВ: {str(e)}'
            }

    def _analyze_candle_volumes(self, symbol):
        """Анализ объемов на последних свечах"""
        try:
            from data import get_candles
            df = get_candles(symbol, "15m", limit=20)

            if len(df) < 10:
                return "INSUFFICIENT_DATA"

            volumes = df['volume'].tail(10).astype(float)
            current_volume = volumes.iloc[-1]
            avg_volume = volumes.mean()

            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

            if volume_ratio > 2.0:
                return "VERY_HIGH_VOLUME"
            elif volume_ratio > 1.5:
                return "HIGH_VOLUME"
            elif volume_ratio > 0.8:
                return "NORMAL_VOLUME"
            else:
                return "LOW_VOLUME"

        except Exception as e:
            return f"ERROR: {str(e)}"

    def _calculate_volume_strength(self, current_volume, price_change, volume_signal):
        """Рассчитывает силу сигнала объема"""
        strength = 0

        # Бонус за высокие объемы
        if volume_signal == "VERY_HIGH_VOLUME":
            strength += 3
        elif volume_signal == "HIGH_VOLUME":
            strength += 2
        elif volume_signal == "LOW_VOLUME":
            strength -= 1

        # Бонус за объемы > $10M
        if current_volume > 10000000:
            strength += 2
        elif current_volume > 5000000:
            strength += 1
        elif current_volume < 1000000:
            strength -= 1

        # Усиление при движении цены с объемом
        if abs(price_change) > 5 and strength > 0:
            strength += 1

        return max(0, min(5, strength))

    def _generate_volume_message(self, current_volume, price_change, volume_signal, strength):
        """Генерирует сообщение об объемах"""
        volume_text = self.format_volume(current_volume)

        if volume_signal == "VERY_HIGH_VOLUME":
            emoji = "📈"
            message = f"ОЧЕНЬ ВЫСОКИЕ ОБЪЕМЫ ({volume_text}) - сигнал усилен"
        elif volume_signal == "HIGH_VOLUME":
            emoji = "📈"
            message = f"ВЫСОКИЕ ОБЪЕМЫ ({volume_text}) - подтверждение тренда"
        elif volume_signal == "NORMAL_VOLUME":
            emoji = "📊"
            message = f"НОРМАЛЬНЫЕ ОБЪЕМЫ ({volume_text})"
        elif volume_signal == "LOW_VOLUME":
            emoji = "📉"
            message = f"НИЗКИЕ ОБЪЕМЫ ({volume_text}) - осторожно"
        else:
            emoji = "📊"
            message = f"ОБЪЕМЫ: {volume_text}"

        # Добавляем оценку силы
        if strength >= 4:
            message += " 💪"
        elif strength <= 1:
            message += " 🚨"

        return f"{emoji} {message}"

    def format_volume(self, volume):
        """Форматирует объем для читаемости"""
        if volume >= 1000000000:  # $1B+
            return f"${volume / 1000000000:.2f}B"
        elif volume >= 1000000:  # $1M+
            return f"${volume / 1000000:.1f}M"
        elif volume >= 1000:  # $1K+
            return f"${volume / 1000:.0f}K"
        else:
            return f"${volume:,.0f}"


# Глобальный экземпляр
volume_analyzer = VolumeAnalyzer()