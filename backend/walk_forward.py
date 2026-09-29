"""Frozen-parameter chronological evaluation of the existing strategy. No AI requests."""

import hashlib
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from backtester import simulate, statistics
from market_data import validate_candles
from strategy_engine import generate_signal, indicator_values

COSTS = {"zero": (0.0, 0.0), "base": (0.001, 0.0005), "double": (0.002, 0.001), "stress": (0.003, 0.002)}


def features_and_signals(df, symbol, timeframe):
    signals, features = {}, {}
    for i in range(119, len(df)):
        frame = df.iloc[i - 119 : i + 1]
        signals[i] = generate_signal(
            frame, symbol, timeframe, df.close_time.iloc[i] + pd.Timedelta(milliseconds=1)
        )
        features[i] = indicator_values(frame)
    return signals, features


def regime(values):
    # Fixed before examining results; normalized per-bar ATR, no future quantiles.
    if values["ATR"] / values["close"] >= 0.02:
        return "high_volatility"
    if values["ADX"] >= 25:
        return "trend_up" if values["SMA_20"] > values["SMA_50"] else "trend_down"
    return "sideways"


def folds(start, end, train_days=180, validation_days=90, test_days=90):
    if min(train_days, validation_days, test_days) < 1:
        raise ValueError("Invalid fold duration")
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    boundary = start + pd.Timedelta(days=train_days + validation_days)
    result = []
    while boundary + pd.Timedelta(days=test_days) <= end:
        result.append(
            {
                "train_start": start,
                "validation_start": boundary - pd.Timedelta(days=validation_days),
                "test_start": boundary,
                "test_end": boundary + pd.Timedelta(days=test_days),
            }
        )
        boundary += pd.Timedelta(days=test_days)
    return result


def metrics(result):
    out = dict(result["stats"])
    pnl = [t["pnl"] for t in result["trades"]]
    wins, losses = [p for p in pnl if p > 0], [-p for p in pnl if p < 0]
    streak = maximum = 0
    for p in pnl:
        streak = streak + 1 if p < 0 else 0
        maximum = max(maximum, streak)
    fees = sum(f["fee"] for f in result["fills"])
    out.update(
        expectancy=float(np.mean(pnl)) if pnl else 0.0,
        avg_win=float(np.mean(wins)) if wins else None,
        avg_loss=float(np.mean(losses)) if losses else None,
        payoff_ratio=float(np.mean(wins) / np.mean(losses)) if wins and losses else None,
        max_loss_streak=maximum,
        fees=fees,
        pre_fee_return=100 * (out["net_pnl"] + fees) / out["initial_capital"],
        ambiguous_bars=result["ambiguous_bars"],
        sample_warning="LESS_THAN_30_TRADES" if len(pnl) < 30 else None,
    )
    return out


def signal_counts(signals, first, end):
    counts = {
        s: sum(signals[i].direction.value == s for i in range(first - 1, end - 1) if i in signals)
        for s in ("LONG", "SHORT", "HOLD")
    }
    n = sum(counts.values())
    return {
        "counts": counts,
        "shares_pct": {k: 100 * v / n if n else 0 for k, v in counts.items()},
        "total": n,
    }


def evaluate(df, signals, features, symbol, timeframe, start, end):
    df = validate_candles(df, timeframe, end, min_bars=121, require_fresh=False)
    windows = folds(start, end)
    if not windows:
        raise ValueError("Insufficient history for a complete walk-forward fold")
    proxy = {i: s for i, s in signals.items() if s.quality >= 7 and features[i]["Volume_Ratio"] >= 1.5}
    results = []
    combined = {}
    for profile, selected in (("technical", signals), ("paper_proxy", proxy)):
        for cost, (fee, slippage) in COSTS.items():
            total_trades, equity, fills, ambiguous = [], [10000.0], [], 0
            for number, window in enumerate(windows, 1):
                first = int(df.time.searchsorted(window["test_start"]))
                last = int(df.time.searchsorted(window["test_end"]))
                if first < 120 or first >= last or df.time.iloc[first] != window["test_start"]:
                    raise ValueError("Insufficient warmup or incomplete fold")
                kwargs = (
                    dict(fixed_notional=1000, max_daily_entries=6, cooldown_minutes=30)
                    if profile == "paper_proxy"
                    else {}
                )
                run = simulate(
                    df.iloc[:last],
                    selected_subset(selected, last),
                    initial=equity[-1],
                    fee=fee,
                    slippage=slippage,
                    start_index=first,
                    **kwargs,
                )
                record = {
                    "fold": number,
                    "profile": profile,
                    "cost": cost,
                    "test_start": str(window["test_start"]),
                    "test_end": str(window["test_end"]),
                    "metrics": metrics(run),
                    "signals": signal_counts(signals, first, last),
                    "eligible_signals": signal_counts(selected, first, last),
                }
                if cost == "base":
                    groups = {}
                    for trade in run["trades"]:
                        i = trade["signal_index"]
                        label = regime({**features[i], "close": float(df.close.iloc[i])})
                        groups.setdefault(label, []).append(trade)
                    record["regimes"] = {
                        k: {
                            "trades": len(v),
                            "net_pnl": sum(t["pnl"] for t in v),
                            "win_rate": 100 * sum(t["pnl"] > 0 for t in v) / len(v),
                        }
                        for k, v in groups.items()
                    }
                results.append(record)
                total_trades.extend(run["trades"])
                equity.extend(run["equity"][1:])
                fills.extend(run["fills"])
                ambiguous += run["ambiguous_bars"]
            aggregate = {
                "stats": statistics(total_trades, equity, 10000.0),
                "trades": total_trades,
                "fills": fills,
                "ambiguous_bars": ambiguous,
            }
            combined[f"{profile}:{cost}"] = metrics(aggregate)
            if cost == "base":
                combined[f"{profile}:{cost}"]["fold_returns"] = [
                    r["metrics"]["total_profit"]
                    for r in results
                    if r["profile"] == profile and r["cost"] == cost
                ]
    # Validation precedes each test window; no settings are fitted or selected from it.
    validation = []
    for number, window in enumerate(windows, 1):
        first, last = (int(df.time.searchsorted(window[k])) for k in ("validation_start", "test_start"))
        run = simulate(df.iloc[:last], selected_subset(signals, last), start_index=first)
        validation.append(
            {
                "fold": number,
                "start": str(window["validation_start"]),
                "end": str(window["test_start"]),
                "metrics": metrics(run),
            }
        )
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "folds": [{k: str(v) for k, v in w.items()} for w in windows],
        "validation": validation,
        "out_of_sample": results,
        "aggregate": combined,
        "excluded_tail_start": str(windows[-1]["test_end"]),
    }


def selected_subset(signals, last):
    return {i: s for i, s in signals.items() if i < last}


def ai_archive_coverage(path, start, end):
    """Read only metadata; never call AI or reinterpret modern outputs as historical."""
    if not Path(path).exists():
        return {"records_in_period": 0, "advisory_comparison": "NO_RECORDED_RESPONSES"}
    with sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro", uri=True) as db:
        rows = db.execute("SELECT input_json, analyzed_at, retrospective FROM analyses").fetchall()
    n = timely = retrospective_count = 0
    for raw, analyzed, retro in rows:
        data = json.loads(raw)
        cutoff = pd.Timestamp(data["as_of"])
        if pd.Timestamp(start) <= cutoff < pd.Timestamp(end):
            n += 1
            retrospective_count += bool(retro)
            timely += not retro and pd.Timestamp(analyzed) <= cutoff
    return {
        "records_in_period": n,
        "timely_records": timely,
        "retrospective_records": retrospective_count,
        "advisory_comparison": "NO_TIMELY_RECORDED_RESPONSES"
        if not timely
        else "ADVISORY_PRESERVES_TECHNICAL_DECISIONS; ARCHIVE_ALIGNMENT_REQUIRED",
    }


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
