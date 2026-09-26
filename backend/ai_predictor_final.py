import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from technical_indicators import calculate_all_indicators

# ДОБАВЬТЕ ЭТОТ СПИСОК В НАЧАЛЕ ФАЙЛА ai_predictor_final.py
POPULAR_COINS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "AVAXUSDT", "DOTUSDT", "DOGEUSDT", "MATICUSDT",
    "LTCUSDT", "LINKUSDT", "ATOMUSDT", "UNIUSDT", "XLMUSDT",
    "ALGOUSDT", "TRXUSDT", "VETUSDT", "ICPUSDT", "FILUSDT",
    "AAVEUSDT", "COMPUSDT", "MKRUSDT", "SNXUSDT", "CRVUSDT",
    "SUSHIUSDT", "YFIUSDT", "1INCHUSDT", "UMAUSDT", "BALUSDT",
    "NEARUSDT", "FTMUSDT", "EGLDUSDT", "ETCUSDT", "XTZUSDT",
    "EOSUSDT", "XMRUSDT", "ZECUSDT", "DASHUSDT", "WAVESUSDT",
    "SHIBUSDT", "PEPEUSDT", "FLOKIUSDT", "BONKUSDT", "MEMEUSDT"
]


class AIPredictorFinal:
    def __init__(self):
        self.prediction_history = {}

    def predict_price(self, symbol, timeframe="1h"):
        """Упрощенный AI прогноз без ML зависимостей"""
        try:
            from data import get_candles
            df = get_candles(symbol, timeframe, limit=100)

            if len(df) < 50:
                return {"error": "Недостаточно данных для прогноза"}

            df = calculate_all_indicators(df)
            prices = df['close'].astype(float)
            current_price = prices.iloc[-1]

            analysis = self._analyze_indicators(df)
            prediction = self._advanced_technical_prediction(df, prices, analysis)

            self._save_to_history(symbol, prediction, current_price)

            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "current_price": current_price,
                "prediction": prediction['direction'],
                "predicted_change": prediction['change'],
                "confidence": prediction['confidence'],
                "confidence_level": prediction['confidence_level'],
                "trend": analysis['trend'],
                "volatility": analysis['volatility'],
                "rsi_signal": analysis['rsi_signal'],
                "macd_signal": analysis['macd_signal'],
                "key_signals": prediction.get('key_signals', []),
                "signal_strength": prediction.get('signal_strength', 0),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": f"🤖 AI прогноз: {prediction['direction']}"
            }

        except Exception as e:
            return {"error": f"Ошибка AI прогноза: {str(e)}"}

    def _analyze_indicators(self, df):
        """Анализирует технические индикаторы"""
        prices = df['close'].astype(float)

        sma_20 = df['SMA_20'].iloc[-1] if 'SMA_20' in df.columns else prices.iloc[-1]
        sma_50 = df['SMA_50'].iloc[-1] if 'SMA_50' in df.columns else prices.iloc[-1]
        trend = "📈 ВОСХОДЯЩИЙ" if sma_20 > sma_50 else "📉 НИСХОДЯЩИЙ"

        rsi = df['RSI'].iloc[-1] if 'RSI' in df.columns else 50
        if rsi < 30:
            rsi_signal = "🟢 ПЕРЕПРОДАНО"
        elif rsi > 70:
            rsi_signal = "🔴 ПЕРЕКУПЛЕНО"
        else:
            rsi_signal = "⚪ НОРМА"

        if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
            macd = df['MACD'].iloc[-1]
            macd_signal = df['MACD_Signal'].iloc[-1]
            macd_direction = "🟢 БЫЧИЙ" if macd > macd_signal else "🔴 МЕДВЕЖИЙ"
        else:
            macd_direction = "⚪ НЕТ ДАННЫХ"

        volatility = df['Volatility'].iloc[-1] if 'Volatility' in df.columns else 0
        if pd.isna(volatility):
            volatility = 0

        return {
            'trend': trend,
            'rsi_signal': rsi_signal,
            'macd_signal': macd_direction,
            'volatility': f"{volatility:.2f}%"
        }

    def _advanced_technical_prediction(self, df, prices, analysis):
        """УЛУЧШЕННЫЙ прогноз на основе технического анализа"""
        signals = []
        signal_strength = 0
        current_price = prices.iloc[-1]

        # 1. Анализ тренда
        if "ВОСХОДЯЩИЙ" in analysis['trend']:
            signals.append("📈 Бычий тренд")
            signal_strength += 3
        else:
            signals.append("📉 Медвежий тренд")
            signal_strength -= 3

        # 2. Анализ RSI
        rsi = df['RSI'].iloc[-1] if 'RSI' in df.columns else 50
        if rsi < 25:
            signals.append("🟢 RSI: КРИТИЧЕСКАЯ перепроданность")
            signal_strength += 4
        elif rsi > 75:
            signals.append("🔴 RSI: КРИТИЧЕСКАЯ перекупленность")
            signal_strength -= 4
        elif rsi < 35:
            signals.append("🟢 RSI: Перепроданность")
            signal_strength += 2
        elif rsi > 65:
            signals.append("🔴 RSI: Перекупленность")
            signal_strength -= 2

        # 3. Анализ MACD
        if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
            macd = df['MACD'].iloc[-1]
            macd_signal = df['MACD_Signal'].iloc[-1]
            if macd > macd_signal:
                signals.append("📊 MACD: Бычий сигнал")
                signal_strength += 2
            else:
                signals.append("📊 MACD: Медвежий сигнал")
                signal_strength -= 2

        # 4. Анализ моментума
        recent_prices = prices.tail(5)
        momentum = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0] * 100
        if momentum > 2:
            signals.append(f"🚀 Моментум: +{momentum:.1f}%")
            signal_strength += 2
        elif momentum < -2:
            signals.append(f"🔻 Моментум: {momentum:.1f}%")
            signal_strength -= 2

        # ФОРМИРУЕМ ПРОГНОЗ
        if signal_strength >= 6:
            direction = "🚀 СИЛЬНЫЙ РОСТ"
            change = f"+{(signal_strength - 3) * 0.5:.1f}%"
            confidence = min(90, 60 + signal_strength * 3)
        elif signal_strength >= 3:
            direction = "🟢 РОСТ"
            change = f"+{(signal_strength - 1) * 0.3:.1f}%"
            confidence = min(80, 50 + signal_strength * 4)
        elif signal_strength <= -6:
            direction = "🔻 СИЛЬНОЕ ПАДЕНИЕ"
            change = f"{(signal_strength + 3) * 0.5:.1f}%"
            confidence = min(90, 60 + abs(signal_strength) * 3)
        elif signal_strength <= -3:
            direction = "🔴 ПАДЕНИЕ"
            change = f"{(signal_strength + 1) * 0.3:.1f}%"
            confidence = min(80, 50 + abs(signal_strength) * 4)
        else:
            direction = "🟡 НЕЙТРАЛЬНО"
            change = "±0.0%"
            confidence = 45

        confidence = max(30, min(95, confidence))

        if confidence > 75:
            confidence_level = "ВЫСОКАЯ"
        elif confidence > 55:
            confidence_level = "СРЕДНЯЯ"
        else:
            confidence_level = "НИЗКАЯ"

        return {
            'direction': direction,
            'change': change,
            'confidence': f"{confidence:.1f}%",
            'confidence_level': confidence_level,
            'signals_count': len(signals),
            'signal_strength': signal_strength,
            'key_signals': signals[:3]
        }

    def _save_to_history(self, symbol, prediction, current_price):
        """Сохраняет прогноз в историю"""
        if symbol not in self.prediction_history:
            self.prediction_history[symbol] = []

        self.prediction_history[symbol].append({
            'timestamp': datetime.now(),
            'prediction': prediction,
            'price': current_price
        })

        if len(self.prediction_history[symbol]) > 50:
            self.prediction_history[symbol] = self.prediction_history[symbol][-50:]

    def scan_top_coins(self, top_n=10):
        """Сканирует топ-N монет"""
        try:
            # ИСПОЛЬЗУЕМ ЛОКАЛЬНЫЙ СПИСОК
            symbols_to_scan = POPULAR_COINS[:top_n]

            print(f"🔍 AI сканирует {len(symbols_to_scan)} монет...")

            scanned_results = []

            for symbol in symbols_to_scan:
                try:
                    prediction = self.predict_price(symbol)

                    if "error" not in prediction:
                        scanned_results.append({
                            'symbol': symbol,
                            'prediction': prediction['prediction'],
                            'confidence': prediction['confidence'],
                            'signal_strength': prediction.get('signal_strength', 0),
                            'price': prediction['current_price'],
                            'trend': prediction['trend'],
                            'key_signals': prediction.get('key_signals', [])
                        })

                    time.sleep(0.5)

                except Exception as e:
                    print(f"Ошибка сканирования {symbol}: {e}")
                    continue

            scanned_results.sort(key=lambda x: x['signal_strength'], reverse=True)
            return scanned_results

        except Exception as e:
            print(f"Ошибка сканирования: {e}")
            return []

    def find_best_opportunity(self):
        """Находит лучшую торговую возможность"""
        try:
            scanned_coins = self.scan_top_coins(15)

            if not scanned_coins:
                return {"error": "Не удалось просканировать монеты"}

            # Ищем лучшую бычью возможность
            best_bullish = None
            for coin in scanned_coins:
                if coin['signal_strength'] > 3:
                    if not best_bullish or coin['signal_strength'] > best_bullish['signal_strength']:
                        best_bullish = coin

            if best_bullish:
                return {
                    "type": "BUY",
                    "symbol": best_bullish['symbol'],
                    "prediction": best_bullish['prediction'],
                    "confidence": best_bullish['confidence'],
                    "signal_strength": best_bullish['signal_strength'],
                    "price": best_bullish['price'],
                    "reason": "СИЛЬНЫЙ бычий сигнал",
                    "key_signals": best_bullish['key_signals'][:2]
                }

            # Ищем лучшую медвежью возможность
            best_bearish = None
            for coin in scanned_coins:
                if coin['signal_strength'] < -3:
                    if not best_bearish or coin['signal_strength'] < best_bearish['signal_strength']:
                        best_bearish = coin

            if best_bearish:
                return {
                    "type": "SELL",
                    "symbol": best_bearish['symbol'],
                    "prediction": best_bearish['prediction'],
                    "confidence": best_bearish['confidence'],
                    "signal_strength": best_bearish['signal_strength'],
                    "price": best_bearish['price'],
                    "reason": "СИЛЬНЫЙ медвежий сигнал",
                    "key_signals": best_bearish['key_signals'][:2]
                }

            # Если нет сильных сигналов, возвращаем лучшую нейтральную
            best_neutral = scanned_coins[0]
            return {
                "type": "HOLD",
                "symbol": best_neutral['symbol'],
                "prediction": best_neutral['prediction'],
                "confidence": best_neutral['confidence'],
                "signal_strength": best_neutral['signal_strength'],
                "price": best_neutral['price'],
                "reason": "Лучшая из доступных возможностей",
                "key_signals": best_neutral['key_signals'][:1]
            }

        except Exception as e:
            return {"error": f"Ошибка поиска возможности: {e}"}

    def get_prediction_stats(self, symbol):
        """Статистика по истории прогнозов"""
        if symbol not in self.prediction_history or len(self.prediction_history[symbol]) < 2:
            return {"error": f"Недостаточно данных для {symbol}"}

        history = self.prediction_history[symbol]

        correct = 0
        total = len(history) - 1

        for i in range(1, len(history)):
            prev = history[i - 1]
            curr = history[i]

            price_change = (curr['price'] - prev['price']) / prev['price'] * 100
            prev_dir = prev['prediction']['direction']

            if "РОСТ" in prev_dir and price_change > 0:
                correct += 1
            elif "ПАДЕНИЕ" in prev_dir and price_change < 0:
                correct += 1

        accuracy = (correct / total) * 100 if total > 0 else 0

        return {
            "symbol": symbol,
            "accuracy": f"{accuracy:.1f}%",
            "total_predictions": len(history),
            "analyzed_periods": total,
            "last_prediction": history[-1]['prediction']['direction']
        }


# Глобальный экземпляр
ai_predictor = AIPredictorFinal()