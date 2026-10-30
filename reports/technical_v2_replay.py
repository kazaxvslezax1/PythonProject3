"""Reproduce frozen candidate replays offline; writes results only to /tmp."""

import csv
import gzip
import hashlib
import json
import math
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from backtester import simulate, statistics  # noqa: E402
from signal_models import Direction, TradePlan, TradingSignal  # noqa: E402

REPORT = ROOT / "reports/TECHNICAL_V2_RESEARCH.json"
OUTPUT_JSON = Path("/tmp/technical_v2_replay.json")
OUTPUT_CSV = Path("/tmp/technical_v2_replay.csv")
protocol = json.loads(REPORT.read_text())
assert protocol["state"] in ("FROZEN_BEFORE_CANDIDATE_EVALUATION", "EVALUATED_OFFLINE")
protocol["state"] = "FROZEN_BEFORE_CANDIDATE_EVALUATION"
protocol["results"] = None
for post_result_key in (
    "winner",
    "evaluation_completed_at_utc",
    "baseline_forward_and_correlation",
    "prospective_entry_timing_sanity_check",
    "baseline_replay_verification",
):
    protocol.pop(post_result_key, None)
old = json.loads((ROOT / "reports/WALK_FORWARD_RESULTS.json").read_text())
assert (
    hashlib.sha256((ROOT / "reports/WALK_FORWARD_RESULTS.json").read_bytes()).hexdigest()
    == protocol["dataset"]["baseline_report_sha256"]
)
assert (
    hashlib.sha256((ROOT / "reports/PROSPECTIVE_32_TRADE_AUDIT.json").read_bytes()).hexdigest()
    == protocol["dataset"]["prospective_audit_sha256"]
)


def read_series(item):
    path = ROOT / item["data"]["file"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert (
        digest
        == item["data"]["sha256"]
        == protocol["dataset"]["csv_sha256_by_series"][item["symbol"] + " " + item["timeframe"]]
    )
    df = pd.read_csv(path, float_precision="round_trip")
    for col in ("time", "close_time"):
        df[col] = pd.to_datetime(df[col], utc=True)
    cache_path = path.with_suffix(".signals.json.gz")
    with gzip.open(cache_path, "rt") as fh:
        cached = json.load(fh)
    assert cached["data_hash"] == digest and cached["code_hash"] == item["signal_code_hash"]
    features = {int(k): v for k, v in cached["features"].items()}
    return df, features, cached


def context_lookup(df1, df4, feat4):
    """Only use 4h candle with close_time <= the 1h signal candle close_time."""
    lookup = {}
    closes = df4.close_time
    for i in range(119, len(df1)):
        j = int(closes.searchsorted(df1.close_time.iloc[i], side="right") - 1)
        if j >= 119 and j in feat4:
            assert closes.iloc[j] <= df1.close_time.iloc[i]
            lookup[i] = {"index": j, "close_time": str(closes.iloc[j]), "features": feat4[j]}
    return lookup


def candidate_signals(name, df, features, symbol, tf, cap, context=None):
    close = df.close.to_numpy(dtype=float)
    high = df.high.to_numpy(dtype=float)
    low = df.low.to_numpy(dtype=float)
    signals = {}
    close_times = df.close_time
    for i in range(120, len(df) - 1):
        v = features.get(i)
        prior = features.get(i - 1)
        if not v or not prior:
            continue
        atr = float(v["ATR"])
        vol = float(v["Volume_Ratio"])
        price = close[i]
        if (
            not math.isfinite(atr)
            or atr <= 0
            or not math.isfinite(vol)
            or vol < 1.5
            or 2 * atr / price > 0.1
            or price - 6 * atr <= 0
        ):
            continue
        trend = v if name != "C_4h_regime_1h_pullback" else (context or {}).get(i, {}).get("features")
        if not trend:
            continue
        sma20, sma50 = float(trend["SMA_20"]), float(trend["SMA_50"])
        if sma20 == sma50:
            continue
        side = 1 if sma20 > sma50 else -1
        if name in ("A_trend_pullback", "C_4h_regime_1h_pullback"):
            if float(trend["ADX"]) < 25:
                continue
            ema = float(v["EMA_12"])
            ema_prev = float(prior["EMA_12"])
            triggered = (
                close[i - 1] <= ema_prev and price > ema
                if side == 1
                else close[i - 1] >= ema_prev and price < ema
            )
            distance = abs(price - ema)
        else:
            prior_high = max(high[i - 20 : i])
            prior_low = min(low[i - 20 : i])
            level = prior_high if side == 1 else prior_low
            triggered = price > level if side == 1 else price < level
            distance = side * (price - level)
        if not triggered or distance < 0 or distance > cap * atr:
            continue
        direction = Direction.LONG if side == 1 else Direction.SHORT
        risk = 2 * atr
        try:
            plan = TradePlan(
                direction=direction,
                entry=price,
                stop_loss=price - side * risk,
                take_profits=[price + side * risk * j for j in (1, 2, 3)],
            )
            signals[i] = TradingSignal(
                symbol=symbol,
                timeframe=tf,
                timestamp=close_times.iloc[i],
                direction=direction,
                quality=0,
                strength=0,
                reasons=[name, "frozen explicit conditions"],
                plan=plan,
                strategy_version="research-candidate-only",
            )
        except ValueError:
            continue
    return signals


def single_run(df, signals, first, last, initial, fee, slip):
    subset = {i: s for i, s in signals.items() if i < last}
    return simulate(
        df.iloc[:last],
        subset,
        initial=initial,
        fee=fee,
        slippage=slip,
        start_index=first,
        fixed_notional=1000,
        max_daily_entries=6,
        cooldown_minutes=30,
    )


def run_folds(df, signals, item, cost, cap):
    fee, slip = protocol["execution"]["costs"][cost]
    equity = 10000.0
    alltrades = []
    allequity = [equity]
    allfills = []
    folds = []
    ambiguous = 0
    for fold_no, w in enumerate(item["folds"], 1):
        first = int(df.time.searchsorted(pd.Timestamp(w["test_start"])))
        last = int(df.time.searchsorted(pd.Timestamp(w["test_end"])))
        assert first >= 120 and first < last and df.time.iloc[first] == pd.Timestamp(w["test_start"])
        result = single_run(df, signals, first, last, equity, fee, slip)
        row = result["stats"]
        folds.append(
            {
                "fold": fold_no,
                "period_start": w["test_start"],
                "period_end": w["test_end"],
                "trades": row["total_trades"],
                "wins": row["winning_trades"],
                "net_pnl_usd": row["net_pnl"],
                "net_return_pct": row["total_profit"],
                "profit_factor": row["profit_factor"],
                "max_drawdown_pct": row["max_drawdown"],
                "ambiguous_bars": result["ambiguous_bars"],
            }
        )
        for t in result["trades"]:
            entry = t["fills"][0]
            alltrades.append(
                {
                    **t,
                    "symbol": item["symbol"],
                    "timeframe": item["timeframe"],
                    "candidate": cost,
                    "fold": fold_no,
                    "entry_notional_usd": entry["price"] * entry["quantity"],
                }
            )
        allequity.extend(result["equity"][1:])
        allfills.extend(result["fills"])
        ambiguous += result["ambiguous_bars"]
        equity = row["final_capital"]
    stat = statistics(alltrades, allequity, 10000.0)
    pnls = [t["pnl"] for t in alltrades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    hold = [
        (pd.Timestamp(t["exit_time"]) - pd.Timestamp(t["entry_time"])).total_seconds() / 3600
        for t in alltrades
    ]
    fee_total = sum(f["fee"] for f in allfills)
    test_days = sum((pd.Timestamp(w["test_end"]) - pd.Timestamp(w["test_start"])).days for w in item["folds"])
    stat.update(
        {
            "expectancy_usd": st.mean(pnls) if pnls else None,
            "gross_before_fees_after_slippage_usd": sum(pnls) + fee_total,
            "gross_expectancy_before_fees_usd": (sum(pnls) + fee_total) / len(pnls) if pnls else None,
            "fees_usd": fee_total,
            "avg_holding_hours": st.mean(hold) if hold else None,
            "trades_per_year": len(alltrades) * 365.25 / test_days,
            "entry_turnover_usd": sum(t["entry_notional_usd"] for t in alltrades),
            "roundtrip_turnover_usd_approx": 2 * sum(t["entry_notional_usd"] for t in alltrades),
            "ambiguous_bars": ambiguous,
            "folds": folds,
            "gross_profit_usd": sum(wins),
            "gross_loss_usd": -sum(losses),
        }
    )
    return stat, alltrades


def pooled(trades):
    pnls = [t["pnl"] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    return {
        "trades": len(pnls),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": 100 * len(wins) / len(pnls) if pnls else None,
        "net_pnl_usd": sum(pnls),
        "expectancy_usd": st.mean(pnls) if pnls else None,
        "avg_trade_usd": st.mean(pnls) if pnls else None,
        "profit_factor": sum(wins) / -sum(losses) if losses else None,
        "gross_profit_usd": sum(wins),
        "gross_loss_usd": -sum(losses),
    }


def excursion(df, signals, folds):
    records = []
    skipped = 0
    opens = df.open.to_numpy(dtype=float)
    highs = df.high.to_numpy(dtype=float)
    lows = df.low.to_numpy(dtype=float)
    for w in folds:
        first = int(df.time.searchsorted(pd.Timestamp(w["test_start"])))
        last = int(df.time.searchsorted(pd.Timestamp(w["test_end"])))
        for i, s in signals.items():
            if i < first - 1 or i >= last - 24:
                continue
            side = 1 if s.direction == Direction.LONG else -1
            entry = opens[i + 1]
            stop = s.plan.stop_loss
            tp1 = s.plan.take_profits[0]
            try:
                moved = TradePlan(
                    direction=s.direction, entry=entry, stop_loss=stop, take_profits=s.plan.take_profits
                )
            except ValueError:
                skipped += 1
                continue
            if moved.rr < 2 or abs(entry - stop) / entry > 0.1:
                skipped += 1
                continue
            favorable = np.array(
                [
                    side * (high - entry) / entry * 100 if side == 1 else side * (low - entry) / entry * 100
                    for high, low in zip(highs[i + 1 : i + 25], lows[i + 1 : i + 25])
                ]
            )
            adverse = np.array(
                [
                    side * (low - entry) / entry * 100 if side == 1 else side * (high - entry) / entry * 100
                    for high, low in zip(highs[i + 1 : i + 25], lows[i + 1 : i + 25])
                ]
            )
            first_touch = "NEITHER"
            first_bar = None
            for n, (high, low) in enumerate(zip(highs[i + 1 : i + 25], lows[i + 1 : i + 25]), 1):
                hit_sl = low <= stop if side == 1 else high >= stop
                hit_tp = high >= tp1 if side == 1 else low <= tp1
                if hit_sl or hit_tp:
                    first_touch = (
                        "AMBIGUOUS_INTRABAR" if hit_sl and hit_tp else "SL_FIRST" if hit_sl else "TP1_FIRST"
                    )
                    first_bar = n
                    break
            records.append(
                {
                    "signal_index": i,
                    "direction": s.direction.value,
                    "mfe_pct_24bar": float(max(0, favorable.max())),
                    "mae_pct_24bar": float(min(0, adverse.min())),
                    "time_to_mfe_bars": int(favorable.argmax() + 1),
                    "time_to_mae_bars": int(adverse.argmin() + 1),
                    "first_touch": first_touch,
                    "first_touch_bar": first_bar,
                    "sl_first_then_tp1_in_24bar": first_touch == "SL_FIRST"
                    and bool(favorable.max() >= (tp1 - entry) * side / entry * 100),
                }
            )
    return records, skipped


def excursion_summary(records, skipped):
    return {
        "eligible_signals_full_horizon": len(records),
        "gap_or_rr_skipped": skipped,
        "first_touch_counts": dict(Counter(x["first_touch"] for x in records)),
        "mfe_pct_median": st.median(x["mfe_pct_24bar"] for x in records) if records else None,
        "mae_pct_median": st.median(x["mae_pct_24bar"] for x in records) if records else None,
        "time_to_mfe_bars_median": st.median(x["time_to_mfe_bars"] for x in records) if records else None,
        "time_to_mae_bars_median": st.median(x["time_to_mae_bars"] for x in records) if records else None,
        "sl_first_then_later_tp1_in_24bar": sum(x["sl_first_then_tp1_in_24bar"] for x in records),
    }


def candidate_summary(name, series_results, base_trades, double_trades, zero_trades, alt_summary):
    bycost = {
        k: pooled(v) for k, v in [("zero", zero_trades), ("base", base_trades), ("double", double_trades)]
    }
    base = bycost["base"]
    double = bycost["double"]
    bysymbol = defaultdict(list)
    bydirection = defaultdict(list)
    bytf = defaultdict(list)
    byfold = defaultdict(list)
    for t in base_trades:
        bysymbol[t["symbol"]].append(t)
        bydirection[t["direction"]].append(t)
        bytf[t["timeframe"]].append(t)
        byfold[t["fold"]].append(t)
    byseries = {(x["symbol"], x["timeframe"]): x for x in series_results}
    baseline_items = [x for x in old["results"] if (x["symbol"], x["timeframe"]) in byseries]
    baseline_sum = sum(x["aggregate"]["paper_proxy:base"]["net_pnl"] for x in baseline_items)
    baseline_dd = st.median(x["aggregate"]["paper_proxy:base"]["max_drawdown"] for x in baseline_items)
    candidate_dd = st.median(x["costs"]["base"]["max_drawdown"] for x in series_results)
    best_symbol = max(bysymbol, key=lambda s: sum(t["pnl"] for t in bysymbol[s])) if bysymbol else None
    best_trade = max(base_trades, key=lambda x: x["pnl"]) if base_trades else None
    symbols_ge10 = sum(len(v) >= 10 for v in bysymbol.values())
    series_positive = sum(x["costs"]["base"]["net_pnl"] > 0 for x in series_results)
    folds_positive = sum(sum(t["pnl"] for t in byfold.get(i, [])) > 0 for i in range(1, 6))
    directions = {k: pooled(v) for k, v in bydirection.items()}
    base_good = (
        base["net_pnl_usd"] > 0
        and base["profit_factor"] is not None
        and base["profit_factor"] >= 1.10
        and base["expectancy_usd"] > 0
        and base["net_pnl_usd"] > baseline_sum
    )
    checks = {
        "sample": base["trades"] >= 100 and symbols_ge10 >= 5,
        "base": base_good,
        "double": double["net_pnl_usd"] >= 0
        and double["profit_factor"] is not None
        and double["profit_factor"] >= 1,
        "folds": folds_positive >= 3,
        "symbols": series_positive >= math.ceil(len(series_results) / 2)
        and best_symbol is not None
        and base["net_pnl_usd"] - sum(t["pnl"] for t in bysymbol[best_symbol]) > 0,
        "directions": all(
            k in directions and directions[k]["trades"] >= 30 and directions[k]["net_pnl_usd"] >= 0
            for k in ("LONG", "SHORT")
        ),
        "drawdown": candidate_dd <= baseline_dd,
        "parameter_plateau": all(
            alt_summary[str(cap)]["base"]["net_pnl_usd"] >= 0
            and alt_summary[str(cap)]["base"]["profit_factor"] is not None
            and alt_summary[str(cap)]["base"]["profit_factor"] >= 1
            for cap in (0.75, 1.25)
        ),
    }
    zero_avg = bycost["zero"]["expectancy_usd"]
    assumed_cost = 3.0
    return {
        "costs": bycost,
        "baseline_same_series_net_usd": baseline_sum,
        "by_symbol": {k: pooled(v) for k, v in bysymbol.items()},
        "by_direction": directions,
        "by_timeframe": {k: pooled(v) for k, v in bytf.items()},
        "by_fold": {str(i): pooled(byfold.get(i, [])) for i in range(1, 6)},
        "sensitivity": {
            "without_best_symbol_usd": base["net_pnl_usd"] - sum(t["pnl"] for t in bysymbol[best_symbol])
            if best_symbol
            else None,
            "best_symbol": best_symbol,
            "without_best_trade_usd": base["net_pnl_usd"] - best_trade["pnl"] if best_trade else None,
            "best_trade_usd": best_trade["pnl"] if best_trade else None,
            "zero_gross_expectancy_over_assumed_roundtrip_3usd_cost": zero_avg / assumed_cost
            if zero_avg is not None
            else None,
            "parameter_caps": alt_summary,
        },
        "consistency": {
            "positive_series_base": series_positive,
            "eligible_series": len(series_results),
            "positive_folds_base": folds_positive,
            "symbols_with_at_least_10_trades": symbols_ge10,
            "median_series_max_dd_base_pct": candidate_dd,
            "baseline_median_series_max_dd_base_pct": baseline_dd,
        },
        "pass_checks": checks,
        "passes_all": all(checks.values()),
    }


def main():
    if protocol["results"] is not None:
        raise ValueError("Research report already evaluated; rerun requires a fresh frozen protocol")
    series_data = {}
    results = {}
    csvrows = []
    for item in old["results"]:
        df, features, cache = read_series(item)
        series_data[(item["symbol"], item["timeframe"])] = (df, features, cache, item)
    print("DATA_VERIFIED", len(series_data), "series", flush=True)
    for name in protocol["candidates"]:
        all_series = []
        inventory = {cost: [] for cost in ("zero", "base", "double")}
        alt_by_cap = {str(cap): {"base_trades": []} for cap in (0.75, 1.25)}
        for symbol in protocol["dataset"]["symbols"]:
            for tf in ("1h",) if name == "C_4h_regime_1h_pullback" else ("1h", "4h"):
                df, features, _, item = series_data[(symbol, tf)]
                context = None
                if name == "C_4h_regime_1h_pullback":
                    d4, f4, _, _ = series_data[(symbol, "4h")]
                    context = context_lookup(df, d4, f4)
                signals = candidate_signals(name, df, features, symbol, tf, 1.0, context)
                series_result = {
                    "symbol": symbol,
                    "timeframe": tf,
                    "formed_signals": len(signals),
                    "costs": {},
                }
                for cost in ("zero", "base", "double"):
                    stats, trades = run_folds(df, signals, item, cost, 1.0)
                    series_result["costs"][cost] = stats
                    inventory[cost].extend(trades)
                    for fold in stats["folds"]:
                        csvrows.append(
                            {
                                "candidate": name,
                                "symbol": symbol,
                                "timeframe": tf,
                                "chase_cap_atr": 1.0,
                                "cost": cost,
                                **fold,
                            }
                        )
                exc, skipped = excursion(df, signals, item["folds"])
                series_result["forward_excursion"] = excursion_summary(exc, skipped)
                series_result["entry_timing"] = {"not_computed_from_outcomes": True}
                all_series.append(series_result)
                for cap in (0.75, 1.25):
                    alt_signals = candidate_signals(name, df, features, symbol, tf, cap, context)
                    alt_stats, alt_trades = run_folds(df, alt_signals, item, "base", cap)
                    alt_by_cap[str(cap)]["base_trades"].extend(alt_trades)
                    for fold in alt_stats["folds"]:
                        csvrows.append(
                            {
                                "candidate": name,
                                "symbol": symbol,
                                "timeframe": tf,
                                "chase_cap_atr": cap,
                                "cost": "base",
                                **fold,
                            }
                        )
                print(
                    name,
                    symbol,
                    tf,
                    "signals",
                    len(signals),
                    "base_trades",
                    series_result["costs"]["base"]["total_trades"],
                    flush=True,
                )
        alt_summary = {
            str(cap): {"base": pooled(alt_by_cap[str(cap)]["base_trades"])} for cap in (0.75, 1.25)
        }
        alt_summary["1.0"] = {"base": pooled(inventory["base"])}
        summary = candidate_summary(
            name, all_series, inventory["base"], inventory["double"], inventory["zero"], alt_summary
        )
        results[name] = {
            "summary": summary,
            "series": all_series,
            "base_trade_inventory": [
                {
                    k: t[k]
                    for k in (
                        "symbol",
                        "timeframe",
                        "entry_time",
                        "exit_time",
                        "direction",
                        "pnl",
                        "profit",
                        "fold",
                        "signal_index",
                        "entry_notional_usd",
                    )
                }
                for t in inventory["base"]
            ],
        }
        print(
            "SUMMARY",
            name,
            summary["costs"]["base"]["trades"],
            round(summary["costs"]["base"]["net_pnl_usd"], 2),
            summary["pass_checks"],
            flush=True,
        )
    protocol["state"] = "EVALUATED_OFFLINE"
    protocol["results"] = results
    protocol["winner"] = (
        "NO CANDIDATE PASSES"
        if not any(x["summary"]["passes_all"] for x in results.values())
        else next(k for k, v in results.items() if v["summary"]["passes_all"])
    )
    for candidate in protocol["results"].values():
        checks = candidate["summary"]["pass_checks"]
        candidate["summary"]["pass_checks"] = {key: bool(value) for key, value in checks.items()}
        candidate["summary"]["passes_all"] = all(candidate["summary"]["pass_checks"].values())
        for series in candidate["series"]:
            for metrics in series["costs"].values():
                metrics["breakeven_trades"] = int(metrics["breakeven_trades"])
    OUTPUT_JSON.write_text(
        json.dumps(protocol, ensure_ascii=False, indent=2, allow_nan=False, default=str) + "\n"
    )
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(csvrows[0]))
        writer.writeheader()
        writer.writerows(csvrows)
    print("WRITTEN", OUTPUT_JSON, OUTPUT_CSV, "winner", protocol["winner"], flush=True)


if __name__ == "__main__":
    main()
