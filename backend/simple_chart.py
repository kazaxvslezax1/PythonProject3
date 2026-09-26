import matplotlib.pyplot as plt
import pandas as pd
import io
import requests
from datetime import datetime


def create_simple_chart(symbol, timeframe):
    """Создает простой график цены"""
    try:
        print(f"🔄 Создаю график для {symbol} {timeframe}...")

        # Получаем данные напрямую из Binance
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": symbol.upper(),
            "interval": timeframe,
            "limit": 50
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        # Создаем DataFrame
        df = pd.DataFrame(data, columns=[
            "time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades",
            "taker_buy_base", "taker_buy_quote", "ignore"
        ])

        # Конвертируем данные
        df["time"] = pd.to_datetime(df["time"], unit="ms")
        df["close"] = pd.to_numeric(df["close"])

        # Создаем график
        plt.figure(figsize=(10, 6))
        plt.plot(df["time"], df["close"], linewidth=2, color='blue')
        plt.title(f'{symbol.upper()} Price - {timeframe.upper()}', fontsize=14, fontweight='bold')
        plt.ylabel('Price (USDT)')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Сохраняем в буфер
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=80, bbox_inches='tight')
        buf.seek(0)
        plt.close()

        print("✅ График создан!")
        return buf

    except Exception as e:
        print(f"❌ Ошибка создания графика: {e}")
        return None