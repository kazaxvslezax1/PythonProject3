import requests
import pandas as pd
import time


def get_binance_candles(symbol="BTCUSDT", timeframe="15m", limit=100):
    """
    Получаем данные с Binance API (больше монет!)
    """
    try:
        # Конвертируем таймфреймы для Binance
        tf_mapping = {
            "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
            "1h": "1h", "4h": "4h", "6h": "6h", "1d": "1d"
        }

        binance_tf = tf_mapping.get(timeframe, "15m")
        url = "https://api.binance.com/api/v3/klines"

        params = {
            "symbol": symbol.upper(),
            "interval": binance_tf,
            "limit": limit
        }

        print(f"🔍 Binance запрос: {symbol} {timeframe}")
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            raise Exception(f"Binance API error: {response.text}")

        data = response.json()

        # Создаем DataFrame
        df = pd.DataFrame(data, columns=[
            "time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades",
            "taker_buy_base", "taker_buy_quote", "ignore"
        ])

        # Конвертируем время и цены
        df["time"] = pd.to_datetime(df["time"], unit="ms")
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col])

        df.sort_values("time", inplace=True)
        df.reset_index(drop=True, inplace=True)

        print(f"✅ Binance: {len(df)} свечей для {symbol}")
        return df[["time", "open", "high", "low", "close", "volume"]]

    except Exception as e:
        print(f"❌ Binance ошибка: {e}")
        raise


# Список популярных монет на Binance
BINANCE_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT",
    "LTCUSDT", "BCHUSDT", "XLMUSDT", "XRPUSDT", "EOSUSDT",
    "TRXUSDT", "ETCUSDT", "XTZUSDT", "ATOMUSDT", "ALGOUSDT",
    "ZECUSDT", "BATUSDT", "MANAUSDT", "SANDUSDT", "MATICUSDT",
    "AVAXUSDT", "FTMUSDT", "NEARUSDT", "SOLUSDT", "DOGEUSDT",
    "SHIBUSDT", "APEUSDT", "GALAUSDT", "SUSHIUSDT", "UNIUSDT"
]