"""Causal and reproducibility checks for the frozen offline basis study."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPORTS = Path(__file__).resolve().parents[1] / "reports"
sys.path.insert(0, str(REPORTS))
import futures_spot_basis_research as research  # noqa: E402


@pytest.mark.parametrize("symbol", ["SHIBUSDT", "PEPEUSDT"])
def test_thousand_contract_normalization(symbol: str) -> None:
    mapping = json.loads(research.PROTOCOL.read_text())["universe_multiplier"][symbol]
    assert mapping[0] == f"1000{symbol}"
    assert mapping[1] == 1000
    spot = pd.Series([0.01, 0.02])
    futures = pd.Series([10.1, 20.2])
    basis = research.normalize_basis(futures, spot, mapping[1])
    assert np.allclose(basis, [1, 1])
    assert (basis.abs() < 20).all()
    assert (research.normalize_basis(futures, spot, 1).abs() > 20).all()


def test_real_source_exact_closed_interval_alignment() -> None:
    reference = json.loads(research.previous.RESULT_JSON.read_text())
    row = next(
        row for row in reference["joined_data"] if row["symbol"] == "BTCUSDT" and row["timeframe"] == "1h"
    )
    spot, futures, info = research.load_prices("BTCUSDT", "1h", 1, row["aggregate_sha256"])
    assert info["integrity"] == "PASS"
    assert spot.index.equals(futures.index)
    assert (spot["time"] == spot.index - pd.Timedelta(hours=1)).all()
    assert (spot["close_time"] == spot.index - pd.Timedelta(milliseconds=1)).all()
    assert (futures["first_open"] == (spot.index - pd.Timedelta(hours=1)).asi8 // 1_000_000).all()
    assert (futures["last_close"] == spot.index.asi8 // 1_000_000 - 1).all()


def test_future_price_mutation_does_not_change_current_features() -> None:
    index = pd.date_range("2024-01-01", periods=120, freq="h", tz="UTC")
    spot = pd.Series(np.linspace(100, 102, 120), index=index)
    futures = spot * 1.001
    original = research.basis_features(research.normalize_basis(futures, spot, 1))
    changed = futures.copy()
    changed.iloc[101:] *= 1.1
    mutated = research.basis_features(research.normalize_basis(changed, spot, 1))
    pd.testing.assert_frame_equal(original.iloc[:101], mutated.iloc[:101])


def test_trailing_percentile_uses_only_preceding_90() -> None:
    series = pd.Series(np.arange(100.0))
    percentile = research.trailing_percentile(series)
    assert percentile.iloc[:90].isna().all()
    assert percentile.iloc[90] == 1
    changed = series.copy()
    changed.iloc[91:] = -1000
    assert research.trailing_percentile(changed).iloc[90] == percentile.iloc[90]


def test_forward_outcome_starts_next_bar_and_purges_split_end() -> None:
    index = pd.date_range("2024-12-31 20:00", periods=6, freq="h", tz="UTC")
    spot = pd.DataFrame(
        {
            "close": [100, 101, 102, 103, 104, 105],
            "high": [100, 102, 103, 104, 105, 106],
            "low": [99, 100, 101, 102, 103, 104],
        },
        index=index,
    )
    outcome = research.forward_outcomes(spot, 2)
    assert outcome.loc[index[0], "signed_pct"] == pytest.approx(2)
    assert outcome.loc[index[0], "mfe_pct"] == pytest.approx(3)
    assert outcome.loc[index[0], "mae_pct"] == pytest.approx(0)
    assert pd.isna(outcome.loc[index[-1], "signed_pct"])
    discovery = research.segment(outcome, "discovery", "1h", 2)
    assert discovery.index.max() == pd.Timestamp("2024-12-31 22:00", tz="UTC")


def test_cost_arithmetic_and_deterministic_features() -> None:
    assert research.cost_hurdles(0.5) == pytest.approx({"zero": 0.5, "base": 0.2, "double": -0.1})
    index = pd.date_range("2024-01-01", periods=100, freq="h", tz="UTC")
    basis = pd.Series(np.linspace(-1, 1, 100), index=index)
    first = research.basis_features(basis)
    second = research.basis_features(basis)
    pd.testing.assert_frame_equal(first, second)


def test_deterministic_model_and_weekly_replay() -> None:
    index = pd.date_range("2024-01-01", periods=120, freq="h", tz="UTC")
    train = pd.DataFrame(
        {
            name: np.sin(np.arange(120) / (i + 2))
            for i, name in enumerate(research.PRICE_COLS + research.BASIS_COLS)
        },
        index=index,
    )
    train["signed_pct"] = train["spot_ret1"] * 0.1 + train["basis_pct"] * 0.2
    columns = research.PRICE_COLS + research.BASIS_COLS
    first = research.previous.fit_predict(train.iloc[:90], train.iloc[90:], columns, "signed_pct")
    second = research.previous.fit_predict(train.iloc[:90], train.iloc[90:], columns, "signed_pct")
    np.testing.assert_array_equal(first, second)
    events = pd.DataFrame(
        {
            "effect_pct": np.linspace(-0.2, 0.4, 30),
            "raw_forward_pct": np.linspace(-0.1, 0.5, 30),
            "week": np.repeat([f"2025-W{i:02}" for i in range(1, 11)], 3),
            "quarter": ["2025Q1"] * 30,
            "symbol": ["BTCUSDT"] * 15 + ["ETHUSDT"] * 15,
            "mfe_pct": np.ones(30),
            "mae_pct": -np.ones(30),
            "basis_pct": np.ones(30) * 0.1,
        }
    )
    first_summary = research.summarize_events(events, 0.01, hypothesis="H1", timeframe="1h")
    second_summary = research.summarize_events(events, 0.01, hypothesis="H1", timeframe="1h")
    assert first_summary == second_summary


def test_protocol_is_frozen_and_source_hash_verified() -> None:
    assert research.sha256(research.PROTOCOL) == research.EXPECTED_PROTOCOL_SHA
    with pytest.raises(RuntimeError, match="Futures aggregate changed"):
        research.load_prices("BTCUSDT", "1h", 1, "0" * 64)
