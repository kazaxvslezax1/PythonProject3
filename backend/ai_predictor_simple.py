import requests
import pandas as pd
import time  # Добавьте эту строку в импорты
import numpy as np
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
            # Измеряем силу тренда
            trend_strength = (df['SMA_20'].iloc[-1] - df['SMA_50'].iloc[-1]) / df['SMA_50'].iloc[-1] * 100
            if trend_strength > 2:
                signals.append(f"📈 ОЧЕНЬ СИЛЬНЫЙ бычий тренд (+{trend_strength:.1f}%)")
                signal_strength += 4
            else:
                signals.append("📈 Бычий тренд")
                signal_strength += 3
        else:
            trend_strength = (df['SMA_50'].iloc[-1] - df['SMA_20'].iloc[-1]) / df['SMA_20'].iloc[-1] * 100
            if trend_strength > 2:
                signals.append(f"📉 ОЧЕНЬ СИЛЬНЫЙ медвежий тренд (-{trend_strength:.1f}%)")
                signal_strength -= 4
            else:
                signals.append("📉 Медвежий тренд")
                signal_strength -= 3

        # 2. Анализ RSI (БОЛЕЕ АГРЕССИВНЫЙ)
        rsi = df['RSI'].iloc[-1] if 'RSI' in df.columns else 50
        if rsi < 20:  # Критическая перепроданность
            signals.append(f"🟢 RSI: КРИТИЧЕСКАЯ перепроданность ({rsi:.1f})")
            signal_strength += 5
        elif rsi > 80:  # Критическая перекупленность
            signals.append(f"🔴 RSI: КРИТИЧЕСКАЯ перекупленность ({rsi:.1f})")
            signal_strength -= 5
        elif rsi < 30:
            signals.append(f"🟢 RSI: Перепроданность ({rsi:.1f})")
            signal_strength += 3
        elif rsi > 70:
            signals.append(f"🔴 RSI: Перекупленность ({rsi:.1f})")
            signal_strength -= 3
        elif rsi > 55:
            signals.append(f"📗 RSI: Бычье настроение ({rsi:.1f})")
            signal_strength += 2
        elif rsi < 45:
            signals.append(f"📕 RSI: Медвежье настроение ({rsi:.1f})")
            signal_strength -= 2
        else:
            signals.append(f"⚪ RSI: Нейтрально ({rsi:.1f})")

        # 3. Анализ MACD (УСИЛЕННЫЙ)
        if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
            macd = df['MACD'].iloc[-1]
            macd_signal = df['MACD_Signal'].iloc[-1]
            macd_histogram = df['MACD_Histogram'].iloc[-1] if 'MACD_Histogram' in df.columns else 0

            macd_strength = abs(macd - macd_signal) / abs(macd_signal) * 100 if macd_signal != 0 else 0

            if macd > macd_signal and macd_histogram > 0:
                if macd_strength > 10:
                    signals.append(f"📊 MACD: ОЧЕНЬ СИЛЬНЫЙ бычий сигнал (+{macd_strength:.1f}%)")
                    signal_strength += 4
                else:
                    signals.append("📊 MACD: Бычий сигнал")
                    signal_strength += 3
            elif macd < macd_signal and macd_histogram < 0:
                if macd_strength > 10:
                    signals.append(f"📊 MACD: ОЧЕНЬ СИЛЬНЫЙ медвежий сигнал (-{macd_strength:.1f}%)")
                    signal_strength -= 4
                else:
                    signals.append("📊 MACD: Медвежий сигнал")
                    signal_strength -= 3
            elif macd > macd_signal:
                signals.append("📊 MACD: Слабый бычий сигнал")
                signal_strength += 1
            else:
                signals.append("📊 MACD: Слабый медвежий сигнал")
                signal_strength -= 1

        # 4. Анализ моментума (РАСШИРЕННЫЙ)
        # Короткий моментум (последние 3 свечи)
        short_momentum = (prices.iloc[-1] - prices.iloc[-4]) / prices.iloc[-4] * 100
        # Средний моментум (последние 10 свечей)
        medium_momentum = (prices.iloc[-1] - prices.iloc[-10]) / prices.iloc[-10] * 100

        if short_momentum > 5 and medium_momentum > 8:
            signals.append(f"🚀 ВЗРЫВНОЙ моментум: +{short_momentum:.1f}% (короткий), +{medium_momentum:.1f}% (средний)")
            signal_strength += 5
        elif short_momentum > 3 and medium_momentum > 5:
            signals.append(f"📈 СИЛЬНЫЙ моментум: +{short_momentum:.1f}% (короткий), +{medium_momentum:.1f}% (средний)")
            signal_strength += 4
        elif short_momentum > 1.5:
            signals.append(f"📈 Положительный моментум: +{short_momentum:.1f}%")
            signal_strength += 2
        elif short_momentum < -5 and medium_momentum < -8:
            signals.append(
                f"🔻 КРИТИЧЕСКИЙ моментум: {short_momentum:.1f}% (короткий), {medium_momentum:.1f}% (средний)")
            signal_strength -= 5
        elif short_momentum < -3 and medium_momentum < -5:
            signals.append(
                f"📉 СИЛЬНЫЙ негативный моментум: {short_momentum:.1f}% (короткий), {medium_momentum:.1f}% (средний)")
            signal_strength -= 4
        elif short_momentum < -1.5:
            signals.append(f"📉 Негативный моментум: {short_momentum:.1f}%")
            signal_strength -= 2

        # 5. Анализ объемов (УСИЛЕННЫЙ)
        current_volume = df['volume'].iloc[-1]
        avg_volume_5 = df['volume'].tail(5).mean()
        avg_volume_20 = df['volume'].tail(20).mean()

        volume_ratio_5 = current_volume / avg_volume_5 if avg_volume_5 > 0 else 1
        volume_ratio_20 = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1

        if volume_ratio_5 > 3.0 or volume_ratio_20 > 2.5:
            signals.append(f"💥 АНОМАЛЬНЫЕ объемы: x{volume_ratio_5:.1f} (5с), x{volume_ratio_20:.1f} (20с)")
            # Усиливаем текущий сигнал при аномальных объемах
            signal_strength = int(signal_strength * 1.8)
        elif volume_ratio_5 > 2.0:
            signals.append(f"💧 Высокие объемы: x{volume_ratio_5:.1f}")
            signal_strength += 3
        elif volume_ratio_5 > 1.3:
            signals.append(f"💧 Объемы выше среднего: x{volume_ratio_5:.1f}")
            signal_strength += 1
        elif volume_ratio_5 < 0.7:
            signals.append(f"💧 Низкие объемы: x{volume_ratio_5:.1f}")
            signal_strength -= 1

        # 6. Анализ волатильности (ОБНОВЛЕННЫЙ)
        volatility = float(analysis['volatility'].replace('%', ''))

        if volatility > 15:
            signals.append(f"🌪️ ЭКСТРЕМАЛЬНАЯ волатильность: {volatility:.1f}%")
            # При экстремальной волатильности снижаем уверенность
            confidence_modifier = -25
        elif volatility > 8:
            signals.append(f"🌊 Высокая волатильность: {volatility:.1f}%")
            confidence_modifier = -15
        elif volatility > 4:
            signals.append(f"🌤️ Средняя волатильность: {volatility:.1f}%")
            confidence_modifier = -5
        elif volatility > 2:
            signals.append(f"💨 Низкая волатильность: {volatility:.1f}%")
            confidence_modifier = +5
        else:
            signals.append(f"🕊️ ОЧЕНЬ НИЗКАЯ волатильность: {volatility:.1f}%")
            confidence_modifier = +10

        # 7. Анализ поддержки/сопротивления (УЛУЧШЕННЫЙ)
        resistance_20 = prices.tail(20).max()
        support_20 = prices.tail(20).min()
        resistance_50 = prices.tail(50).max()
        support_50 = prices.tail(50).min()

        distance_to_resistance_20 = (resistance_20 - current_price) / current_price * 100
        distance_to_support_20 = (current_price - support_20) / current_price * 100

        # Определяем ближайшие ключевые уровни
        nearest_resistance = min(distance_to_resistance_20, (resistance_50 - current_price) / current_price * 100)
        nearest_support = min(distance_to_support_20, (current_price - support_50) / current_price * 100)

        if nearest_resistance < 1:
            signals.append("⛔ ОЧЕНЬ БЛИЗКО к сопротивлению!")
            signal_strength -= 3
        elif nearest_resistance < 3:
            signals.append(f"⚠️ Близко к сопротивлению (+{nearest_resistance:.1f}%)")
            signal_strength -= 2
        elif nearest_support < 1:
            signals.append("🛡️ ОЧЕНЬ БЛИЗКО к поддержке!")
            signal_strength += 3
        elif nearest_support < 3:
            signals.append(f"📌 Близко к поддержке (-{nearest_support:.1f}%)")
            signal_strength += 2

        # 8. Анализ цены относительно BB (ОБНОВЛЕННЫЙ)
        if 'BB_Upper' in df.columns and 'BB_Lower' in df.columns:
            bb_upper = df['BB_Upper'].iloc[-1]
            bb_lower = df['BB_Lower'].iloc[-1]
            bb_middle = df['BB_Middle'].iloc[-1]

            bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) * 100

            if current_price < bb_lower:
                signals.append("🎯 Цена НИЖЕ Bollinger Bands - СИЛЬНЫЙ сигнал покупки!")
                signal_strength += 4
            elif current_price > bb_upper:
                signals.append("🎯 Цена ВЫШЕ Bollinger Bands - СИЛЬНЫЙ сигнал продажи!")
                signal_strength -= 4
            elif bb_position < 10:
                signals.append(f"📊 Цена у нижней границы BB ({bb_position:.1f}%)")
                signal_strength += 3
            elif bb_position > 90:
                signals.append(f"📊 Цена у верхней границы BB ({bb_position:.1f}%)")
                signal_strength -= 3
            elif bb_position < 30:
                signals.append(f"📊 Цена в нижней зоне BB ({bb_position:.1f}%)")
                signal_strength += 2
            elif bb_position > 70:
                signals.append(f"📊 Цена в верхней зоне BB ({bb_position:.1f}%)")
                signal_strength -= 2

        # ФОРМИРУЕМ ФИНАЛЬНЫЙ ПРОГНОЗ (ОБНОВЛЕННАЯ ЛОГИКА)
        base_confidence = 60  # Повысили базовую уверенность

        # Рассчитываем прогнозируемое изменение на основе силы сигналов
        predicted_change = signal_strength * 0.4  # Более агрессивный множитель

        if signal_strength >= 10:
            direction = "🚀 ВЗРЫВНОЙ РОСТ"
            change = f"+{abs(predicted_change):.1f}%"
            confidence = min(95, base_confidence + signal_strength * 2 + confidence_modifier)
        elif signal_strength >= 6:
            direction = "🟢 СИЛЬНЫЙ РОСТ"
            change = f"+{abs(predicted_change):.1f}%"
            confidence = min(88, base_confidence + signal_strength * 2 + confidence_modifier)
        elif signal_strength >= 3:
            direction = "📈 УМЕРЕННЫЙ РОСТ"
            change = f"+{abs(predicted_change):.1f}%"
            confidence = min(80, base_confidence + signal_strength * 3 + confidence_modifier)
        elif signal_strength <= -10:
            direction = "🔻 КРИТИЧЕСКОЕ ПАДЕНИЕ"
            change = f"{predicted_change:.1f}%"
            confidence = min(95, base_confidence + abs(signal_strength) * 2 + confidence_modifier)
        elif signal_strength <= -6:
            direction = "🔴 СИЛЬНОЕ ПАДЕНИЕ"
            change = f"{predicted_change:.1f}%"
            confidence = min(88, base_confidence + abs(signal_strength) * 2 + confidence_modifier)
        elif signal_strength <= -3:
            direction = "📉 УМЕРЕННОЕ ПАДЕНИЕ"
            change = f"{predicted_change:.1f}%"
            confidence = min(80, base_confidence + abs(signal_strength) * 3 + confidence_modifier)
        else:
            # Для нейтральных сигналов все равно даем небольшое направление
            if signal_strength > 0:
                direction = "🟡 НЕБОЛЬШОЙ РОСТ"
                change = f"+{abs(predicted_change):.1f}%"
            elif signal_strength < 0:
                direction = "🟡 НЕБОЛЬШОЕ ПАДЕНИЕ"
                change = f"{predicted_change:.1f}%"
            else:
                direction = "🟡 СТАБИЛЬНО"
                change = "±0.0%"
            confidence = base_confidence + confidence_modifier

        # Гарантируем разумные пределы уверенности
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
            'key_signals': signals[:5]  # Показываем топ-5 сигналов
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

        # Ограничиваем историю последними 50 прогнозами
        if len(self.prediction_history[symbol]) > 50:
            self.prediction_history[symbol] = self.prediction_history[symbol][-50:]

    def get_prediction_accuracy(self, symbol):
        """Рассчитывает точность предыдущих прогнозов"""
        if symbol not in self.prediction_history or len(self.prediction_history[symbol]) < 3:
            return "Недостаточно данных для анализа точности"

        history = self.prediction_history[symbol]
        correct_predictions = 0

        for i in range(1, len(history)):
            prev_pred = history[i - 1]
            curr_data = history[i]

            prev_price = prev_pred['price']
            curr_price = curr_data['price']
            prev_direction = prev_pred['prediction']['direction']

            # Проверяем, сбылся ли прогноз
            if "РОСТ" in prev_direction and curr_price > prev_price:
                correct_predictions += 1
            elif "ПАДЕНИЕ" in prev_direction and curr_price < prev_price:
                correct_predictions += 1

        accuracy = (correct_predictions / (len(history) - 1)) * 100
        return f"{accuracy:.1f}%"


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
                    # Извлекаем силу сигнала из прогноза
                    signal_strength = 0
                    if "РОСТ" in prediction['prediction']:
                        signal_strength = prediction.get('signal_strength', 0)
                    elif "ПАДЕНИЕ" in prediction['prediction']:
                        signal_strength = -prediction.get('signal_strength', 0)

                    scanned_results.append({
                        'symbol': symbol,
                        'prediction': prediction['prediction'],
                        'confidence': prediction['confidence'],
                        'signal_strength': signal_strength,
                        'price': prediction['current_price'],
                        'trend': prediction['trend'],
                        'key_signals': prediction.get('key_signals', [])
                    })

                # Пауза между запросами чтобы не перегружать API
                time.sleep(0.5)

            except Exception as e:
                print(f"Ошибка сканирования {symbol}: {e}")
                continue

        # Сортируем по силе сигнала (убывание)
        scanned_results.sort(key=lambda x: x['signal_strength'], reverse=True)

        return scanned_results

    except Exception as e:
        print(f"Ошибка сканирования: {e}")
        return []


def find_best_opportunity(self):
    """Находит лучшую торговую возможность"""
    try:
        # Сканируем топ-15 монет для лучшего выбора
        scanned_coins = self.scan_top_coins(15)

        if not scanned_coins:
            return {"error": "Не удалось просканировать монеты"}

        # Ищем монеты с самыми сильными бычьими сигналами
        bullish_coins = [coin for coin in scanned_coins if coin['signal_strength'] > 3]

        if bullish_coins:
            best_coin = bullish_coins[0]  # Самая сильная бычья монета
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

        # Если нет сильных бычьих, ищем сильные медвежьи
        bearish_coins = [coin for coin in scanned_coins if coin['signal_strength'] < -3]

        if bearish_coins:
            best_coin = bearish_coins[0]  # Самая сильная медвежья монета
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

        # Если нет сильных сигналов, возвращаем лучшую из нейтральных
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

    # Анализируем точность
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

        # Проверяем точность прогноза
        if "РОСТ" in prev_direction and price_change > 0.1:  # Небольшой порог
            correct_predictions += 1
        elif "ПАДЕНИЕ" in prev_direction and price_change < -0.1:
            correct_predictions += 1
        elif "НЕЙТРАЛЬНО" in prev_direction and abs(price_change) < 0.5:
            correct_predictions += 1

        total_analyzed += 1

    accuracy = (correct_predictions / total_analyzed) * 100 if total_analyzed > 0 else 0

    # Статистика
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
        "history": history[-5:]  # Последние 5 прогнозов
    }


def scan_top_coins(self, top_n=10):
    """Сканирует топ-N монет и возвращает лучшие возможности"""
    try:
        # Используем популярные монеты из data.py
        from data import POPULAR_COINS

        scanned_results = []
        symbols_to_scan = POPULAR_COINS[:top_n]

        print(f"🔍 AI сканирует {len(symbols_to_scan)} монет...")

        for symbol in symbols_to_scan:
            try:
                prediction = self.predict_price(symbol)

                if "error" not in prediction:
                    # Извлекаем силу сигнала
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

                # Пауза между запросами
                import time
                time.sleep(0.5)

            except Exception as e:
                print(f"Ошибка сканирования {symbol}: {e}")
                continue

        # Сортируем по силе сигнала (убывание)
        scanned_results.sort(key=lambda x: x['signal_strength'], reverse=True)

        return scanned_results

    except Exception as e:
        print(f"Ошибка сканирования: {e}")
        return []


def find_best_opportunity(self):
    """Находит лучшую торговую возможность"""
    try:
        # Сканируем топ-15 монет
        scanned_coins = self.scan_top_coins(15)

        if not scanned_coins:
            return {"error": "Не удалось просканировать монеты"}

        # Ищем монеты с сильными бычьими сигналами
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

        # Ищем сильные медвежьи сигналы
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

        # Лучшая из нейтральных
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

    # Анализируем точность
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

        # Проверяем точность прогноза
        if "РОСТ" in prev_direction and price_change > 0.1:
            correct_predictions += 1
        elif "ПАДЕНИЕ" in prev_direction and price_change < -0.1:
            correct_predictions += 1
        elif "НЕЙТРАЛЬНО" in prev_direction and abs(price_change) < 0.5:
            correct_predictions += 1

        total_analyzed += 1

    accuracy = (correct_predictions / total_analyzed) * 100 if total_analyzed > 0 else 0

    # Статистика
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
        "history": history[-5:]  # Последние 5 прогнозов
    }

# Глобальный экземпляр
ai_predictor = SimpleAIPredictor()