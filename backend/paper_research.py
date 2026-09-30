"""Versioned, prospective research metadata alongside the authoritative PAPER journal."""

import json
from datetime import datetime, timezone

from paper_journal import as_utc, compact, now_utc, uid

REGIME_VERSION = "regime-v1"
OUTCOME_VERSION = "ohlcv-first-touch-v1"


class ExperimentConfigMismatch(ValueError):
    """An immutable research parameter changed for an existing experiment."""

    reason_code = "EXPERIMENT_CONFIG_MISMATCH"


def quality_bucket(score):
    if score < 4:
        return "0-<4"
    if score < 7:
        return "4-<7"
    return "7-10"


def regime_labels(analysis):
    """Descriptive labels using only indicators available at the signal candle."""
    values = analysis["indicators"]
    close = float(analysis["frame"].close.iloc[-1])
    atr_fraction = values["ATR"] / close
    return {
        "version": REGIME_VERSION,
        "trend": "TRENDING" if values["ADX"] >= 25 else "NON_TRENDING",
        "volatility": "HIGH" if atr_fraction >= 0.03 else "MEDIUM" if atr_fraction >= 0.01 else "LOW",
        "volume": "ABOVE_AVERAGE" if values["Volume_Ratio"] >= 1 else "BELOW_AVERAGE",
        "structure": "BULLISH"
        if values["SMA_20"] > values["SMA_50"]
        else "BEARISH"
        if values["SMA_20"] < values["SMA_50"]
        else "NEUTRAL",
    }


def classify_origin(candle_close, observed_at, live_max_age_sec):
    age = (observed_at - candle_close).total_seconds()
    return "LIVE" if 0 <= age <= live_max_age_sec else "BACKFILL_TECHNICAL"


def evaluate_outcome(signal, future_bars, horizon=24):
    """First-touch labels; ambiguous OHLC bars never receive an invented fill order."""
    if signal.plan is None:
        return None
    side = 1 if signal.direction.value == "LONG" else -1
    entry = signal.plan.entry
    stop = signal.plan.stop_loss
    targets = signal.plan.take_profits
    reached = [False, False, False]
    mfe = mae = 0.0
    status = "PENDING"
    bars_to_outcome = None
    considered = future_bars[:horizon]
    for number, bar in enumerate(considered, 1):
        high, low = float(bar.high), float(bar.low)
        favorable = (high - entry) / entry * 100 if side == 1 else (entry - low) / entry * 100
        adverse = (low - entry) / entry * 100 if side == 1 else (entry - high) / entry * 100
        mfe = max(mfe, favorable)
        mae = min(mae, adverse)
        stop_hit = low <= stop if side == 1 else high >= stop
        target_hits = [high >= level if side == 1 else low <= level for level in targets]
        if stop_hit and any(target_hits):
            status, bars_to_outcome = "AMBIGUOUS_INTRABAR", number
            break
        reached = [old or hit for old, hit in zip(reached, target_hits)]
        if stop_hit:
            status, bars_to_outcome = "SL", number
            break
        if reached[-1]:
            status, bars_to_outcome = "TP3", number
            break
    if status == "PENDING" and len(considered) >= horizon:
        status, bars_to_outcome = "NEITHER", horizon
    return {
        "status": status,
        "reached_sl": status == "SL",
        "reached_tp1": reached[0],
        "reached_tp2": reached[1],
        "reached_tp3": reached[2],
        "mfe_pct": mfe,
        "mae_pct": mae,
        "bars": len(considered) if status == "PENDING" else bars_to_outcome,
        "bars_to_outcome": bars_to_outcome,
        "version": OUTCOME_VERSION,
    }


class ResearchStore:
    def __init__(self, journal):
        self.journal = journal

    def register_experiment(self, experiment_id, config, started_at=None):
        encoded = compact(config)
        with self.journal.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT config_json, started_at FROM research_experiments WHERE id=?", (experiment_id,)
            ).fetchone()
            if row is None:
                started = as_utc(started_at) if started_at is not None else now_utc()
                db.execute(
                    "INSERT INTO research_experiments VALUES (?,?,?)", (experiment_id, encoded, started)
                )
                db.execute(
                    "INSERT OR IGNORE INTO scanner_state(experiment_id, healthy) VALUES (?,1)",
                    (experiment_id,),
                )
                return started
            stored = json.loads(row["config_json"])
            # v2 journals froze this operational switch with research parameters.
            # Preserve the stored JSON while allowing a recorded PAPER entry-mode change.
            stored.pop("auto_paper_entries", None)
            comparable = dict(config)
            comparable.pop("auto_paper_entries", None)
            if stored != comparable:
                raise ExperimentConfigMismatch(
                    "Experiment configuration changed; choose a new PAPER_EXPERIMENT_ID"
                )
            return row["started_at"]

    def record_operation_mode(self, experiment_id, auto_paper_entries):
        """Audit an opt-in execution switch without rewriting the frozen experiment."""
        with self.journal.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            experiment = db.execute(
                "SELECT config_json FROM research_experiments WHERE id=?", (experiment_id,)
            ).fetchone()
            if experiment is None:
                raise ValueError("Research experiment is not registered")
            previous = db.execute(
                "SELECT payload_json FROM journal_events WHERE kind='RESEARCH_OPERATION_MODE' "
                "AND signal_id=? ORDER BY recorded_at DESC, rowid DESC LIMIT 1",
                (experiment_id,),
            ).fetchone()
            old_mode = (
                json.loads(previous["payload_json"])["auto_paper_entries"]
                if previous
                else json.loads(experiment["config_json"]).get("auto_paper_entries")
            )
            if old_mode == auto_paper_entries:
                return False
            when = now_utc()
            self.journal.event(
                db,
                uid(experiment_id, "RESEARCH_OPERATION_MODE", when, auto_paper_entries),
                "RESEARCH_OPERATION_MODE",
                when,
                signal_id=experiment_id,
                payload={"experiment_id": experiment_id, "auto_paper_entries": auto_paper_entries},
            )
            return True

    def current_operation_mode(self, experiment_id):
        with self.journal.connect() as db:
            previous = db.execute(
                "SELECT payload_json FROM journal_events WHERE kind='RESEARCH_OPERATION_MODE' "
                "AND signal_id=? ORDER BY recorded_at DESC, rowid DESC LIMIT 1",
                (experiment_id,),
            ).fetchone()
            if previous:
                return json.loads(previous["payload_json"])["auto_paper_entries"]
            experiment = db.execute(
                "SELECT config_json FROM research_experiments WHERE id=?", (experiment_id,)
            ).fetchone()
        return json.loads(experiment["config_json"]).get("auto_paper_entries") if experiment else None

    def operation_mode_at(self, experiment_id, observed_at):
        """Use the mode in force when a signal was first observed, never today's switch."""
        with self.journal.connect() as db:
            previous = db.execute(
                "SELECT payload_json FROM journal_events WHERE kind='RESEARCH_OPERATION_MODE' "
                "AND signal_id=? AND recorded_at<=? ORDER BY recorded_at DESC, rowid DESC LIMIT 1",
                (experiment_id, as_utc(observed_at)),
            ).fetchone()
            if previous:
                return json.loads(previous["payload_json"])["auto_paper_entries"]
            experiment = db.execute(
                "SELECT config_json FROM research_experiments WHERE id=?", (experiment_id,)
            ).fetchone()
        return json.loads(experiment["config_json"]).get("auto_paper_entries") if experiment else None

    def latest_candle(self, experiment_id, symbol, timeframe):
        with self.journal.connect() as db:
            row = db.execute(
                "SELECT MAX(o.candle_close) FROM observations o JOIN research_observations r "
                "ON r.signal_id=o.id WHERE r.experiment_id=? AND o.symbol=? AND o.timeframe=?",
                (experiment_id, symbol, timeframe),
            ).fetchone()
        return row[0]

    def experiment_config(self, experiment_id):
        with self.journal.connect() as db:
            row = db.execute(
                "SELECT config_json FROM research_experiments WHERE id=?", (experiment_id,)
            ).fetchone()
        return json.loads(row["config_json"]) if row else None

    def observation(self, signal_id):
        with self.journal.connect() as db:
            row = db.execute(
                "SELECT o.*, r.origin, r.experiment_id FROM observations o "
                "JOIN research_observations r ON r.signal_id=o.id WHERE o.id=?",
                (signal_id,),
            ).fetchone()
        return dict(row) if row else None

    def claim_ai(self, signal_id, model, prompt_version, max_requests=1):
        """Durably claim before any paid request; unknown in-flight calls are never repeated."""
        with self.journal.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT state, attempts, reason FROM research_ai_requests WHERE signal_id=?",
                (signal_id,),
            ).fetchone()
            if row is not None:
                retryable = row["reason"] in ("API_TIMEOUT_OR_TRANSPORT", "API_RETRY_EXHAUSTED")
                if row["state"] != "DONE" or not retryable or row["attempts"] >= max_requests:
                    return False
                db.execute(
                    "UPDATE research_ai_requests SET state='STARTED', attempts=attempts+1, "
                    "requested_at=?, responded_at=NULL, reason=NULL WHERE signal_id=?",
                    (now_utc(), signal_id),
                )
                return True
            db.execute(
                "INSERT INTO research_ai_requests(signal_id,state,attempts,requested_at,model,"
                "prompt_version,budget_decision) VALUES (?,?,?,?,?,?,?)",
                (signal_id, "STARTED", 1, now_utc(), model, prompt_version, "PENDING"),
            )
            return True

    def ai_request(self, signal_id):
        with self.journal.connect() as db:
            row = db.execute("SELECT * FROM research_ai_requests WHERE signal_id=?", (signal_id,)).fetchone()
        return dict(row) if row else None

    def pending_ai(self, experiment_id):
        with self.journal.connect() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT o.id, o.signal_json, o.market_json, o.candle_close, o.symbol, "
                    "o.timeframe, r.origin, a.state FROM observations o "
                    "JOIN research_observations r ON r.signal_id=o.id "
                    "LEFT JOIN research_ai_requests a ON a.signal_id=o.id "
                    "WHERE r.experiment_id=? AND r.origin='LIVE' "
                    "AND ((o.ai_status IS NULL AND a.state IS NULL) OR a.state='STARTED')",
                    (experiment_id,),
                )
            ]

    def complete_ai(self, signal_id, response, latency_ms, usage=None, estimated_cost=None):
        reason = response.reason if response.reason and response.reason.isupper() else None
        budget = "EXCEEDED" if reason == "BUDGET_EXHAUSTED" else "RESERVED_OR_CACHED"
        with self.journal.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "UPDATE research_ai_requests SET state='DONE', responded_at=?, latency_ms=?, "
                "budget_decision=?, reason=?, usage_json=?, estimated_cost_usd=? WHERE signal_id=?",
                (now_utc(), latency_ms, budget, reason, compact(usage or {}), estimated_cost, signal_id),
            )

    def skip_ai(self, signal_id, reason):
        with self.journal.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "INSERT OR IGNORE INTO research_ai_requests(signal_id,state,attempts,budget_decision,reason) "
                "VALUES (?,'SKIPPED',0,'NOT_REQUESTED',?)",
                (signal_id, reason),
            )

    def record_execution(self, signal_id, status, reason):
        with self.journal.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO research_execution VALUES (?,?,?,?)",
                (signal_id, status, reason, now_utc()),
            )

    def missing_execution_metadata(self, experiment_id):
        """Recover metadata after a crash between AI review and bridge eligibility."""
        with self.journal.connect() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT o.id, o.signal_json, r.origin, r.observed_at FROM observations o "
                    "JOIN research_observations r ON r.signal_id=o.id "
                    "LEFT JOIN research_execution e ON e.signal_id=o.id "
                    "WHERE r.experiment_id=? AND e.signal_id IS NULL "
                    "ORDER BY r.observed_at",
                    (experiment_id,),
                )
            ]

    def pending_execution(self, experiment_id, limit=50):
        with self.journal.connect() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT o.id, o.signal_json, o.market_json FROM observations o "
                    "JOIN research_observations r ON r.signal_id=o.id "
                    "JOIN research_execution e ON e.signal_id=o.id "
                    "WHERE r.experiment_id=? AND r.origin='LIVE' "
                    "AND e.status='NOT_ATTEMPTED' AND e.reason='PAPER_BRIDGE_PENDING' "
                    "ORDER BY r.observed_at LIMIT ?",
                    (experiment_id, limit),
                )
            ]

    def claim_execution(self, signal_id):
        with self.journal.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            changed = db.execute(
                "UPDATE research_execution SET status='CLAIMED', reason='PAPER_BRIDGE_CLAIMED', "
                "recorded_at=? WHERE signal_id=? AND status='NOT_ATTEMPTED' "
                "AND reason='PAPER_BRIDGE_PENDING'",
                (now_utc(), signal_id),
            ).rowcount
        return bool(changed)

    def complete_execution(self, signal_id, status, reason):
        with self.journal.connect() as db:
            db.execute(
                "UPDATE research_execution SET status=?, reason=?, recorded_at=? WHERE signal_id=? "
                "AND status='CLAIMED'",
                (status, reason, now_utc(), signal_id),
            )

    def claimed_execution(self, experiment_id):
        with self.journal.connect() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT e.signal_id, e.recorded_at, a.status AS attempt_status, a.reason AS attempt_reason, "
                    "p.id AS position_id FROM research_execution e "
                    "JOIN research_observations r ON r.signal_id=e.signal_id "
                    "LEFT JOIN entry_attempts a ON a.signal_id=e.signal_id "
                    "LEFT JOIN paper_positions p ON p.signal_id=e.signal_id "
                    "WHERE r.experiment_id=? AND e.status='CLAIMED'",
                    (experiment_id,),
                )
            ]

    def outcomes_due(self, experiment_id, symbol, timeframe):
        with self.journal.connect() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT o.id, o.candle_close, o.signal_json FROM observations o "
                    "JOIN research_observations r ON r.signal_id=o.id "
                    "LEFT JOIN research_outcomes u ON u.signal_id=o.id "
                    "WHERE r.experiment_id=? AND o.symbol=? AND o.timeframe=? "
                    "AND o.technical_direction!='HOLD' "
                    "AND (u.status IS NULL OR u.status='PENDING')",
                    (experiment_id, symbol, timeframe),
                )
            ]

    def save_outcome(self, signal_id, evaluated_through, result):
        with self.journal.connect() as db:
            db.execute(
                "INSERT INTO research_outcomes VALUES (?,?,?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(signal_id) DO UPDATE SET evaluated_through=excluded.evaluated_through, "
                "status=excluded.status, reached_sl=excluded.reached_sl, "
                "reached_tp1=excluded.reached_tp1, reached_tp2=excluded.reached_tp2, "
                "reached_tp3=excluded.reached_tp3, mfe_pct=excluded.mfe_pct, "
                "mae_pct=excluded.mae_pct, bars=excluded.bars, "
                "bars_to_outcome=excluded.bars_to_outcome",
                (
                    signal_id,
                    as_utc(evaluated_through),
                    result["status"],
                    int(result["reached_sl"]),
                    int(result["reached_tp1"]),
                    int(result["reached_tp2"]),
                    int(result["reached_tp3"]),
                    result["mfe_pct"],
                    result["mae_pct"],
                    result["bars"],
                    result["bars_to_outcome"],
                    result["version"],
                ),
            )

    def heartbeat(self, experiment_id, *, success=False, candle_close=None, next_scan=None, healthy=True):
        with self.journal.connect() as db:
            db.execute(
                "UPDATE scanner_state SET heartbeat_at=?, last_success_at=CASE WHEN ? THEN ? "
                "ELSE last_success_at END, last_candle_close=COALESCE(?,last_candle_close), "
                "next_scan_at=?, healthy=? WHERE experiment_id=?",
                (
                    now_utc(),
                    int(success),
                    now_utc(),
                    as_utc(candle_close) if candle_close is not None else None,
                    as_utc(next_scan) if next_scan is not None else None,
                    int(healthy),
                    experiment_id,
                ),
            )

    def error(self, stage, exc, symbol=None, timeframe=None):
        with self.journal.connect() as db:
            db.execute(
                "INSERT INTO scanner_errors(occurred_at,stage,error_type,symbol,timeframe) "
                "VALUES (?,?,?,?,?)",
                (now_utc(), stage, type(exc).__name__, symbol, timeframe),
            )
            db.execute(
                "DELETE FROM scanner_errors WHERE id NOT IN "
                "(SELECT id FROM scanner_errors ORDER BY id DESC LIMIT 200)"
            )

    def status(self, experiment_id):
        today = datetime.now(timezone.utc).date().isoformat()
        with self.journal.connect() as db:
            state = db.execute(
                "SELECT * FROM scanner_state WHERE experiment_id=?", (experiment_id,)
            ).fetchone()
            counts = db.execute(
                "SELECT COUNT(*), SUM(r.origin='LIVE'), SUM(r.origin='BACKFILL_TECHNICAL') "
                "FROM research_observations r JOIN observations o ON o.id=r.signal_id "
                "WHERE r.experiment_id=? AND substr(r.observed_at,1,10)=?",
                (experiment_id, today),
            ).fetchone()
            ai = db.execute(
                "SELECT SUM(a.attempts), SUM(a.reason IS NOT NULL AND a.state='DONE') "
                "FROM research_ai_requests a JOIN research_observations r ON r.signal_id=a.signal_id "
                "WHERE r.experiment_id=? AND substr(a.requested_at,1,10)=?",
                (experiment_id, today),
            ).fetchone()
            backlog = db.execute(
                "SELECT COUNT(*) FROM research_ai_requests a JOIN research_observations r "
                "ON r.signal_id=a.signal_id WHERE r.experiment_id=? AND a.state='STARTED'",
                (experiment_id,),
            ).fetchone()[0]
        return {
            "heartbeat_at": state["heartbeat_at"] if state else None,
            "last_success_at": state["last_success_at"] if state else None,
            "last_candle_close": state["last_candle_close"] if state else None,
            "next_scan_at": state["next_scan_at"] if state else None,
            "healthy": bool(state["healthy"]) if state else False,
            "observations_today": counts[0],
            "live_today": counts[1] or 0,
            "backfill_today": counts[2] or 0,
            "ai_calls_today": ai[0] or 0,
            "ai_failures_today": ai[1] or 0,
            "inflight_unknown": backlog,
        }

    def errors(self, limit=10):
        with self.journal.connect() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT occurred_at, stage, error_type, symbol, timeframe FROM scanner_errors "
                    "ORDER BY id DESC LIMIT ?",
                    (max(1, min(int(limit), 20)),),
                )
            ]
