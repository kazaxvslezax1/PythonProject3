import requests
import pandas as pd
from datetime import datetime
from technical_indicators import calculate_all_indicators


class TrendAnalyzer:
    def __init__(self):
        self.timeframes = ['15m', '1h', '4h', '1d']

    def multi_timeframe_analysis(self, symbol):
        """Анализ тренда на нескольких таймфреймах"""
        try:
            from data import get_candles

            timeframe_signals = {}
            confluence_score = 0
            total_bullish = 0
            total_bearish = 0

            for timeframe in self.timeframes:
                try:
                    df = get_candles(symbol, timeframe, limit=100)
                    if len(df) < 20:
                        continue

                    df = calculate_all_indicators(df)
                    trend_signal = self._analyze_trend(df, timeframe)

                    timeframe_signals[timeframe] = trend_signal

                    if trend_signal['direction'] == 'BULLISH':
                        total_bullish += trend_signal['strength']
                    elif trend_signal['direction'] == 'BEARISH':
                        total_bearish += trend_signal['strength']

                except Exception as e:
                    print(f"Ошибка анализа {timeframe}: {e}")
                    continue

            # Расчет конфлюэнса
            if total_bullish + total_bearish > 0:
                confluence_score = (total_bullish - total_bearish) / (total_bullish + total_bearish) * 100

            # Определение общего направления
            if confluence_score > 20:
                overall_trend = "🟢 СИЛЬНЫЙ ВОСХОДЯЩИЙ"
            elif confluence_score > 5:
                overall_trend = "🟢 ВОСХОДЯЩИЙ"
            elif confluence_score < -20:
                overall_trend = "🔴 СИЛЬНЫЙ НИСХОДЯЩИЙ"
            elif confluence_score < -5:
                overall_trend = "🔴 НИСХОДЯЩИЙ"
            else:
                overall_trend = "🟡 НЕЙТРАЛЬНЫЙ"

            return {
                'symbol': symbol,
                'confluence_score': round(confluence_score, 1),
                'overall_trend': overall_trend,
                'timeframe_signals': timeframe_signals,
                'total_bullish': total_bullish,
                'total_bearish': total_bearish
            }

        except Exception as e:
            return {"error": f"Ошибка анализа трендов: {str(e)}"}

    def _analyze_trend(self, df, timeframe):
        """Анализ тренда на одном таймфрейме"""
        try:
            # Анализ скользящих средних
            ma_signal = self._ma_analysis(df)

            # Анализ RSI
            rsi_signal = self._rsi_analysis(df)

            # Анализ MACD
            macd_signal = self._macd_analysis(df)

            # Анализ цены относительно SMA
            price_signal = self._price_analysis(df)

            # Суммируем силу сигнала
            total_strength = ma_signal['strength'] + rsi_signal['strength'] + macd_signal['strength'] + price_signal[
                'strength']

            # Определяем направление
            if total_strength > 0:
                direction = "BULLISH"
                strength_level = min(10, total_strength)
            elif total_strength < 0:
                direction = "BEARISH"
                strength_level = min(10, abs(total_strength))
            else:
                direction = "NEUTRAL"
                strength_level = 0

            signals = [
                ma_signal['description'],
                rsi_signal['description'],
                macd_signal['description'],
                price_signal['description']
            ]

            return {
                'timeframe': timeframe,
                'direction': direction,
                'strength': strength_level,
                'signals': signals
            }

        except Exception as e:
            return {
                'timeframe': timeframe,
                'direction': 'NEUTRAL',
                'strength': 0,
                'signals': [f"Ошибка анализа: {str(e)}"]
            }

    def _ma_analysis(self, df):
        """Анализ скользящих средних"""
        try:
            if 'SMA_20' not in df.columns or 'SMA_50' not in df.columns:
                return {'strength': 0, 'description': 'MA: нет данных'}

            sma_20 = float(df['SMA_20'].iloc[-1])
            sma_50 = float(df['SMA_50'].iloc[-1])

            if sma_20 > sma_50:
                return {'strength': 2, 'description': f'MA: бычий (20>{50})'}
            else:
                return {'strength': -2, 'description': f'MA: медвежий (20<{50})'}
        except:
            return {'strength': 0, 'description': 'MA: ошибка'}

    def _rsi_analysis(self, df):
        """Анализ RSI"""
        try:
            if 'RSI' not in df.columns:
                return {'strength': 0, 'description': 'RSI: нет данных'}

            rsi = float(df['RSI'].iloc[-1])

            if rsi < 30:
                return {'strength': 3, 'description': f'RSI: перепродан ({rsi:.1f})'}
            elif rsi > 70:
                return {'strength': -3, 'description': f'RSI: перекуплен ({rsi:.1f})'}
            elif rsi > 50:
                return {'strength': 1, 'description': f'RSI: бычий ({rsi:.1f})'}
            else:
                return {'strength': -1, 'description': f'RSI: медвежий ({rsi:.1f})'}
        except:
            return {'strength': 0, 'description': 'RSI: ошибка'}

    def _macd_analysis(self, df):
        """Анализ MACD"""
        try:
            if 'MACD' not in df.columns or 'MACD_Signal' not in df.columns:
                return {'strength': 0, 'description': 'MACD: нет данных'}

            macd = float(df['MACD'].iloc[-1])
            signal = float(df['MACD_Signal'].iloc[-1])

            if macd > signal:
                return {'strength': 2, 'description': 'MACD: бычий'}
            else:
                return {'strength': -2, 'description': 'MACD: медвежий'}
        except:
            return {'strength': 0, 'description': 'MACD: ошибка'}

    def _price_analysis(self, df):
        """Анализ цены"""
        try:
            prices = df['close'].tail(10).astype(float)
            current_price = prices.iloc[-1]

            # Проверяем обновление максимумов/минимумов
            if current_price == prices.max():
                return {'strength': 2, 'description': 'Цена: обновление максимума'}
            elif current_price == prices.min():
                return {'strength': -2, 'description': 'Цена: обновление минимума'}
            else:
                return {'strength': 0, 'description': 'Цена: в диапазоне'}
        except:
            return {'strength': 0, 'description': 'Цена: ошибка'}


# Глобальный экземпляр
trend_analyzer = TrendAnalyzer()