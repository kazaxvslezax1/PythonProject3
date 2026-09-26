import pandas as pd
import numpy as np
from technical_indicators import calculate_all_indicators


class TargetCalculator:
    def __init__(self):
        self.risk_reward_ratio = 2.0  # Риск:прибыль = 1:2

    def calculate_targets(self, symbol, timeframe="15m"):
        """Рассчитывает целевые уровни с улучшенной логикой"""
        try:
            from data import get_candles
            df = get_candles(symbol, timeframe, limit=100)

            if len(df) < 20:
                return {"error": "Недостаточно данных"}

            df = calculate_all_indicators(df)
            current_price = float(df['close'].iloc[-1])

            # Расчет волатильности для стоп-лосса
            atr = self._calculate_atr(df)
            support, resistance = self._calculate_support_resistance(df)

            # Определяем направление тренда
            trend = self._determine_trend(df)

            # Улучшенный расчет стоп-лосса на основе ATR
            if trend == "UP":
                entry_price = current_price
                # Стоп-лосс = минимум или цена - 2*ATR
                stop_loss = min(support, entry_price - 2 * atr)
                take_profit = entry_price + (entry_price - stop_loss) * self.risk_reward_ratio
                direction = "LONG"
            else:
                entry_price = current_price
                # Стоп-лосс = максимум или цена + 2*ATR
                stop_loss = max(resistance, entry_price + 2 * atr)
                take_profit = entry_price - (stop_loss - entry_price) * self.risk_reward_ratio
                direction = "SHORT"

            # Расчет риска в процентах
            risk_percent = abs((stop_loss - entry_price) / entry_price * 100)
            reward_percent = abs((take_profit - entry_price) / entry_price * 100)

            # Оценка качества целей
            quality_score = self._calculate_quality_score(risk_percent, reward_percent, atr, current_price)

            return {
                "symbol": symbol,
                "direction": direction,
                "entry_price": round(entry_price, 4),
                "stop_loss": round(stop_loss, 4),
                "take_profit": round(take_profit, 4),
                "risk_percent": round(risk_percent, 2),
                "reward_percent": round(reward_percent, 2),
                "risk_reward_ratio": round(reward_percent / risk_percent, 2) if risk_percent > 0 else 0,
                "atr": round(atr, 4),
                "atr_percent": round(atr / current_price * 100, 2),
                "current_support": round(support, 4),
                "current_resistance": round(resistance, 4),
                "trend": trend,
                "quality_score": quality_score,
                "recommendation": self._get_recommendation(quality_score, risk_percent)
            }

        except Exception as e:
            return {"error": f"Ошибка расчета: {str(e)}"}

    def _calculate_atr(self, df, period=14):
        """Расчет Average True Range (ATR)"""
        try:
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            close = df['close'].astype(float)

            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())

            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(period).mean().iloc[-1]

            return atr if not pd.isna(atr) else (high - low).mean()
        except:
            return 0.0

    def _calculate_support_resistance(self, df, window=20):
        """Расчет уровней поддержки и сопротивления"""
        try:
            highs = df['high'].tail(window).astype(float)
            lows = df['low'].tail(window).astype(float)
            closes = df['close'].tail(window).astype(float)

            # Берем экстремумы
            support = lows.min()
            resistance = highs.max()

            # Уточняем уровни используя скользящие средние
            if 'SMA_20' in df.columns:
                sma_20 = float(df['SMA_20'].iloc[-1])
                support = min(support, sma_20 * 0.99)  # Немного ниже SMA
                resistance = max(resistance, sma_20 * 1.01)  # Немного выше SMA

            if 'SMA_50' in df.columns:
                sma_50 = float(df['SMA_50'].iloc[-1])
                support = min(support, sma_50 * 0.98)
                resistance = max(resistance, sma_50 * 1.02)

            return support, resistance
        except:
            current_price = float(df['close'].iloc[-1])
            return current_price * 0.95, current_price * 1.05

    def _determine_trend(self, df):
        """Определение тренда с улучшенной логикой"""
        try:
            if 'SMA_20' in df.columns and 'SMA_50' in df.columns:
                sma_20 = float(df['SMA_20'].iloc[-1])
                sma_50 = float(df['SMA_50'].iloc[-1])

                # Также смотрим наклон SMA
                sma_20_prev = float(df['SMA_20'].iloc[-2]) if len(df) > 1 else sma_20
                sma_50_prev = float(df['SMA_50'].iloc[-2]) if len(df) > 1 else sma_50

                sma_20_trend = "UP" if sma_20 > sma_20_prev else "DOWN"
                sma_50_trend = "UP" if sma_50 > sma_50_prev else "DOWN"

                if sma_20 > sma_50 and sma_20_trend == "UP":
                    return "UP"
                elif sma_20 < sma_50 and sma_20_trend == "DOWN":
                    return "DOWN"
                else:
                    return "NEUTRAL"

            return "NEUTRAL"
        except:
            return "NEUTRAL"

    def _calculate_quality_score(self, risk_percent, reward_percent, atr, current_price):
        """Оценка качества целей от 1 до 10"""
        score = 5.0

        # Оценка риска
        if risk_percent <= 2:
            score += 2
        elif risk_percent <= 5:
            score += 1
        elif risk_percent > 10:
            score -= 2

        # Оценка соотношения риск/прибыль
        rr_ratio = reward_percent / risk_percent if risk_percent > 0 else 0
        if rr_ratio >= 3:
            score += 3
        elif rr_ratio >= 2:
            score += 2
        elif rr_ratio < 1:
            score -= 2

        # Оценка волатильности
        atr_percent = atr / current_price * 100
        if atr_percent <= 5:
            score += 1
        elif atr_percent > 15:
            score -= 1

        return max(1, min(10, round(score)))

    def _get_recommendation(self, quality_score, risk_percent):
        """Рекомендация на основе качества целей"""
        if quality_score >= 8:
            return "✅ ОТЛИЧНЫЕ ЦЕЛИ - низкий риск, хорошее соотношение"
        elif quality_score >= 6:
            return "🟢 ХОРОШИЕ ЦЕЛИ - умеренный риск"
        elif quality_score >= 4:
            return "🟡 УДОВЛЕТВОРИТЕЛЬНО - будьте осторожны"
        else:
            return "🔴 ВЫСОКИЙ РИСК - рассмотрите другие варианты"


# Глобальный экземпляр
target_calculator = TargetCalculator()