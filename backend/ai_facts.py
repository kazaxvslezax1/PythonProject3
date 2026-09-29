"""Deterministic comparisons; thresholds are review facts, never trading rules."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class FactClaim(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    fact_id: str
    relation: Literal["above", "below", "equal"]


def fact_catalog(snapshot):
    refs = snapshot.references()
    pairs = [("close", k) for k in ("SMA_20", "SMA_50", "EMA_12", "EMA_26", "support", "resistance")]
    pairs += [("SMA_20", "SMA_50"), ("EMA_12", "EMA_26"), ("MACD", "MACD_Signal")]
    facts = {
        f"{left}_vs_{right}": {
            "left": left,
            "right": right,
            "left_value": refs[left],
            "right_value": refs[right],
        }
        for left, right in pairs
    }
    for left, threshold in [
        ("RSI", 30),
        ("RSI", 70),
        ("MACD", 0),
        ("ADX", 25),
        ("Volume_Ratio", 1),
        ("volume_change_pct", 0),
    ]:
        facts[f"{left}_vs_{threshold}"] = dict(
            left=left, right=str(threshold), left_value=refs[left], right_value=threshold
        )
    return facts


def relation(fact):
    left, right = fact["left_value"], fact["right_value"]
    return "above" if left > right else "below" if left < right else "equal"


def check_facts(claims, snapshot):
    catalog = fact_catalog(snapshot)
    ids = [claim.fact_id for claim in claims]
    if len(ids) != len(set(ids)) or set(ids) != set(catalog):
        return ["FACT_COVERAGE_MISMATCH"]
    return [
        key
        for key, fact in catalog.items()
        if next(c.relation for c in claims if c.fact_id == key) != relation(fact)
    ]


def format_facts(claims, snapshot):
    catalog = fact_catalog(snapshot)
    signs = {"above": ">", "below": "<", "equal": "="}
    return "; ".join(
        f"{catalog[c.fact_id]['left']}={catalog[c.fact_id]['left_value']:.10g} "
        f"{signs[c.relation]} {catalog[c.fact_id]['right']}={catalog[c.fact_id]['right_value']:.10g}"
        for c in claims
    )


class FactExplanationError(ValueError):
    """Safe reason code; never includes model prose or malformed input values."""


def explain_facts(claims, snapshot):
    """Presentation only. Recheck the complete fact set before selecting up to five factors."""
    import math

    try:
        catalog = fact_catalog(snapshot)
        if not all(math.isfinite(f[k]) for f in catalog.values() for k in ("left_value", "right_value")):
            raise FactExplanationError("INVALID_MARKET_DATA")
        if check_facts(claims, snapshot):
            raise FactExplanationError("AI_FACT_CHECK_FAILED")
    except (KeyError, TypeError, AttributeError):
        raise FactExplanationError("INVALID_MARKET_DATA") from None

    refs = snapshot.references()
    rel = {c.fact_id: c.relation for c in claims}
    up, down, risks = [], [], []
    words = {"above": "выше", "below": "ниже", "equal": "на уровне"}
    price, averages = rel["close_vs_SMA_20"], rel["SMA_20_vs_SMA_50"]
    trend = (
        f"Цена ({refs['close']:.10g}) {words[price]} SMA20 ({refs['SMA_20']:.10g}); "
        f"SMA20 {words[averages]} SMA50 ({refs['SMA_50']:.10g})."
    )
    if price == averages == "above":
        up.append(trend + " Цена и расположение средних согласованы в сторону роста.")
    elif price == averages == "below":
        down.append(trend + " Цена и расположение средних согласованы в сторону снижения.")
    else:
        risks.append(trend + " Смешанная картина по цене и средним.")

    macd = rel["MACD_vs_MACD_Signal"]
    momentum = f"MACD ({refs['MACD']:.6g}) {words[macd]} сигнальной линии ({refs['MACD_Signal']:.6g})"
    if macd == "above":
        up.append(momentum + ": положительный импульс по MACD.")
    elif macd == "below":
        down.append(momentum + ": отрицательный импульс по MACD.")
    else:
        risks.append(momentum + ": направленного перевеса нет.")

    adx = rel["ADX_vs_25"]
    risks.append(
        f"ADX={refs['ADX']:.6g} "
        + {
            "below": "ниже 25: тренд недостаточно выражен.",
            "above": "выше 25: тренд выражен; ADX сам не задаёт направление.",
            "equal": "равен 25: пограничное значение выраженности тренда.",
        }[adx]
    )
    volume = rel["Volume_Ratio_vs_1"]
    risks.append(
        f"Объём={refs['Volume_Ratio']:.6g}× среднего: "
        + {
            "below": "движение не сопровождается повышенной торговой активностью.",
            "above": "активность повышена, но сама по себе не подтверждает направление.",
            "equal": "обычная активность, без превышения среднего.",
        }[volume]
    )
    if rel["RSI_vs_70"] == "above":
        risks.append(f"RSI={refs['RSI']:.6g} выше 70: зона перекупленности, а не доказательство разворота.")
    elif rel["RSI_vs_30"] == "below":
        risks.append(f"RSI={refs['RSI']:.6g} ниже 30: зона перепроданности, а не доказательство разворота.")

    if price == averages == macd == "above":
        conclusion = "Цена, средние и MACD согласованы в сторону роста. Это не прогноз продолжения движения."
    elif price == averages == macd == "below":
        conclusion = (
            "Цена, средние и MACD согласованы в сторону снижения. Это не прогноз продолжения движения."
        )
    else:
        conclusion = "Подтверждения разнонаправленны или нейтральны; однозначного вывода о направлении нет."
    if adx == "below" and volume == "below":
        conclusion += " Низкие ADX и относительный объём ограничивают подтверждение движения."
    elif adx == "below":
        conclusion += " Подтверждение направленного движения ограничено низким ADX."
    elif volume == "below":
        conclusion += " Объём не даёт дополнительного подтверждения движения."
    return {"up": up, "down": down, "risks": risks, "conclusion": conclusion}
