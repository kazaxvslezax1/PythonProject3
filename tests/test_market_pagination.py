import pandas as pd
import pytest
from market_data import load_candles, validate_candles


def test_paginated_closed_history(candles):
    df = candles(n=1302, slope=0.005)
    rows = []
    for row in df.itertuples():
        rows.append(
            [
                int(row.time.timestamp() * 1000),
                str(row.open),
                str(row.high),
                str(row.low),
                str(row.close),
                str(row.volume),
                int(row.close_time.timestamp() * 1000),
                "0",
                1,
                "0",
                "0",
                "0",
            ]
        )
    calls = []

    class Reply:
        def __init__(self, data):
            self.data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self.data

    class Session:
        def get(self, url, params, timeout):
            calls.append(params)
            assert timeout == (5, 20)
            data = [r for r in rows if r[0] <= params["endTime"]]
            return Reply(data[-params["limit"] :])

    result = load_candles(
        "BTCUSDT", "1h", 1200, as_of=df.close_time.iloc[-1] + pd.Timedelta(milliseconds=1), session=Session()
    )
    assert len(result) == 1200 and len(calls) == 2
    assert result.time.iloc[0] == df.time.iloc[-1200]
    assert "close_time" in result


def test_invalid_ohlcv_rejected(candles):
    df = candles()
    cutoff = df.close_time.iloc[-1] + pd.Timedelta(milliseconds=1)
    df.loc[100, "volume"] = float("nan")
    with pytest.raises(ValueError, match="Non-finite"):
        validate_candles(df, "1h", cutoff)
