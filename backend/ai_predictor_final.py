"""Legacy prediction API now presents the shared technical signal, not a second strategy."""

from analysis_service import analyze_market

POPULAR_COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT"]


class AIPredictorFinal:
    def __init__(self):
        self.prediction_history = {}

    def predict_price(self, symbol, timeframe="1h"):
        try:
            data = analyze_market(symbol, timeframe)
            s = data["technical_signal"]
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "current_price": data["last_price"],
                "prediction": s.direction.value,
                "predicted_change": "Н/Д: точечный прогноз не строится",
                "confidence": f"{s.quality:.1f}/10 (эвристика)",
                "confidence_level": "ОЦЕНКА, НЕ ВЕРОЯТНОСТЬ",
                "trend": s.direction.value,
                "volatility": f"{data['indicators']['Volatility']:.2f}%",
                "rsi_signal": str(data["indicators"]["RSI"]),
                "macd_signal": str(data["indicators"]["MACD"]),
                "key_signals": s.reasons,
                "signal_strength": s.strength,
                "timestamp": s.timestamp.isoformat(),
                "message": s.direction.value,
            }
        except Exception as exc:
            return {"error": type(exc).__name__}

    def scan_top_coins(self, top_n=10):
        results = []
        for symbol in POPULAR_COINS[:top_n]:
            item = self.predict_price(symbol)
            if "error" not in item:
                item["price"] = item["current_price"]
                results.append(item)
        return sorted(results, key=lambda x: abs(x["signal_strength"]), reverse=True)

    def find_best_opportunity(self):
        results = self.scan_top_coins()
        for item in results:
            if item["prediction"] != "HOLD":
                return {
                    **item,
                    "type": "BUY" if item["prediction"] == "LONG" else "SELL",
                    "reason": "Shared technical strategy; not a calibrated forecast",
                }
        return {"error": "No confirmed trade plan"}

    def get_prediction_stats(self, symbol):
        return {"error": "Prediction accuracy requires fixed-horizon outcomes; use validated replay reports"}


ai_predictor = AIPredictorFinal()
