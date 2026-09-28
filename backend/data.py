"""Compatibility entry point. One venue and one closed-candle policy."""
from market_data import load_candles


def get_candles(symbol='BTCUSDT', timeframe='15m', limit=100, as_of=None):
    return load_candles(symbol, timeframe, limit, as_of=as_of)


def get_gemini_candles(*args, **kwargs):
    raise ValueError('Gemini fallback disabled: mixing USD/USDT venues is not permitted')
