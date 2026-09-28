from analysis_service import analyze_market
from fastapi import FastAPI
from strategy import find_best_timeframe

app = FastAPI(title="Trading analysis (paper only)")


@app.get("/")
def home():
    return {"status": "ok", "execution": "paper-only"}


@app.post("/analyze")
def analyze(symbol: str = "BTCUSDT", timeframe: str = "1h"):
    try:
        data = analyze_market(symbol, timeframe)
        from ai_runtime import review_analysis
        from strategy_engine import legacy_result

        review = review_analysis(data)
        if review is not None:
            data.update(legacy_result(review.final, data["frame"]))
            data["deepseek"] = review.ai.model_dump(mode="json") if review.ai else None
        return {
            k: v for k, v in data.items() if k not in ("frame", "technical_signal", "as_of", "ai_snapshot")
        }
    except Exception as exc:
        return {"error": type(exc).__name__, "action": "HOLD", "status": "DATA_UNAVAILABLE"}


@app.post("/analyze-smart")
def analyze_smart(symbol: str = "BTCUSDT"):
    return analyze(symbol, find_best_timeframe(symbol)["best_timeframe"])


@app.get("/ai/status")
def ai_status():
    from ai_runtime import api_status

    return api_status()


@app.post("/ai/review")
def ai_review(symbol: str = "BTCUSDT", timeframe: str = "1h", advisory: bool = False):
    from ai_runtime import review_analysis
    from hybrid_strategy import AIMode, HybridDecision
    from market_snapshot import build_snapshot
    from telegram_ai import format_decision

    try:
        data = analyze_market(symbol, timeframe)
        decision = review_analysis(data, mode_override="ADVISORY" if advisory else None)
        if decision is None:
            decision = HybridDecision(
                technical=data["technical_signal"], final=data["technical_signal"], mode=AIMode.OFF
            )
        snapshot = data.get("ai_snapshot") or build_snapshot(
            data["frame"], data["symbol"], data["timeframe"], data["as_of"]
        )
        return {"text": format_decision(snapshot, decision), "source": "API_SERVER"}
    except Exception:
        return {"text": "AI_UNAVAILABLE: API_ANALYSIS_ERROR", "source": "API_SERVER"}
