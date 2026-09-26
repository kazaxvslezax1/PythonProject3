import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from technical_indicators import calculate_all_indicators


class SimpleAIPredictor:
    def __init__(self):
        self.prediction_history = {}

    def predict_price(self, symbol, timeframe="1h"):
        """Упрощенный AI прогноз без ML зависимостей"""
        try:
            # Получаем исторические данные
            from data import get_candles
            df = get_candles(symbol, timeframe, limit=100)

            if len(df) < 50:
                return {"error": "Недостаточно данных для прогноза"}

            # Добавляем технические индикаторы
            df = calculate_all_indicators(df)

            prices = df['close'].astype(float)
            current_price = prices.iloc[-1]

            # Анализируем индикаторы
            analysis = self._analyze_indicators(df)

            # Улучшенный прогноз на основе технического анализа
            prediction = self._advanced_technical_prediction(df, prices, analysis)

            # Сохраняем в историю
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

        # Тренд (скользящие средние)
        sma_20 = df['SMA_20'].iloc[-1] if 'SMA_20' in df.columns else prices.iloc[-1]
        sma_50 = df['SMA_50'].iloc[-1] if 'SMA_50' in df.columns else prices.iloc[-1]
        trend = "📈 ВОСХОДЯЩИЙ" if sma_20 > sma_50 else "📉 НИСХОДЯЩИЙ"

        # RSI анализ
        rsi = df['RSI'].iloc[-1] if 'RSI' in df.columns else 50
        if rsi < 30:
            rsi_signal = "🟢 ПЕРЕПРОДАНО"
        elif rsi > 70:
            rsi_signal = "🔴 ПЕРЕКУПЛЕНО"
        else:
            rsi_signal = "⚪ НОРМА"

        # MACD анализ
        if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
            macd = df['MACD'].iloc[-1]
            macd_signal = df['MACD_Signal'].iloc[-1]
            macd_direction = "🟢 БЫЧИЙ" if macd > macd_signal else "🔴 МЕДВЕЖИЙ"
        else:
            macd_direction = "⚪ НЕТ ДАННЫХ"

        # Волатильность
        volatility = df['Volatility'].iloc[-1] if 'Volatility' in df.columns else 0
        if pd.isna(volatility):
            volatility = 0

        # Объемы
        volume_trend = "📈 РАСТУТ" if df['volume'].iloc[-1] > df['volume'].mean() else "📉 ПАДАЮТ"

        return {
            'trend': trend,
            'rsi_signal': rsi_signal,
            'macd_signal': macd_direction,
            'volatility': f"{volatility:.2f}%",
            'volume_trend': volume_trend
        }

    def _advanced_technical_prediction(self, df, prices, analysis):
        """УЛУЧШЕННЫЙ прогноз на основе технического анализа"""
        # Собираем все сигналы
        signals = []
        signal_strength = 0

        current_price = prices.iloc[-1]

        # 1. Анализ тренда (УСИЛЕННЫЙ)
        if "ВОСХОДЯЩИЙ" in analysis['trend']:
            signals.append("📈 Сильный бычий тренд")
            signal_strength += 3
        else:
            signals.append("📉 Сильный медвежий тренд")
            signal_strength -= 3

        # 2. Анализ RSI (более чувствительный)
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
        elif rsi > 50:
            signals.append("📗 RSI: Бычье настроение")
            signal_strength += 1
        else:
            signals.append("📕 RSI: Медвежье настроение")
            signal_strength -= 1

        # 3. Анализ MACD (более детальный)
        if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
            macd = df['MACD'].iloc[-1]
            macd_signal = df['MACD_Signal'].iloc[-1]
            macd_histogram = df['MACD_Histogram'].iloc[-1] if 'MACD_Histogram' in df.columns else 0

            if macd > macd_signal and macd_histogram > 0:
                signals.append("📊 MACD: СИЛЬНЫЙ бычий сигнал")
                signal_strength += 3
            elif macd < macd_signal and macd_histogram < 0:
                signals.append("📊 MACD: СИЛЬНЫЙ медвежий сигнал")
                signal_strength -= 3
            elif macd > macd_signal:
                signals.append("📊 MACD: Бычье расхождение")
                signal_strength += 2
            else:
                signals.append("📊 MACD: Медвежье расхождение")
                signal_strength -= 2

        # 4. Анализ моментума (расширенный)
        recent_prices = prices.tail(10)
        short_momentum = (recent_prices.iloc[-1] - recent_prices.iloc[-3]) / recent_prices.iloc[-3] * 100

        if short_momentum > 3:
            signals.append(f"🚀 Моментум: СИЛЬНЫЙ рост +{short_momentum:.1f}%")
            signal_strength += 3
        elif short_momentum < -3:
            signals.append(f"🔻 Моментум: СИЛЬНОЕ падение {short_momentum:.1f}%")
            signal_strength -= 3
        elif short_momentum > 1.5:
            signals.append(f"📈 Моментум: Рост +{short_momentum:.1f}%")
            signal_strength += 2
        elif short_momentum < -1.5:
            signals.append(f"📉 Моментум: Падение {short_momentum:.1f}%")
            signal_strength -= 2

        # ФОРМИРУЕМ ФИНАЛЬНЫЙ ПРОГНОЗ
        base_confidence = 60

        if signal_strength >= 8:
            direction = "🚀 ВЗРЫВНОЙ РОСТ"
            change = f"+{(signal_strength - 5) * 0.8:.1f}%"
            confidence = min(95, base_confidence + signal_strength * 2)
        elif signal_strength >= 5:
            direction = "🟢 СИЛЬНЫЙ РОСТ"
            change = f"+{(signal_strength - 2) * 0.5:.1f}%"
            confidence = min(88, base_confidence + signal_strength * 2)
        elif signal_strength >= 2:
            direction = "📈 УМЕРЕННЫЙ РОСТ"
            change = f"+{signal_strength * 0.3:.1f}%"
            confidence = min(80, base_confidence + signal_strength * 3)
        elif signal_strength <= -8:
            direction = "🔻 КРИТИЧЕСКОЕ ПАДЕНИЕ"
            change = f"{(signal_strength + 5) * 0.8:.1f}%"
            confidence = min(95, base_confidence + abs(signal_strength) * 2)
        elif signal_strength <= -5:
            direction = "🔴 СИЛЬНОЕ ПАДЕНИЕ"
            change = f"{(signal_strength + 2) * 0.5:.1f}%"
            confidence = min(88, base_confidence + abs(signal_strength) * 2)
        elif signal_strength <= -2:
            direction = "📉 УМЕРЕННОЕ ПАДЕНИЕ"
            change = f"{signal_strength * 0.3:.1f}%"
            confidence = min(80, base_confidence + abs(signal_strength) * 3)
        else:
            direction = "🟡 НЕЙТРАЛЬНО"
            change = "±0.2%"
            confidence = base_confidence

        confidence = max(35, min(97, confidence))

        # Уровень уверенности
        if confidence > 85:
            confidence_level = "ОЧЕНЬ ВЫСОКАЯ"
        elif confidence > 70:
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
            'key_signals': signals[:4]
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

    # НОВЫЕ МЕТОДЫ ДЛЯ КОМАНД БОТА
    def scan_top_coins(self, top_n=10):
        """Сканирует топ-N монет и возвращает лучшие возможности"""
        try:
            from data import POPULAR_COINS

            scanned_results = []
            symbols_to_scan = POPULAR_COINS[:top_n]

            print(f"🔍 AI сканирует {len(symbols_to_scan)} монет...")

            for symbol in symbols_to_scan:
                try:
                    prediction = self.predict_price(symbol)

                    if "error" not in prediction:
                        signal_strength = prediction.get('signal_strength', 0)

                        scanned_results.append({
                            'symbol': symbol,
                            'prediction': prediction['prediction'],
                            'confidence': prediction['confidence'],
                            'signal_strength': signal_strength,
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

            bullish_coins = [coin for coin in scanned_coins if coin['signal_strength'] > 3]

            if bullish_coins:
                best_coin = bullish_coins[0]
                return {
                    "type": "BUY",
                    "symbol": best_coin['symbol'],
                    "prediction": best_coin['prediction'],
                    "confidence": best_coin['confidence'],
                    "signal_strength": best_coin['signal_strength'],
                    "price": best_coin['price'],
                    "reason": "СИЛЬНЫЙ бычий сигнал",
                    "key_signals": best_coin['key_signals'][:3] if best_coin['key_signals'] else []
                }

            bearish_coins = [coin for coin in scanned_coins if coin['signal_strength'] < -3]

            if bearish_coins:
                best_coin = bearish_coins[0]
                return {
                    "type": "SELL",
                    "symbol": best_coin['symbol'],
                    "prediction": best_coin['prediction'],
                    "confidence": best_coin['confidence'],
                    "signal_strength": best_coin['signal_strength'],
                    "price": best_coin['price'],
                    "reason": "СИЛЬНЫЙ медвежий сигнал",
                    "key_signals": best_coin['key_signals'][:3] if best_coin['key_signals'] else []
                }

            best_neutral = scanned_coins[0]
            return {
                "type": "HOLD" if abs(best_neutral['signal_strength']) < 2 else "WATCH",
                "symbol": best_neutral['symbol'],
                "prediction": best_neutral['prediction'],
                "confidence": best_neutral['confidence'],
                "signal_strength": best_neutral['signal_strength'],
                "price": best_neutral['price'],
                "reason": "Лучшая из доступных возможностей",
                "key_signals": best_neutral['key_signals'][:2] if best_neutral['key_signals'] else []
            }

        except Exception as e:
            return {"error": f"Ошибка поиска возможности: {e}"}

    def get_prediction_stats(self, symbol):
        """Возвращает статистику по истории прогнозов"""
        if symbol not in self.prediction_history or len(self.prediction_history[symbol]) < 3:
            return {"error": f"Недостаточно данных для {symbol}. Нужно минимум 3 прогноза."}

        history = self.prediction_history[symbol]

        correct_predictions = 0
        total_analyzed = 0
        price_changes = []

        for i in range(1, len(history)):
            prev_pred = history[i - 1]
            curr_data = history[i]

            prev_price = prev_pred['price']
            curr_price = curr_data['price']
            prev_direction = prev_pred['prediction']['direction']

            price_change = (curr_price - prev_price) / prev_price * 100
            price_changes.append(price_change)

            if "РОСТ" in prev_direction and price_change > 0.1:
                correct_predictions += 1
            elif "ПАДЕНИЕ" in prev_direction and price_change < -0.1:
                correct_predictions += 1
            elif "НЕЙТРАЛЬНО" in prev_direction and abs(price_change) < 0.5:
                correct_predictions += 1

            total_analyzed += 1

        accuracy = (correct_predictions / total_analyzed) * 100 if total_analyzed > 0 else 0

        avg_confidence = sum([float(h['prediction']['confidence'].replace('%', '')) for h in history]) / len(history)
        total_predictions = len(history)

        return {
            "symbol": symbol,
            "accuracy": f"{accuracy:.1f}%",
            "total_predictions": total_predictions,
            "analyzed_periods": total_analyzed,
            "avg_confidence": f"{avg_confidence:.1f}%",
            "recent_price_change": f"{price_changes[-1]:.2f}%" if price_changes else "N/A",
            "last_prediction": history[-1]['prediction']['direction'],
            "history": history[-5:]
        }


# Глобальный экземпляр
ai_predictor = SimpleAIPredictor()