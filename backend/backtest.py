import pandas as pd


def backtest(df):
    """
    Простой бэктест торговой стратегии
    """
    try:
        # Проверяем, что DataFrame не пустой
        if df is None or len(df) < 50:
            return 0.0

        # Создаем копию DataFrame чтобы не менять оригинал
        df_test = df.copy()

        # Простая стратегия: покупаем когда цена выше SMA20, продаем когда ниже
        df_test['SMA_20'] = df_test['close'].rolling(window=20).mean()
        df_test['SMA_50'] = df_test['close'].rolling(window=50).mean()

        # Создаем торговые сигналы
        df_test['position'] = 0  # 0 = нет позиции, 1 = лонг

        # Сигнал на покупку: бычий тренд (SMA20 > SMA50)
        df_test.loc[df_test['SMA_20'] > df_test['SMA_50'], 'position'] = 1

        # Сдвигаем позицию на 1 шаг вперед (торгуем на следующий бар после сигнала)
        df_test['position'] = df_test['position'].shift(1)

        # Заполняем NaN значения (первые бары)
        df_test['position'] = df_test['position'].fillna(0)

        # Рассчитываем доходность
        df_test['returns'] = df_test['close'].pct_change()
        df_test['strategy_returns'] = df_test['position'] * df_test['returns']

        # Итоговая доходность в процентах
        total_return = (df_test['strategy_returns'].sum() * 100)

        return round(total_return, 2)

    except Exception as e:
        print(f"❌ Ошибка в бэктесте: {e}")
        return 0.0