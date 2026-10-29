"""Causality and replay checks for the frozen 4h/1d Spot research."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPORTS = Path(__file__).resolve().parents[1] / "reports"
sys.path.insert(0, str(REPORTS))
import higher_timeframe_edge_research as study  # noqa: E402


def candles(count: int = 12) -> pd.DataFrame:
    index = pd.date_range("2020-01-01", periods=count, freq="4h", tz="UTC", name="time")
    close = np.linspace(100, 100 + count / 10, count)
    return pd.DataFrame(
        {
            "open": close - 0.1,
            "high": close + 0.2,
            "low": close - 0.3,
            "close": close,
            "volume": np.ones(count),
        },
        index=index,
    )


def test_daily_utc_aggregation_requires_six_complete_bars() -> None:
    source = candles()
    daily, incomplete = study.aggregate_daily(source)
    assert incomplete == 0
    assert len(daily) == 2
    assert daily.iloc[0]["open"] == pytest.approx(source.iloc[0]["open"])
    assert daily.iloc[0]["close"] == pytest.approx(source.iloc[5]["close"])
    assert daily.iloc[0]["high"] == pytest.approx(source.iloc[:6]["high"].max())
    assert daily.iloc[0]["volume"] == pytest.approx(6)
    broken = source.copy()
    broken.iloc[2, broken.columns.get_loc("close")] = np.nan
    partial, incomplete = study.aggregate_daily(broken)
    assert incomplete == 1
    assert pd.isna(partial.iloc[0]["close"])


def test_no_future_feature_leakage_and_prior_trend() -> None:
    source = candles(1600)
    before = study.price_features(source, "4h")
    mutated = source.copy()
    mutated.iloc[1550:, mutated.columns.get_loc("close")] *= 1.1
    after = study.price_features(mutated, "4h")
    pd.testing.assert_frame_equal(before.iloc[:1550], after.iloc[:1550])
    assert before.iloc[1550]["pre_trend_z"] == pytest.approx(after.iloc[1550]["pre_trend_z"])


def test_breakout_uses_preceding_range_and_cooldown() -> None:
    index = pd.date_range("2024-01-01", periods=4, freq="1D", tz="UTC")
    frame = pd.DataFrame(
        {
            "close": [100, 106, 107, 108],
            "pre_high": [105] * 4,
            "pre_low": [95] * 4,
            "range_percentile": [0.3, 0.2, 0.2, 0.2],
            "z7": [1] * 4,
            "pre_trend_z": [1] * 4,
            "pullback_z": [0] * 4,
            "vol_state": ["normal"] * 4,
        },
        index=index,
    )
    events, controls = study.select_family(frame, "H3")
    assert controls.empty
    assert events.index.tolist() == [index[1]]
    assert events.iloc[0]["direction"] == 1


def test_forward_starts_at_next_open_and_split_purges() -> None:
    source = candles(6)
    source.iloc[0, source.columns.get_loc("high")] = 1000
    outcome = study.forward_outcomes(source, 2, "4h")
    assert outcome.iloc[0]["entry_open"] == pytest.approx(source.iloc[1]["open"])
    assert outcome.iloc[0]["signed_pct"] == pytest.approx(
        (source.iloc[2]["close"] / source.iloc[1]["open"] - 1) * 100
    )
    assert outcome.iloc[0]["mfe_pct"] < 10  # event-candle high=1000 is excluded
    index = pd.date_range("2022-12-31 12:00", periods=5, freq="4h", tz="UTC")
    data = pd.DataFrame({"signed_pct": np.ones(5), "entry_open": np.ones(5)}, index=index)
    eligible = study.eligible_segment(data, "discovery", "4h", 2)
    assert eligible.index.max() == pd.Timestamp("2022-12-31 12:00", tz="UTC")


def test_trailing_percentile_and_future_mutation() -> None:
    values = pd.Series(np.arange(12.0))
    before = study.trailing_percentile(values, 5)
    changed = values.copy()
    changed.iloc[9:] = -100
    after = study.trailing_percentile(changed, 5)
    assert before.iloc[:9].equals(after.iloc[:9])
    assert before.iloc[:5].isna().all()


def test_cross_section_excludes_unlisted_asset() -> None:
    stamp = study.START + pd.Timedelta(days=1400)
    assert stamp in pd.date_range(study.START, study.END, freq="14D", tz="UTC")

    def row(i: int) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "z30": [float(i)],
                "signed_pct": [float(i)],
                "mfe_pct": [float(i) + 1],
                "mae_pct": [float(i) - 1],
                "btc_regime": ["up"],
            },
            index=pd.DatetimeIndex([stamp]),
        )

    four = {symbol: row(i) for i, symbol in enumerate(("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"))}
    events, _ = study.cross_section_events(four, "1d", "validation")
    assert events == []
    five = four | {"PEPEUSDT": row(4)}
    events, _ = study.cross_section_events(five, "1d", "validation")
    assert len(events) == 1 and events[0]["active_symbols"] == 5
    assert "PEPEUSDT" in events[0]["top_symbols"]
    missing_future = {symbol: frame.copy() for symbol, frame in five.items()}
    missing_future["PEPEUSDT"].loc[stamp, "signed_pct"] = np.nan
    unavailable, _ = study.cross_section_events(missing_future, "1d", "validation")
    assert len(unavailable) == 1
    assert unavailable[0]["active_symbols"] == 5
    assert unavailable[0]["top_symbols"] == events[0]["top_symbols"]
    assert unavailable[0]["outcome_available"] is False


def test_missing_future_cannot_change_causal_episode_selection() -> None:
    index = pd.date_range("2024-01-01", periods=2, freq="1D", tz="UTC")
    frame = pd.DataFrame(
        {
            "z7": [2.5, 2.6],
            "vol_state": ["normal"] * 2,
            "signed_pct": [np.nan, 1.0],
            "entry_open": [np.nan, 100.0],
            "mfe_pct": [np.nan, 2.0],
            "mae_pct": [np.nan, -1.0],
            "btc_regime": ["up"] * 2,
        },
        index=index,
    )
    before = study.family_events(frame, "BTCUSDT", "1d", "validation", "H1_H2")
    changed = frame.copy()
    changed.loc[index[0], ["signed_pct", "entry_open", "mfe_pct", "mae_pct"]] = [1.0, 100.0, 2.0, -1.0]
    after = study.family_events(changed, "BTCUSDT", "1d", "validation", "H1_H2")
    assert {item["decision_time"] for item in before} == {item["decision_time"] for item in after}
    assert {item["decision_time"] for item in before} == {index[0].isoformat()}
    assert all(not item["outcome_available"] for item in before)
    assert all(item["outcome_available"] for item in after)


def test_cost_arithmetic_and_deterministic_block_replay() -> None:
    assert study.cost_hurdles(0.5) == pytest.approx({"zero": 0.5, "base": 0.2, "double": -0.1})
    events = pd.DataFrame(
        {"month": ["2023-01"] * 3 + ["2023-02"] * 3, "effect_pct": [0.1, 0.2, -0.1, 0.4, 0.2, 0.1]}
    )
    first = study.block_bootstrap(events, "H3", "1d")
    second = study.block_bootstrap(events, "H3", "1d")
    assert first == second
    balanced = pd.DataFrame({"month": ["2023-01", "2023-02"], "effect_pct": [1.0, -1.0]})
    assert study.block_bootstrap(balanced, "H3", "1d")["p"] > 0.5


def test_frozen_protocol_hash() -> None:
    assert study.sha256(study.PROTOCOL) == study.PROTOCOL_SHA
