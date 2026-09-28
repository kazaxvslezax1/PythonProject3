"""Compatibility return uses the same strategy and execution engine."""
from backtester import signals_for, simulate
from market_data import INTERVALS


def backtest(df,symbol='BTCUSDT',timeframe=None):
    if timeframe is None:
        seconds=int((df.time.iloc[1]-df.time.iloc[0]).total_seconds())
        timeframe=next(k for k,v in INTERVALS.items() if v==seconds)
    return simulate(df,signals_for(df,symbol,timeframe))['stats']['total_profit']
