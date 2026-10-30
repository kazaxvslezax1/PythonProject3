"""Shared signal commands and ranking, independent of Telegram global state."""

from analysis_service import analyze_market, consensus_from_analysis
from signal_presenter import format_technical


def ranked_signals(symbols, premium=False, analyzer=None):
    analyzer = analyzer or analyze_market
    result = []
    for symbol in symbols:
        try:
            data = analyzer(symbol)
            signal = data["technical_signal"]
            if signal.plan is None:
                continue
            if premium and (signal.quality < 7 or data["volume_ratio"] < 1.2 or signal.plan.rr < 2.5):
                continue
            result.append(data)
        except Exception:
            continue
    return sorted(result, key=lambda d: d["technical_signal"].quality, reverse=True)


def scan_command(bot, message, symbols, premium=False):
    results = ranked_signals(symbols, premium)
    if not results:
        bot.reply_to(message, "Подтверждённых сигналов нет; HOLD / недостаточно данных")
    for data in results[:3]:
        bot.reply_to(message, format_technical(data), parse_mode=None)


def premium_alert(data):
    from trade_targets import targets_from_analysis

    return {
        "symbol": data["symbol"],
        "action": data["action"],
        "strength": data["strength"],
        "targets": targets_from_analysis(data),
        "volume_ratio": data["volume_ratio"],
        "confluence": consensus_from_analysis(data)["consensus_level"],
        "ai_analysis": {
            "ai_confidence_score": data["quality"],
            "recommendation": "Heuristic technical quality",
        },
        "premium_score": data["quality"],
        "premium_bonus": 0,
        "timestamp": data["as_of"].to_pydatetime(),
    }
