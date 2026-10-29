"""Offline event-distribution research. Reads archived OHLCV; writes reports only.

Run ``python -B reports/market_edge_discovery.py --freeze`` before evaluation.
Then run ``python -B reports/market_edge_discovery.py --evaluate``. No network,
SQLite, exchange, Telegram, or AI client is imported by this script.
"""

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
BASELINE = REPORTS / "WALK_FORWARD_RESULTS.json"
PROTOCOL = REPORTS / "MARKET_EDGE_DISCOVERY.json"
EVENTS_CSV = REPORTS / "MARKET_EDGE_EVENTS.csv"
MARKDOWN = REPORTS / "MARKET_EDGE_DISCOVERY.md"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "SHIBUSDT", "PEPEUSDT")
HORIZONS = (1, 2, 3, 6, 12, 24, 48)
SEED = 20261026
NA = float("nan")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_items():
    baseline = json.loads(BASELINE.read_text())
    return baseline, baseline["results"]


def verify_csv(item):
    path = ROOT / item["data"]["file"]
    expected = item["data"]["sha256"]
    if digest(path) != expected:
        raise ValueError(f"OHLCV SHA mismatch for {path.name}")
    df = pd.read_csv(path, float_precision="round_trip")
    if list(df.columns) != ["time", "close_time", "open", "high", "low", "close", "volume"]:
        raise ValueError(f"Unexpected columns: {path.name}")
    for col in ("time", "close_time"):
        df[col] = pd.to_datetime(df[col], utc=True)
    if len(df) != item["data"]["rows"] or df.time.isna().any() or df.close_time.isna().any():
        raise ValueError(f"Rows/timestamps invalid: {path.name}")
    duration = pd.Timedelta(hours=1 if item["timeframe"] == "1h" else 4)
    missing = int((df.time.diff().iloc[1:] != duration).sum())
    duplicates = int(df.time.duplicated().sum())
    wrong_close = int((df.close_time != df.time + duration - pd.Timedelta(milliseconds=1)).sum())
    prices = df[["open", "high", "low", "close", "volume"]].to_numpy(dtype=float)
    invalid_price = int((~np.isfinite(prices)).any(axis=1).sum())
    invalid_ohlc = int(
        (
            (df.high < df[["open", "close", "low"]].max(axis=1))
            | (df.low > df[["open", "close", "high"]].min(axis=1))
            | (df.low <= 0)
            | (df.volume < 0)
        ).sum()
    )
    if missing or duplicates or wrong_close or invalid_price or invalid_ohlc:
        raise ValueError(f"OHLCV integrity failure: {path.name}")
    return df, {
        "symbol": item["symbol"],
        "timeframe": item["timeframe"],
        "file": item["data"]["file"],
        "sha256": expected,
        "rows": len(df),
        "first_open_utc": str(df.time.iloc[0]),
        "last_close_utc": str(df.close_time.iloc[-1]),
        "missing_internal": missing,
        "duplicates": duplicates,
        "wrong_close": wrong_close,
        "invalid_price": invalid_price,
        "invalid_ohlc": invalid_ohlc,
    }


def freeze():
    if PROTOCOL.exists():
        raise FileExistsError("Frozen protocol already exists; never overwrite it to refit results")
    baseline, items = source_items()
    integrity = [verify_csv(item)[1] for item in items]
    if len(items) != 16 or {item["symbol"] for item in items} != set(SYMBOLS):
        raise ValueError("Unexpected historical universe")
    folds = items[0]["folds"]
    if any(item["folds"] != folds for item in items):
        raise ValueError("Fold boundaries differ across series")
    protocol = {
        "state": "FROZEN_BEFORE_EVENT_RESULTS",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_only": True,
        "input_sha256": {
            "walk_forward_results": digest(BASELINE),
            "walk_forward_audit": digest(REPORTS / "WALK_FORWARD_AUDIT.md"),
            "prospective_32_audit": digest(REPORTS / "PROSPECTIVE_32_TRADE_AUDIT.json"),
            "technical_v2_research": digest(REPORTS / "TECHNICAL_V2_RESEARCH.json"),
        },
        "dataset": {
            "source": "https://api.binance.com/api/v3/klines (archived CSV; no live fetch)",
            "period": "2024-01-01 <= open < 2026-01-01 UTC, plus 120-candle warmup",
            "timezone": "UTC",
            "candle_semantics": "event at closed candle; next-open hypothetical entry",
            "symbols": list(SYMBOLS),
            "timeframes": ["1h", "4h"],
            "integrity": integrity,
            "folds": folds,
            "discovery_folds": [1, 2, 3],
            "validation_folds": [4, 5],
            "validation_warning": "Internal chronological holdout, not pristine: earlier research reviewed these historical windows.",
        },
        "event_definitions": {
            "breakout_N": "close strictly exceeds previous N-bar high (LONG) or is below previous N-bar low (SHORT); N=12,24,48",
            "pullback_depth": "prior 24-bar signed move >=2 ATR; opposite-color previous candle; prior close 0.5-1/1-2/2-3 ATR from prior 12-bar extreme; current close through previous candle high/low in trend direction",
            "range_rejection_24": "prior 24-bar efficiency <=0.15; current wick reaches outer 20% of previous 24-bar range; current close returns to inner 70% and body points toward middle",
            "compression_90_p20": "ATR14/close below its previous 90-bar 20th percentile, first compressed candle; orientation is sign of past 24-bar move, not a directional prediction",
            "large_move_5": "absolute 5-bar move / ATR14: normal <1, extended 2-3, high >=3; orientation is prior move direction",
            "failed_breakout_24": "current high pierces previous 24-bar high and closes back below, or low pierces previous low and closes back above; direction opposes failed extension; dual-side bars excluded",
            "volume_condition": "volume / median(previous 20 volumes): normal <1.5, elevated 1.5-3, extreme >=3; applied to breakout24, failed24 and high 5-bar move",
            "volatility_condition": "ATR14/close versus previous 90-bar 33rd/67th percentiles: low/normal/high; applied to breakout24 and failed24",
            "market_regime": "24-bar efficiency ratio of net move to sum of absolute moves: trend >=0.35, range <=0.15, uncertain otherwise; applied to breakout24 and failed24",
            "btc_context": "for altcoin breakout24, align BTC same-timeframe closed candle exactly; BTC 24-bar direction aligned/opposed, high volatility, >=2 ATR 5-bar move, trend/range efficiency, each conditioning separately",
            "cross_section": "at each synchronous 8-symbol close, rank 24-bar return / ATR14; top2, middle4, bottom2; test continuation and reversal orientations separately",
        },
        "horizons_bars": list(HORIZONS),
        "forward_measure": "signed next-open to close at event index+h; high/low path indices event+1..event+h; horizon must end inside the same archived test fold",
        "control": "same symbol, timeframe, calendar month, causal ATR/price volatility tertile and causal 24-bar momentum sign; all eligible bars in stratum, including events (conservative dilution); no future data in event/control matching attributes",
        "costs": {
            "zero_pct": 0.0,
            "base_pct": 0.3,
            "double_pct": 0.6,
            "basis": "fee/slippage each side 0.10%/0.05% base; doubled 0.20%/0.10%; round-trip approximation, no funding/spread/impact",
        },
        "uncertainty": {
            "method": "calendar-week cluster bootstrap over all symbols/timeframes, with replacement; 300 draws for top five 24-bar effects",
            "seed": SEED,
            "quantiles": [0.025, 0.975],
        },
        "sample_labels": {"sufficient_exploratory": 200, "small": 50, "insufficient": 0},
        "promotion_criteria_frozen": {
            "horizon": 24,
            "discovery_min_n": 200,
            "validation_min_n": 100,
            "validation_raw_mean_gt_base_cost_pct": 0.3,
            "validation_excess_gt_zero_pct": 0.0,
            "validation_base_net_gt_zero_pct": 0.0,
            "positive_validation_folds": "2/2",
            "positive_validation_symbols": "at least 5 of 8, with >=10 observations each",
            "leave_one_symbol_out": "all 8 validation raw net-after-base means positive",
            "neighboring_definition": "same family broad neighboring definition has positive validation net-after-base; where no neighbor exists, event cannot be ROBUST",
            "bootstrap": "validation week-cluster lower 95% bound of raw mean after base costs >0",
            "multiple_testing": "screen discovery only; validation promotion is conjunction of all criteria, not smallest p-value",
            "robust_status": "ROBUST requires a truly untouched future market interval as well; this historical internal holdout can at most yield PROMISING",
        },
        "screening_frozen": {
            "selection": "rank 24-bar discovery evidence only, then inspect validation; choose top five with at most one per broad family before filling remaining slots",
            "score": "min(1,N/200)+min(1,max(0,discovery base-net mean)/0.5)+min(1,max(0,discovery matched-control excess)/0.5)+fraction positive discovery folds+fraction positive discovery symbols+indicator(median after base >0)",
            "family_groups": [
                "breakout",
                "pullback",
                "range",
                "compression",
                "large_move",
                "failed_breakout",
                "cross_section",
            ],
            "neighboring_definitions": "breakout 12/24/48; pullback shallow/medium/deep; large move normal/extended/high; conditioning buckets are separate exploratory overlays, not independent confirmations",
        },
        "results": None,
    }
    PROTOCOL.write_text(json.dumps(protocol, ensure_ascii=False, indent=2) + "\n")
    print(f"FROZEN {PROTOCOL}; 16 series; {sum(x['rows'] for x in integrity)} candles")


def as_array(series):
    return series.to_numpy(dtype=float)


def trailing_features(df):
    o, h, lo, c, v = (df[x].astype(float) for x in ("open", "high", "low", "close", "volume"))
    prev_c = c.shift(1)
    tr = pd.concat(((h - lo), (h - prev_c).abs(), (lo - prev_c).abs()), axis=1).max(axis=1)
    atr = tr.rolling(14, min_periods=14).mean()
    ar = atr / c
    q20 = ar.shift(1).rolling(90, min_periods=90).quantile(0.20)
    q33 = ar.shift(1).rolling(90, min_periods=90).quantile(1 / 3)
    q67 = ar.shift(1).rolling(90, min_periods=90).quantile(2 / 3)
    vol_regime = np.select([ar <= q33, ar >= q67], ["low", "high"], default="normal")
    volume_ratio = v / v.shift(1).rolling(20, min_periods=20).median().replace(0, np.nan)
    move5 = (c - c.shift(5)) / atr
    move24 = (c - c.shift(24)) / atr
    variation = c.diff().abs().rolling(24, min_periods=24).sum()
    efficiency = (c - c.shift(24)).abs() / variation.replace(0, np.nan)
    prior_eff = (c.shift(1) - c.shift(25)).abs() / variation.shift(1).replace(0, np.nan)
    regime = np.select([efficiency >= 0.35, efficiency <= 0.15], ["trend", "range"], default="uncertain")
    out = pd.DataFrame(
        {
            "open": o,
            "high": h,
            "low": lo,
            "close": c,
            "volume": v,
            "atr": atr,
            "atr_fraction": ar,
            "vol_regime": vol_regime,
            "compression": ar <= q20,
            "volume_ratio": volume_ratio,
            "move5": move5,
            "move24": move24,
            "momentum_sign": np.sign(c - c.shift(24)).fillna(0).astype(int),
            "efficiency": efficiency,
            "prior_efficiency": prior_eff,
            "market_regime": regime,
        }
    )
    for n in (12, 24, 48):
        out[f"prior_high_{n}"] = h.shift(1).rolling(n, min_periods=n).max()
        out[f"prior_low_{n}"] = lo.shift(1).rolling(n, min_periods=n).min()
    return out


def sides(features):
    """Only trailing/current closed-bar values; 0 means no event."""
    f = features
    c, o, h, lo, atr = (f[x] for x in ("close", "open", "high", "low", "atr"))
    out = {}

    def directional(name, long_mask, short_mask):
        out[name] = np.select([long_mask & ~short_mask, short_mask & ~long_mask], [1, -1], 0).astype(np.int8)

    for n in (12, 24, 48):
        directional(f"breakout_{n}", c > f[f"prior_high_{n}"], c < f[f"prior_low_{n}"])
    trend = f.move24
    depth_long = (f.prior_high_12 - c.shift(1)) / atr
    depth_short = (c.shift(1) - f.prior_low_12) / atr
    prior_down = c.shift(1) < o.shift(1)
    prior_up = c.shift(1) > o.shift(1)
    resume_long = (trend >= 2) & prior_down & (c > h.shift(1))
    resume_short = (trend <= -2) & prior_up & (c < lo.shift(1))
    for name, minimum, maximum in (("shallow", 0.5, 1), ("medium", 1, 2), ("deep", 2, 3)):
        directional(
            f"pullback_{name}",
            resume_long & (depth_long >= minimum) & (depth_long < maximum),
            resume_short & (depth_short >= minimum) & (depth_short < maximum),
        )
    span = (f.prior_high_24 - f.prior_low_24).replace(0, np.nan)
    quiet = f.prior_efficiency <= 0.15
    directional(
        "range_rejection_24",
        quiet & (lo <= f.prior_low_24 + 0.2 * span) & (c >= f.prior_low_24 + 0.3 * span) & (c > o),
        quiet & (h >= f.prior_high_24 - 0.2 * span) & (c <= f.prior_high_24 - 0.3 * span) & (c < o),
    )
    compressed = f.compression & ~f.compression.shift(1, fill_value=False)
    directional("compression_90_p20", compressed & (f.momentum_sign > 0), compressed & (f.momentum_sign < 0))
    magnitude = f.move5.abs()
    for name, mask in (
        ("normal", magnitude < 1),
        ("extended", (magnitude >= 2) & (magnitude < 3)),
        ("high", magnitude >= 3),
    ):
        directional(f"large_move_{name}", mask & (f.move5 > 0), mask & (f.move5 < 0))
    directional(
        "failed_breakout_24",
        (lo < f.prior_low_24) & (c > f.prior_low_24) & ~(h > f.prior_high_24),
        (h > f.prior_high_24) & (c < f.prior_high_24) & ~(lo < f.prior_low_24),
    )
    volume_buckets = {
        "normal": f.volume_ratio < 1.5,
        "elevated": (f.volume_ratio >= 1.5) & (f.volume_ratio < 3),
        "extreme": f.volume_ratio >= 3,
    }
    for parent in ("breakout_24", "failed_breakout_24", "large_move_high"):
        for label, mask in volume_buckets.items():
            out[f"{parent}_volume_{label}"] = np.where(mask, out[parent], 0).astype(np.int8)
    for parent in ("breakout_24", "failed_breakout_24"):
        for label in ("low", "normal", "high"):
            out[f"{parent}_volatility_{label}"] = np.where(f.vol_regime == label, out[parent], 0).astype(
                np.int8
            )
        for label in ("trend", "range", "uncertain"):
            out[f"{parent}_regime_{label}"] = np.where(f.market_regime == label, out[parent], 0).astype(
                np.int8
            )
    return out


def load_research_data(protocol):
    baseline, items = source_items()
    if digest(BASELINE) != protocol["input_sha256"]["walk_forward_results"]:
        raise ValueError("Baseline report changed since protocol freeze")
    for label, filename in (
        ("walk_forward_audit", "WALK_FORWARD_AUDIT.md"),
        ("prospective_32_audit", "PROSPECTIVE_32_TRADE_AUDIT.json"),
        ("technical_v2_research", "TECHNICAL_V2_RESEARCH.json"),
    ):
        if digest(REPORTS / filename) != protocol["input_sha256"][label]:
            raise ValueError(f"Research source changed since protocol freeze: {filename}")
    data = {}
    for item in items:
        df, integrity = verify_csv(item)
        key = (item["symbol"], item["timeframe"])
        if integrity != next(
            x for x in protocol["dataset"]["integrity"] if (x["symbol"], x["timeframe"]) == key
        ):
            raise ValueError(f"Integrity metadata changed for {key}")
        f = trailing_features(df)
        fold = np.zeros(len(df), dtype=np.int8)
        for number, window in enumerate(item["folds"], 1):
            inside = (df.time >= pd.Timestamp(window["test_start"])) & (
                df.time < pd.Timestamp(window["test_end"])
            )
            fold[inside.to_numpy()] = number
        data[key] = {"df": df, "f": f, "fold": fold, "events": sides(f)}
    # Rank only pairs known and closed at the same timestamp. No future universe membership.
    for tf in ("1h", "4h"):
        momentum = pd.concat(
            {
                symbol: data[(symbol, tf)]["f"].set_axis(data[(symbol, tf)]["df"].close_time)["move24"]
                for symbol in SYMBOLS
            },
            axis=1,
        ).dropna(how="any")
        ranks = momentum.rank(axis=1, ascending=False, method="first")
        for symbol in SYMBOLS:
            entry = data[(symbol, tf)]
            f = entry["f"]
            rank = ranks[symbol].reindex(entry["df"].close_time).to_numpy(dtype=float)
            sign = np.sign(f.move24.fillna(0).to_numpy(dtype=float)).astype(np.int8)
            events = entry["events"]
            events["cross_section_top2_continue"] = np.where(rank <= 2, 1, 0).astype(np.int8)
            events["cross_section_bottom2_continue"] = np.where(rank >= 7, -1, 0).astype(np.int8)
            events["cross_section_middle4_continue"] = np.where((rank > 2) & (rank < 7), sign, 0).astype(
                np.int8
            )
            events["cross_section_top2_revert"] = -events["cross_section_top2_continue"]
            events["cross_section_bottom2_revert"] = -events["cross_section_bottom2_continue"]
    for tf in ("1h", "4h"):
        btc = data[("BTCUSDT", tf)]
        bf = btc["f"].set_axis(btc["df"].close_time)
        for symbol in SYMBOLS[1:]:
            entry = data[(symbol, tf)]
            aligned = bf.reindex(entry["df"].close_time)
            if not aligned.index.equals(pd.Index(entry["df"].close_time)):
                raise ValueError("BTC context alignment failed")
            side = entry["events"]["breakout_24"]
            conditions = {
                "aligned": np.sign(aligned.move24.to_numpy(dtype=float)) == side,
                "opposed": np.sign(aligned.move24.to_numpy(dtype=float)) == -side,
                "high_vol": aligned.vol_regime.to_numpy() == "high",
                "large_move": aligned.move5.abs().to_numpy(dtype=float) >= 2,
                "trend": aligned.market_regime.to_numpy() == "trend",
                "range": aligned.market_regime.to_numpy() == "range",
            }
            for label, condition in conditions.items():
                entry["events"][f"breakout_24_btc_{label}"] = np.where(
                    condition & (side != 0), side, 0
                ).astype(np.int8)
    # BTC-context events are alt-only; the evaluation loop skips them for BTC.
    return data, baseline


def forward_arrays(entry, horizon):
    f, df = entry["f"], entry["df"]
    length = len(df)
    highs = sliding_window_view(f.high.to_numpy(dtype=float)[1:], horizon)
    lows = sliding_window_view(f.low.to_numpy(dtype=float)[1:], horizon)
    open_next = f.open.to_numpy(dtype=float)[1 : length - horizon + 1]
    exit_close = f.close.to_numpy(dtype=float)[horizon:]
    atr = f.atr.to_numpy(dtype=float)[: length - horizon]
    raw = (exit_close / open_next - 1) * 100
    max_h = highs.max(axis=1)
    min_l = lows.min(axis=1)
    mfe_long = (max_h / open_next - 1) * 100
    mfe_short = (1 - min_l / open_next) * 100
    mae_long = (min_l / open_next - 1) * 100
    mae_short = (1 - max_h / open_next) * 100
    fold = entry["fold"][: length - horizon]
    valid = (fold > 0) & (fold == entry["fold"][horizon:]) & np.isfinite(atr) & (atr > 0)
    features = f.iloc[: length - horizon]
    month = df.time.iloc[: length - horizon].dt.strftime("%Y-%m").to_numpy()
    # Control is a within-series, within-month, causal-regime reference distribution.
    controls = pd.DataFrame(
        {
            "fold": fold,
            "month": month,
            "vol": features.vol_regime.to_numpy(),
            "mom": features.momentum_sign.to_numpy(),
            "raw": raw,
            "absolute": np.abs(raw),
            "valid": valid,
        }
    )
    eligible = controls.loc[controls.valid].copy()
    keys = ["month", "vol", "mom"]
    means = eligible.groupby(keys)[["raw", "absolute"]].transform("mean")
    counts = eligible.groupby(keys).raw.transform("size")
    fallback = eligible.groupby(["month", "vol"])[["raw", "absolute"]].transform("mean")
    means = means.where(counts >= 20, fallback)
    control_raw = np.full(len(raw), NA)
    control_abs = np.full(len(raw), NA)
    control_raw[valid] = means.raw.to_numpy(dtype=float)
    control_abs[valid] = means.absolute.to_numpy(dtype=float)
    result = {
        "valid": valid,
        "fold": fold,
        "raw": raw,
        "open_next": open_next,
        "mfe_long": mfe_long,
        "mfe_short": mfe_short,
        "mae_long": mae_long,
        "mae_short": mae_short,
        "control_raw": control_raw,
        "control_abs": control_abs,
        "atr": atr,
        "month": month,
        "week": df.time.iloc[: length - horizon].dt.strftime("%G-W%V").to_numpy(),
        "time": df.time.iloc[: length - horizon].to_numpy(),
    }
    if horizon == 24:
        result["high_windows"] = highs
        result["low_windows"] = lows
        result["time_mfe_long"] = highs.argmax(axis=1) + 1
        result["time_mfe_short"] = lows.argmin(axis=1) + 1
        result["time_mae_long"] = lows.argmin(axis=1) + 1
        result["time_mae_short"] = highs.argmax(axis=1) + 1
    return result


def observation_frame(name, symbol, tf, side_full, future, horizon):
    length = len(future["raw"])
    side = side_full[:length]
    selected = np.flatnonzero(future["valid"] & (side != 0) & np.isfinite(future["control_raw"]))
    if not len(selected):
        return None
    sign = side[selected]
    long = sign == 1
    entry = future["open_next"][selected]
    atr = future["atr"][selected]
    mfe = np.where(long, future["mfe_long"][selected], future["mfe_short"][selected])
    mae = np.where(long, future["mae_long"][selected], future["mae_short"][selected])
    signed = sign * future["raw"][selected]
    control = sign * future["control_raw"][selected]
    fold = future["fold"][selected]
    frame = pd.DataFrame(
        {
            "event": name,
            "horizon": horizon,
            "symbol": symbol,
            "timeframe": tf,
            "fold": fold,
            "split": np.where(fold <= 3, "discovery", "validation"),
            "side": np.where(long, "LONG", "SHORT"),
            "time": future["time"][selected],
            "week": future["week"][selected],
            "month": future["month"][selected],
            "return_pct": signed,
            "excess_pct": signed - control,
            "absolute_move_atr": np.abs(future["raw"][selected]) * entry / (100 * atr),
            "control_absolute_pct": future["control_abs"][selected],
            "mfe_pct": mfe,
            "mae_pct": mae,
            "atr_pct": atr / entry * 100,
        }
    )
    if horizon == 24:
        high = future["high_windows"][selected]
        low = future["low_windows"][selected]
        frame["time_to_mfe"] = np.where(
            long, future["time_mfe_long"][selected], future["time_mfe_short"][selected]
        )
        frame["time_to_mae"] = np.where(
            long, future["time_mae_long"][selected], future["time_mae_short"][selected]
        )
        for threshold in (0.5, 1.0, 1.5, 2.0):
            favorable = np.where(
                long[:, None],
                high >= entry[:, None] + threshold * atr[:, None],
                low <= entry[:, None] - threshold * atr[:, None],
            )
            adverse = np.where(
                long[:, None],
                low <= entry[:, None] - threshold * atr[:, None],
                high >= entry[:, None] + threshold * atr[:, None],
            )
            frame[f"favor_{threshold}_atr"] = favorable.any(axis=1)
            frame[f"adverse_{threshold}_atr"] = adverse.any(axis=1)
            if threshold in (0.5, 1.0):
                frame[f"time_favor_{threshold}_atr"] = np.where(
                    favorable.any(axis=1), favorable.argmax(axis=1) + 1, NA
                )
                frame[f"time_adverse_{threshold}_atr"] = np.where(
                    adverse.any(axis=1), adverse.argmax(axis=1) + 1, NA
                )
    return frame


def finite(value):
    return float(value) if pd.notna(value) and math.isfinite(float(value)) else None


def metrics(frame):
    n = len(frame)
    if not n:
        return {"n": 0}
    returns = frame.return_pct.to_numpy(dtype=float)
    mfe, mae = frame.mfe_pct.to_numpy(dtype=float), frame.mae_pct.to_numpy(dtype=float)
    excess = frame.excess_pct.to_numpy(dtype=float)
    result = {
        "n": n,
        "mean_return_pct": float(np.mean(returns)),
        "median_return_pct": float(np.median(returns)),
        "std_return_pct": float(np.std(returns, ddof=1)) if n > 1 else None,
        "positive_probability": float(np.mean(returns > 0)),
        "return_p05_pct": float(np.quantile(returns, 0.05)),
        "return_p10_pct": float(np.quantile(returns, 0.10)),
        "return_p25_pct": float(np.quantile(returns, 0.25)),
        "return_p75_pct": float(np.quantile(returns, 0.75)),
        "return_p90_pct": float(np.quantile(returns, 0.90)),
        "mean_excess_vs_matched_control_pct": float(np.mean(excess)),
        "median_excess_vs_matched_control_pct": float(np.median(excess)),
        "mean_after_base_cost_pct": float(np.mean(returns) - 0.3),
        "mean_after_double_cost_pct": float(np.mean(returns) - 0.6),
        "median_after_base_cost_pct": float(np.median(returns) - 0.3),
        "cost_hurdle_ratio_base": float(np.mean(returns) / 0.3),
        "mean_mfe_pct": float(np.mean(mfe)),
        "median_mfe_pct": float(np.median(mfe)),
        "mfe_p10_pct": float(np.quantile(mfe, 0.10)),
        "mfe_p90_pct": float(np.quantile(mfe, 0.90)),
        "mean_mae_pct": float(np.mean(mae)),
        "median_mae_pct": float(np.median(mae)),
        "mae_p10_pct": float(np.quantile(mae, 0.10)),
        "mae_p90_pct": float(np.quantile(mae, 0.90)),
        "median_mfe_to_abs_mae": finite(np.median(mfe) / abs(np.median(mae))) if np.median(mae) else None,
        "mean_absolute_move_atr": float(frame.absolute_move_atr.mean()),
        "prob_absolute_move_ge_1atr": float((frame.absolute_move_atr >= 1).mean()),
        "prob_absolute_move_ge_2atr": float((frame.absolute_move_atr >= 2).mean()),
        "mean_absolute_return_minus_control_pct": float(
            np.mean(np.abs(returns) - frame.control_absolute_pct.to_numpy(dtype=float))
        ),
    }
    if "time_to_mfe" in frame:
        result.update(
            {
                "median_time_to_mfe_bars": float(frame.time_to_mfe.median()),
                "median_time_to_mae_bars": float(frame.time_to_mae.median()),
            }
        )
        for threshold in (0.5, 1.0, 1.5, 2.0):
            result[f"prob_mfe_ge_{threshold}_atr"] = float(frame[f"favor_{threshold}_atr"].mean())
            result[f"prob_mae_ge_{threshold}_atr"] = float(frame[f"adverse_{threshold}_atr"].mean())
            if threshold in (0.5, 1.0):
                result[f"median_time_to_favor_{threshold}_atr"] = finite(
                    frame[f"time_favor_{threshold}_atr"].median()
                )
                result[f"median_time_to_adverse_{threshold}_atr"] = finite(
                    frame[f"time_adverse_{threshold}_atr"].median()
                )
    return result


def group_metrics(frame, event, horizon, rows):
    result = {
        "all": metrics(frame),
        "discovery": metrics(frame.loc[frame.split == "discovery"]),
        "validation": metrics(frame.loc[frame.split == "validation"]),
        "by_fold": {},
        "by_symbol": {},
        "by_timeframe": {},
        "by_timeframe_discovery": {},
        "by_timeframe_validation": {},
        "by_side": {},
        "by_side_discovery": {},
        "by_side_validation": {},
        "by_symbol_discovery": {},
        "by_symbol_validation": {},
    }
    groups = [
        ("all", "all", frame),
        ("split", "discovery", frame.loc[frame.split == "discovery"]),
        ("split", "validation", frame.loc[frame.split == "validation"]),
    ]
    for fold in range(1, 6):
        subset = frame.loc[frame.fold == fold]
        result["by_fold"][str(fold)] = metrics(subset)
        groups.append(("fold", str(fold), subset))
    for symbol in SYMBOLS:
        subset = frame.loc[frame.symbol == symbol]
        result["by_symbol"][symbol] = metrics(subset)
        result["by_symbol_discovery"][symbol] = metrics(subset.loc[subset.split == "discovery"])
        result["by_symbol_validation"][symbol] = metrics(subset.loc[subset.split == "validation"])
        groups.append(("symbol", symbol, subset))
    for tf in ("1h", "4h"):
        subset = frame.loc[frame.timeframe == tf]
        result["by_timeframe"][tf] = metrics(subset)
        result["by_timeframe_discovery"][tf] = metrics(subset.loc[subset.split == "discovery"])
        result["by_timeframe_validation"][tf] = metrics(subset.loc[subset.split == "validation"])
        groups.append(("timeframe", tf, subset))
        groups.append(("validation_timeframe", tf, subset.loc[subset.split == "validation"]))
    for side in ("LONG", "SHORT"):
        subset = frame.loc[frame.side == side]
        result["by_side"][side] = metrics(subset)
        result["by_side_discovery"][side] = metrics(subset.loc[subset.split == "discovery"])
        result["by_side_validation"][side] = metrics(subset.loc[subset.split == "validation"])
        groups.append(("side", side, subset))
        groups.append(("validation_side", side, subset.loc[subset.split == "validation"]))
    for group_type, group, subset in groups:
        rows.append(
            {
                "event": event,
                "horizon_bars": horizon,
                "group_type": group_type,
                "group": group,
                **metrics(subset),
            }
        )
    result["events_per_year_universe"] = len(frame) / (450 / 365.25)
    result["events_per_month_universe"] = len(frame) / (450 / 30.4375)
    result["sample_label"] = (
        "SUFFICIENT_EXPLORATORY" if len(frame) >= 200 else "SMALL" if len(frame) >= 50 else "INSUFFICIENT"
    )
    return result


def family(name):
    if name.startswith("breakout_"):
        return "breakout"
    if name.startswith("pullback_"):
        return "pullback"
    if name.startswith("range_"):
        return "range"
    if name.startswith("compression_"):
        return "compression"
    if name.startswith("large_move_"):
        return "large_move"
    if name.startswith("failed_breakout_"):
        return "failed_breakout"
    return "cross_section"


def discovery_evidence_score(summary):
    d = summary["discovery"]
    if not d["n"]:
        return -1.0
    folds = [summary["by_fold"][str(i)] for i in (1, 2, 3)]
    fold_share = sum(x["n"] >= 10 and x["mean_after_base_cost_pct"] > 0 for x in folds) / 3
    symbols = list(summary["by_symbol_discovery"].values())
    symbol_share = sum(x["n"] >= 10 and x["mean_after_base_cost_pct"] > 0 for x in symbols) / 8
    return (
        min(1, d["n"] / 200)
        + min(1, max(0, d["mean_after_base_cost_pct"]) / 0.5)
        + min(1, max(0, d["mean_excess_vs_matched_control_pct"]) / 0.5)
        + fold_share
        + symbol_share
        + int(d["median_after_base_cost_pct"] > 0)
    )


def select_top_five(results):
    ranked = sorted(
        results,
        key=lambda name: (-results[name]["24"]["discovery_evidence_score"], name),
    )
    selected = []
    seen = set()
    for name in ranked:
        group = family(name)
        if group not in seen:
            selected.append(name)
            seen.add(group)
            if len(selected) == 5:
                return selected, ranked
    for name in ranked:
        if name not in selected:
            selected.append(name)
            if len(selected) == 5:
                break
    return selected, ranked


def cluster_bootstrap(frame, seed):
    if len(frame) < 2:
        return {"weeks": 0, "raw_mean_after_base_ci95": None, "excess_mean_ci95": None}
    clusters = frame.groupby("week").agg(
        n=("return_pct", "size"), raw_sum=("return_pct", "sum"), excess_sum=("excess_pct", "sum")
    )
    weeks = len(clusters)
    if weeks < 3:
        return {"weeks": weeks, "raw_mean_after_base_ci95": None, "excess_mean_ci95": None}
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, weeks, size=(300, weeks))
    n = clusters.n.to_numpy(dtype=float)
    raw = clusters.raw_sum.to_numpy(dtype=float)
    excess = clusters.excess_sum.to_numpy(dtype=float)
    denominator = n[draws].sum(axis=1)
    base_means = raw[draws].sum(axis=1) / denominator - 0.3
    excess_means = excess[draws].sum(axis=1) / denominator
    return {
        "weeks": weeks,
        "raw_mean_after_base_ci95": [float(x) for x in np.quantile(base_means, [0.025, 0.975])],
        "excess_mean_ci95": [float(x) for x in np.quantile(excess_means, [0.025, 0.975])],
    }


def neighbor_names(name, universe):
    mapping = {
        "breakout_12": ["breakout_24"],
        "breakout_24": ["breakout_12", "breakout_48"],
        "breakout_48": ["breakout_24"],
        "pullback_shallow": ["pullback_medium"],
        "pullback_medium": ["pullback_shallow", "pullback_deep"],
        "pullback_deep": ["pullback_medium"],
        "large_move_normal": ["large_move_extended"],
        "large_move_extended": ["large_move_normal", "large_move_high"],
        "large_move_high": ["large_move_extended"],
    }
    return [x for x in mapping.get(name, []) if x in universe]


def promotion(name, results, observations, bootstrap):
    summary = results[name]["24"]
    d, v = summary["discovery"], summary["validation"]
    validation = observations.loc[observations.split == "validation"]
    leave_one_out = {
        symbol: {
            "n": len(subset),
            "mean_after_base_cost_pct": finite(subset.return_pct.mean() - 0.3),
        }
        for symbol in SYMBOLS
        for subset in (validation.loc[validation.symbol != symbol],)
    }
    neighbors = neighbor_names(name, results)
    checks = {
        "discovery_n_ge_200": d["n"] >= 200,
        "validation_n_ge_100": v["n"] >= 100,
        "validation_raw_mean_gt_base_cost": v["n"] > 0 and v["mean_after_base_cost_pct"] > 0,
        "validation_excess_gt_zero": v["n"] > 0 and v["mean_excess_vs_matched_control_pct"] > 0,
        "two_positive_validation_folds": all(
            summary["by_fold"][str(i)]["n"] >= 10
            and summary["by_fold"][str(i)]["mean_after_base_cost_pct"] > 0
            for i in (4, 5)
        ),
        "five_positive_validation_symbols": sum(
            x["n"] >= 10 and x["mean_after_base_cost_pct"] > 0
            for x in summary["by_symbol_validation"].values()
        )
        >= 5,
        "leave_one_symbol_out_positive": all(
            x["n"] > 0 and x["mean_after_base_cost_pct"] > 0 for x in leave_one_out.values()
        ),
        "neighbor_positive_after_base": bool(neighbors)
        and any(
            results[x]["24"]["validation"]["n"] >= 100
            and results[x]["24"]["validation"]["mean_after_base_cost_pct"] > 0
            for x in neighbors
        ),
        "bootstrap_lower_bound_positive": (
            bootstrap["raw_mean_after_base_ci95"] is not None and bootstrap["raw_mean_after_base_ci95"][0] > 0
        ),
    }
    raw = validation.return_pct.to_numpy(dtype=float)
    without_best = float((raw.sum() - raw.max()) / (len(raw) - 1) - 0.3) if len(raw) > 1 else None
    winsorized = float(np.clip(raw, *np.quantile(raw, [0.01, 0.99])).mean() - 0.3) if len(raw) > 1 else None
    return {
        "checks": checks,
        "internal_promotion_pass": all(checks.values()),
        "neighbors": neighbors,
        "leave_one_symbol_out": leave_one_out,
        "without_best_observation_mean_after_base_pct": without_best,
        "winsorized_1pct_mean_after_base_pct": winsorized,
        "bootstrap": bootstrap,
    }


def overlap_matrix(observations):
    sets = {
        name: set(zip(frame.symbol, frame.timeframe, frame.time.astype(str), frame.side))
        for name, frame in observations.items()
    }
    names = sorted(sets)
    matrix = {}
    pairs = []
    for i, left in enumerate(names):
        matrix[left] = {}
        for right in names:
            common = len(sets[left] & sets[right])
            denominator = min(len(sets[left]), len(sets[right]))
            ratio = common / denominator if denominator else None
            matrix[left][right] = {"same_symbol_tf_time_side": common, "fraction_of_smaller": ratio}
            if names.index(right) > i and ratio is not None:
                pairs.append((ratio, common, left, right))
    pairs.sort(reverse=True)

    def as_records(entries):
        return [
            {"left": left, "right": right, "shared": common, "fraction_of_smaller": ratio}
            for ratio, common, left, right in entries
        ]

    cross_family = [pair for pair in pairs if pair[1] >= 50 and family(pair[2]) != family(pair[3])]
    return matrix, as_records(pairs[:25]), as_records(cross_family[:25])


def range_path_diagnostic(data):
    """Descriptive 24-bar boundary touches, not an ordered execution path."""
    records = []
    for (symbol, tf), entry in data.items():
        future = forward_arrays(entry, 24)
        f = entry["f"]
        side = entry["events"]["range_rejection_24"][: len(future["raw"])]
        indexes = np.flatnonzero(future["valid"] & (side != 0))
        if not len(indexes):
            continue
        direction = side[indexes]
        opening = future["open_next"][indexes]
        prior_high = f.prior_high_24.to_numpy(dtype=float)[indexes]
        prior_low = f.prior_low_24.to_numpy(dtype=float)[indexes]
        midpoint = (prior_high + prior_low) / 2
        high = future["high_windows"][indexes].max(axis=1)
        low = future["low_windows"][indexes].min(axis=1)
        nontrivial = np.where(direction == 1, opening < midpoint, opening > midpoint)
        midpoint_touch = np.where(direction == 1, high >= midpoint, low <= midpoint)
        other_boundary = np.where(direction == 1, high >= prior_high, low <= prior_low)
        adverse_rebreak = np.where(direction == 1, low < prior_low, high > prior_high)
        for offset, at in enumerate(indexes):
            records.append(
                {
                    "symbol": symbol,
                    "timeframe": tf,
                    "fold": int(future["fold"][at]),
                    "nontrivial_midpoint": bool(nontrivial[offset]),
                    "midpoint_touch": bool(midpoint_touch[offset]),
                    "other_boundary_touch": bool(other_boundary[offset]),
                    "adverse_rebreak": bool(adverse_rebreak[offset]),
                }
            )
    if not records:
        return {"n": 0}
    frame = pd.DataFrame(records)
    nontrivial = frame.loc[frame.nontrivial_midpoint]
    return {
        "n": len(frame),
        "nontrivial_midpoint_n": len(nontrivial),
        "midpoint_touch_among_nontrivial": float(nontrivial.midpoint_touch.mean())
        if len(nontrivial)
        else None,
        "opposite_boundary_touch": float(frame.other_boundary_touch.mean()),
        "adverse_rebreak": float(frame.adverse_rebreak.mean()),
        "both_midpoint_and_adverse_rebreak": float((frame.midpoint_touch & frame.adverse_rebreak).mean()),
        "note": "Both hits may occur in the same candle or unknown order; this is not TP-before-SL or strategy PnL.",
    }


def fmt(value, digits=3):
    return "—" if value is None else f"{value:+.{digits}f}"


def table_for(report, names):
    lines = [
        "| Event | D N | D gross % | D excess % | V N | V gross % | V excess % | V base-net % | V double-net % | V folds + | V symbols + |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in names:
        if name not in report["events"] or "24" not in report["events"][name]:
            continue
        x = report["events"][name]["24"]
        d, v = x["discovery"], x["validation"]
        fold_n = sum(
            x["by_fold"][str(i)]["n"] >= 10 and x["by_fold"][str(i)]["mean_after_base_cost_pct"] > 0
            for i in (4, 5)
        )
        symbol_n = sum(
            y["n"] >= 10 and y["mean_after_base_cost_pct"] > 0 for y in x["by_symbol_validation"].values()
        )
        lines.append(
            f"| `{name}` | {d['n']} | {fmt(d.get('mean_return_pct'))} | {fmt(d.get('mean_excess_vs_matched_control_pct'))} "
            f"| {v['n']} | {fmt(v.get('mean_return_pct'))} | {fmt(v.get('mean_excess_vs_matched_control_pct'))} "
            f"| {fmt(v.get('mean_after_base_cost_pct'))} | {fmt(v.get('mean_after_double_cost_pct'))} "
            f"| {fold_n}/2 | {symbol_n}/8 |"
        )
    return "\n".join(lines)


def render_markdown(report):
    dataset = report["dataset"]
    top = report["results"]["top_five_discovery_selected"]
    events = report["results"]["events"]
    shadow = events["breakout_24_btc_range"]["24"]
    lines = [
        "# MARKET EDGE DISCOVERY — причинные рыночные события, не стратегия",
        "",
        f"**Вердикт: `{report['results']['verdict']}`.** Это исследование распределений после наблюдаемых событий, "
        "а не торговый план. События/пороги и критерии были записаны в JSON до расчёта outcome. "
        "Предыдущие исследования уже раскрыли часть той же исторической полосы: внутренние folds 4–5 "
        "проверяют хронологическую устойчивость, но не являются полностью нетронутым внешним тестом. "
        "Даже `PROMISING` здесь не означало бы подтверждённую прибыльную стратегию.",
        "",
        "## Данные и причинность",
        "",
        f"Источник — локальные CSV публичного Binance Spot `/api/v3/klines`: {len(dataset['integrity'])} рядов, "
        f"{sum(x['rows'] for x in dataset['integrity']):,} закрытых свечей; 8 пар × 1h/4h. "
        "UTC, 2024-01-01–2026-01-01 плюс 120 свечей прогрева. "
        "Во всех рядах SHA256 совпал с исходным walk-forward; внутренних пропусков, дубликатов, "
        "нарушений OHLC/объёма и времени закрытия — 0. Пропуски не заполнялись. "
        "Подробности каждого ряда и хеши — в JSON.",
        "",
        "Те же пять неперекрывающихся 90-дневных test-окон 2024-09-27–2025-12-21 UTC: "
        "folds 1–3 — discovery, 4–5 — внутренняя validation. Событие использует только текущую закрытую "
        "и более старые свечи; BTC-контекст и кросс-секция синхронизированы по закрытию. "
        "Forward результат начинается на следующем open и полностью помещается в текущий fold. "
        "Будущие high/low/close применяются только для оценки результата. Центрированных окон и будущих экстремумов в условии нет.",
        "",
        "Контроль: обычные бары того же символа/TF/месяца с тем же причинным волатильностным "
        "терцилем и знаком прошлых 24 баров. Контроль включает event-бары и может разбавлять эффект; "
        "это описательный matched baseline, не экспериментальная причинная идентификация. "
        "Все forward проценты — signed в ожидаемом направлении. Расходы за круг: zero 0%, "
        "base ≈0,30%, double ≈0,60% (комиссия и проскальзывание каждой стороны), без funding/spread/depth. "
        "Это cost hurdle для гипотетического next-open→horizon-close, **не PnL стратегии**; "
        "путь между ними может сделать сделку неисполняемой или потребовать стопа.",
        "",
        "## Заранее определённый экран",
        "",
        "Все семейства и соседние определения приведены в JSON. Горизонты: 1/2/3/6/12/24/48 баров; "
        "24 бара — 24 часа на 1h и четыре дня на 4h, поэтому pooled эффект смешивает разные календарные горизонты. "
        "В CSV для каждого события есть N, среднее/медиана/σ/квантили, доля положительных, MFE/MAE "
        "и excess относительно контроля по split/fold/паре/TF/стороне. "
        "Для отбора заранее выбран 24-барный горизонт. Топ-5 ранжирован **только по discovery**: "
        "N, положительный base-net и matched excess, согласованность по folds/парам и медиана; "
        "не по максимальному PnL. Сначала максимум одно событие на широкое семейство. "
        "Validation рассматривается после отбора. Это защита от множественного тестирования, "
        "но не статистическое доказательство — проверено много взаимосвязанных событий. "
        "Экран выбирает по одному представителю семейства даже при отрицательном discovery эффекте; "
        "попадание в топ-5 не означает перспективности.",
        "",
        "Продвижение требует discovery N≥200 и validation N≥100, validation mean >0,30% и "
        "excess>0, положительных обоих validation folds и ≥5 пар (каждая N≥10), "
        "положительного base-net после исключения любой пары, положительного соседнего широкого "
        "определения и нижней границы 95% недельного cluster-bootstrap выше нуля после base. "
        "Даже выполнение этих условий дало бы максимум `PROMISING`, пока нет внешнего нового периода.",
        "",
        "## Топ-5 по заранее заданному discovery score, 24 бара",
        "",
        table_for(report["results"], top),
        "",
    ]
    for name in top:
        x = events[name]["24"]
        p = x["promotion"]
        v = x["validation"]
        ci = p["bootstrap"]["raw_mean_after_base_ci95"]
        checks_failed = [key for key, good in p["checks"].items() if not good]
        lines.append(
            f"- `{name}`: **{x['status']}**; validation N={v['n']}, median={fmt(v.get('median_return_pct'))}%, "
            f"MFE/MAE medians={fmt(v.get('median_mfe_pct'))}%/{fmt(v.get('median_mae_pct'))}%, "
            f"cluster CI base-net={ci if ci is not None else 'недостаточно недель'}, "
            f"без лучшего исхода={fmt(p['without_best_observation_mean_after_base_pct'])}%, "
            f"winsor 1%={fmt(p['winsorized_1pct_mean_after_base_pct'])}%. "
            f"Невыполненные критерии: {', '.join(checks_failed) if checks_failed else 'нет для внутреннего экрана'}."
        )
    lines += [
        "",
        "Частота top-5 — сумма по независимым рядам на общей полосе 450 test-дней; "
        "это число событий, а не независимых торговых возможностей. Расклад по парам есть в JSON/CSV:",
        "",
        "| Event | Событий/год, весь universe | Событий/месяц | 1h N | 4h N | LONG N | SHORT N |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in top:
        x = events[name]["24"]
        lines.append(
            f"| `{name}` | {x['events_per_year_universe']:.1f} | {x['events_per_month_universe']:.1f} "
            f"| {x['by_timeframe']['1h']['n']} | {x['by_timeframe']['4h']['n']} "
            f"| {x['by_side']['LONG']['n']} | {x['by_side']['SHORT']['n']} |"
        )
    lines += ["", "## Семейства и проверки механизмов", ""]
    sections = [
        (
            "Пробой 12/24/48",
            ["breakout_12", "breakout_24", "breakout_48"],
            "Close за предыдущим максимумом/минимумом; текущая свеча не входит в уровень. "
            "Продолжение нужно сравнивать с matched-контролем, а не принимать breakout как edge.",
        ),
        (
            "Pullback в простом тренде",
            ["pullback_shallow", "pullback_medium", "pullback_deep"],
            "Один price-тренд, один trigger через предыдущую свечу; shallow/medium/deep — заранее заданная глубина.",
        ),
        (
            "Граница диапазона",
            ["range_rejection_24"],
            "Диапазон и низкая эффективность известны до текущего close; проверяется возврат к середине, "
            "но достижение середины без остановки/очереди исполнения не эквивалентно сделке.",
        ),
        (
            "Сжатие волатильности",
            ["compression_90_p20"],
            "Направление для signed-анализа задаёт только прошлый 24-барный ход. "
            "Рост абсолютного движения отдельно от предсказания знака: смотрите mean_absolute_return_minus_control в JSON.",
        ),
        (
            "Большой предыдущий ход",
            ["large_move_normal", "large_move_extended", "large_move_high"],
            "Сравнение normal/extended/high показывает, есть ли continuation либо chase penalty, без подбора точного порога.",
        ),
        (
            "Неудавшийся выход за экстремум",
            ["failed_breakout_24"],
            "Тень за прошлым 24-bar экстремумом и возврат close внутрь; двойной выход за обе границы исключён.",
        ),
    ]
    for title, names, explanation in sections:
        lines += [f"### {title}", "", explanation, "", table_for(report["results"], names), ""]
    path = report["results"]["range_path_24"]
    lines += [
        f"Для range rejection за 24 бара: N={path['n']}, середина исходного диапазона впереди "
        f"next open в {path['nontrivial_midpoint_n']} случаях; касание середины среди них "
        f"{path['midpoint_touch_among_nontrivial']:.1%}; касание противоположной границы "
        f"{path['opposite_boundary_touch']:.1%}; повторный выход за исходную границу против идеи "
        f"{path['adverse_rebreak']:.1%}. Эта дополнительная описательная диагностика не входила в "
        "замороженный экран и не меняет статус события. Порядок касаний неизвестен; "
        "это не вероятность выигрышной сделки.",
        "",
    ]
    lines += [
        "### Объём, волатильность и рыночный режим",
        "",
        "Объём — только условие для breakout/failed move/large move, не самостоятельный прогноз направления. "
        "Волатильность и эффективность price path вычислены по прошлым данным; условные buckets "
        "перекрываются с родительскими событиями и между собой не являются независимыми проверками.",
        "",
        table_for(
            report["results"],
            [
                "breakout_24_volume_normal",
                "breakout_24_volume_elevated",
                "breakout_24_volume_extreme",
                "failed_breakout_24_volume_normal",
                "failed_breakout_24_volume_elevated",
                "failed_breakout_24_volume_extreme",
                "large_move_high_volume_normal",
                "large_move_high_volume_elevated",
                "large_move_high_volume_extreme",
                "breakout_24_volatility_low",
                "breakout_24_volatility_normal",
                "breakout_24_volatility_high",
                "failed_breakout_24_volatility_low",
                "failed_breakout_24_volatility_normal",
                "failed_breakout_24_volatility_high",
            ],
        ),
        "",
        "",
        table_for(
            report["results"],
            [
                f"{parent}_regime_{regime}"
                for parent in ("breakout_24", "failed_breakout_24")
                for regime in ("trend", "range", "uncertain")
            ],
        ),
        "",
        "Условный эффект без позитивного validation excess и учёта затрат не является trading edge.",
        "",
        "### Контекст BTC и относительная сила",
        "",
        "BTC-контекст проверяется только для альткоинов и строго по одновременно уже закрытой свече "
        "того же TF. Сравнение с собственным состоянием альткоина учтено в matched-контроле; "
        "однофакторное условие BTC не доказывает самостоятельную причинную ценность.",
        "",
        table_for(
            report["results"],
            [
                f"breakout_24_btc_{x}"
                for x in ("aligned", "opposed", "high_vol", "large_move", "trend", "range")
            ],
        ),
        "",
        "**Вторичное наблюдение, вне замороженного top-5:** `breakout_24_btc_range` "
        f"имеет validation N={shadow['validation']['n']}, base-net "
        f"{fmt(shadow['validation']['mean_after_base_cost_pct'])}%, matched excess "
        f"{fmt(shadow['validation']['mean_excess_vs_matched_control_pct'])}%. "
        "Оно не выбрано discovery-экраном: от breakout/BTC-family уже был выбран `btc_opposed`. "
        "Выделять `btc_range` после просмотра validation означало бы новую гипотезу на той же истории; "
        "его статус остаётся WEAK, для продвижения нужен новый период. "
        f"Validation 1h: N={shadow['by_timeframe_validation']['1h']['n']}, "
        f"base-net={fmt(shadow['by_timeframe_validation']['1h'].get('mean_after_base_cost_pct'))}%; "
        f"4h: N={shadow['by_timeframe_validation']['4h']['n']}, "
        f"base-net={fmt(shadow['by_timeframe_validation']['4h'].get('mean_after_base_cost_pct'))}%. "
        "Разница TF также означает разные 24-барные календарные горизонты.",
        "",
        "Кросс-секция использует фиксированные восемь пар и одновременные close; "
        "ранжирование только по прошлым 24 барам/ATR. Результат strongest/middle/weakest следует "
        "сравнивать друг с другом; физическая стратегия с short/перебалансировкой здесь не моделируется.",
        "",
        table_for(
            report["results"],
            [
                "cross_section_top2_continue",
                "cross_section_middle4_continue",
                "cross_section_bottom2_continue",
                "cross_section_top2_revert",
                "cross_section_bottom2_revert",
            ],
        ),
        "",
    ]
    lines += ["## Forward path, overlap и устойчивость", ""]
    lines.append(
        "Для каждого horizon в JSON/CSV: MFE/MAE mean/median/p10/p90, доля достижения "
        "0.5/1/1.5/2 ATR и для 24 баров медианное время до MFE/MAE и до 0.5/1 ATR в обе стороны. "
        "High/low внутри одной свечи не упорядочены; MFE/MAE может учитывать путь после потенциального стопа. "
        "Это свойства распределения, не выбираемые TP/SL. Для top-5 ниже числа в validation на 24 барах:"
    )
    lines += [
        "",
        "| Event | V MFE med % | V MAE med % | P(MFE≥1ATR) | P(MAE≥1ATR) | T→MFE | T→MAE |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in top:
        v = events[name]["24"]["validation"]
        lines.append(
            f"| `{name}` | {fmt(v.get('median_mfe_pct'))} | {fmt(v.get('median_mae_pct'))} "
            f"| {fmt(v.get('prob_mfe_ge_1.0_atr'))} | {fmt(v.get('prob_mae_ge_1.0_atr'))} "
            f"| {fmt(v.get('median_time_to_mfe_bars'), 1)} | {fmt(v.get('median_time_to_mae_bars'), 1)} |"
        )
    lines += [
        "",
        "Матрица overlap по (symbol, TF, закрытие свечи, направление) — в JSON. "
        "Ниже наибольшие совпадения; дочерние volume/regime/BTC buckets ожидаемо вложены в parent "
        "и не считаются новой независимой информацией.",
        "",
        "| Event 1 | Event 2 | Общих | Доля меньшей выборки |",
        "| --- | --- | ---: | ---: |",
    ]
    for pair in report["results"]["top_overlap_pairs"][:10]:
        lines.append(
            f"| `{pair['left']}` | `{pair['right']}` | {pair['shared']} | {pair['fraction_of_smaller']:.1%} |"
        )
    lines += [
        "",
        "Наиболее пересекающиеся *разные* семейства (не отдельное подтверждение):",
        "",
        "| Event 1 | Event 2 | Общих | Доля меньшей выборки |",
        "| --- | --- | ---: | ---: |",
    ]
    for pair in report["results"]["cross_family_overlap_pairs"][:10]:
        lines.append(
            f"| `{pair['left']}` | `{pair['right']}` | {pair['shared']} | {pair['fraction_of_smaller']:.1%} |"
        )
    lines += [
        "",
        "По каждой паре, стороне и TF, каждому из пяти folds, leave-one-symbol-out, "
        "удалению лучшего исхода и winsorized-проверке top-5 — числа в JSON. "
        "Недельный cluster-bootstrap (300 повторов, seed 20261026) пересэмплирует совместно все пары/TF "
        "внутри календарной недели, поскольку часы и криптоактивы зависимы. Интервал не устраняет "
        "bias прежнего просмотра этих окон и ошибки модели исполнения.",
        "",
        "## Итог и дальнейшие данные",
        "",
        f"Статусы всех {len(events)} событий: {report['results']['status_counts']}. "
        "`ROBUST` не присваивается на уже просмотренной истории. Positive gross mean не является "
        "net-after-cost преимуществом: положительная средняя величина должна превосходить 0,30/0,60% "
        "и контроль, выдерживать validation, пары, folds, соседние определения и неопределённость. "
        "Даже тогда исследуется событие, а не готовая стратегия. Здесь итог указан в первой строке; "
        "никаких параметров SL/TP/позиции по исходам не выбиралось.",
        "",
        "Наиболее ценный следующий тест — заранее записанный **новый, ещё не просмотренный** период "
        "того же universe, с зафиксированной моделью торговых издержек. Если событийный эффект "
        "не выдержит её, для дальнейшего discovery могут потребоваться trade/order-book данные "
        "(спред, глубина, агрессивный поток), funding/open interest для SHORT или другой рынок/масштаб; "
        "это гипотезы о данных, не найденное преимущество. 32 PAPER-сделки не использовались для выбора порогов.",
        "",
        "**Безопасность:** прочитаны только архивные CSV/отчёты. Скрипт записывает только эти три "
        "research-файла в `reports/`; production, SQLite, PAPER, scanner, bridge, Telegram, DeepSeek, "
        "AI_MODE и риск не меняются. Сетевых запросов, реальных ордеров, commit/push нет.",
        "",
        "Повторный запуск из корня проекта: `.venv/bin/python -B reports/market_edge_discovery.py --evaluate`. "
        "Он сверяет SHA256 всех CSV и исходных отчётов с замороженным протоколом и детерминированно "
        "перезаписывает только исследовательские результаты.",
        "",
    ]
    MARKDOWN.write_text("\n".join(lines), encoding="utf-8")


def evaluate():
    if not PROTOCOL.exists():
        raise FileNotFoundError("Freeze the protocol before calculating event outcomes")
    protocol = json.loads(PROTOCOL.read_text())
    if protocol["state"] not in ("FROZEN_BEFORE_EVENT_RESULTS", "EVALUATED_OFFLINE"):
        raise ValueError("Unexpected protocol state")
    data, _baseline = load_research_data(protocol)
    names = sorted(set().union(*(entry["events"].keys() for entry in data.values())))
    results = {name: {} for name in names}
    csv_rows = []
    observations24 = {}
    for horizon in HORIZONS:
        futures = {key: forward_arrays(entry, horizon) for key, entry in data.items()}
        for name in names:
            frames = []
            for (symbol, tf), entry in data.items():
                if name not in entry["events"]:
                    continue
                frame = observation_frame(
                    name, symbol, tf, entry["events"][name], futures[(symbol, tf)], horizon
                )
                if frame is not None:
                    frames.append(frame)
            if not frames:
                continue
            combined = pd.concat(frames, ignore_index=True)
            summary = group_metrics(combined, name, horizon, csv_rows)
            if horizon == 24:
                summary["discovery_evidence_score"] = discovery_evidence_score(summary)
                observations24[name] = combined[
                    [
                        "symbol",
                        "timeframe",
                        "fold",
                        "split",
                        "side",
                        "time",
                        "week",
                        "return_pct",
                        "excess_pct",
                        "mfe_pct",
                        "mae_pct",
                    ]
                ].copy()
            results[name][str(horizon)] = summary
        print(
            f"horizon {horizon}: {sum(str(horizon) in x for x in results.values())} event definitions",
            flush=True,
        )
    selected, ranked = select_top_five(results)
    for number, name in enumerate(selected):
        boot = cluster_bootstrap(
            observations24[name].loc[observations24[name].split == "validation"], SEED + number
        )
        results[name]["24"]["promotion"] = promotion(name, results, observations24[name], boot)
    for name in results:
        if "24" not in results[name]:
            results[name]["status"] = "REJECT"
            continue
        d = results[name]["24"]["discovery"]
        if name in selected and results[name]["24"]["promotion"]["internal_promotion_pass"]:
            status = "PROMISING"
        elif (
            d["n"] >= 200
            and d["mean_after_base_cost_pct"] > 0
            and d["mean_excess_vs_matched_control_pct"] > 0
        ):
            status = "WEAK"
        else:
            status = "REJECT"
        results[name]["24"]["status"] = status
        results[name]["status"] = status
    matrix, top_pairs, cross_family_pairs = overlap_matrix(observations24)
    range_path = range_path_diagnostic(data)
    statuses = Counter(x["status"] for x in results.values())
    verdict = "PROMISING BUT UNCONFIRMED" if statuses["PROMISING"] else "NO ROBUST EDGE FOUND"
    protocol["state"] = "EVALUATED_OFFLINE"
    protocol["results"] = {
        "verdict": verdict,
        "implementation_sha256": digest(Path(__file__)),
        "events": results,
        "event_count": len(results),
        "top_five_discovery_selected": selected,
        "discovery_ranked_all": ranked,
        "status_counts": dict(statuses),
        "overlap_matrix": matrix,
        "top_overlap_pairs": top_pairs,
        "cross_family_overlap_pairs": cross_family_pairs,
        "range_path_24": range_path,
        "no_live_calls": True,
        "no_production_changes": True,
    }
    # Allow no NaN/Inf in a machine-consumable report.
    PROTOCOL.write_text(json.dumps(protocol, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    fields = list(dict.fromkeys(key for row in csv_rows for key in row))
    with EVENTS_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(csv_rows)
    render_markdown(protocol)
    print(f"VERDICT {verdict}; top five: {', '.join(selected)}; CSV rows: {len(csv_rows)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument(
        "--freeze", action="store_true", help="verify inputs and freeze protocol before outcomes"
    )
    actions.add_argument("--evaluate", action="store_true", help="offline event distribution analysis")
    options = parser.parse_args()
    if options.freeze:
        freeze()
    else:
        evaluate()


if __name__ == "__main__":
    main()
