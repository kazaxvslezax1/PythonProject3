"""Offline replay of AI reviews. Missing records are reported, never synthesized."""

import json
from pathlib import Path

import pandas as pd
from backtester import simulate
from hybrid_strategy import AIMode, hybrid_signal
from market_snapshot import build_snapshot
from storage import atomic_json


async def compare_ai(
    df, symbol, timeframe, analyzer, *, retrospective=False, allow_api=False, holdout_fraction=0.3
):
    if not 0.1 <= holdout_fraction <= 0.5 or len(df) < 180:
        raise ValueError("Need at least 180 candles and a chronological holdout")
    # Every input ends at the current bar. No contemporary requests by default.
    baseline = {}
    filtered = {}
    missing = 0
    reviewed = 0
    timing_skipped = 0
    for i in range(119, len(df) - 1):
        frame = df.iloc[max(0, i - 119) : i + 1]
        cutoff = frame.close_time.iloc[-1] + pd.Timedelta(milliseconds=1)
        snapshot = build_snapshot(frame, symbol, timeframe, cutoff)
        baseline[i] = snapshot.technical
        if snapshot.technical.plan is None:
            continue
        decision = await hybrid_signal(
            snapshot, analyzer, AIMode.FILTER, retrospective=retrospective, replay=not allow_api
        )
        if decision.ai.status != "OK":
            missing += 1
            continue
        # Modern calls on historical data are experiments, never historical live evidence.
        if not retrospective:
            available = pd.Timestamp(decision.ai.analyzed_at)
            if available > df.time.iloc[i + 1]:
                timing_skipped += 1
                continue
        reviewed += 1
        filtered[i] = decision.final
    split = max(120, int(len(df) * (1 - holdout_fraction)))
    segments = {}
    for name, start, end in [("development", 120, split), ("holdout", split, len(df))]:
        # Independent capital and no position crossing evaluation boundary.
        ordinary = simulate(df.iloc[:end], baseline, start_index=start)
        hybrid = simulate(df.iloc[:end], filtered, start_index=start)
        segments[name] = {"technical": ordinary["stats"], "hybrid_filter": hybrid["stats"]}
    complete = missing == 0 and timing_skipped == 0 and reviewed > 0
    delta = (
        segments["holdout"]["hybrid_filter"]["total_profit"]
        - segments["holdout"]["technical"]["total_profit"]
    )
    return {
        "kind": "RETROSPECTIVE_AI_EXPERIMENT" if retrospective else "RECORDED_AI_REPLAY",
        "symbol": symbol,
        "timeframe": timeframe,
        "model": analyzer.model,
        "prompt_version": analyzer.status()["prompt_version"],
        "reviewed": reviewed,
        "missing_reviews": missing,
        "late_reviews": timing_skipped,
        "complete": complete,
        "segments": segments,
        "holdout_return_delta": delta,
        "conclusion": (
            "Insufficient replay coverage; AI benefit cannot be assessed"
            if not complete
            else "AI did not improve holdout net return"
            if delta <= 0
            else "Higher holdout net return in this experiment; no proof of live profitability"
        ),
        "warning": "Modern model responses to historical data do not establish past live trading results.",
    }


def save_comparison(report, path=None):
    path = path or Path(__file__).resolve().parent.parent / "runtime" / "ai_performance.json"
    atomic_json(path, report)


def load_comparison(path=None):
    path = Path(path or Path(__file__).resolve().parent.parent / "runtime" / "ai_performance.json")
    if not path.exists():
        return {"conclusion": "No validated AI comparison yet. Benefit of DeepSeek is not established."}
    return json.loads(path.read_text())
