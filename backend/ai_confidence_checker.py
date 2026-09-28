"""Legacy heuristic quality adapter. DeepSeek lives in deepseek_analyzer.py."""

import math
from datetime import datetime, timedelta, timezone


class AIConfidenceChecker:
    def __init__(self):
        self.analysis_cache = {}
        self.cache_duration = timedelta(minutes=5)
        self._sent = {}

    def get_coin_type(self, symbol):
        return "BLUECHIP" if symbol in ("BTCUSDT", "ETHUSDT", "BNBUSDT") else "MIDCAP"

    def get_coin_parameters(self, coin_type):
        return {
            "volume_weight": 0.5,
            "confluence_weight": 0.5,
            "min_volume": 1.0,
            "min_ai_buy": 7.0,
            "description": "Heuristic quality",
        }

    def analyze_signal_quality(self, symbol, signal_data):
        try:
            volume = float(signal_data["volume_ratio"])
            agreement = float(signal_data["confluence"])
            if (
                not math.isfinite(volume)
                or not math.isfinite(agreement)
                or volume < 0
                or abs(agreement) > 100
            ):
                raise ValueError("Invalid metrics")
            action = signal_data.get("direction", signal_data.get("action"))
            if action in ("SHORT", "SELL"):
                agreement = -agreement
            elif action not in ("LONG", "BUY"):
                agreement = abs(agreement)
            score = round((min(volume / 2, 1) * 10 + max(0, agreement) / 10) / 2, 1)
            return {
                "ai_confidence_score": score,
                "ai_confidence": score,
                "ai_confidence_real": score,
                "recommendation": "QUALITY_CONFIRMED" if score >= 7 else "INSUFFICIENT_CONFIRMATION",
                "direction": action or "HOLD",
                "color": "🟢" if score >= 7 else "🟡",
                "passed_checks": int(volume >= 1) + int(agreement >= 60),
                "total_checks": 2,
                "coin_type": self.get_coin_type(symbol),
                "status": "OK",
                "metrics": {"volume_ratio": volume, "aligned_confluence": agreement},
            }
        except (KeyError, ValueError, TypeError):
            return {
                "ai_confidence_score": 0.0,
                "ai_confidence": 0.0,
                "ai_confidence_real": 0.0,
                "recommendation": "DATA_UNAVAILABLE",
                "direction": "HOLD",
                "color": "🔴",
                "passed_checks": 0,
                "total_checks": 2,
                "status": "DATA_UNAVAILABLE",
                "metrics": {},
            }

    get_combined_confidence = analyze_signal_quality

    def should_send_alert(self, symbol, action, strength):
        return action in ("BUY", "SELL", "LONG", "SHORT") and abs(strength) >= 3

    def prioritize_alerts(self, alerts):
        result = []
        for alert in alerts:
            item = dict(alert)
            item["ai_confidence"] = min(
                10, abs(item.get("strength", 0)) + abs(item.get("confluence_score", 0)) / 25
            )
            result.append(item)
        return sorted(result, key=lambda x: x["ai_confidence"], reverse=True)

    def filter_duplicate_alerts(self, alerts):
        now = datetime.now(timezone.utc)
        self._sent = {k: v for k, v in self._sent.items() if now - v < timedelta(hours=1)}
        result = []
        for alert in alerts:
            key = (alert["symbol"], alert.get("signal_type"))
            if key not in self._sent and alert.get("ai_confidence", 0) >= 6:
                result.append(alert)
                self._sent[key] = now
        return result

    def get_global_market_sentiment(self):
        return None, "Sentiment unavailable; not inferred"


ai_checker = AIConfidenceChecker()
smart_alerts_ai = ai_checker
