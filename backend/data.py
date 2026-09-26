import requests
import pandas as pd
from binance_data import get_binance_candles, BINANCE_SYMBOLS


def get_candles(symbol="btcusd", timeframe="15m", limit=100):
    """
    Умный выбор API: пробуем Gemini, если нет - Binance
    """
    # Конвертируем символы
    gemini_symbol = symbol.replace('usdt', 'usd').replace('USDT', 'USD')
    binance_symbol = symbol.replace('usd', 'USDT').upper()

    # Сначала пробуем Gemini (для BTCUSD, ETHUSD)
    if gemini_symbol in ['btcusd', 'ethusd', 'solusd', 'linkusd']:
        try:
            return get_gemini_candles(gemini_symbol, timeframe, limit)
        except:
            print(f"⚠️ Gemini не сработал, пробуем Binance для {binance_symbol}")

    # Потом Binance (все остальные монеты)
    try:
        if binance_symbol in BINANCE_SYMBOLS:
            return get_binance_candles(binance_symbol, timeframe, limit)
        else:
            # Если символ не в списке, всё равно пробуем
            return get_binance_candles(binance_symbol, timeframe, limit)
    except Exception as e:
        raise Exception(f"Не удалось получить данные для {symbol}: {e}")


def get_gemini_candles(symbol="btcusd", timeframe="15m", limit=100):
    """Получаем данные с Gemini"""
    try:
        timeframe_mapping = {
            "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
            "1h": "1hr", "6h": "6hr", "1d": "1day"
        }

        gemini_timeframe = timeframe_mapping.get(timeframe, "15m")
        url = f"https://api.gemini.com/v2/candles/{symbol}/{gemini_timeframe}"
        params = {"limit": limit}

        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            raise Exception(f"Gemini: {response.text}")

        data = response.json()
        df = pd.DataFrame(data, columns=["time", "open", "high", "low", "close", "volume"])
        df["time"] = pd.to_datetime(df["time"], unit="ms")

        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col])

        df.sort_values("time", inplace=True)
        df.reset_index(drop=True, inplace=True)

        print(f"✅ Gemini: {len(df)} свечей")
        return df

    except Exception as e:
        raise Exception(f"Gemini error: {e}")