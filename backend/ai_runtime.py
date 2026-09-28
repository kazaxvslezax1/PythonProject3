"""One lazily started async worker shared by synchronous Telegram threads."""

import os
import threading

from deepseek_analyzer import MODEL_PRICES, AIResponse
from hybrid_strategy import AIMode, HybridDecision, hold, hybrid_signal
from market_snapshot import build_snapshot, live_snapshot

_lock = threading.Lock()
_worker = None
_analyzer = None


def review_analysis(analysis, mode_override=None):
    global _worker, _analyzer
    mode = AIMode(mode_override or os.environ.get("AI_MODE", "ADVISORY").upper())
    if mode == AIMode.OFF:
        return None
    try:
        snapshot = build_snapshot(
            analysis["frame"], analysis["symbol"], analysis["timeframe"], analysis["as_of"]
        )
        if os.environ.get("DEEPSEEK_API_KEY"):
            from data import get_candles

            def loader(symbol, timeframe, **kwargs):
                return (
                    analysis["frame"]
                    if timeframe == analysis["timeframe"]
                    else get_candles(symbol, timeframe, **kwargs)
                )

            snapshot = live_snapshot(
                analysis["symbol"], analysis["timeframe"], analysis["as_of"], loader=loader
            )
        analysis["ai_snapshot"] = snapshot
        with _lock:
            if _worker is None:
                from deepseek_analyzer import DeepSeekAnalyzer
                from telegram_ai import AsyncWorker

                _analyzer = DeepSeekAnalyzer()
                _worker = AsyncWorker()
        return _worker.run(hybrid_signal(snapshot, _analyzer, mode))
    except Exception:
        technical = analysis["technical_signal"]
        veto = "AI_UNAVAILABLE" if mode == AIMode.FILTER else None
        return HybridDecision(
            technical=technical,
            final=hold(technical, veto) if veto else technical,
            mode=mode,
            veto_reason=veto,
            ai=AIResponse(
                status="AI_UNAVAILABLE",
                model=os.environ.get("DEEPSEEK_MODEL", "deepseek-flash")
                if os.environ.get("DEEPSEEK_MODEL", "deepseek-flash") in MODEL_PRICES
                else "INVALID_CONFIGURATION",
                reason="AI_CONFIGURATION_DATA_OR_STORAGE_ERROR",
            ),
        )


def api_status():
    """Process-local snapshot only: no paid call and no provider connectivity claim."""
    with _lock:
        analyzer = _analyzer
    model = analyzer.model if analyzer is not None else os.environ.get("DEEPSEEK_MODEL", "deepseek-flash")
    mode = os.environ.get("AI_MODE", "ADVISORY").upper()
    return {
        "source": "API_SERVER",
        "mode": mode if mode in ("OFF", "ADVISORY", "FILTER") else "INVALID_CONFIGURATION",
        "configured": bool(analyzer.key)
        if analyzer is not None
        else bool(os.environ.get("DEEPSEEK_API_KEY")),
        "model": model if model in MODEL_PRICES else "INVALID_CONFIGURATION",
        "last_status": analyzer.last_status if analyzer is not None else "NOT_CHECKED",
        "connectivity": "NOT_PROBED_STATUS_ONLY",
    }
