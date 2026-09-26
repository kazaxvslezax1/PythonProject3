from data import get_candles


def test_all_timeframes():
    """Тестируем все таймфреймы через нашу функцию"""
    timeframes = ["1m", "5m", "15m", "30m", "1h", "6h", "1d"]
    symbol = "btcusd"

    print("🧪 Тестируем все таймфреймы через get_candles()")
    print("=" * 50)

    for tf in timeframes:
        try:
            print(f"\n🔍 Тестируем {symbol} на {tf}...")
            df = get_candles(symbol, tf, limit=10)
            print(f"✅ {tf}: УСПЕХ - {len(df)} свечей")
            print(f"   Последняя цена: {df['close'].iloc[-1]}")
            print(f"   Время от {df['time'].iloc[0]} до {df['time'].iloc[-1]}")

        except Exception as e:
            print(f"❌ {tf}: ОШИБКА - {e}")

        print("-" * 30)


if __name__ == "__main__":
    test_all_timeframes()