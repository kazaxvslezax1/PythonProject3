import logging

from analysis_service import analyze_market
from fastapi import FastAPI, HTTPException, Request
from strategy import find_best_timeframe

app = FastAPI(title="Trading analysis (paper only)")
logger = logging.getLogger(__name__)


@app.get("/")
def home():
    return {"status": "ok", "execution": "paper-only"}


@app.post("/analyze")
def analyze(symbol: str = "BTCUSDT", timeframe: str = "1h"):
    try:
        data = analyze_market(symbol, timeframe)
        from ai_runtime import review_analysis
        from paper_journal import PaperJournal
        from strategy_engine import legacy_result

        journal = PaperJournal()
        signal_id = journal.record_signal(data, origin="API_ANALYZE")
        review = review_analysis(data)
        if review is not None:
            journal.record_ai(signal_id, review)
            data.update(legacy_result(review.final, data["frame"]))
            data["deepseek"] = review.ai.model_dump(mode="json") if review.ai else None
            if data.get("ai_snapshot") is not None:
                from telegram_ai import format_decision

                data["ai_summary"] = format_decision(data["ai_snapshot"], review)
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


@app.get("/paper/journal/status")
def paper_journal_status(request: Request):
    """Local, read-only journal identity for comparing the API and Telegram processes."""
    from paper_journal import PaperJournal, journal_path

    if request.client is None or request.client.host not in ("127.0.0.1", "::1", "testclient"):
        raise HTTPException(status_code=403, detail="Local journal diagnostics only")
    path = journal_path()
    exists = path.is_file()
    logger.info("PAPER journal API path=%s exists=%s", path, exists)
    report = PaperJournal().report() if exists else None
    logger.info("PAPER journal API signals=%d", report["signals"] if report else 0)
    return {
        "source": "API_SERVER",
        "path": str(path),
        "exists": exists,
        "signals": report["signals"] if report else 0,
        "ai_ok": report["ai_ok"] if report else 0,
        "paired_ai_observations": report["paired_ai_observations"] if report else 0,
    }


@app.post("/ai/review")
def ai_review(symbol: str = "BTCUSDT", timeframe: str = "1h", advisory: bool = False, detailed: bool = False):
    from ai_runtime import review_analysis
    from hybrid_strategy import AIMode, HybridDecision
    from market_snapshot import build_snapshot
    from paper_journal import PaperJournal
    from telegram_ai import format_decision

    try:
        data = analyze_market(symbol, timeframe)
        journal = PaperJournal()
        signal_id = journal.record_signal(data, origin="API_REVIEW")
        logger.info(
            "PAPER technical persisted observation=%s symbol=%s timeframe=%s direction=%s",
            signal_id[:12],
            data["technical_signal"].symbol,
            data["technical_signal"].timeframe,
            data["technical_signal"].direction.value,
        )
        decision = review_analysis(data, mode_override="ADVISORY" if advisory else None)
        if decision is None:
            decision = HybridDecision(
                technical=data["technical_signal"], final=data["technical_signal"], mode=AIMode.OFF
            )
        journal.record_ai(signal_id, decision)
        if decision.ai is not None:
            logger.info(
                "PAPER AI persisted observation=%s status=%s",
                signal_id[:12],
                decision.ai.status,
            )
        snapshot = data.get("ai_snapshot") or build_snapshot(
            data["frame"], data["symbol"], data["timeframe"], data["as_of"]
        )
        return {"text": format_decision(snapshot, decision, detailed=detailed), "source": "API_SERVER"}
    except Exception as exc:
        logger.error("PAPER API review failed type=%s", type(exc).__name__)
        return {"text": "AI_UNAVAILABLE: API_ANALYSIS_ERROR", "source": "API_SERVER"}
