"""One lazily started async worker shared by synchronous Telegram threads."""

import os
import threading

from deepseek_analyzer import AIResponse
from hybrid_strategy import AIMode, HybridDecision, hold, hybrid_signal
from market_snapshot import build_snapshot, live_snapshot

_lock = threading.Lock()
_worker = None
_analyzer = None


def review_analysis(analysis):
    global _worker, _analyzer
    mode = AIMode(os.environ.get("AI_MODE", "ADVISORY").upper())
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
                model=os.environ.get("DEEPSEEK_MODEL", "deepseek-flash"),
                reason="AI_CONFIGURATION_DATA_OR_STORAGE_ERROR",
            ),
        )
