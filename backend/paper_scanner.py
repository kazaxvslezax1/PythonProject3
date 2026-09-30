"""API-owned, opt-in closed-candle research worker. It has no order-placement path."""

import asyncio
import hashlib
import json
import logging
import math
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from ai_facts import check_facts
from analysis_service import analyze_market
from data import get_candles
from deepseek_analyzer import MODEL_PRICES, PROMPT_VERSION, AIResponse, AnalysisStore, DeepSeekAnalyzer
from hybrid_strategy import AIMode, HybridDecision, hybrid_signal
from market_data import INTERVALS, validate_candles
from market_snapshot import build_snapshot, live_snapshot
from paper_journal import PaperJournal, cost_settings
from paper_research import (
    OUTCOME_VERSION,
    REGIME_VERSION,
    ExperimentConfigMismatch,
    ResearchStore,
    classify_origin,
    evaluate_outcome,
    quality_bucket,
    regime_labels,
)
from signal_models import TradingSignal

LOGGER = logging.getLogger(__name__)
SYMBOLS = (
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "SHIBUSDT",
    "PEPEUSDT",
)
TIMEFRAMES = ("1h", "4h")


def utc_now():
    return datetime.now(timezone.utc)


def env_bool(name, default=False):
    raw = os.environ.get(name)
    if raw is None:
        return default
    if raw.lower() not in ("true", "false", "1", "0"):
        raise ValueError(f"{name} must be true or false")
    return raw.lower() in ("true", "1")


def next_due(now, timeframes=TIMEFRAMES, delay_seconds=15):
    """UTC exchange interval boundary + final-candle publication delay."""
    stamps = []
    for timeframe in timeframes:
        step = INTERVALS[timeframe]
        current = math.floor(now.timestamp() / step) * step + delay_seconds
        stamps.append(current if current > now.timestamp() else current + step)
    return datetime.fromtimestamp(min(stamps), timezone.utc)


@dataclass(frozen=True)
class ScannerConfig:
    enabled: bool = False
    close_delay_sec: int = 15
    live_max_age_sec: int = 300
    max_backfill_bars: int = 72
    ai_on_hold: bool = False
    ai_max_requests: int = 1
    auto_paper_entries: bool = False
    experiment_id: str = "paper-baseline-v1"
    symbols: tuple[str, ...] = SYMBOLS
    timeframes: tuple[str, ...] = TIMEFRAMES

    @classmethod
    def from_env(cls):
        config = cls(
            enabled=env_bool("PAPER_SCANNER_ENABLED"),
            close_delay_sec=int(os.environ.get("PAPER_SCANNER_CLOSE_DELAY_SEC", "15")),
            live_max_age_sec=int(os.environ.get("PAPER_SCANNER_LIVE_MAX_AGE_SEC", "300")),
            max_backfill_bars=int(os.environ.get("PAPER_SCANNER_MAX_BACKFILL_BARS", "72")),
            ai_on_hold=env_bool("PAPER_SCANNER_AI_ON_HOLD"),
            ai_max_requests=int(os.environ.get("PAPER_SCANNER_AI_MAX_REQUESTS", "1")),
            auto_paper_entries=env_bool("PAPER_SCANNER_AUTO_PAPER_ENTRIES"),
            experiment_id=os.environ.get("PAPER_EXPERIMENT_ID", "paper-baseline-v1"),
        )
        if not (0 <= config.close_delay_sec <= 300):
            raise ValueError("Invalid PAPER_SCANNER_CLOSE_DELAY_SEC")
        if not (30 <= config.live_max_age_sec <= 1800):
            raise ValueError("Invalid PAPER_SCANNER_LIVE_MAX_AGE_SEC")
        if not (1 <= config.max_backfill_bars <= 1000):
            raise ValueError("Invalid PAPER_SCANNER_MAX_BACKFILL_BARS")
        if config.ai_max_requests not in (1, 2):
            raise ValueError("PAPER_SCANNER_AI_MAX_REQUESTS must be one or two")
        if (
            not config.experiment_id
            or len(config.experiment_id) > 64
            or not all(ch.isalnum() or ch in "-_" for ch in config.experiment_id)
        ):
            raise ValueError("Invalid PAPER_EXPERIMENT_ID")
        return config


def baseline_config(config):
    root = Path(__file__).resolve().parent
    source_hash = hashlib.sha256()
    for name in ("strategy_engine.py", "technical_indicators.py", "ai_facts.py", "position_manager.py"):
        source_hash.update((root / name).read_bytes())
    return {
        "strategy_version": "technical-v1",
        "code_sha256": source_hash.hexdigest(),
        "symbols": list(config.symbols),
        "timeframes": list(config.timeframes),
        "ai_mode": os.environ.get("AI_MODE", "ADVISORY").upper(),
        "ai_model": os.environ.get("DEEPSEEK_MODEL", "deepseek-flash"),
        "prompt_version": PROMPT_VERSION,
        "regime_version": REGIME_VERSION,
        "outcome_version": OUTCOME_VERSION,
        "cost_model": cost_settings(),
        "portfolio_model": "existing-paper-manager-v1",
        "ai_on_hold": config.ai_on_hold,
        "ai_max_requests": config.ai_max_requests,
        "close_delay_sec": config.close_delay_sec,
        "live_max_age_sec": config.live_max_age_sec,
    }


def safe_scanner_reason(exc):
    if isinstance(exc, ExperimentConfigMismatch):
        return exc.reason_code
    if isinstance(exc, ValueError):
        known = {
            "Journal cost settings changed; use a new PAPER_JOURNAL_PATH": "JOURNAL_COST_MISMATCH",
            "Backfill exceeds configured history window": "BACKFILL_WINDOW_EXCEEDED",
        }
        return known.get(str(exc), "INVALID_SCANNER_CONFIGURATION")
    return "SCANNER_STARTUP_FAILED"


def unavailable_decision(signal, reason):
    return HybridDecision(
        technical=signal,
        final=signal,
        mode=AIMode.ADVISORY,
        ai=AIResponse(
            status="AI_UNAVAILABLE",
            model=os.environ.get("DEEPSEEK_MODEL", "deepseek-flash"),
            reason=reason,
        ),
    )


class ResearchScanner:
    def __init__(self, journal=None, config=None, loader=None, analyzer=None, clock=None):
        self.journal = journal or PaperJournal()
        self.store = ResearchStore(self.journal)
        self.config = config or ScannerConfig.from_env()
        self.loader = loader or get_candles
        self.clock = clock or utc_now
        self.analyzer = analyzer
        self.running = False
        self.healthy = True
        self.experiment_start = None
        self.last_error = None
        self._next_run = None
        self._checked_buckets = {}

    def initialize(self):
        if self.experiment_start is None:
            self.experiment_start = datetime.fromisoformat(
                self.store.register_experiment(
                    self.config.experiment_id, baseline_config(self.config), self.clock()
                )
            )
            self.store.record_operation_mode(self.config.experiment_id, self.config.auto_paper_entries)

    def _analyzer(self):
        if self.analyzer is None:
            # One HTTP attempt per claim; the shared provider cache/budget remains authoritative.
            self.analyzer = DeepSeekAnalyzer(attempts=1)
        return self.analyzer

    def _snapshot(self, analysis):
        if not os.environ.get("DEEPSEEK_API_KEY"):
            return build_snapshot(
                analysis["frame"], analysis["symbol"], analysis["timeframe"], analysis["as_of"]
            )

        def loader(symbol, timeframe, **kwargs):
            return (
                analysis["frame"]
                if timeframe == analysis["timeframe"]
                else self.loader(symbol, timeframe, **kwargs)
            )

        return live_snapshot(analysis["symbol"], analysis["timeframe"], analysis["as_of"], loader=loader)

    async def _review(self, signal_id, analysis, origin):
        signal = analysis["technical_signal"]
        existing = self.store.ai_request(signal_id)
        if existing and existing["state"] == "SKIPPED":
            return
        if existing and existing["state"] == "DONE":
            retryable = existing["reason"] in ("API_TIMEOUT_OR_TRANSPORT", "API_RETRY_EXHAUSTED")
            age = (self.clock() - signal.timestamp).total_seconds()
            if (
                not retryable
                or existing["attempts"] >= self.config.ai_max_requests
                or age > self.config.live_max_age_sec
            ):
                return
        if origin != "LIVE":
            self.store.skip_ai(signal_id, "BACKFILL_NO_HISTORICAL_AI")
            return
        if signal.plan is None and not self.config.ai_on_hold:
            self.store.skip_ai(signal_id, "HOLD_COST_POLICY")
            return
        if os.environ.get("AI_MODE", "ADVISORY").upper() != "ADVISORY":
            self.store.skip_ai(signal_id, "AI_MODE_NOT_ADVISORY")
            return
        if not os.environ.get("DEEPSEEK_API_KEY") and self.analyzer is None:
            self.store.skip_ai(signal_id, "MISSING_API_KEY")
            self.journal.record_ai(signal_id, unavailable_decision(signal, "MISSING_API_KEY"))
            return
        try:
            snapshot = await asyncio.to_thread(self._snapshot, analysis)
        except Exception as exc:
            self.store.error("SNAPSHOT", exc, signal.symbol, signal.timeframe)
            reason = (
                "UNKNOWN_AFTER_CRASH"
                if existing and existing["state"] == "STARTED"
                else "SNAPSHOT_UNAVAILABLE"
            )
            self.journal.record_ai(signal_id, unavailable_decision(signal, reason))
            if reason == "UNKNOWN_AFTER_CRASH":
                self.store.complete_ai(
                    signal_id,
                    AIResponse(
                        status="AI_UNAVAILABLE",
                        model=os.environ.get("DEEPSEEK_MODEL", "deepseek-flash"),
                        reason=reason,
                    ),
                    0,
                )
            else:
                self.store.skip_ai(signal_id, reason)
            return
        analyzer = self._analyzer()
        if existing and existing["state"] == "STARTED":
            # After a crash the provider may have billed the call. Replay cache only.
            cached = analyzer.store.get(analyzer.identity(snapshot))
            if cached and cached.status == "OK" and not check_facts(cached.result.facts, snapshot):
                cached.result.validate_references(snapshot)
                recovered = HybridDecision(technical=signal, final=signal, mode=AIMode.ADVISORY, ai=cached)
                self.journal.record_ai(signal_id, recovered)
                self.store.complete_ai(signal_id, cached, 0, analyzer.store.usage(cached.request_hash))
            else:
                row = self.store.observation(signal_id)
                if row["ai_status"] is None:
                    self.journal.record_ai(signal_id, unavailable_decision(signal, "UNKNOWN_AFTER_CRASH"))
                self.store.complete_ai(
                    signal_id,
                    AIResponse(status="AI_UNAVAILABLE", model=analyzer.model, reason="UNKNOWN_AFTER_CRASH"),
                    0,
                )
            return
        while self.store.claim_ai(signal_id, analyzer.model, PROMPT_VERSION, self.config.ai_max_requests):
            started = time.monotonic()
            try:
                decision = await hybrid_signal(snapshot, analyzer, AIMode.ADVISORY)
            except Exception as exc:
                self.store.error("AI", exc, signal.symbol, signal.timeframe)
                decision = unavailable_decision(signal, "AI_WORKER_ERROR")
            elapsed = (time.monotonic() - started) * 1000
            self.journal.record_ai(signal_id, decision)
            usage = analyzer.store.usage(decision.ai.request_hash) if decision.ai.request_hash else None
            estimate = None
            if usage and decision.ai.status == "OK" and not decision.ai.cached:
                input_rate, output_rate = MODEL_PRICES[analyzer.model]
                estimate = (
                    usage.get("prompt_tokens", 0) * input_rate
                    + usage.get("completion_tokens", 0) * output_rate
                ) / 1e6
            self.store.complete_ai(signal_id, decision.ai, elapsed, usage, estimate)
            if decision.ai.reason not in ("API_TIMEOUT_OR_TRANSPORT", "API_RETRY_EXHAUSTED"):
                break
            if (self.clock() - signal.timestamp).total_seconds() > self.config.live_max_age_sec:
                break

    async def _recover_ai(self, now):
        for row in self.store.pending_ai(self.config.experiment_id):
            try:
                observed = self.store.observation(row["id"])
                if row["state"] == "STARTED" and observed["ai_status"] is not None:
                    self.store.complete_ai(
                        row["id"],
                        AIResponse(
                            status=observed["ai_status"],
                            model=observed["ai_model"] or "deepseek-flash",
                            reason=observed["ai_reason"],
                        ),
                        0,
                    )
                    continue
                close = datetime.fromisoformat(row["candle_close"])
                if row["state"] is None and (now - close).total_seconds() > self.config.live_max_age_sec:
                    self.store.skip_ai(row["id"], "RECOVERY_NOT_LIVE")
                    continue
                market = json.loads(row["market_json"])
                signal = TradingSignal.model_validate_json(row["signal_json"])
                analysis = {
                    "technical_signal": signal,
                    "frame": pd.DataFrame(market["candles"]),
                    "indicators": market["indicators"],
                    "symbol": signal.symbol,
                    "timeframe": signal.timeframe,
                    "as_of": close + timedelta(milliseconds=1),
                }
                await self._review(row["id"], analysis, row["origin"])
            except Exception as exc:
                self.store.error("RECOVERY", exc, row["symbol"], row["timeframe"])
                LOGGER.warning("PAPER AI recovery failed type=%s", type(exc).__name__)

    def _record_execution_metadata(self, signal_id, signal, origin, auto_paper_entries=None):
        if auto_paper_entries is None:
            auto_paper_entries = self.config.auto_paper_entries
        self.store.record_execution(
            signal_id,
            "NOT_ELIGIBLE" if signal.plan is None else "NOT_ATTEMPTED",
            "TECHNICAL_HOLD"
            if signal.plan is None
            else "PAPER_BRIDGE_PENDING"
            if auto_paper_entries and origin == "LIVE"
            else "RESEARCH_ONLY_NO_AUTOMATED_ENTRY",
        )

    def _recover_execution_metadata(self):
        for row in self.store.missing_execution_metadata(self.config.experiment_id):
            signal = TradingSignal.model_validate_json(row["signal_json"])
            mode_at_observation = self.store.operation_mode_at(
                self.config.experiment_id, row["observed_at"]
            )
            self._record_execution_metadata(
                row["id"], signal, row["origin"], auto_paper_entries=bool(mode_at_observation)
            )

    def _outcomes(self, symbol, timeframe, frame):
        for row in self.store.outcomes_due(self.config.experiment_id, symbol, timeframe):
            signal = TradingSignal.model_validate_json(row["signal_json"])
            if signal.plan is None:
                continue
            future = frame.loc[frame.close_time > signal.timestamp]
            if future.empty:
                continue
            # A truncated history cannot establish a first touch without bias.
            if future.time.iloc[0].to_pydatetime() != signal.timestamp + timedelta(milliseconds=1):
                self.store.error(
                    "OUTCOME_HISTORY_GAP", ValueError("missing early future bars"), symbol, timeframe
                )
                continue
            result = evaluate_outcome(signal, list(future.itertuples(index=False)))
            self.store.save_outcome(row["id"], future.close_time.iloc[-1].to_pydatetime(), result)

    async def _scan_pair(self, symbol, timeframe, now):
        last = self.store.latest_candle(self.config.experiment_id, symbol, timeframe)
        cutoff = datetime.fromisoformat(last) if last else self.experiment_start
        interval = INTERVALS[timeframe]
        published_boundary = math.floor((now.timestamp() - self.config.close_delay_sec) / interval) * interval
        expected_close = datetime.fromtimestamp(published_boundary, timezone.utc) - timedelta(milliseconds=1)
        missing = max(1, math.ceil((expected_close - cutoff).total_seconds() / interval))
        if missing > self.config.max_backfill_bars:
            raise ValueError("Backfill exceeds configured history window")
        limit = 120 + min(missing + 2, self.config.max_backfill_bars)
        frame = await asyncio.to_thread(self.loader, symbol, timeframe, limit=limit, as_of=now)
        frame = validate_candles(frame, timeframe, now, min_bars=120, require_fresh=False)
        if frame.close_time.iloc[-1].to_pydatetime() < expected_close:
            raise ValueError("Expected closed Binance candle not published yet")
        candidates = [i for i in range(119, len(frame)) if frame.close_time.iloc[i].to_pydatetime() > cutoff]
        latest = None
        for index in candidates:
            close = frame.close_time.iloc[index].to_pydatetime()
            history = frame.iloc[: index + 1].tail(120).reset_index(drop=True)
            analysis = await asyncio.to_thread(
                analyze_market,
                symbol,
                timeframe,
                close + timedelta(milliseconds=1),
                lambda *_, **__: history,
            )
            origin = classify_origin(close, now, self.config.live_max_age_sec)
            signal_id = self.journal.record_signal(
                analysis,
                origin="SCANNER_" + origin,
                research={
                    "experiment_id": self.config.experiment_id,
                    "origin": origin,
                    "data_source": "BINANCE_SPOT_KLINES",
                    "regime": regime_labels(analysis),
                    "quality_bucket": quality_bucket(analysis["technical_signal"].quality),
                },
            )
            recorded = self.store.observation(signal_id)
            actual_origin = recorded["origin"]
            signal = analysis["technical_signal"]
            await self._review(signal_id, analysis, actual_origin)
            self._record_execution_metadata(signal_id, signal, actual_origin)
            latest = close
        self._outcomes(symbol, timeframe, frame)
        return latest

    async def scan_once(self, now=None):
        self.initialize()
        now = now or self.clock()
        await self._recover_ai(now)
        self._recover_execution_metadata()
        latest = None
        errors = 0
        for timeframe in self.config.timeframes:
            bucket = math.floor((now.timestamp() - self.config.close_delay_sec) / INTERVALS[timeframe])
            if self._checked_buckets.get(timeframe) == bucket:
                continue
            timeframe_errors = 0
            for symbol in self.config.symbols:
                try:
                    observed = await self._scan_pair(symbol, timeframe, now)
                    if observed is not None and (latest is None or observed > latest):
                        latest = observed
                except Exception as exc:
                    errors += 1
                    timeframe_errors += 1
                    self.store.error("MARKET_OR_JOURNAL", exc, symbol, timeframe)
                    LOGGER.warning(
                        "PAPER scanner pair failed symbol=%s timeframe=%s type=%s",
                        symbol,
                        timeframe,
                        type(exc).__name__,
                    )
            if not timeframe_errors:
                self._checked_buckets[timeframe] = bucket
        self.healthy = errors == 0
        self._next_run = (
            now + timedelta(seconds=60)
            if errors
            else next_due(now, self.config.timeframes, self.config.close_delay_sec)
        )
        self.store.heartbeat(
            self.config.experiment_id,
            success=not errors,
            candle_close=latest,
            next_scan=self._next_run,
            healthy=not errors,
        )

    async def run(self):
        self.running = True
        try:
            while True:
                now = self.clock()
                if self._next_run is None or now >= self._next_run:
                    await self.scan_once(now)
                else:
                    self.store.heartbeat(
                        self.config.experiment_id, next_scan=self._next_run, healthy=self.healthy
                    )
                wait = max(1.0, min(60.0, (self._next_run - self.clock()).total_seconds()))
                await asyncio.sleep(wait)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.healthy = False
            self.last_error = safe_scanner_reason(exc)
            LOGGER.error("PAPER scanner stopped type=%s reason=%s", type(exc).__name__, self.last_error)
            try:
                self.store.error("WORKER", exc)
                self.store.heartbeat(self.config.experiment_id, healthy=False)
            except Exception:
                LOGGER.error("PAPER scanner storage unavailable type=%s", type(exc).__name__)
        finally:
            self.running = False

    def status(self):
        result = {
            "enabled": self.config.enabled,
            "running": self.running,
            "experiment_id": self.config.experiment_id,
            "strategy_version": "technical-v1",
            "symbols": list(self.config.symbols),
            "timeframes": list(self.config.timeframes),
            "journal_path": str(self.journal.path),
        }
        if self.experiment_start is not None:
            result.update(self.store.status(self.config.experiment_id))
        else:
            result.update({"healthy": False, "error": self.last_error or "NOT_STARTED"})
        result["auto_paper_entries"] = self.config.auto_paper_entries
        if self.last_error:
            result["error"] = self.last_error
        if self.analyzer is not None:
            spent = self.analyzer.store.spent(self.clock().date().isoformat())
            result["budget_used_usd"] = spent
            result["budget_remaining_usd"] = max(0, self.analyzer.daily_budget - spent)
        else:
            store = AnalysisStore(Path(__file__).resolve().parent.parent / "runtime" / "ai.sqlite3")
            spent = store.spent(self.clock().date().isoformat())
            limit = float(os.environ.get("DEEPSEEK_DAILY_BUDGET_USD", "1.0"))
            result["budget_used_usd"] = spent
            result["budget_remaining_usd"] = max(0, limit - spent)
        return result
