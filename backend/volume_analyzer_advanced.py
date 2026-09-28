from data import get_candles


class AdvancedVolumeAnalyzer:
    def get_volume_spike_analysis(self, symbol, timeframe="1h", period=50, as_of=None):
        try:
            df = get_candles(symbol, timeframe, max(period, 21), as_of=as_of)
            mean = float(df.volume.iloc[-21:-1].mean())
            if mean <= 0:
                raise ValueError("No volume baseline")
            ratio = float(df.volume.iloc[-1]) / mean
            change = (float(df.close.iloc[-1]) / float(df.close.iloc[-2]) - 1) * 100
            signal = (
                "PUMP_START"
                if ratio > 2 and change > 2
                else "DUMP_START"
                if ratio > 2 and change < -2
                else "ACCUMULATION"
                if ratio > 2
                else "NO_SPIKE"
            )
            return {
                "current_volume": float(df.volume.iloc[-1]),
                "average_volume": mean,
                "volume_ratio": ratio,
                "price_change_percent": change,
                "is_volume_spike": ratio > 2,
                "spike_strength": min(ratio / 2, 3),
                "signal": signal,
                "confidence": "HEURISTIC",
                "timestamp": str(df.close_time.iloc[-1]),
            }
        except Exception as exc:
            return {"error": type(exc).__name__}

    def get_real_time_volume_alert(self, symbol, timeframe="15m"):
        data = self.get_volume_spike_analysis(symbol, timeframe)
        if "error" in data or not data["is_volume_spike"]:
            return None
        return {**data, "symbol": symbol, "price_change": data["price_change_percent"]}


advanced_volume_analyzer = AdvancedVolumeAnalyzer()
