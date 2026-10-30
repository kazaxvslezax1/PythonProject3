"""Pure, causal technical strategy shared by live adapters and replay."""

import math
from dataclasses import dataclass

from market_data import normalize_symbol, validate_candles
from signal_models import Direction, TradePlan, TradingSignal
from technical_indicators import calculate_all_indicators


@dataclass(frozen=True)
class StrategySettings:
    min_strength: float = 2.0
    atr_stop: float = 2.0
    max_stop_fraction: float = 0.10
    version: str = "technical-v1"


def generate_signal(df, symbol, timeframe, as_of, settings=None):
    settings = settings or StrategySettings()
    df = validate_candles(df, timeframe, as_of, min_bars=60).tail(120)
    row = calculate_all_indicators(df).iloc[-1]
    required = [
        "RSI",
        "MACD",
        "MACD_Signal",
        "SMA_20",
        "SMA_50",
        "ATR",
        "ADX",
        "BB_Upper",
        "BB_Lower",
        "Volume_Ratio",
    ]
    if not all(math.isfinite(float(row[key])) for key in required):
        raise ValueError("Unready or invalid indicators")
    score, reasons = 0, []
    for condition, weight, positive, negative in [
        (row.SMA_20 > row.SMA_50, 2, "SMA20 above SMA50", "SMA20 at/below SMA50"),
        (row.MACD > row.MACD_Signal, 1, "MACD above signal", "MACD at/below signal"),
    ]:
        score += weight if condition else -weight
        reasons.append(positive if condition else negative)
    score += 3 if row.RSI < 30 else -3 if row.RSI > 70 else 1 if row.RSI > 50 else -1
    reasons.append(f"RSI={row.RSI:.2f}")
    score += 2 if row.close < row.BB_Lower else -2 if row.close > row.BB_Upper else 0
    side = (
        Direction.LONG
        if score >= settings.min_strength
        else Direction.SHORT
        if score <= -settings.min_strength
        else Direction.HOLD
    )
    quality = min(10.0, abs(score) + min(float(row.Volume_Ratio), 3.0) + min(float(row.ADX) / 25, 2.0))
    plan = None
    risk = float(row.ATR) * settings.atr_stop
    if side != Direction.HOLD:
        sign = 1 if side == Direction.LONG else -1
        if risk <= 0 or risk / row.close > settings.max_stop_fraction or row.close - 3 * risk <= 0:
            side = Direction.HOLD
            reasons.append("Risk veto: invalid or excessive ATR stop")
        else:
            plan = TradePlan(
                direction=side,
                entry=float(row.close),
                stop_loss=float(row.close - sign * risk),
                take_profits=[float(row.close + sign * risk * r) for r in (1, 2, 3)],
            )
    return TradingSignal(
        symbol=normalize_symbol(symbol),
        timeframe=timeframe,
        timestamp=row.close_time.to_pydatetime(),
        direction=side,
        quality=quality,
        strength=score,
        reasons=reasons,
        plan=plan,
        strategy_version=settings.version,
    )


def indicator_values(df):
    row = calculate_all_indicators(df.tail(120)).iloc[-1]
    keys = [
        "RSI",
        "MACD",
        "MACD_Signal",
        "SMA_20",
        "SMA_50",
        "EMA_12",
        "EMA_26",
        "ATR",
        "ADX",
        "BB_Upper",
        "BB_Middle",
        "BB_Lower",
        "Volume_Ratio",
        "Volatility",
    ]
    return {key: float(row[key]) for key in keys}


def legacy_result(signal, df):
    row = df.iloc[-1]
    indicators = indicator_values(df)
    return {
        "symbol": signal.symbol,
        "timeframe": signal.timeframe,
        "best_timeframe": signal.timeframe,
        "action": {"LONG": "BUY", "SHORT": "SELL", "HOLD": "HOLD"}[signal.direction.value],
        "direction": signal.direction.value,
        "strength": signal.strength,
        "quality": signal.quality,
        "quality_label": "Heuristic score, not probability",
        "recommendation": signal.direction.value,
        "signals": " | ".join(signal.reasons),
        "last_price": float(row.close),
        "candles_count": len(df),
        "timestamp": signal.timestamp.isoformat(),
        "signal": signal.model_dump(mode="json"),
        "indicators": {
            "price": float(row.close),
            "sma_20": indicators["SMA_20"],
            "sma_50": indicators["SMA_50"],
            "rsi": indicators["RSI"],
            "macd": indicators["MACD"],
            "bb_upper": indicators["BB_Upper"],
            "bb_lower": indicators["BB_Lower"],
            **indicators,
        },
    }
