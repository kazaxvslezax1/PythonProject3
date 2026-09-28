from market_data import load_candles


def get_binance_candles(symbol="BTCUSDT", timeframe="15m", limit=100, as_of=None):
    return load_candles(symbol, timeframe, limit, as_of=as_of)


BINANCE_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT",
    "LTCUSDT", "BCHUSDT", "XLMUSDT", "XRPUSDT", "EOSUSDT",
    "TRXUSDT", "ETCUSDT", "XTZUSDT", "ATOMUSDT", "ALGOUSDT",
    "ZECUSDT", "BATUSDT", "MANAUSDT", "SANDUSDT", "MATICUSDT",
    "AVAXUSDT", "FTMUSDT", "NEARUSDT", "SOLUSDT", "DOGEUSDT",
    "SHIBUSDT", "APEUSDT", "GALAUSDT", "SUSHIUSDT", "UNIUSDT"
]