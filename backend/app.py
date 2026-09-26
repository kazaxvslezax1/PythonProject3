from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from data import get_candles
from strategy import generate_strategy
from backtest import backtest

app = FastAPI(title="Crypto Assistant Backend")

# Разрешение запросов с фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/')
def home():
    return {"status": "ok", "message": "Crypto Assistant Backend is running"}


@app.post("/analyze")
def analyze(symbol: str = "btcusd", timeframe: str = "15m"):
    """
    Анализ на указанном таймфрейме
    Поддерживаемые timeframe: 1m, 5m, 15m, 30m, 1h, 6h, 1d
    (Автоматически конвертируются в формат Gemini: 1hr, 6hr, 1day)
    """
    try:
        print(f"🎯 Анализ {symbol} на таймфрейме {timeframe}")
        df = get_candles(symbol, timeframe)
        strategy_info = generate_strategy(df)
        total = backtest(df)

        # Если стратегия вернула словарь (умная стратегия)
        if isinstance(strategy_info, dict):
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "recommendation": strategy_info.get("recommendation", "N/A"),
                "action": strategy_info.get("action", "HOLD"),
                "strength": strategy_info.get("strength", 0),
                "signals": strategy_info.get("signals", "N/A"),
                "backtest_return_%": total,
                "last_price": df["close"].iloc[-1],
                "candles_count": len(df),
                "indicators": strategy_info.get("indicators", {})
            }
        else:
            # Если стратегия вернула строку (простая стратегия)
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "strategy": strategy_info,
                "backtest_return_%": total,
                "last_price": df["close"].iloc[-1],
                "candles_count": len(df)
            }

    except Exception as e:
        return {"error": f"Ошибка анализа: {str(e)}"}


@app.post("/analyze-smart")
def analyze_smart(symbol: str = "btcusd"):
    """
    Умный анализ: сам выбирает лучший таймфрейм и стратегию
    """
    # Импортируем нашу новую функцию
    from strategy import find_best_timeframe

    print(f"🧠 Запускаем умный анализ для {symbol}...")

    # 1. Находим лучший таймфрейм
    timeframe_result = find_best_timeframe(symbol)

    # Если произошла ошибка
    if "error" in timeframe_result:
        return {"error": "Не удалось проанализировать таймфреймы"}

    # Извлекаем лучший таймфрейм из результата
    best_tf = timeframe_result["best_timeframe"]
    best_return = timeframe_result["best_return"]

    print(f"✅ Найден лучший таймфрейм: {best_tf}")

    # 2. Получаем данные на лучшем таймфрейме
    df = get_candles(symbol, best_tf, limit=200)

    # 3. Генерируем стратегию на этих данных
    strategy_info = generate_strategy(df)

    # 4. Делаем финальный бэктест
    total_return = backtest(df)

    # 5. Возвращаем красивый результат
    result = {
        "symbol": symbol,
        "best_timeframe": best_tf,
        "best_return_%": round(best_return, 2),
        "backtest_return_%": round(total_return, 2),
        "last_price": round(df["close"].iloc[-1], 2),
        "tested_timeframes": timeframe_result["all_timeframes"],
        "message": f"Рекомендуется торговать на таймфрейме {best_tf}"
    }

    # Добавляем данные стратегии если они есть
    if isinstance(strategy_info, dict):
        result.update({
            "recommendation": strategy_info.get("recommendation", "N/A"),
            "action": strategy_info.get("action", "HOLD"),
            "strength": strategy_info.get("strength", 0),
            "signals": strategy_info.get("signals", "N/A"),
            "indicators": strategy_info.get("indicators", {})
        })
    else:
        result["strategy"] = strategy_info

    return result