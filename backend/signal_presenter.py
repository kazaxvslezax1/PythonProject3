"""Shared text formatter; preserve full price precision and quality units."""


def format_technical(data):
    if "error" in data:
        return "DATA_UNAVAILABLE: " + str(data["error"])
    signal = data["signal"]
    lines = [
        f"{data['symbol']} {data['timeframe']}: {signal['direction']}",
        f"Оценка {signal['quality']:.1f}/10 — эвристика, не вероятность",
        "Причины: " + "; ".join(signal["reasons"]),
        f"Закрытая свеча: {signal['timestamp']}",
    ]
    values = data["indicators"]
    lines.append(
        " | ".join(f"{k}={values[k]:.7g}" for k in ("RSI", "MACD", "SMA_20", "SMA_50", "ATR", "ADX"))
    )
    plan = signal.get("plan")
    if plan:
        lines.append(
            f"Entry {plan['entry']:.10g}; SL {plan['stop_loss']:.10g}; TP "
            + ", ".join(f"{x:.10g}" for x in plan["take_profits"])
        )
    ai = data.get("deepseek")
    if ai:
        lines.append("DeepSeek: " + ai["status"])
        if ai.get("result"):
            lines.append("AI interpretation: unverified; free text omitted")
        elif ai.get("reason"):
            lines.append(ai["reason"])
    lines.append("Режим PAPER; реальные ордера отключены.")
    return "\n".join(lines)
