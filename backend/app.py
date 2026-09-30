import asyncio
import logging
from contextlib import asynccontextmanager

from analysis_service import analyze_market
from fastapi import FastAPI, HTTPException, Request
from strategy import find_best_timeframe

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application):
    task = None
    application.state.paper_scanner = None
    application.state.paper_scanner_error = None
    try:
        from paper_scanner import ResearchScanner, ScannerConfig, safe_scanner_reason

        config = ScannerConfig.from_env()
        if config.enabled:
            scanner = ResearchScanner(config=config)
            application.state.paper_scanner = scanner
            task = asyncio.create_task(scanner.run(), name="paper-research-scanner")
            logger.info("PAPER research scanner started experiment=%s", config.experiment_id)
    except Exception as exc:
        reason = safe_scanner_reason(exc) if "safe_scanner_reason" in locals() else "SCANNER_STARTUP_FAILED"
        application.state.paper_scanner_error = reason
        logger.error(
            "PAPER research scanner initialization failed type=%s reason=%s",
            type(exc).__name__,
            reason,
        )
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(title="Trading analysis (paper only)", lifespan=lifespan)


def local_diagnostics(request):
    if request.client is None or request.client.host not in ("127.0.0.1", "::1", "testclient"):
        raise HTTPException(status_code=403, detail="Local diagnostics only")


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

    local_diagnostics(request)
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


@app.get("/paper/scanner/status")
def paper_scanner_status(request: Request):
    from paper_journal import journal_path
    from paper_scanner import ScannerConfig

    local_diagnostics(request)
    scanner = getattr(app.state, "paper_scanner", None)
    if scanner is not None:
        return scanner.status()
    try:
        config = ScannerConfig.from_env()
        enabled, experiment_id = config.enabled, config.experiment_id
        auto_paper_entries = config.auto_paper_entries
        symbols, timeframes = list(config.symbols), list(config.timeframes)
    except Exception:
        enabled, experiment_id = False, None
        auto_paper_entries = False
        symbols, timeframes = [], []
    return {
        "enabled": enabled,
        "running": False,
        "healthy": False,
        "auto_paper_entries": auto_paper_entries,
        "experiment_id": experiment_id,
        "strategy_version": "technical-v1",
        "symbols": symbols,
        "timeframes": timeframes,
        "journal_path": str(journal_path()),
        "error": getattr(app.state, "paper_scanner_error", None) or "NOT_STARTED",
    }


@app.get("/paper/scanner/errors")
def paper_scanner_errors(request: Request):
    from paper_journal import PaperJournal
    from paper_research import ResearchStore

    local_diagnostics(request)
    return {"errors": ResearchStore(PaperJournal()).errors()}


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
