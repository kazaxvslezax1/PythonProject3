"""Prospective, paper-only event journal shared by API and Telegram processes.

The existing JSON position ledger remains authoritative for actual PAPER execution.
Only explicitly selected market/decision fields enter this database or its exports.
"""

import csv
import hashlib
import io
import json
import os
import re
import sqlite3
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from deepseek_analyzer import MODEL_PRICES, PROMPT_VERSION
from market_data import normalize_symbol, validate_candles

DEFAULT_PATH = Path(__file__).resolve().parents[1] / "runtime" / "paper_journal.sqlite3"
STRATEGY_VERSION = "technical-v1"
JOURNAL_VERSION = "paper-observe-v1"
MARK_INTERVAL_SECONDS = 300


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def as_utc(value):
    stamp = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    return stamp.astimezone(timezone.utc).isoformat()


def uid(*values):
    return hashlib.sha256("|".join(map(str, values)).encode()).hexdigest()


def compact(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"), default=str)


def cost_settings():
    fee = float(os.environ.get("PAPER_JOURNAL_FEE_RATE", "0.001"))
    slip = float(os.environ.get("PAPER_JOURNAL_SLIPPAGE_RATE", "0.0005"))
    capital = float(os.environ.get("PAPER_JOURNAL_CAPITAL_USD", "10000"))
    if not (0 <= fee <= 0.03 and 0 <= slip <= 0.03 and capital > 0):
        raise ValueError("Invalid PAPER journal cost/capital configuration")
    return {"fee_rate": fee, "slippage_rate": slip, "capital_usd": capital}


def journal_path(path=None):
    """Resolve relative overrides from the project root, independent of process CWD."""
    selected = Path(path or os.environ.get("PAPER_JOURNAL_PATH") or DEFAULT_PATH).expanduser()
    if not selected.is_absolute():
        selected = DEFAULT_PATH.parents[1] / selected
    return selected.resolve()


class PaperJournal:
    def __init__(self, path=None):
        self.path = journal_path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.costs = cost_settings()
        self.config_version = uid(
            JOURNAL_VERSION,
            compact(self.costs),
            os.environ.get("AI_MODE", "ADVISORY"),
            os.environ.get("DEEPSEEK_MODEL", "deepseek-flash"),
            os.environ.get("STRATEGY_TIMEFRAME", "1h"),
        )[:16]
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version > 1:
                raise ValueError("Paper journal schema is newer than this code")
            if version == 0:
                db.executescript("""
                    CREATE TABLE journal_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                    CREATE TABLE observations (
                        id TEXT PRIMARY KEY, strategy_version TEXT NOT NULL,
                        config_version TEXT NOT NULL, symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL, candle_close TEXT NOT NULL,
                        first_seen TEXT NOT NULL, technical_direction TEXT NOT NULL,
                        quality REAL NOT NULL, signal_json TEXT NOT NULL,
                        market_json TEXT NOT NULL, ai_mode TEXT NOT NULL,
                        ai_model TEXT, prompt_version TEXT, ai_at TEXT,
                        ai_status TEXT, fact_check TEXT, ai_direction TEXT,
                        ai_reason TEXT, final_direction TEXT NOT NULL,
                        shadow_decision TEXT NOT NULL, shadow_reason TEXT);
                    CREATE TABLE entry_attempts (
                        id TEXT PRIMARY KEY, signal_id TEXT, chat_id INTEGER NOT NULL,
                        attempted_at TEXT NOT NULL, status TEXT NOT NULL,
                        reason TEXT NOT NULL, position_id TEXT,
                        portfolio_json TEXT NOT NULL);
                    CREATE TABLE paper_positions (
                        id TEXT PRIMARY KEY, signal_id TEXT, symbol TEXT NOT NULL,
                        timeframe TEXT, direction TEXT NOT NULL,
                        opened_at TEXT NOT NULL, closed_at TEXT, status TEXT NOT NULL,
                        notional REAL NOT NULL, quantity REAL NOT NULL,
                        entry REAL NOT NULL, entry_quote REAL, stop_loss REAL NOT NULL,
                        targets_json TEXT NOT NULL, close_reason TEXT,
                        realized_pct REAL NOT NULL, source TEXT NOT NULL,
                        first_recorded TEXT NOT NULL, last_recorded TEXT NOT NULL);
                    CREATE TABLE paper_fills (
                        id TEXT PRIMARY KEY, position_id TEXT NOT NULL,
                        ordinal INTEGER NOT NULL, occurred_at TEXT NOT NULL,
                        reason TEXT NOT NULL, trigger_price REAL,
                        fill_price REAL NOT NULL, size_pct REAL NOT NULL,
                        net_pnl_pct REAL NOT NULL,
                        UNIQUE(position_id, ordinal));
                    CREATE TABLE journal_events (
                        id TEXT PRIMARY KEY, kind TEXT NOT NULL,
                        occurred_at TEXT NOT NULL, recorded_at TEXT NOT NULL,
                        signal_id TEXT, position_id TEXT,
                        payload_json TEXT NOT NULL);
                    CREATE INDEX ix_observations_time ON observations(first_seen);
                    CREATE INDEX ix_positions_status ON paper_positions(status, source);
                    CREATE INDEX ix_events_position ON journal_events(position_id);
                """)
                db.execute("INSERT INTO journal_meta VALUES ('created_at', ?)", (now_utc(),))
                db.execute("INSERT INTO journal_meta VALUES ('cost_settings', ?)", (compact(self.costs),))
                db.execute("PRAGMA user_version=1")
            self.started_at = db.execute("SELECT value FROM journal_meta WHERE key='created_at'").fetchone()[
                0
            ]
            stored = db.execute("SELECT value FROM journal_meta WHERE key='cost_settings'").fetchone()
            if stored is None:  # Upgrade journals created by early v1 builds.
                db.execute("INSERT INTO journal_meta VALUES ('cost_settings', ?)", (compact(self.costs),))
            elif json.loads(stored["value"]) != self.costs:
                raise ValueError("Journal cost settings changed; use a new PAPER_JOURNAL_PATH")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA busy_timeout=10000")
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def event(db, event_id, kind, occurred_at, signal_id=None, position_id=None, payload=None):
        db.execute(
            "INSERT OR IGNORE INTO journal_events VALUES (?,?,?,?,?,?,?)",
            (event_id, kind, occurred_at, now_utc(), signal_id, position_id, compact(payload or {})),
        )

    def record_signal(self, analysis, *, origin="API"):
        signal = analysis["technical_signal"]
        if normalize_symbol(signal.symbol) != signal.symbol:
            raise ValueError("Invalid observed symbol")
        frame = validate_candles(
            analysis["frame"].tail(120),
            signal.timeframe,
            datetime.now(timezone.utc),
            min_bars=60,
            require_fresh=False,
        )
        candle_close = as_utc(signal.timestamp)
        if frame.empty or as_utc(frame.close_time.iloc[-1].to_pydatetime()) != candle_close:
            raise ValueError("Signal and last closed candle differ")
        if signal.timestamp >= datetime.now(timezone.utc):
            raise ValueError("Cannot journal an unclosed or future candle")
        signal_id = uid(signal.strategy_version, signal.symbol, signal.timeframe, candle_close)
        market = {
            "candles": [
                {
                    key: str(getattr(row, key)) if key in ("time", "close_time") else float(getattr(row, key))
                    for key in ("time", "close_time", "open", "high", "low", "close", "volume")
                }
                for row in frame.itertuples(index=False)
            ],
            "indicators": {
                key: float(value)
                for key, value in analysis["indicators"].items()
                if key
                in (
                    "RSI",
                    "MACD",
                    "MACD_Signal",
                    "SMA_20",
                    "SMA_50",
                    "EMA_12",
                    "EMA_26",
                    "ATR",
                    "ADX",
                    "BB_Upper",
                    "BB_Middle",
                    "BB_Lower",
                    "Volume_Ratio",
                    "Volatility",
                )
            },
        }
        first_seen = now_utc()
        mode = os.environ.get("AI_MODE", "ADVISORY").upper()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT id, candle_close, signal_json, market_json FROM observations WHERE id=?",
                (signal_id,),
            ).fetchone()
            if existing is None:
                # Reuse an older v1 row written with an equivalent non-UTC offset.
                for row in db.execute(
                    "SELECT id, candle_close, signal_json, market_json FROM observations "
                    "WHERE strategy_version=? AND symbol=? AND timeframe=? ORDER BY first_seen",
                    (signal.strategy_version, signal.symbol, signal.timeframe),
                ):
                    if as_utc(row["candle_close"]) == candle_close:
                        signal_id, existing = row["id"], row
                        break
            if existing is not None:
                frozen = json.loads(existing["signal_json"])
                current = signal.model_dump(mode="json")
                frozen.pop("timestamp")
                current.pop("timestamp")
                if frozen != current or json.loads(existing["market_json"]) != market:
                    raise ValueError("Conflicting analysis for an already observed candle")
            else:
                db.execute(
                    "INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        signal_id,
                        signal.strategy_version,
                        self.config_version,
                        signal.symbol,
                        signal.timeframe,
                        candle_close,
                        first_seen,
                        signal.direction.value,
                        signal.quality,
                        signal.model_dump_json(),
                        compact(market),
                        mode,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        signal.direction.value,
                        "HOLD" if signal.plan is None else "UNREVIEWED",
                        None,
                    ),
                )
            self.event(
                db,
                uid(signal_id, "SIGNAL"),
                "SIGNAL",
                first_seen,
                signal_id,
                payload={"origin": origin, "direction": signal.direction.value, "configured_mode": mode},
            )
        return signal_id

    def record_ai(self, signal_id, decision):
        ai = decision.ai
        if ai is None:
            return
        technical = decision.technical
        if technical.plan is None:
            shadow, shadow_reason = "HOLD", "TECHNICAL_HOLD"
        elif ai.status != "OK" or ai.fact_check_status != "PASSED" or ai.result is None:
            shadow, shadow_reason = "UNAVAILABLE", ai.reason or "AI_NOT_VERIFIED"
        elif ai.result.direction == technical.direction.value and ai.result.confirmation == "SUFFICIENT":
            shadow, shadow_reason = "ALLOW", "AI_CONFIRMED"
        else:
            shadow, shadow_reason = "VETO", "AI_CONFLICT_OR_INSUFFICIENT"
        response_time = now_utc()  # Journal receipt, including cache hits; never backdate availability.
        model = ai.model if ai.model in MODEL_PRICES else "INVALID_CONFIGURATION"
        reason = ai.reason if ai.reason and re.fullmatch(r"[A-Z0-9_]{1,80}", ai.reason) else None
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT ai_status, symbol, timeframe, candle_close, technical_direction "
                "FROM observations WHERE id=?",
                (signal_id,),
            ).fetchone()
            if row is None:
                raise ValueError("AI review has no journaled signal")
            if (row["symbol"], row["timeframe"], as_utc(row["candle_close"]), row["technical_direction"]) != (
                technical.symbol,
                technical.timeframe,
                as_utc(technical.timestamp),
                technical.direction.value,
            ):
                raise ValueError("AI review identity mismatch")
            if row["ai_status"] is not None:
                self.event(
                    db,
                    uuid.uuid4().hex,
                    "AI_RETRY",
                    response_time,
                    signal_id,
                    payload={
                        "status": ai.status,
                        "fact_check": ai.fact_check_status,
                        "shadow": shadow,
                        "model": model,
                        "prompt_version": ai.prompt_version or PROMPT_VERSION,
                        "cached": ai.cached,
                        "provider_analyzed_at": ai.analyzed_at,
                    },
                )
                return  # Freeze the first prospective decision; retain retry diagnostics.
            db.execute(
                "UPDATE observations SET ai_mode=?, ai_model=?, prompt_version=?, ai_at=?, ai_status=?, "
                "fact_check=?, ai_direction=?, ai_reason=?, final_direction=?, shadow_decision=?, "
                "shadow_reason=? WHERE id=?",
                (
                    decision.mode.value,
                    model,
                    ai.prompt_version or PROMPT_VERSION,
                    response_time,
                    ai.status,
                    ai.fact_check_status,
                    ai.result.direction if ai.result else None,
                    reason,
                    decision.final.direction.value,
                    shadow,
                    shadow_reason,
                    signal_id,
                ),
            )
            self.event(
                db,
                uid(signal_id, "AI_FIRST"),
                "AI_REVIEW",
                response_time,
                signal_id,
                payload={
                    "status": ai.status,
                    "fact_check": ai.fact_check_status,
                    "shadow": shadow,
                    "cached": ai.cached,
                    "provider_analyzed_at": ai.analyzed_at,
                },
            )

    def has_attempt(self, signal_id, chat_id):
        with self.connect() as db:
            row = db.execute(
                "SELECT status, position_id FROM entry_attempts WHERE id=?",
                (uid(signal_id, chat_id),),
            ).fetchone()
        return dict(row) if row else None

    def paper_equity(self):
        with self.connect() as db:
            realized = db.execute(
                "SELECT COALESCE(SUM(notional * realized_pct / 100), 0) "
                "FROM paper_positions WHERE source='PROSPECTIVE'"
            ).fetchone()[0]
        return self.costs["capital_usd"] + realized

    def record_attempt(self, signal_id, chat_id, status, reason, portfolio, position_id=None):
        attempt_id = uid(signal_id, chat_id) if signal_id else uuid.uuid4().hex
        occurred = now_utc()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            shadow = None
            if signal_id:
                row = db.execute(
                    "SELECT shadow_decision, ai_status, fact_check FROM observations WHERE id=?", (signal_id,)
                ).fetchone()
                shadow = (
                    row["shadow_decision"]
                    if row and row["ai_status"] == "OK" and row["fact_check"] == "PASSED"
                    else None
                )
                if shadow is None:
                    retries = db.execute(
                        "SELECT payload_json FROM journal_events WHERE signal_id=? AND kind='AI_RETRY' "
                        "ORDER BY recorded_at ASC",
                        (signal_id,),
                    ).fetchall()
                    for retry in retries:
                        payload = json.loads(retry["payload_json"])
                        if payload["status"] == "OK" and payload["fact_check"] == "PASSED":
                            shadow = payload["shadow"]
                            break
            has_capacity = (
                portfolio["active_slots_global"] < portfolio["slot_limit"]
                and portfolio["available_model_usd"] >= portfolio["requested_notional_usd"]
            )
            technical_control = (
                "NOT_LINKED"
                if not signal_id
                else "REJECTED"
                if status == "REJECTED"
                else "ALLOW"
                if has_capacity
                else "VETO_PORTFOLIO"
            )
            ai_control = (
                "NOT_LINKED"
                if not signal_id
                else "REJECTED"
                if technical_control != "ALLOW"
                else "ALLOW"
                if shadow == "ALLOW"
                else "VETO_AI"
                if shadow == "VETO"
                else "UNKNOWN_AI"
            )
            portfolio = {
                **portfolio,
                "technical_control": technical_control,
                "ai_control": ai_control,
                "ai_shadow_at_attempt": shadow,
            }
            db.execute(
                "INSERT OR IGNORE INTO entry_attempts VALUES (?,?,?,?,?,?,?,?)",
                (
                    attempt_id,
                    signal_id,
                    int(chat_id),
                    occurred,
                    status,
                    reason,
                    position_id,
                    compact(portfolio),
                ),
            )
            self.event(
                db,
                uid(attempt_id, "ATTEMPT"),
                "ENTRY_DECISION",
                occurred,
                signal_id,
                position_id,
                {"status": status, "reason": reason, "portfolio": portfolio},
            )
        return attempt_id

    def reconcile_positions(self, active, history, *, recovering=False):
        """Idempotently copy the authoritative JSON ledger; never invent a fill."""
        positions = {p["position_id"]: p for p in [*history, *active.values()]}
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            for pid, p in positions.items():
                created = as_utc(p["created_at"])
                source = "PROSPECTIVE" if created >= self.started_at else "LEGACY_IMPORT"
                observed = now_utc()
                existed = db.execute(
                    "SELECT id, stop_loss, realized_pct, status FROM paper_positions WHERE id=?",
                    (pid,),
                ).fetchone()
                db.execute(
                    "INSERT INTO paper_positions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
                    "ON CONFLICT(id) DO UPDATE SET closed_at=excluded.closed_at, "
                    "status=excluded.status, stop_loss=excluded.stop_loss, "
                    "close_reason=excluded.close_reason, realized_pct=excluded.realized_pct, "
                    "last_recorded=excluded.last_recorded",
                    (
                        pid,
                        p.get("signal_id"),
                        p["symbol"],
                        p.get("timeframe"),
                        p["direction"],
                        created,
                        as_utc(p["closed_at"]) if p.get("closed_at") else None,
                        p["status"],
                        float(p.get("paper_notional") or float(p.get("quantity", 0)) * p["entry_price"]),
                        float(p.get("quantity", 0)),
                        float(p["entry_price"]),
                        p.get("entry_quote_price"),
                        float(p["stop_loss"]),
                        compact(p["take_profits"]),
                        p.get("close_reason"),
                        float(p.get("realized_pnl_pct", 0)),
                        source,
                        observed,
                        observed,
                    ),
                )
                if not existed:
                    seen = db.execute(
                        "SELECT first_seen FROM observations WHERE id=?", (p.get("signal_id"),)
                    ).fetchone()
                    delay_ms = (
                        max(
                            0.0,
                            (
                                datetime.fromisoformat(created) - datetime.fromisoformat(seen["first_seen"])
                            ).total_seconds()
                            * 1000,
                        )
                        if seen
                        else None
                    )
                    self.event(
                        db,
                        uid(pid, "OPEN"),
                        "POSITION_OPEN",
                        created,
                        p.get("signal_id"),
                        pid,
                        {
                            "source": source,
                            "symbol": p["symbol"],
                            "entry": p["entry_price"],
                            "requested_entry": p.get("requested_entry_price"),
                            "observed_quote": p.get("entry_quote_price"),
                            "signal_to_entry_ms": delay_ms,
                            "notional": p.get("paper_notional"),
                        },
                    )
                for ordinal, fill in enumerate(p.get("fills", [])):
                    fill_id = uid(pid, "FILL", ordinal)
                    db.execute(
                        "INSERT OR IGNORE INTO paper_fills VALUES (?,?,?,?,?,?,?,?,?)",
                        (
                            fill_id,
                            pid,
                            ordinal,
                            as_utc(fill["timestamp"]),
                            fill["reason"],
                            fill.get("trigger_price"),
                            fill["price"],
                            fill["size"],
                            fill["net_pnl_pct"],
                        ),
                    )
                    self.event(
                        db,
                        fill_id,
                        "POSITION_FILL",
                        as_utc(fill["timestamp"]),
                        p.get("signal_id"),
                        pid,
                        {"reason": fill["reason"], "price": fill["price"], "size_pct": fill["size"]},
                    )
                if (
                    existed
                    and p["status"] == "ACTIVE"
                    and (
                        existed["stop_loss"] != p["stop_loss"]
                        or existed["realized_pct"] != p.get("realized_pnl_pct", 0)
                    )
                ):
                    self.event(
                        db,
                        uid(pid, "UPDATE", len(p.get("fills", []))),
                        "POSITION_UPDATE",
                        observed,
                        p.get("signal_id"),
                        pid,
                        {
                            "new_stop_loss": p["stop_loss"],
                            "remaining_pct": p["current_size"],
                            "realized_pct": p.get("realized_pnl_pct", 0),
                        },
                    )
                if p["status"] == "CLOSED":
                    observed_fills = db.execute(
                        "SELECT * FROM paper_fills WHERE position_id=? ORDER BY ordinal", (pid,)
                    ).fetchall()
                    projection = {
                        "direction": p["direction"],
                        "entry_quote": p.get("entry_quote_price"),
                        "quantity": p.get("quantity", 0),
                    }
                    self.event(
                        db,
                        uid(pid, "CLOSE"),
                        "POSITION_CLOSE",
                        as_utc(p["closed_at"]) if p.get("closed_at") else observed,
                        p.get("signal_id"),
                        pid,
                        {
                            "reason": p.get("close_reason"),
                            "realized_pct": p.get("realized_pnl_pct", 0),
                            "same_fills_base_usd": self.modeled_pnl(
                                projection,
                                observed_fills,
                                self.costs["fee_rate"],
                                self.costs["slippage_rate"],
                            ),
                            "same_fills_double_usd": self.modeled_pnl(
                                projection,
                                observed_fills,
                                self.costs["fee_rate"] * 2,
                                self.costs["slippage_rate"] * 2,
                            ),
                        },
                    )
                elif recovering:
                    self.event(
                        db,
                        uuid.uuid4().hex,
                        "POSITION_RECOVERED",
                        observed,
                        p.get("signal_id"),
                        pid,
                        {"source": source},
                    )
                if p.get("signal_id"):
                    db.execute(
                        "UPDATE entry_attempts SET status='OPEN', position_id=? "
                        "WHERE signal_id=? AND chat_id=? AND status='PENDING'",
                        (pid, p["signal_id"], p["chat_id"]),
                    )

    def record_mark(self, position_id, price, position):
        sign = 1 if position["direction"] == "LONG" else -1
        unrealized = (
            sign * (price - position["entry_price"]) * position["quantity"] * (position["current_size"] / 100)
        )
        notional = float(position.get("paper_notional") or position["quantity"] * position["entry_price"])
        observed_pnl = notional * float(position.get("realized_pnl_pct", 0)) / 100 + unrealized
        observed = now_utc()
        with self.connect() as db:
            last = db.execute(
                "SELECT occurred_at, payload_json FROM journal_events "
                "WHERE kind='POSITION_MARK' AND position_id=? "
                "ORDER BY recorded_at DESC LIMIT 1",
                (position_id,),
            ).fetchone()
            if (
                last
                and (
                    datetime.fromisoformat(observed) - datetime.fromisoformat(last["occurred_at"])
                ).total_seconds()
                < MARK_INTERVAL_SECONDS
            ):
                return
            prior_peak = json.loads(last["payload_json"]).get("peak_pnl_usd", 0) if last else 0
            peak = max(0.0, prior_peak, observed_pnl)
            sampled_drawdown = 100 * (peak - observed_pnl) / notional if notional > 0 else None
            self.event(
                db,
                uuid.uuid4().hex,
                "POSITION_MARK",
                observed,
                position.get("signal_id"),
                position_id,
                {
                    "price": float(price),
                    "gross_unrealized_usd": unrealized,
                    "observed_pnl_usd": observed_pnl,
                    "peak_pnl_usd": peak,
                    "sampled_position_drawdown_pct": sampled_drawdown,
                },
            )

    @staticmethod
    def modeled_pnl(position, fills, fee_rate, slippage_rate):
        """Cost sensitivity on observed fills; does not claim a new executed trade."""
        quote = position["entry_quote"]
        if quote is None or not fills or any(f["trigger_price"] is None for f in fills):
            return None
        side = 1 if position["direction"] == "LONG" else -1
        entry = quote * (1 + side * slippage_rate)
        quantity = position["quantity"]
        pnl = -entry * quantity * fee_rate
        for fill in fills:
            fraction = fill["size_pct"] / 100
            exit_price = fill["trigger_price"] * (1 - side * slippage_rate)
            pnl += quantity * fraction * (side * (exit_price - entry) - exit_price * fee_rate)
        return pnl

    def report(self):
        with self.connect() as db:
            observations = db.execute("SELECT * FROM observations ORDER BY first_seen").fetchall()
            attempts = db.execute("SELECT * FROM entry_attempts").fetchall()
            positions = db.execute(
                "SELECT * FROM paper_positions WHERE source='PROSPECTIVE' ORDER BY closed_at, opened_at"
            ).fetchall()
            all_active = db.execute("SELECT notional FROM paper_positions WHERE status='ACTIVE'").fetchall()
            ai_retries = [
                json.loads(row["payload_json"])
                for row in db.execute("SELECT payload_json FROM journal_events WHERE kind='AI_RETRY'")
            ]
            marks = [
                json.loads(row["payload_json"])
                for row in db.execute(
                    "SELECT e.payload_json FROM journal_events e JOIN paper_positions p "
                    "ON p.id=e.position_id WHERE e.kind='POSITION_MARK' AND p.source='PROSPECTIVE'"
                )
            ]
            fills = {}
            for fill in db.execute("SELECT * FROM paper_fills ORDER BY position_id, ordinal"):
                fills.setdefault(fill["position_id"], []).append(fill)
        realized = 0.0
        peak = self.costs["capital_usd"]
        worst = 0.0
        groups = {}
        modeled = {"base_usd": 0.0, "double_usd": 0.0, "covered_positions": 0}
        for p in positions:
            key = f"{p['symbol']} {p['timeframe'] or 'unknown'}"
            group = groups.setdefault(key, {"positions": 0, "closed": 0, "net_pnl_usd": 0.0})
            group["positions"] += 1
            if p["status"] == "CLOSED":
                pnl = p["notional"] * p["realized_pct"] / 100
                group["closed"] += 1
                group["net_pnl_usd"] += pnl
                realized += pnl
                peak = max(peak, self.costs["capital_usd"] + realized)
                worst = max(worst, 100 * (peak - self.costs["capital_usd"] - realized) / peak)
                scenario = self.modeled_pnl(
                    p, fills.get(p["id"], []), self.costs["fee_rate"], self.costs["slippage_rate"]
                )
                if scenario is not None:
                    modeled["covered_positions"] += 1
                    modeled["base_usd"] += scenario
                    modeled["double_usd"] += self.modeled_pnl(
                        p,
                        fills[p["id"]],
                        self.costs["fee_rate"] * 2,
                        self.costs["slippage_rate"] * 2,
                    )
        paired = {
            a["signal_id"]
            for a in attempts
            if a["signal_id"] and json.loads(a["portfolio_json"]).get("ai_control") in ("ALLOW", "VETO_AI")
        }
        observed_equity = self.costs["capital_usd"] + sum(
            p["notional"] * p["realized_pct"] / 100 for p in positions
        )
        reserved_upper = sum(p["notional"] for p in all_active)
        unknown_active_notional = any(p["notional"] <= 0 for p in all_active)
        controls = {
            "technical_allow": 0,
            "ai_allow": 0,
            "ai_veto": 0,
            "ai_unknown": 0,
            "actual_vs_global_model_mismatch": 0,
        }
        rejected_reasons = {}
        last_portfolio = None
        for attempt in attempts:
            portfolio = json.loads(attempt["portfolio_json"])
            if last_portfolio is None or attempt["attempted_at"] >= last_portfolio[0]:
                last_portfolio = (attempt["attempted_at"], portfolio)
            if attempt["status"] == "REJECTED":
                rejected_reasons[attempt["reason"]] = rejected_reasons.get(attempt["reason"], 0) + 1
            controls["technical_allow"] += portfolio.get("technical_control") == "ALLOW"
            controls["ai_allow"] += portfolio.get("ai_control") == "ALLOW"
            controls["ai_veto"] += portfolio.get("ai_control") == "VETO_AI"
            controls["ai_unknown"] += portfolio.get("ai_control") == "UNKNOWN_AI"
            controls["actual_vs_global_model_mismatch"] += (
                attempt["status"] == "OPEN" and portfolio.get("technical_control") == "VETO_PORTFOLIO"
            )
        return {
            "period_start": observations[0]["first_seen"] if observations else self.started_at,
            "period_end": now_utc(),
            "signals": len(observations),
            "signal_directions": {
                side: sum(r["technical_direction"] == side for r in observations)
                for side in ("LONG", "SHORT", "HOLD")
            },
            "hold": sum(r["technical_direction"] == "HOLD" for r in observations),
            "rejected_entries": sum(a["status"] == "REJECTED" for a in attempts),
            "rejected_reasons": rejected_reasons,
            "latest_portfolio_model": last_portfolio[1] if last_portfolio else None,
            "latest_portfolio_recorded_at": last_portfolio[0] if last_portfolio else None,
            "current_portfolio_model": {
                "capital_after_realized_usd": observed_equity,
                "reserved_upper_bound_usd": reserved_upper,
                "available_lower_bound_usd": None
                if unknown_active_notional
                else max(0.0, observed_equity - reserved_upper),
                "active_slots_global": len(all_active),
                "slot_limit": last_portfolio[1]["slot_limit"] if last_portfolio else 5,
                "note": "unknown if legacy notional missing; otherwise conservative, without partial releases",
            },
            "paper_positions": len(positions),
            "closed_positions": sum(p["status"] == "CLOSED" for p in positions),
            "net_pnl_usd_closed": realized,
            "realized_max_drawdown_pct": worst,
            "sampled_max_position_drawdown_pct": max(
                (
                    m["sampled_position_drawdown_pct"]
                    for m in marks
                    if m.get("sampled_position_drawdown_pct") is not None
                ),
                default=None,
            ),
            "by_pair_timeframe": groups,
            "ai_ok": sum(r["ai_status"] == "OK" for r in observations),
            "ai_retry_ok": sum(r["status"] == "OK" and r["fact_check"] == "PASSED" for r in ai_retries),
            "ai_unavailable": sum(r["ai_status"] == "AI_UNAVAILABLE" for r in observations),
            "ai_error_reasons": {
                reason: sum(r["ai_reason"] == reason for r in observations)
                for reason in sorted({r["ai_reason"] for r in observations if r["ai_reason"]})
            },
            "ai_not_reviewed": sum(r["ai_status"] is None for r in observations),
            "ai_observations": sum(r["ai_status"] is not None for r in observations),
            "paired_ai_observations": sum(
                r["ai_status"] == "OK" and r["fact_check"] == "PASSED" for r in observations
            ),
            "entry_aligned_ai_decisions": sum(r["id"] in paired for r in observations),
            "shadow_allow": sum(r["shadow_decision"] == "ALLOW" for r in observations),
            "shadow_veto": sum(r["shadow_decision"] == "VETO" for r in observations),
            "control_decisions": controls,
            "modeled_same_fills_costs": modeled,
            "costs": self.costs,
            "sample_warning": "INSUFFICIENT_CLOSED_POSITIONS"
            if sum(p["status"] == "CLOSED" for p in positions) < 30
            else None,
            "drawdown_scope": "realized closed PAPER positions; excludes unrealized/intrabar risk",
            "cost_scope": "same observed fills; alternate costs do not create simulated trades",
        }

    def export(self, kind="json"):
        """Allowlisted fields only. No chat ids, raw AI text, HTTP data or environment values."""
        if kind not in ("json", "csv"):
            raise ValueError("Use json or csv")
        with self.connect() as db:
            observations = [
                dict(r)
                for r in db.execute(
                    "SELECT id, symbol, timeframe, candle_close, first_seen, technical_direction, "
                    "quality, ai_mode, ai_model, prompt_version, ai_at, ai_status, fact_check, "
                    "ai_direction, final_direction, shadow_decision FROM observations ORDER BY first_seen"
                )
            ]
            positions = [
                dict(r)
                for r in db.execute(
                    "SELECT id, signal_id, symbol, timeframe, direction, opened_at, closed_at, "
                    "status, notional, entry, stop_loss, close_reason, realized_pct, source "
                    "FROM paper_positions ORDER BY opened_at"
                )
            ]
        if kind == "json":
            return json.dumps(
                {"observations": observations, "positions": positions}, ensure_ascii=False, indent=2
            )
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "record_type",
                "id",
                "signal_id",
                "symbol",
                "timeframe",
                "time",
                "direction",
                "status",
                "net_pnl_pct",
            ],
        )
        writer.writeheader()
        for o in observations:
            writer.writerow(
                {
                    "record_type": "SIGNAL",
                    "id": o["id"],
                    "symbol": o["symbol"],
                    "timeframe": o["timeframe"],
                    "time": o["candle_close"],
                    "direction": o["technical_direction"],
                    "status": o["ai_status"] or "NOT_REVIEWED",
                }
            )
        for p in positions:
            writer.writerow(
                {
                    "record_type": "PAPER_POSITION",
                    "id": p["id"],
                    "signal_id": p["signal_id"],
                    "symbol": p["symbol"],
                    "timeframe": p["timeframe"],
                    "time": p["opened_at"],
                    "direction": p["direction"],
                    "status": p["status"],
                    "net_pnl_pct": p["realized_pct"] if p["status"] == "CLOSED" else "",
                }
            )
        return output.getvalue()

    def backup(self, destination):
        """Consistent SQLite backup, including committed WAL pages; private file mode."""
        destination = Path(destination)
        if destination.resolve() == self.path.resolve():
            raise ValueError("Backup destination must differ from active journal")
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=destination.parent, prefix=".paper-", suffix=".sqlite3")
        os.close(fd)
        try:
            with sqlite3.connect(self.path, timeout=10) as source:
                with sqlite3.connect(temporary) as target:
                    source.backup(target)
            os.replace(temporary, destination)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
