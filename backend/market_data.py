"""Validated, closed Binance spot candles; no order endpoints."""
import re
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import requests

INTERVALS = {'1m': 60, '5m': 300, '15m': 900, '30m': 1800, '1h': 3600,
             '4h': 14400, '6h': 21600, '1d': 86400}


def normalize_symbol(symbol):
    symbol = symbol.upper()
    if symbol.endswith('USD'):
        symbol += 'T'
    if not re.fullmatch(r'[A-Z0-9]{2,20}USDT', symbol):
        raise ValueError('Unsupported symbol')
    return symbol


def utc(value=None):
    stamp = pd.Timestamp(value if value is not None else datetime.now(timezone.utc))
    return stamp.tz_localize('UTC') if stamp.tzinfo is None else stamp.tz_convert('UTC')


def validate_candles(df, timeframe, as_of=None, min_bars=50, require_fresh=True):
    if timeframe not in INTERVALS:
        raise ValueError('Unsupported timeframe')
    required = ['time', 'close_time', 'open', 'high', 'low', 'close', 'volume']
    if not set(required).issubset(df.columns):
        raise ValueError('Missing OHLCV timestamps or columns')
    df = df[required].copy()
    for col in ('time', 'close_time'):
        df[col] = pd.to_datetime(df[col], utc=True)
    if df[['time', 'close_time']].isna().any().any():
        raise ValueError('Invalid timestamp')
    cutoff = utc(as_of)
    df = df[df.close_time < cutoff].copy()
    if len(df) < min_bars:
        raise ValueError('Insufficient closed candles')
    if not df.time.is_monotonic_increasing or df.time.duplicated().any():
        raise ValueError('Unsorted or duplicate candles')
    step = pd.Timedelta(seconds=INTERVALS[timeframe])
    if not (df.time.diff().dropna() == step).all():
        raise ValueError('Missing candles')
    if not ((df.close_time - df.time) == step - pd.Timedelta(milliseconds=1)).all():
        raise ValueError('Invalid candle duration')
    for col in required[2:]:
        df[col] = pd.to_numeric(df[col], errors='raise')
    if not np.isfinite(df[required[2:]].to_numpy()).all():
        raise ValueError('Non-finite OHLCV')
    if (df[['open', 'high', 'low', 'close']] <= 0).any().any() or (df.volume < 0).any():
        raise ValueError('Invalid price or volume')
    if ((df.high < df[['open', 'close', 'low']].max(axis=1)) |
            (df.low > df[['open', 'close', 'high']].min(axis=1))).any():
        raise ValueError('Invalid OHLC bounds')
    if require_fresh and cutoff - df.close_time.iloc[-1] > step + pd.Timedelta(seconds=30):
        raise ValueError('Stale candles')
    return df.reset_index(drop=True)


def load_candles(symbol, timeframe='15m', limit=200, as_of=None, session=None):
    symbol = normalize_symbol(symbol)
    if timeframe not in INTERVALS or not 1 <= limit <= 100000:
        raise ValueError('Invalid timeframe or candle count')
    cutoff = utc(as_of)
    end = int(cutoff.timestamp() * 1000) - 1
    rows = []
    get = (session or requests).get
    # Backward pagination, including one possible open candle.
    while len(rows) < limit + 1:
        count = min(1000, limit + 1 - len(rows))
        response = get('https://api.binance.com/api/v3/klines', params={
            'symbol': symbol, 'interval': timeframe, 'limit': count, 'endTime': end}, timeout=(5, 20))
        response.raise_for_status()
        page = response.json()
        if not isinstance(page, list) or not page:
            break
        if rows and int(page[-1][0]) >= int(rows[0][0]):
            raise ValueError('Pagination made no progress')
        rows = page + rows
        end = int(page[0][0]) - 1
    columns = ['time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
               'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore']
    df = pd.DataFrame(rows, columns=columns)
    for col in ('time', 'close_time'):
        df[col] = pd.to_datetime(df[col], unit='ms', utc=True)
    df = validate_candles(df, timeframe, cutoff, min_bars=limit)
    return df.tail(limit).reset_index(drop=True)
