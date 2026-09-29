import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def candles():
    def build(n=150, slope=0.1, end="2026-09-28T10:00:00Z", timeframe="1h"):
        step = pd.Timedelta(timeframe)
        times = pd.date_range(end=pd.Timestamp(end) - step, periods=n, freq=step)
        prices = 100 + np.arange(n) * slope + np.sin(np.arange(n) / 3) * 0.15
        return pd.DataFrame(
            {
                "time": times,
                "close_time": times + step - pd.Timedelta(milliseconds=1),
                "open": prices,
                "high": prices + 0.5,
                "low": prices - 0.5,
                "close": prices,
                "volume": np.full(n, 100.0),
            }
        )

    return build


@pytest.fixture(autouse=True)
def no_external_network(monkeypatch, tmp_path):
    import socket

    def blocked(*args, **kwargs):
        raise AssertionError("Network prohibited in tests")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setenv("PAPER_JOURNAL_PATH", str(tmp_path / "paper_journal.sqlite3"))


@pytest.fixture
def snapshot(candles):
    from datetime import timedelta

    from market_snapshot import build_snapshot

    df = candles(n=84, slope=0.005)
    df.loc[len(df) - 1, "volume"] = 400
    return build_snapshot(
        df, "BTCUSDT", "1h", df.close_time.iloc[-1].to_pydatetime() + timedelta(milliseconds=1)
    )
