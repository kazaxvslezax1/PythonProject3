"""Optional Telegram-side consumer of LIVE research signals using only the PAPER manager."""

import json
import logging
import os
import threading
from datetime import datetime, timedelta, timezone

from entry_prefilter import AI_REQUEST_POLICY, PREFILTER_REJECTED
from paper_research import ResearchStore
from signal_models import TradingSignal

LOGGER = logging.getLogger(__name__)


class PaperExecutionBridge:
    def __init__(self, manager, chat_id, *, experiment_id="paper-baseline-v1", max_age_sec=300, clock=None):
        self.manager = manager
        self.chat_id = chat_id
        self.experiment_id = experiment_id
        self.max_age_sec = max_age_sec
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.store = ResearchStore(manager.journal)
        self._stop = threading.Event()
        self._thread = None
        self.healthy = True
        self.last_successful_cycle = None
        self.last_claimed_observation = None
        self.last_execution_result = None
        self.last_error = None
        self.next_poll_at = None

    def status(self):
        return {
            "enabled": True,
            "running": bool(self._thread and self._thread.is_alive()),
            "healthy": self.healthy,
            "last_successful_cycle": self.last_successful_cycle,
            "last_claimed_observation": self.last_claimed_observation,
            "last_execution_result": self.last_execution_result,
            "last_error": self.last_error,
            "next_poll_at": self.next_poll_at,
            "journal_path": str(self.manager.journal.path),
            "experiment_id": self.experiment_id,
        }

    def recover_claimed(self):
        for row in self.store.claimed_execution(self.experiment_id):
            age = (self.clock() - datetime.fromisoformat(row["recorded_at"])).total_seconds()
            if row["position_id"] or any(
                position.get("signal_id") == row["signal_id"]
                for position in [*self.manager.active_positions.values(), *self.manager.trade_history]
            ):
                self.store.complete_execution(row["signal_id"], "OPEN", "PAPER_POSITION_RESTORED")
            elif row["attempt_status"] == "REJECTED":
                self.store.complete_execution(row["signal_id"], "REJECTED", row["attempt_reason"])
            elif age >= 120:
                # A prior process may have placed a PAPER entry before dying. Never replay blindly.
                self.store.complete_execution(row["signal_id"], "UNKNOWN", "INTERRUPTED_NO_RETRY")

    def process_once(self):
        self.next_poll_at = (self.clock() + timedelta(seconds=30)).isoformat()
        experiment = self.store.experiment_config(self.experiment_id)
        if experiment is None:
            self.healthy = False
            self.last_error = "EXPERIMENT_NOT_REGISTERED"
            return 0
        if self.store.current_operation_mode(self.experiment_id) is not True:
            self.healthy = False
            self.last_error = "RESEARCH_AUTO_ENTRIES_DISABLED"
            return 0
        self.healthy = True
        self.last_error = None
        self.recover_claimed()
        processed = 0
        for row in self.store.pending_execution(self.experiment_id):
            if not self.store.claim_execution(row["id"]):
                continue
            self.last_claimed_observation = row["id"]
            processed += 1
            try:
                signal = TradingSignal.model_validate_json(row["signal_json"])
                age = (self.clock() - signal.timestamp).total_seconds()
                if age < 0 or age > self.max_age_sec:
                    self.store.complete_execution(row["id"], "NOT_ATTEMPTED", "STALE_SIGNAL_NO_ENTRY")
                    self.last_execution_result = "STALE_SIGNAL_NO_ENTRY"
                    continue
                if self.manager.journal.has_attempt(row["id"], self.chat_id):
                    self.store.complete_execution(row["id"], "UNKNOWN", "ALREADY_ATTEMPTED")
                    self.last_execution_result = "ALREADY_ATTEMPTED"
                    continue
                market = json.loads(row["market_json"])
                volume_ratio = float(market["indicators"]["Volume_Ratio"])
                allowed, reason = self.manager.should_open_trade(
                    self.chat_id, signal.symbol, signal.quality, volume_ratio
                )
                if not allowed:
                    if row["ai_request_policy"] == AI_REQUEST_POLICY and reason in (
                        "Quality or volume filter rejected",
                        "Invalid quality or volume",
                    ):
                        ai_request = self.store.ai_request(row["id"])
                        if ai_request and ai_request["reason"] != PREFILTER_REJECTED:
                            LOGGER.warning(
                                "PAPER prefilter disagreement symbol=%s timeframe=%s",
                                signal.symbol,
                                signal.timeframe,
                            )
                    self.manager.record_skipped_signal(
                        self.chat_id,
                        reason,
                        signal_id=row["id"],
                        symbol=signal.symbol,
                        execution_source="PAPER_RESEARCH_BRIDGE",
                        experiment_id=self.experiment_id,
                    )
                    self.store.complete_execution(row["id"], "REJECTED", reason)
                    self.last_execution_result = "REJECTED: " + reason
                    continue
                plan = signal.plan
                position_id = self.manager.create_auto_trade(
                    self.chat_id,
                    signal.symbol,
                    plan.entry,
                    plan.stop_loss,
                    plan.take_profits,
                    signal.direction.value,
                    signal.quality,
                    volume_ratio,
                    signal_id=row["id"],
                    timeframe=signal.timeframe,
                    execution_source="PAPER_RESEARCH_BRIDGE",
                    experiment_id=self.experiment_id,
                    strategy_version=signal.strategy_version,
                )
                if position_id:
                    self.store.complete_execution(row["id"], "OPEN", "PAPER_MANAGER_OPENED")
                    self.last_execution_result = "OPEN: PAPER_MANAGER_OPENED"
                else:
                    attempt = self.manager.journal.has_attempt(row["id"], self.chat_id)
                    if attempt and attempt["status"] == "REJECTED":
                        self.store.complete_execution(row["id"], "REJECTED", "PAPER_MANAGER_REJECTED")
                        self.last_execution_result = "REJECTED: PAPER_MANAGER_REJECTED"
                    else:
                        self.store.complete_execution(row["id"], "UNKNOWN", "PAPER_RESULT_UNKNOWN")
                        self.last_execution_result = "UNKNOWN: PAPER_RESULT_UNKNOWN"
            except Exception as exc:
                LOGGER.error("PAPER bridge failed type=%s", type(exc).__name__)
                self.healthy = False
                self.last_error = type(exc).__name__
                self.store.error("PAPER_EXECUTION", exc)
                # Preserve CLAIMED. Recovery inspects the ledger and never blindly retries.
        if self.healthy:
            self.last_successful_cycle = self.clock().isoformat()
        return processed

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        def work():
            try:
                while not self._stop.is_set():
                    try:
                        self.process_once()
                    except Exception as exc:
                        LOGGER.error("PAPER bridge cycle failed type=%s", type(exc).__name__)
                        self.healthy = False
                        self.last_error = type(exc).__name__
                        self.store.error("PAPER_BRIDGE", exc)
                    self._stop.wait(30)
            finally:
                if not self._stop.is_set():
                    self.healthy = False
                    self.last_error = "WORKER_TERMINATED"
                    LOGGER.error("PAPER bridge fatal error: worker terminated unexpectedly")

        self._thread = threading.Thread(target=work, daemon=True, name="paper-execution-bridge")
        self._thread.start()
        LOGGER.info("PAPER bridge started experiment=%s", self.experiment_id)

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        LOGGER.info("PAPER bridge stopped experiment=%s", self.experiment_id)


def bridge_from_env(manager, allowed_chat_ids):
    if os.environ.get("PAPER_SCANNER_AUTO_PAPER_ENTRIES", "false").lower() not in ("true", "1"):
        return None
    raw = os.environ.get("PAPER_SCANNER_CHAT_ID", "")
    if not raw.lstrip("-").isdigit() or int(raw) not in allowed_chat_ids:
        raise ValueError("PAPER_SCANNER_CHAT_ID must be an allowed Telegram chat")
    max_age = int(os.environ.get("PAPER_SCANNER_LIVE_MAX_AGE_SEC", "300"))
    if not 30 <= max_age <= 1800:
        raise ValueError("Invalid PAPER_SCANNER_LIVE_MAX_AGE_SEC")
    return PaperExecutionBridge(
        manager,
        int(raw),
        experiment_id=os.environ.get("PAPER_EXPERIMENT_ID", "paper-baseline-v1"),
        max_age_sec=max_age,
    )
