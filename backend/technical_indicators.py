import pandas as pd
import numpy as np


# ----------------------------------------------------
# 1. CORE INDICATORS
# ----------------------------------------------------

def calculate_rsi(prices, period=14):
    """Рассчитывает RSI (Relative Strength Index)"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    # 🛑 ИСПРАВЛЕНИЕ: Добавление защиты от деления на ноль для rs
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Рассчитывает MACD"""
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    macd_histogram = macd - macd_signal
    return macd, macd_signal, macd_histogram


def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Рассчитывает Bollinger Bands"""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, sma, lower_band


# ----------------------------------------------------
# 2. NEW INDICATORS
# ----------------------------------------------------

def calculate_atr(df, period=14):
    """Рассчитывает ATR (Average True Range)"""
    high = df['high'].astype(float)
    low = df['low'].astype(float)
    close_prev = df['close'].shift(1).astype(float)

    tr1 = high - low
    tr2 = abs(high - close_prev)
    tr3 = abs(low - close_prev)

    true_range = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)

    # ATR (EMA of TR)
    atr = true_range.ewm(span=period, adjust=False).mean()
    return atr


def calculate_adx(df, period=14):
    """Рассчитывает ADX (Average Directional Index)"""
    high = df['high'].astype(float)
    low = df['low'].astype(float)

    up_move = high.diff()
    down_move = low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

    atr = calculate_atr(df, period)

    # +/-DI
    plus_di = 100 * (pd.Series(plus_dm).rolling(window=period).sum() / atr)
    minus_di = 100 * (pd.Series(minus_dm).rolling(window=period).sum() / atr)

    # 🛑 ИСПРАВЛЕНИЕ: Защита от деления на ноль для DX
    sum_di = plus_di + minus_di
    sum_di = sum_di.replace(0, np.nan)
    dx = 100 * abs(plus_di - minus_di) / sum_di

    # ADX
    adx = dx.ewm(span=period, adjust=False).mean()

    # 🛑 ФИНАЛЬНАЯ ОЧИСТКА: Удаляем Inf, которые могут остаться
    adx = adx.replace([np.inf, -np.inf], np.nan)

    return adx


# ----------------------------------------------------
# 3. MAIN CALCULATION FUNCTION
# ----------------------------------------------------

def calculate_all_indicators(df):
    """Рассчитывает все технические индикаторы, включая критическое исправление NaN/Inf"""

    df = df.copy()
    prices = df['close'].astype(float)

    # RSI
    df['RSI'] = calculate_rsi(prices)
    df['RSI'] = df['RSI'].replace([np.inf, -np.inf], np.nan).fillna(50)  # Заменяем Inf/NaN на 50

    # MACD
    df['MACD'], df['MACD_Signal'], df['MACD_Histogram'] = calculate_macd(prices)

    # Bollinger Bands
    df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = calculate_bollinger_bands(prices)

    # Простая скользящая средняя
    df['SMA_10'] = prices.rolling(window=10).mean()
    df['SMA_20'] = prices.rolling(window=20).mean()
    df['SMA_50'] = prices.rolling(window=50).mean()

    # ATR и SMA ATR
    df['ATR'] = calculate_atr(df)
    df['SMA_ATR_10'] = df['ATR'].rolling(window=10).mean()

    # ADX
    df['ADX'] = calculate_adx(df)

    # Объем и SMA Объем
    if 'volume' in df.columns:
        df['SMA_Volume_10'] = df['volume'].rolling(window=10).mean()

    df['Volatility'] = prices.pct_change().rolling(window=20).std() * 100

    return df