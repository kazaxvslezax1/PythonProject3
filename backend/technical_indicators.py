"""Causal indicators. Wilder uses SMA seed then alpha=1/period; MACD adjust=False."""
import numpy as np
import pandas as pd


def wilder(values, period=14):
    values = values.astype(float)
    result = pd.Series(np.nan, index=values.index, dtype=float)
    valid = values.first_valid_index()
    if valid is None:
        return result
    start = values.index.get_loc(valid)
    seed = start + period - 1
    if seed >= len(values):
        return result
    result.iloc[seed] = values.iloc[start:seed + 1].mean()
    for i in range(seed + 1, len(values)):
        result.iloc[i] = (result.iloc[i - 1] * (period - 1) + values.iloc[i]) / period
    return result


def calculate_rsi(prices, period=14):
    delta = prices.astype(float).diff()
    gain = wilder(delta.clip(lower=0), period)
    loss = wilder(-delta.clip(upper=0), period)
    result = 100 - 100 / (1 + gain / loss.replace(0, np.nan))
    result = result.mask((loss == 0) & (gain > 0), 100)
    return result.mask((loss == 0) & (gain == 0), 50)


def calculate_macd(prices, fast=12, slow=26, signal=9):
    macd = prices.ewm(span=fast, adjust=False).mean() - prices.ewm(span=slow, adjust=False).mean()
    line = macd.ewm(span=signal, adjust=False).mean()
    return macd, line, macd - line


def calculate_bollinger_bands(prices, period=20, std_dev=2):
    middle = prices.rolling(period).mean()
    std = prices.rolling(period).std(ddof=0)
    return middle + std_dev * std, middle, middle - std_dev * std


def true_range(df):
    prev = df['close'].shift(1)
    return pd.concat([df.high - df.low, (df.high - prev).abs(), (df.low - prev).abs()], axis=1).max(axis=1)


def calculate_atr(df, period=14):
    return wilder(true_range(df), period)


def calculate_adx(df, period=14):
    up, down = df.high.diff(), -df.low.diff()
    plus = up.where((up > down) & (up > 0), 0.0)
    minus = down.where((down > up) & (down > 0), 0.0)
    plus.iloc[0] = minus.iloc[0] = np.nan
    # Common smoothing factor cancels in DX; preserve the original index.
    plus, minus = wilder(plus, period), wilder(minus, period)
    denominator = plus + minus
    dx = (100 * (plus - minus).abs() / denominator.replace(0, np.nan)).mask(denominator == 0, 0)
    return wilder(dx, period)


def calculate_all_indicators(df):
    df = df.copy()
    prices = df.close.astype(float)
    df['RSI'] = calculate_rsi(prices)
    df['MACD'], df['MACD_Signal'], df['MACD_Histogram'] = calculate_macd(prices)
    df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = calculate_bollinger_bands(prices)
    for period in (10, 20, 50, 200):
        df[f'SMA_{period}'] = prices.rolling(period).mean()
    for period in (12, 26):
        df[f'EMA_{period}'] = prices.ewm(span=period, adjust=False).mean()
    df['ATR'] = calculate_atr(df)
    df['SMA_ATR_10'] = df.ATR.rolling(10).mean()
    df['ADX'] = calculate_adx(df)
    df['SMA_Volume_10'] = df.volume.shift(1).rolling(10).mean()
    df['Volume_Ratio'] = df.volume / df.volume.shift(1).rolling(20).mean().replace(0, np.nan)
    df['Volatility'] = prices.pct_change().rolling(20).std() * 100
    return df
