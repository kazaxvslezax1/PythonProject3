"""One analysis cutoff. Network access is isolated from the pure strategy."""

from data import get_candles
from market_data import utc
from strategy_engine import generate_signal, indicator_values, legacy_result


def analyze_market(symbol, timeframe="1h", as_of=None, loader=None):
    cutoff = utc(as_of)
    loader = loader or get_candles
    df = loader(symbol, timeframe, limit=120, as_of=cutoff)
    signal = generate_signal(df, symbol, timeframe, cutoff)
    result = legacy_result(signal, df)
    result["frame"] = df
    result["technical_signal"] = signal
    result["as_of"] = cutoff
    result["volume_ratio"] = indicator_values(df)["Volume_Ratio"]
    return result


def consensus_from_analysis(analysis):
    signal = analysis["technical_signal"]
    indicators = analysis["indicators"]
    sign = 1 if signal.direction.value == "LONG" else -1 if signal.direction.value == "SHORT" else 0
    votes = [
        1 if indicators["SMA_20"] > indicators["SMA_50"] else -1,
        1 if indicators["MACD"] > indicators["MACD_Signal"] else -1,
        1 if indicators["RSI"] > 50 else -1,
    ]
    agreed = sum(v == sign for v in votes) if sign else 0
    return {
        "systems_checked": len(votes),
        "systems_agreed": agreed,
        "signals": signal.reasons,
        "consensus_level": agreed / len(votes) * 100,
        "final_direction": signal.direction.value,
        "confidence": signal.quality * 10,
        "ai_confidence_real": signal.quality,
        "ai_confidence_filtered": signal.quality,
        "ai_recommendation": signal.direction.value,
        "risk_level": "LOW" if signal.quality >= 7 else "MEDIUM",
        "status": "OK",
    }


def get_consensus(symbol):
    try:
        return consensus_from_analysis(analyze_market(symbol))
    except (ValueError, OSError, RuntimeError) as exc:
        return unavailable_consensus(type(exc).__name__)
    except Exception:
        return unavailable_consensus("DATA_UNAVAILABLE")


def unavailable_consensus(reason):
    return {
        "systems_checked": 0,
        "systems_agreed": 0,
        "signals": [reason],
        "consensus_level": 0,
        "final_direction": "HOLD",
        "confidence": 0,
        "ai_confidence_real": 0,
        "ai_confidence_filtered": 0,
        "ai_recommendation": "HOLD",
        "risk_level": "HIGH",
        "status": "DATA_UNAVAILABLE",
    }
