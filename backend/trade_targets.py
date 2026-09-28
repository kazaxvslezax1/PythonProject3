"""Adapters for the plan produced by the shared strategy. No fabricated prices."""

from analysis_service import analyze_market
from signal_models import direction


def targets_for(symbol, timeframe="1h", requested_direction=None, as_of=None):
    data = analyze_market(symbol, timeframe, as_of)
    return targets_from_analysis(data, requested_direction)


def targets_from_analysis(data, requested_direction=None):
    symbol = data["symbol"]
    signal = data["technical_signal"]
    if signal.plan is None:
        return {"error": "HOLD: no trade plan", "direction": "HOLD"}
    plan = signal.plan
    if requested_direction is not None and direction(requested_direction) != plan.direction:
        return {"error": "Requested direction conflicts with technical signal", "direction": "HOLD"}
    risk = abs(plan.entry - plan.stop_loss) / plan.entry
    frame = data["frame"]
    return {
        "symbol": symbol,
        "direction": plan.direction.value,
        "entry_price": plan.entry,
        "stop_loss": plan.stop_loss,
        "take_profit": plan.take_profits[-1],
        "take_profits": plan.take_profits,
        "risk_reward_ratio": plan.rr,
        "risk_reward": plan.rr,
        "stop_loss_percent": risk,
        "smart_stop_percent": risk * 100,
        "risk_percent": risk * 100,
        "reward_percent": risk * 100 * plan.rr,
        "atr": data["indicators"]["ATR"],
        "atr_percent": data["indicators"]["ATR"] / plan.entry * 100,
        "current_volatility": data["indicators"]["Volatility"],
        "quality_score": signal.quality,
        "current_support": float(frame.low.tail(20).min()),
        "current_resistance": float(frame.high.tail(20).max()),
        "trend": plan.direction.value,
        "recommendation": "Technical plan; heuristic quality",
        "volatility_adjusted": True,
        "volatility_message": "ATR Wilder; closed candles",
        "timestamp": signal.timestamp.isoformat(),
    }
