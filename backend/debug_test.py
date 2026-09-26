from data import get_candles
from strategy import generate_strategy
from backtest import backtest


def debug_test():
    print("🐛 Дебаг тест...")

    try:
        # 1. Получаем данные
        print("1. Получаем данные...")
        df = get_candles("btcusd", "15m", limit=50)
        print(f"   ✅ Данные: {len(df)} строк")

        # 2. Проверяем данные
        print("2. Проверяем DataFrame...")
        print(f"   Колонки: {df.columns.tolist()}")
        print(f"   Первые 3 цены: {df['close'].head(3).tolist()}")

        # 3. Тестируем стратегию
        print("3. Тестируем стратегию...")
        strategy = generate_strategy(df)
        print(f"   ✅ Стратегия: {strategy}")

        # 4. Тестируем бэктест
        print("4. Тестируем бэктест...")
        result = backtest(df)
        print(f"   ✅ Бэктест: {result}%")

        print("🎉 ВСЁ РАБОТАЕТ!")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_test()