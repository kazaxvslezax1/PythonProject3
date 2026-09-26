# volume_analyzer_advanced.py
import requests
import numpy as np
from datetime import datetime, timedelta


class AdvancedVolumeAnalyzer:
    def __init__(self):
        self.volume_threshold = 2.0  # Порог для всплеска объемов

    def get_volume_spike_analysis(self, symbol, timeframe='1h', period=50):
        """Анализ всплесков объемов"""
        try:
            response = requests.get(
                f"https://api.binance.com/api/v3/klines",
                params={
                    'symbol': symbol,
                    'interval': timeframe,
                    'limit': period
                }
            )

            if response.status_code == 200:
                data = response.json()
                volumes = [float(candle[5]) for candle in data]  # Volume
                closes = [float(candle[4]) for candle in data]  # Close prices

                # Анализ объемов
                avg_volume = np.mean(volumes)
                current_volume = volumes[-1]
                volume_ratio = current_volume / avg_volume

                # Определяем тип движения
                price_change = ((closes[-1] - closes[-2]) / closes[-2]) * 100

                analysis = {
                    'current_volume': current_volume,
                    'average_volume': avg_volume,
                    'volume_ratio': round(volume_ratio, 2),
                    'price_change_percent': round(price_change, 2),
                    'is_volume_spike': volume_ratio > self.volume_threshold,
                    'spike_strength': min(volume_ratio / self.volume_threshold, 3.0)  # Макс 3.0
                }

                # Определяем тип сигнала
                if analysis['is_volume_spike']:
                    if price_change > 2:
                        analysis['signal'] = 'PUMP_START'
                        analysis['confidence'] = 'HIGH'
                    elif price_change < -2:
                        analysis['signal'] = 'DUMP_START'
                        analysis['confidence'] = 'HIGH'
                    else:
                        analysis['signal'] = 'ACCUMULATION'
                        analysis['confidence'] = 'MEDIUM'
                else:
                    analysis['signal'] = 'NO_SPIKE'
                    analysis['confidence'] = 'LOW'

                return analysis

        except Exception as e:
            print(f"Ошибка анализа объемов {symbol}: {e}")

        return {'error': 'Не удалось проанализировать объемы'}

    # Добавь в класс AdvancedVolumeAnalyzer
    def get_real_time_volume_alert(self, symbol, timeframe='15m'):
        """Проверка для реального времени - быстрая и легкая"""
        try:
            response = requests.get(
                f"https://api.binance.com/api/v3/klines",
                params={
                    'symbol': symbol,
                    'interval': timeframe,
                    'limit': 20  # Только последние 20 свечей для скорости
                },
                timeout=5  # Быстрый таймаут
            )

            if response.status_code == 200:
                data = response.json()
                if len(data) < 2:
                    return None

                # Берем последние 2 свечи для сравнения
                current_candle = data[-1]
                previous_candle = data[-2]

                current_volume = float(current_candle[5])
                previous_volume = float(previous_candle[5])
                current_close = float(current_candle[4])
                previous_close = float(previous_candle[4])

                # Быстрый расчет
                volume_change = (current_volume / previous_volume) if previous_volume > 0 else 1
                price_change = ((current_close - previous_close) / previous_close) * 100

                # Определяем сигнал
                if volume_change > 3.0:  # Объем вырос в 3+ раза
                    if price_change > 2.0:
                        return {
                            'symbol': symbol,
                            'signal': 'PUMP_START',
                            'volume_ratio': round(volume_change, 1),
                            'price_change': round(price_change, 2),
                            'confidence': 'HIGH',
                            'timestamp': datetime.now()
                        }
                    elif price_change < -2.0:
                        return {
                            'symbol': symbol,
                            'signal': 'DUMP_START',
                            'volume_ratio': round(volume_change, 1),
                            'price_change': round(price_change, 2),
                            'confidence': 'HIGH',
                            'timestamp': datetime.now()
                        }
                    else:
                        return {
                            'symbol': symbol,
                            'signal': 'VOLUME_SPIKE',
                            'volume_ratio': round(volume_change, 1),
                            'price_change': round(price_change, 2),
                            'confidence': 'MEDIUM',
                            'timestamp': datetime.now()
                        }

        except Exception as e:
            print(f"Ошибка real-time volume для {symbol}: {e}")

        return None
# Создаем глобальный экземпляр
advanced_volume_analyzer = AdvancedVolumeAnalyzer()