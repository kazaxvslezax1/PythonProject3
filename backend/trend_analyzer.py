"""Directional agreement at a common cutoff; no future higher-timeframe candles."""

from data import get_candles
from market_data import utc
from strategy_engine import generate_signal


class TrendAnalyzer:
    def __init__(self):
        self.timeframes = ["15m", "1h", "4h", "1d"]

    def multi_timeframe_analysis(self, symbol, as_of=None):
        try:
            cutoff = utc(as_of)
            signals = {}
            bullish = bearish = 0.0
            for tf in self.timeframes:
                df = get_candles(symbol, tf, 120, as_of=cutoff)
                s = generate_signal(df, symbol, tf, cutoff)
                direction = {"LONG": "BULLISH", "SHORT": "BEARISH", "HOLD": "NEUTRAL"}[s.direction.value]
                signals[tf] = {
                    "timeframe": tf,
                    "direction": direction,
                    "strength": abs(s.strength),
                    "signals": s.reasons,
                }
                if s.direction.value == "LONG":
                    bullish += abs(s.strength)
                if s.direction.value == "SHORT":
                    bearish += abs(s.strength)
            signed = (bullish - bearish) / (bullish + bearish) * 100 if bullish + bearish else 0
            return {
                "symbol": symbol,
                "confluence_score": signed,
                "overall_trend": "ВОСХОДЯЩИЙ"
                if signed > 0
                else "НИСХОДЯЩИЙ"
                if signed < 0
                else "НЕЙТРАЛЬНЫЙ",
                "timeframe_signals": signals,
                "total_bullish": bullish,
                "total_bearish": bearish,
            }
        except Exception as exc:
            return {"error": type(exc).__name__}


trend_analyzer = TrendAnalyzer()
