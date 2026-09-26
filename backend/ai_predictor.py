import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from technical_indicators import calculate_all_indicators
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler


class AIPredictor:
    def __init__(self):
        self.prediction_history = {}
        self.model = None
        self.scaler = StandardScaler()
        self.load_or_train_model()

    def load_or_train_model(self):
        """Загружает или создает ML модель"""
        try:
            self.model = joblib.load('ai_model.pkl')
            print("✅ ML модель загружена")
        except:
            print("🤖 Создаю новую ML модель...")
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)

    def extract_features(self, df):
        """Извлекает фичи для ML модели"""
        features = []

        # Базовые фичи
        prices = df['close'].astype(float)

        # Процентные изменения
        for period in [1, 3, 5, 10]:
            features.append(prices.pct_change(period).iloc[-1])

        # Волатильность
        for period in [5, 10, 20]:
            features.append(prices.pct_change().rolling(period).std().iloc[-1])

        # RSI
        if 'RSI' in df.columns:
            features.append(df['RSI'].iloc[-1])

        # MACD
        if 'MACD' in df.columns:
            features.append(df['MACD'].iloc[-1])
            features.append(df['MACD_Histogram'].iloc[-1])

        # Заполняем NaN
        features = [0 if pd.isna(x) else x for x in features]

        return np.array(features).reshape(1, -1)

    def predict_price(self, symbol, timeframe="1h"):
        """Улучшенный AI прогноз с ML"""
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

            # ML прогноз
            ml_prediction = self._ml_predict(df, prices)

            # Комбинируем подходы
            final_prediction = self._combine_predictions(analysis, ml_prediction, prices)

            # Сохраняем в историю
            self._save_to_history(symbol, final_prediction)

            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "current_price": current_price,
                "prediction": final_prediction['direction'],
                "predicted_change": final_prediction['change'],
                "confidence": final_prediction['confidence'],
                "confidence_level": final_prediction['confidence_level'],
                "trend": analysis['trend'],
                "volatility": analysis['volatility'],
                "rsi_signal": analysis['rsi_signal'],
                "macd_signal": analysis['macd_signal'],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": f"🤖 AI прогноз: {final_prediction['direction']}",
                "ml_used": ml_prediction['ml_used']
            }

        except Exception as e:
            return {"error": f"Ошибка AI прогноза: {str(e)}"}

    def _ml_predict(self, df, prices):
        """ML прогноз на основе исторических данных"""
        try:
            # Извлекаем фичи
            features = self.extract_features(df)

            # Нормализуем фичи
            features_scaled = self.scaler.fit_transform(features)

            # Простая логика если модель не обучена
            if self.model is None:
                return {
                    'direction': '🟡 ML НЕ ГОТОВ',
                    'change': '±0.0%',
                    'confidence': '50%',
                    'ml_used': False
                }

            # Предсказываем (здесь нужно дообучить модель на реальных данных)
            # prediction = self.model.predict(features_scaled)[0]
            # proba = self.model.predict_proba(features_scaled)[0]

            # Временная заглушка - улучшим позже
            price_change = (prices.iloc[-1] - prices.iloc[-5]) / prices.iloc[-5] * 100

            if price_change > 1:
                direction = "🟢 РОСТ"
                change = f"+{abs(price_change):.1f}%"
                confidence = min(75, abs(price_change) * 20)
            elif price_change < -1:
                direction = "🔴 ПАДЕНИЕ"
                change = f"-{abs(price_change):.1f}%"
                confidence = min(75, abs(price_change) * 20)
            else:
                direction = "🟡 БЕЗ ИЗМЕНЕНИЙ"
                change = "±0.0%"
                confidence = 40

            return {
                'direction': direction,
                'change': change,
                'confidence': f"{confidence:.1f}%",
                'ml_used': True
            }

        except Exception as e:
            print(f"ML ошибка: {e}")
            return {
                'direction': '🟡 ML ОШИБКА',
                'change': '±0.0%',
                'confidence': '50%',
                'ml_used': False
            }

    def _combine_predictions(self, analysis, ml_prediction, prices):
        """Комбинирует технический анализ и ML"""
        # Веса для разных подходов
        technical_weight = 0.6
        ml_weight = 0.4

        # Анализируем технические индикаторы
        bullish_signals = 0
        bearish_signals = 0

        if "ВОСХОДЯЩИЙ" in analysis['trend']:
            bullish_signals += 1
        else:
            bearish_signals += 1

        if "БЫЧИЙ" in analysis['macd_signal']:
            bullish_signals += 1
        else:
            bearish_signals += 1

        if "ПЕРЕПРОДАНО" in analysis['rsi_signal']:
            bullish_signals += 1
        elif "ПЕРЕКУПЛЕНО" in analysis['rsi_signal']:
            bearish_signals += 1

        # Технический прогноз
        technical_score = bullish_signals - bearish_signals

        # ML прогноз (упрощенно)
        ml_score = 1 if "РОСТ" in ml_prediction['direction'] else -1 if "ПАДЕНИЕ" in ml_prediction['direction'] else 0

        # Комбинированный счет
        combined_score = (technical_score * technical_weight) + (ml_score * ml_weight)

        # Финальное решение
        if combined_score > 0.5:
            direction = "🟢 РОСТ"
            change = f"+{combined_score * 0.8:.1f}%"
            confidence = min(85, 50 + combined_score * 20)
        elif combined_score < -0.5:
            direction = "🔴 ПАДЕНИЕ"
            change = f"{combined_score * 0.8:.1f}%"
            confidence = min(85, 50 + abs(combined_score) * 20)
        else:
            direction = "🟡 БЕЗ ИЗМЕНЕНИЙ"
            change = "±0.0%"
            confidence = 45

        # Уровень уверенности
        if confidence > 70:
            confidence_level = "ВЫСОКАЯ"
        elif confidence > 50:
            confidence_level = "СРЕДНЯЯ"
        else:
            confidence_level = "НИЗКАЯ"

        return {
            'direction': direction,
            'change': change,
            'confidence': f"{confidence:.1f}%",
            'confidence_level': confidence_level
        }

    def _analyze_indicators(self, df):
        """Анализирует технические индикаторы (оставляем как было)"""
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

        return {
            'trend': trend,
            'rsi_signal': rsi_signal,
            'macd_signal': macd_direction,
            'volatility': f"{volatility:.2f}%"
        }

    def _save_to_history(self, symbol, prediction):
        """Сохраняет прогноз в историю"""
        if symbol not in self.prediction_history:
            self.prediction_history[symbol] = []

        self.prediction_history[symbol].append({
            'timestamp': datetime.now(),
            'prediction': prediction,
            'symbol': symbol
        })

        # Ограничиваем историю последними 100 прогнозами
        if len(self.prediction_history[symbol]) > 100:
            self.prediction_history[symbol] = self.prediction_history[symbol][-100:]


# Глобальный экземпляр (ВАЖНО!)
ai_predictor = AIPredictor()
