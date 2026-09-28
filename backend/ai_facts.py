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
