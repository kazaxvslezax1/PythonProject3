import pandas as pd


def generate_strategy(df):
    """
    Умная торговая стратегия на основе нескольких индикаторов
    """
    if len(df) < 50:
        return {"error": "❌ Недостаточно данных для анализа (нужно минимум 50 свечей)"}

    try:
        # ====================
        # 1. РАСЧЕТ ИНДИКАТОРОВ
        # ====================

        # Скользящие средние (тренд)
        df['SMA_20'] = df['close'].rolling(window=20).mean()
        df['SMA_50'] = df['close'].rolling(window=50).mean()
        df['SMA_200'] = df['close'].rolling(window=200).mean()
        df['EMA_12'] = df['close'].ewm(span=12).mean()
        df['EMA_26'] = df['close'].ewm(span=26).mean()

        # MACD (тренд и импульс)
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']

        # RSI (сила движения)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # Bollinger Bands (волатильность)
        df['BB_Middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)

        # ====================
        # 2. ТЕКУЩИЕ ЗНАЧЕНИЯ (последняя свеча)
        # ====================

        current_price = df['close'].iloc[-1]
        sma_20_current = df['SMA_20'].iloc[-1]
        sma_50_current = df['SMA_50'].iloc[-1]
        current_rsi = df['RSI'].iloc[-1]
        current_macd = df['MACD'].iloc[-1]
        current_macd_signal = df['MACD_Signal'].iloc[-1]
        bb_upper = df['BB_Upper'].iloc[-1]
        bb_lower = df['BB_Lower'].iloc[-1]

        # ====================
        # 3. АНАЛИЗ СИГНАЛОВ
        # ====================

        signals = []
        strength = 0  # Сила сигнала от -10 до +10

        # 🔵 Анализ тренда (скользящие средние)
        if sma_20_current > sma_50_current:
            signals.append("📈 Восходящий тренд")
            strength += 2
        else:
            signals.append("📉 Нисходящий тренд")
            strength -= 2

        # 🟡 Анализ MACD
        if current_macd > current_macd_signal:
            signals.append("MACD ↗️ Бычий")
            strength += 1
        else:
            signals.append("MACD ↘️ Медвежий")
            strength -= 1

        # 🟢 Анализ RSI
        if current_rsi < 30:
            signals.append("🟢 RSI: ПЕРЕПРОДАННОСТЬ (покупка)")
            strength += 3
        elif current_rsi > 70:
            signals.append("🔴 RSI: ПЕРЕКУПЛЕННОСТЬ (продажа)")
            strength -= 3
        elif current_rsi > 50:
            signals.append("🟡 RSI: Бычье настроение")
            strength += 1
        else:
            signals.append("🔵 RSI: Медвежье настроение")
            strength -= 1

        # 🟣 Анализ Bollinger Bands
        if current_price < bb_lower:
            signals.append("🎯 Цена НИЖЕ BB - возможен отскок вверх")
            strength += 2
        elif current_price > bb_upper:
            signals.append("🎯 Цена ВЫШЕ BB - возможен отскок вниз")
            strength -= 2
        else:
            signals.append("📊 Цена в канале BB")

        # ====================
        # 4. ФОРМИРУЕМ РЕКОМЕНДАЦИЮ
        # ====================

        if strength >= 4:
            recommendation = "🚀 СИЛЬНЫЙ СИГНАЛ НА ПОКУПКУ"
            action = "BUY"
        elif strength >= 2:
            recommendation = "✅ СИГНАЛ НА ПОКУПКУ"
            action = "BUY"
        elif strength <= -4:
            recommendation = "🔻 СИЛЬНЫЙ СИГНАЛ НА ПРОДАЖУ"
            action = "SELL"
        elif strength <= -2:
            recommendation = "❌ СИГНАЛ НА ПРОДАЖУ"
            action = "SELL"
        else:
            recommendation = "⚪ НЕТ ЧЕТКОГО СИГНАЛА - ЖДАТЬ"
            action = "HOLD"

        # ====================
        # 5. ФОРМИРУЕМ ИТОГОВЫЙ ОТЧЕТ
        # ====================

        result = {
            "recommendation": recommendation,
            "action": action,
            "strength": strength,
            "signals": " | ".join(signals),
            "indicators": {
                "price": round(current_price, 2),
                "sma_20": round(sma_20_current, 2),
                "sma_50": round(sma_50_current, 2),
                "rsi": round(current_rsi, 2),
                "macd": round(current_macd, 4),
                "bb_upper": round(bb_upper, 2),
                "bb_lower": round(bb_lower, 2)
            }
        }

        return result

    except Exception as e:
        return {"error": f"❌ Ошибка в стратегии: {str(e)}"}


def find_best_timeframe(symbol="btcusd"):
    """
    Тестирует стратегию на разных таймфреймах и выбирает лучший
    """
    # Используем только таймфреймы, которые поддерживает Gemini
    timeframes = ["5m", "15m", "1h", "6h"]
    best_result = -100
    best_timeframe = None
    results = {}

    print(f"🔍 Тестируем таймфреймы для {symbol}...")

    for tf in timeframes:
        try:
            # Получаем данные
            from data import get_candles
            df = get_candles(symbol, tf, limit=200)

            if len(df) < 50:  # Слишком мало данных
                print(f"   {tf}: недостаточно данных")
                continue

            # Тестируем стратегию
            from backtest import backtest
            result = backtest(df)

            results[tf] = result
            print(f"   {tf}: {result:.2f}%")

            # Выбираем лучший результат
            if result > best_result:
                best_result = result
                best_timeframe = tf

        except Exception as e:
            print(f"   {tf}: ошибка - {e}")
            continue

    if best_timeframe:
        print(f"✅ Лучший таймфрейм: {best_timeframe} ({best_result:.2f}%)")
        return {
            "best_timeframe": best_timeframe,
            "best_return": best_result,
            "all_timeframes": timeframes,
            "all_results": results
        }
    else:
        return {"error": "Не удалось протестировать таймфрейсы"}