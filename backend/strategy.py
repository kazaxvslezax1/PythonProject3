"""Compatibility adapter; no separate indicator or direction rules."""

import os

import pandas as pd
from strategy_engine import generate_signal, legacy_result


def generate_strategy(df, symbol="BTCUSDT", timeframe=None, as_of=None):
    try:
        if timeframe is None:
            from market_data import INTERVALS

            seconds = int((df.time.iloc[1] - df.time.iloc[0]).total_seconds())
            timeframe = next(k for k, v in INTERVALS.items() if v == seconds)
        cutoff = as_of if as_of is not None else df.close_time.iloc[-1] + pd.Timedelta(milliseconds=1)
        signal = generate_signal(df, symbol, timeframe, cutoff)
        return legacy_result(signal, df)
    except Exception as exc:
        return {"error": type(exc).__name__, "action": "HOLD", "direction": "HOLD", "strength": 0}


def find_best_timeframe(symbol="BTCUSDT"):
    # Explicit configuration, never choose the best in-sample return.
    tf = os.environ.get("STRATEGY_TIMEFRAME", "1h")
    return {
        "best_timeframe": tf,
        "best_return": None,
        "all_timeframes": [tf],
        "all_results": {},
        "selection": "configured; no in-sample optimization",
    }
