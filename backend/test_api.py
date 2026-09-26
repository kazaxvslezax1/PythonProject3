import requests


def test_gemini_api():
    """Тестируем доступность Gemini API"""
    symbols = ["btcusd", "ethusd", "btcusdt"]
    timeframes = ["1m", "5m", "15m", "1h"]

    for symbol in symbols:
        gemini_symbol = symbol.replace('usdt', 'usd').replace('USDT', 'USD')

        for tf in timeframes:
            url = f"https://api.gemini.com/v2/candles/{gemini_symbol}/{tf}?limit=10"
            print(f"Testing: {url}")

            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {symbol} {tf}: OK ({len(data)} свечей)")
                else:
                    print(f"❌ {symbol} {tf}: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"💥 {symbol} {tf}: Ошибка - {e}")

            print("-" * 50)


if __name__ == "__main__":
    test_gemini_api()