import numpy as np
import pandas as pd
import pytest
from market_data import validate_candles
from technical_indicators import calculate_adx, calculate_all_indicators, calculate_rsi, wilder


@pytest.mark.parametrize(
    "prices,expected", [(np.arange(1.0, 80), 100), (np.arange(80.0, 1, -1), 0), (np.ones(80), 50)]
)
def test_rsi_extremes(prices, expected):
    assert calculate_rsi(pd.Series(prices)).iloc[-1] == expected


def test_wilder_reference():
    assert list(wilder(pd.Series([1.0, 2.0, 3.0, 6.0, 9.0]), 3).dropna()) == pytest.approx(
        [2.0, 10 / 3, 47 / 9]
    )


@pytest.mark.parametrize("slope", [1, -1])
def test_adx_direction_and_index(candles, slope):
    df = candles(n=70, slope=slope)
    df.index = pd.date_range("2020-01-01", periods=len(df))
    assert calculate_adx(df).index.equals(df.index)
    assert calculate_adx(df).iloc[-1] == pytest.approx(100)


def test_indicators_causal(candles):
    df = candles()
    a = calculate_all_indicators(df.iloc[:100])
    b = calculate_all_indicators(df)
    pd.testing.assert_frame_equal(a, b.iloc[:100])


def test_closed_fresh_and_gaps(candles):
    df = candles()
    cutoff = df.time.iloc[-1] + pd.Timedelta(minutes=20)
    checked = validate_candles(df, "1h", cutoff)
    assert len(checked) == len(df) - 1
    with pytest.raises(ValueError, match="Missing candles"):
        validate_candles(df.drop(10), "1h", df.close_time.iloc[-1] + pd.Timedelta(seconds=1))
    with pytest.raises(ValueError, match="Stale"):
        validate_candles(df, "1h", "2026-09-29T10:00:00Z")
