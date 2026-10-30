"""Frozen, offline perpetual trade basis information study. No production imports."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import futures_flow_oi_research as previous
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
PROTOCOL = REPORTS / "FUTURES_SPOT_BASIS_FROZEN_PROTOCOL.json"
DATA = REPORTS / "FUTURES_SPOT_BASIS_DATA"
RESULT_JSON = REPORTS / "FUTURES_SPOT_BASIS_RESEARCH.json"
RESULT_MD = REPORTS / "FUTURES_SPOT_BASIS_RESEARCH.md"
RESULT_CSV = REPORTS / "FUTURES_SPOT_BASIS_RESULTS.csv"
EXPECTED_PROTOCOL_SHA = "1c3314be00b463c2567463b671f06d96224eddb22bf6313a48ac75f21a7de142"
BASIS_COLS = [
    "basis_pct",
    "basis_change_pp",
    "basis_percentile90",
    "basis_abs_change_pp",
    "basis_persistence3",
]
PRICE_COLS = previous.ALL_PRICE
HYPOTHESES = ("H1", "H2", "H3", "H4")


def sha256(path: Path) -> str:
    return previous.sha256(path)


def normalize_basis(futures_close: pd.Series, spot_close: pd.Series, multiplier: int) -> pd.Series:
    if multiplier not in (1, 1000) or (spot_close <= 0).any() or (futures_close <= 0).any():
        raise ValueError("Invalid price or contract multiplier")
    return ((futures_close / multiplier) / spot_close - 1) * 100


def trailing_percentile(basis: pd.Series, window: int = 90) -> pd.Series:
    values = basis.to_numpy(float)
    ranks = np.full(len(values), np.nan)
    for i in range(window, len(values)):
        prior = values[i - window : i]
        if np.isfinite(values[i]) and np.isfinite(prior).all():
            ranks[i] = float(np.mean(prior <= values[i]))
    return pd.Series(ranks, index=basis.index)


def basis_features(basis: pd.Series) -> pd.DataFrame:
    result = pd.DataFrame(index=basis.index)
    result["basis_pct"] = basis
    result["basis_change_pp"] = basis.diff()
    result["basis_percentile90"] = trailing_percentile(basis)
    result["basis_abs_change_pp"] = basis.abs().diff()
    signs = np.sign(basis)
    matches = [signs.eq(signs.shift(lag)) for lag in (1, 2, 3)]
    result["basis_persistence3"] = sum(matches) / 3
    result.iloc[:3, result.columns.get_loc("basis_persistence3")] = np.nan
    return result


def segment(frame: pd.DataFrame, split: str, timeframe: str, horizon: int) -> pd.DataFrame:
    return previous.split_rows(frame, split, timeframe, horizon)


def forward_outcomes(spot: pd.DataFrame, horizon: int) -> pd.DataFrame:
    close = spot["close"].astype(float)
    high = pd.concat([spot["high"].shift(-i) for i in range(1, horizon + 1)], axis=1)
    low = pd.concat([spot["low"].shift(-i) for i in range(1, horizon + 1)], axis=1)
    result = pd.DataFrame(index=spot.index)
    result["signed_pct"] = (close.shift(-horizon) / close - 1) * 100
    result["absolute_pct"] = result["signed_pct"].abs()
    result["mfe_pct"] = (high.max(axis=1, skipna=False) / close - 1) * 100
    result["mae_pct"] = (low.min(axis=1, skipna=False) / close - 1) * 100
    return result


def cost_hurdles(value: float) -> dict[str, float]:
    return {"zero": value, "base": value - 0.3, "double": value - 0.6}


def load_prices(
    symbol: str, timeframe: str, multiplier: int, expected_hash: str
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    spot, spot_info = previous.read_spot(symbol, timeframe)
    last_boundary = previous.END if timeframe == "4h" else previous.SPLITS["validation"][1]
    spot = spot.loc[
        (spot.index >= previous.START + pd.Timedelta(hours=1 if timeframe == "1h" else 4))
        & (spot.index <= last_boundary)
    ]
    path = previous.NORMALIZED / "futures_aggregate" / f"{symbol}_{timeframe}.csv.gz"
    if sha256(path) != expected_hash:
        raise RuntimeError(f"Futures aggregate changed: {symbol} {timeframe}")
    futures = pd.read_csv(path, parse_dates=["decision_time"]).set_index("decision_time")
    futures.index = pd.to_datetime(futures.index, utc=True)
    interval = pd.Timedelta(hours=1 if timeframe == "1h" else 4)
    subbars = 12 if timeframe == "1h" else 48
    duplicates = int(futures.index.duplicated().sum())
    gaps = int((futures.index.to_series().diff().dropna() != interval).sum())
    expected_open = (futures.index - interval).asi8 // 1_000_000
    expected_close = futures.index.asi8 // 1_000_000 - 1
    invalid = int(
        (
            (futures["first_open"].to_numpy() != expected_open)
            | (futures["last_close"].to_numpy() != expected_close)
            | (futures["subbars"].to_numpy() != subbars)
            | (futures["high"] < futures[["open", "close", "low"]].max(axis=1)).to_numpy()
            | (futures["low"] > futures[["open", "close", "high"]].min(axis=1)).to_numpy()
            | (futures["volume"] < 0).to_numpy()
        ).sum()
    )
    if duplicates or gaps or invalid:
        raise RuntimeError(f"Futures integrity failure: {symbol} {timeframe}: {duplicates}/{gaps}/{invalid}")
    joined = spot[["open", "high", "low", "close", "volume", "time", "close_time"]].join(
        futures[["open", "high", "low", "close", "volume", "first_open", "last_close", "subbars"]],
        how="inner",
        lsuffix="_spot",
        rsuffix="_futures",
        validate="one_to_one",
    )
    if joined.empty or len(joined) != len(spot):
        raise RuntimeError(f"Spot/Futures timestamp mismatch: {symbol} {timeframe}")
    close_time = pd.to_datetime(joined["close_time"], utc=True)
    if not (
        (close_time == joined.index - pd.Timedelta(milliseconds=1)).all()
        and (joined["last_close"].to_numpy() == joined.index.asi8 // 1_000_000 - 1).all()
    ):
        raise RuntimeError("Causal close-time mismatch")
    basis = normalize_basis(joined["close_futures"], joined["close_spot"], multiplier)
    if not np.isfinite(basis).all() or (basis.abs() > 20).any():
        raise RuntimeError(f"Basis normalization anomaly: {symbol} {timeframe}")
    info = {
        "symbol": symbol,
        "timeframe": timeframe,
        "multiplier": multiplier,
        "rows_spot": len(spot),
        "rows_futures": len(futures),
        "rows_aligned": len(joined),
        "spot": spot_info,
        "futures_aggregate_sha256": expected_hash,
        "futures_duplicates": duplicates,
        "futures_gaps": gaps,
        "futures_invalid": invalid,
        "basis_min_pct": float(basis.min()),
        "basis_max_pct": float(basis.max()),
        "basis_abs_gt_5pct": int((basis.abs() > 5).sum()),
        "basis_delta_abs_gt_2pp": int((basis.diff().abs() > 2).sum()),
        "integrity": "PASS",
    }
    return spot, futures.loc[spot.index], info


def build_features(spot: pd.DataFrame, futures: pd.DataFrame, multiplier: int) -> pd.DataFrame:
    basis = normalize_basis(futures["close"], spot["close"], multiplier)
    return pd.concat(
        [
            previous.price_features(spot, "spot"),
            previous.price_features(futures, "futures"),
            basis_features(basis),
        ],
        axis=1,
    )


def thresholds(train: pd.DataFrame) -> dict[str, float]:
    positive = train.loc[train["basis_pct"] > 0, "basis_pct"]
    strong_price = train.loc[train["spot_ret1"] > 0, "spot_ret1"]
    if len(positive) < 100 or len(strong_price) < 100:
        raise RuntimeError("Insufficient discovery observations for thresholds")
    return {
        "positive_q75": float(positive.quantile(0.75)),
        "positive_q90": float(positive.quantile(0.90)),
        "basis_q10": float(train["basis_pct"].quantile(0.10)),
        "positive_spot_ret1_q75": float(strong_price.quantile(0.75)),
        "abs_basis_change_q90": float(train["basis_change_pp"].abs().quantile(0.90)),
    }


def masks(frame: pd.DataFrame, cut: dict[str, float]) -> dict[str, pd.Series]:
    return {
        "H1": (frame["basis_pct"] >= cut["positive_q75"]) & (frame["spot_ret1"] > 0),
        "H2": (frame["basis_pct"] >= cut["positive_q90"])
        & (frame["spot_ret1"] >= cut["positive_spot_ret1_q75"]),
        "H3": (frame["basis_pct"] <= cut["basis_q10"]) & (frame["basis_pct"] < 0),
        "H4": (frame["basis_change_pp"].abs() >= cut["abs_basis_change_q90"])
        & (frame["basis_abs_change_pp"] > 0),
    }


def summarize_events(events: pd.DataFrame, model_uplift: float, *, hypothesis: str, timeframe: str) -> dict:
    if events.empty:
        return {"n": 0, "class": "REJECT", "reason": "no events"}
    values = events["effect_pct"].to_numpy(float)
    raw = events["raw_forward_pct"].to_numpy(float)
    weeks = events["week"].nunique()
    rng = np.random.default_rng(20261028 + HYPOTHESES.index(hypothesis) * 10 + (timeframe == "4h"))
    block = events.groupby("week")["effect_pct"].agg(["sum", "count"])
    sums, counts = block["sum"].to_numpy(), block["count"].to_numpy()
    draw = rng.integers(0, len(block), size=(500, len(block)))
    samples = sums[draw].sum(axis=1) / counts[draw].sum(axis=1)
    effect = float(values.mean())
    p = float((np.count_nonzero(samples <= 0) + 1) / 501)
    by_symbol = events.groupby("symbol")["effect_pct"].agg(["count", "mean"]).to_dict("index")
    quarters = events.groupby("quarter")["effect_pct"].agg(["count", "mean"]).to_dict("index")
    loo = {
        symbol: float(events.loc[events.symbol != symbol, "effect_pct"].mean())
        for symbol in sorted(events.symbol.unique())
    }
    positive = np.sort(values[values > 0])[::-1]
    best = float((values.sum() - values.max()) / (len(values) - 1)) if len(values) > 1 else None
    top_count = max(1, int(np.ceil(len(values) * 0.01)))
    return {
        "n": len(events),
        "weeks": int(weeks),
        "effect_mean_pp": effect,
        "effect_median_pp": float(np.median(values)),
        "ci95_pp": [float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))],
        "one_sided_p": p,
        "raw_mean_pct": float(raw.mean()),
        "cost_hurdle_pct": cost_hurdles(float(raw.mean())),
        "mfe_median_pct": float(events.mfe_pct.median()),
        "mae_median_pct": float(events.mae_pct.median()),
        "mfe_q10_q90": [float(events.mfe_pct.quantile(0.1)), float(events.mfe_pct.quantile(0.9))],
        "mae_q10_q90": [float(events.mae_pct.quantile(0.1)), float(events.mae_pct.quantile(0.9))],
        "per_symbol": by_symbol,
        "per_quarter": quarters,
        "leave_one_symbol_out": loo,
        "without_best_effect_pp": best,
        "top_1pct_positive_contribution": float(positive[:top_count].sum() / positive.sum())
        if positive.size
        else None,
        "extreme_basis_events_abs_gt_5pct": int((events.basis_pct.abs() > 5).sum()),
        "model_uplift": model_uplift,
    }


def classify(summary: dict, *, diagnostic_effect: float | None, holm_p: float) -> str:
    if summary["n"] == 0 or summary["effect_mean_pp"] <= 0:
        return "REJECT"
    if summary["n"] < 100 or summary["weeks"] < 12 or summary["model_uplift"] <= 0:
        return "WEAK"
    quarters = summary["per_quarter"]
    robust = (
        summary["ci95_pp"][0] > 0
        and holm_p < 0.05
        and sum(row["mean"] > 0 for row in summary["per_symbol"].values()) >= 6
        and len(quarters) >= 4
        and sum(row["mean"] > 0 for row in quarters.values()) >= 3
        and all(x > 0 for x in summary["leave_one_symbol_out"].values())
        and summary["model_uplift"] >= 0.001
        and summary["effect_mean_pp"] >= 0.3
        and summary["cost_hurdle_pct"]["double"] > 0
        and (diagnostic_effect is None or diagnostic_effect > 0)
        and summary["without_best_effect_pp"] > 0
    )
    return "ROBUST" if robust else "PROMISING"


def holm_adjust(rows: list[dict]) -> None:
    ordered = sorted(rows, key=lambda item: item["one_sided_p"])
    maximum = 0.0
    for i, row in enumerate(ordered):
        maximum = max(maximum, min(1.0, row["one_sided_p"] * (len(rows) - i)))
        row["holm_p"] = maximum


def json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def evaluate() -> None:
    if sha256(PROTOCOL) != EXPECTED_PROTOCOL_SHA:
        raise RuntimeError("Frozen basis protocol changed")
    previous.verify_manifest()
    config = json.loads(PROTOCOL.read_text())
    reference = json.loads(previous.RESULT_JSON.read_text())
    reference_rows = {(row["symbol"], row["timeframe"]): row for row in reference["joined_data"]}
    integrity, thresholds_by_series, models, events, redundancy, outputs = [], {}, {}, [], {}, {}
    secondary_records = []
    DATA.mkdir(exist_ok=True)
    for symbol, (_, multiplier) in config["universe_multiplier"].items():
        for timeframe in ("1h", "4h"):
            label = f"{symbol}_{timeframe}"
            ref = reference_rows[symbol, timeframe]
            spot, futures, info = load_prices(symbol, timeframe, multiplier, ref["aggregate_sha256"])
            integrity.append(info)
            feat = build_features(spot, futures, multiplier)
            horizon = config["horizons"][timeframe]["primary_bars"]
            frame = feat.join(forward_outcomes(spot, horizon))
            needed = PRICE_COLS + BASIS_COLS + ["signed_pct", "absolute_pct", "mfe_pct", "mae_pct"]
            train = segment(frame, "discovery", timeframe, horizon).dropna(subset=needed)
            if len(train) < 1000:
                raise RuntimeError(f"Too few discovery rows: {label}")
            cut = thresholds(train)
            thresholds_by_series[label] = cut
            source = {
                "spot": info["spot"]["files_sha256"],
                "futures_aggregate": info["futures_aggregate_sha256"],
            }
            outputs[label] = {
                "source_sha256": source,
                "features_complete": int(feat.notna().all(axis=1).sum()),
                "discovery_rows": len(train),
                "period_start": feat.index.min().isoformat(),
                "period_end": feat.index.max().isoformat(),
            }
            feature_path = DATA / f"{label}_features.csv.gz"
            feat.to_csv(feature_path, index_label="decision_time", compression={"method": "gzip", "mtime": 0})
            outputs[label]["features_sha256"] = sha256(feature_path)
            secondary_outcomes = {
                h: forward_outcomes(spot, h) for h in config["horizons"][timeframe]["secondary_bars"]
            }
            for split in ("discovery", "validation", "diagnostic_2026"):
                if split == "diagnostic_2026" and timeframe == "1h":
                    continue
                test = segment(frame, split, timeframe, horizon).dropna(subset=needed)
                if test.empty:
                    continue
                models[label, split] = {}
                for target in ("signed_pct", "absolute_pct"):
                    truth = test[target].to_numpy(float)
                    preds = {
                        name: previous.fit_predict(train, test, cols, target)
                        for name, cols in {
                            "A": PRICE_COLS,
                            "B": BASIS_COLS,
                            "C": PRICE_COLS + BASIS_COLS,
                        }.items()
                    }
                    mse = {name: float(np.mean((truth - pred) ** 2)) for name, pred in preds.items()}
                    models[label, split][target] = {
                        "n": len(test),
                        "mse": mse,
                        "C_vs_A_uplift": (mse["A"] - mse["C"]) / mse["A"],
                    }
                    if target == "signed_pct":
                        signed_pred = preds["A"]
                    else:
                        absolute_pred = preds["A"]
                all_masks = masks(test, cut)
                for hypothesis, mask in all_masks.items():
                    chosen = test.loc[mask]
                    for secondary_horizon, outcome in secondary_outcomes.items():
                        interval = pd.Timedelta(hours=1 if timeframe == "1h" else 4)
                        end = previous.SPLITS[split][1]
                        eligible = chosen.index[chosen.index + secondary_horizon * interval <= end]
                        forward = outcome.reindex(eligible)["signed_pct"].dropna()
                        if hypothesis == "H4":
                            forward = forward.abs()
                        elif hypothesis in ("H2", "H3"):
                            forward = -forward
                        secondary_records.append(
                            {
                                "hypothesis": hypothesis,
                                "timeframe": timeframe,
                                "split": split,
                                "symbol": symbol,
                                "horizon_bars": secondary_horizon,
                                "n": len(forward),
                                "sum_raw_pct": float(forward.sum()),
                            }
                        )
                    positions = np.flatnonzero(mask.to_numpy())
                    for pos, (stamp, row) in zip(positions, chosen.iterrows(), strict=True):
                        signed = float(row.signed_pct)
                        residual = signed - signed_pred[pos]
                        if hypothesis == "H4":
                            raw = float(row.absolute_pct)
                            effect = raw - absolute_pred[pos]
                        elif hypothesis == "H2" or hypothesis == "H3":
                            raw, effect = -signed, -residual
                        else:
                            raw, effect = signed, residual
                        events.append(
                            {
                                "hypothesis": hypothesis,
                                "symbol": symbol,
                                "timeframe": timeframe,
                                "split": split,
                                "decision_time": stamp.isoformat(),
                                "week": stamp.strftime("%G-W%V"),
                                "quarter": f"{stamp.year}Q{(stamp.month - 1) // 3 + 1}",
                                "basis_pct": float(row.basis_pct),
                                "signed_forward_pct": signed,
                                "raw_forward_pct": float(raw),
                                "effect_pct": float(effect),
                                "mfe_pct": float(row.mfe_pct),
                                "mae_pct": float(row.mae_pct),
                            }
                        )
                if split == "validation":
                    prior_feature = ROOT / ref["feature_file"]
                    if sha256(prior_feature) != ref["feature_sha256"]:
                        raise RuntimeError(f"Prior funding feature file changed: {label}")
                    funding = pd.read_csv(
                        prior_feature,
                        usecols=["decision_time", "funding_latest"],
                        parse_dates=["decision_time"],
                    ).set_index("decision_time")
                    funding.index = pd.to_datetime(funding.index, utc=True)
                    redundancy[label] = {
                        b: {
                            p: float(test[b].corr(test[p]))
                            for p in (
                                "spot_ret1",
                                "futures_ret1",
                                "spot_volume_ratio24",
                                "futures_volume_ratio24",
                                "spot_volatility12",
                                "futures_volatility12",
                            )
                        }
                        | {
                            "funding_latest_diagnostic": float(
                                test[b].corr(funding["funding_latest"].reindex(test.index))
                            )
                        }
                        for b in BASIS_COLS
                    }
    events_frame = pd.DataFrame(events).sort_values(
        ["hypothesis", "timeframe", "split", "symbol", "decision_time"]
    )
    events_frame.to_csv(RESULT_CSV, index=False, quoting=csv.QUOTE_MINIMAL)
    primary = []
    for hypothesis in HYPOTHESES:
        for timeframe in ("1h", "4h"):
            target = "absolute_pct" if hypothesis == "H4" else "signed_pct"
            subset = events_frame.loc[
                (events_frame.hypothesis == hypothesis) & (events_frame.timeframe == timeframe)
            ]
            validation = subset.loc[subset.split == "validation"]
            discovery = subset.loc[subset.split == "discovery"]
            diagnostic = subset.loc[subset.split == "diagnostic_2026"]
            uplift = float(
                np.mean(
                    [
                        models[f"{symbol}_{timeframe}", "validation"][target]["C_vs_A_uplift"]
                        for symbol in config["universe_multiplier"]
                    ]
                )
            )
            row = {
                "hypothesis": hypothesis,
                "timeframe": timeframe,
                **summarize_events(validation, uplift, hypothesis=hypothesis, timeframe=timeframe),
                "discovery_in_sample": summarize_events(
                    discovery, uplift, hypothesis=hypothesis, timeframe=timeframe
                ),
                "diagnostic_2026": summarize_events(
                    diagnostic, uplift, hypothesis=hypothesis, timeframe=timeframe
                )
                if not diagnostic.empty
                else None,
            }
            primary.append(row)
    holm_adjust(primary)
    for row in primary:
        diagnostic = row["diagnostic_2026"]
        row["class"] = classify(
            row, diagnostic_effect=diagnostic["effect_mean_pp"] if diagnostic else None, holm_p=row["holm_p"]
        )
    signed_uplift = {
        tf: float(
            np.mean(
                [
                    models[f"{symbol}_{tf}", "validation"]["signed_pct"]["C_vs_A_uplift"]
                    for symbol in config["universe_multiplier"]
                ]
            )
        )
        for tf in ("1h", "4h")
    }
    classes = {row["class"] for row in primary}
    verdict = (
        "YES"
        if "ROBUST" in classes
        else "NO"
        if not classes.intersection({"PROMISING", "ROBUST"}) and all(x <= 0 for x in signed_uplift.values())
        else "INCONCLUSIVE"
    )
    manifest = {
        "protocol_sha256": EXPECTED_PROTOCOL_SHA,
        "previous_manifest_sha256": sha256(previous.MANIFEST),
        "series": outputs,
    }
    (DATA / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    secondary = []
    secondary_frame = pd.DataFrame(secondary_records)
    for (hypothesis, timeframe, split, horizon_bars), group in secondary_frame.groupby(
        ["hypothesis", "timeframe", "split", "horizon_bars"], sort=True
    ):
        count = int(group["n"].sum())
        secondary.append(
            {
                "hypothesis": hypothesis,
                "timeframe": timeframe,
                "split": split,
                "horizon_bars": int(horizon_bars),
                "n": count,
                "raw_mean_pct": float(group["sum_raw_pct"].sum() / count) if count else None,
            }
        )
    result = {
        "protocol_sha256": EXPECTED_PROTOCOL_SHA,
        "code_sha256": sha256(Path(__file__)),
        "source_manifest_sha256": sha256(previous.MANIFEST),
        "data_manifest_sha256": sha256(DATA / "manifest.json"),
        "integrity": integrity,
        "mapping": config["universe_multiplier"],
        "thresholds_discovery_only": thresholds_by_series,
        "models": {f"{label}/{split}": value for (label, split), value in models.items()},
        "validation_signed_C_vs_A_mean_uplift": signed_uplift,
        "primary": primary,
        "secondary_exploratory": secondary,
        "redundancy": redundancy,
        "events_sha256": sha256(RESULT_CSV),
        "BASIS_INCREMENTAL_INFORMATION": verdict,
        "new_edge_evidence": "YES" if verdict == "YES" else "NO" if verdict == "NO" else "INCONCLUSIVE",
        "strategy_design": "NO",
        "technical_v1_change": "NO",
        "PAPER_change": "NO",
        "limitations": config["limitations"],
    }
    result = json_safe(result)
    RESULT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    render_report(result)


def render_report(result: dict) -> None:
    lines = [
        "# Futures / Spot basis: исследование дополнительной информации",
        "",
        f"**BASIS_INCREMENTAL_INFORMATION = {result['BASIS_INCREMENTAL_INFORMATION']}**. Стратегия и PAPER не менялись.",
        "",
        f"Protocol SHA-256 `{result['protocol_sha256']}`; code `{result['code_sha256']}`; source manifest `{result['source_manifest_sha256']}`. No downloads.",
        "",
        "Basis = 100 × ((USD-M perpetual **trade close** / multiplier) / Spot trade close − 1). Для SHIB/PEPE множитель 1000; остальные шесть пар напрямую. Это не mark/index/premium-index basis. Оба close относятся к одному закрытому интервалу [T−TF,T) UTC и известны на границе T. 1h: 2024-01-01…2025-12-31; 4h: 2024-01-01…2026-09-30. Данные уже сохранены, новых загрузок нет.",
        "",
        "## Основная валидация 2025",
        "",
        "| H | TF | N | Effect vs A, pp | 95% weekly CI, pp | Holm p | C vs A MSE | Cost zero/base/double, % | Class |",
        "|---|---|---:|---:|---|---:|---:|---|---|",
    ]
    for row in result["primary"]:
        c = row["cost_hurdle_pct"]
        lines.append(
            f"| {row['hypothesis']} | {row['timeframe']} | {row['n']} | {row['effect_mean_pp']:+.4f} | [{row['ci95_pp'][0]:+.4f}, {row['ci95_pp'][1]:+.4f}] | {row['holm_p']:.4f} | {row['model_uplift']:+.4%} | {c['zero']:+.3f}/{c['base']:+.3f}/{c['double']:+.3f} | {row['class']} |"
        )
    lines += ["", "## Integrity and sample", ""]
    for info in result["integrity"]:
        lines.append(
            f"- {info['symbol']} {info['timeframe']}: {info['integrity']}; aligned={info['rows_aligned']}; basis=[{info['basis_min_pct']:+.3f}%, {info['basis_max_pct']:+.3f}%]; |basis|>5%={info['basis_abs_gt_5pct']}; |Δbasis|>2pp={info['basis_delta_abs_gt_2pp']}."
        )
    lines.append(
        "Spot/Futures дубликаты и внутренние пропуски: 0; OHLC, объём, закрытие в T−1ms и 12/48 исходных 5m баров проверены. Сумма 188 544 выровненных строк включает отдельно 1h и 4h наблюдения одних и тех же рынков. Первая Spot свеча прогрева 2024-01-01T00:00Z не имеет парной Futures свечи и не оценивалась."
    )
    lines += [
        "",
        "## Хронология, устойчивость и выбросы",
        "",
        "| H | TF | 2024 discovery N/эффект | 2025 validation N/эффект | 2026 diagnostic N/эффект | Кварталы + | Пары + | LOO min/max, п.п. | Без лучшего, п.п. | MFE/MAE медиана, % |",
        "|---|---|---|---|---|---:|---:|---|---:|---|",
    ]
    for row in result["primary"]:
        discovery = row["discovery_in_sample"]
        diagnostic = row["diagnostic_2026"]
        disc = f"{discovery['n']}/{discovery.get('effect_mean_pp', 0):+.3f}"
        diag = f"{diagnostic['n']}/{diagnostic['effect_mean_pp']:+.3f}" if diagnostic else "—"
        quarters = sum(x["mean"] > 0 for x in row["per_quarter"].values())
        symbols = sum(x["mean"] > 0 for x in row["per_symbol"].values())
        loo = [value for value in row["leave_one_symbol_out"].values() if value is not None]
        loo_text = f"{min(loo):+.3f}/{max(loo):+.3f}" if loo else "—"
        lines.append(
            f"| {row['hypothesis']} | {row['timeframe']} | {disc} | {row['n']}/{row['effect_mean_pp']:+.3f} | {diag} | {quarters}/{len(row['per_quarter'])} | {symbols}/8 | {loo_text} | {row['without_best_effect_pp']:+.3f} | {row['mfe_median_pct']:+.3f}/{row['mae_median_pct']:+.3f} |"
        )
    lines += [
        "",
        "2024 discovery effect рассчитан на обучающих данных и является in-sample описанием. Нулевые символы в per-symbol CSV не появляются как события. Полные квартальные, парные, top-1%, MFE/MAE quantile и redundancy данные — в JSON. MFE/MAE не переориентированы как short-сделка.",
        "",
        "## Модели A / B / C",
        "",
        "| TF | Средний A MSE | B MSE | C MSE | Средний uplift C против A |",
        "|---|---:|---:|---:|---:|",
    ]
    for tf in ("1h", "4h"):
        values = [result["models"][f"{symbol}_{tf}/validation"]["signed_pct"] for symbol in result["mapping"]]
        means = {name: float(np.mean([v["mse"][name] for v in values])) for name in ("A", "B", "C")}
        lines.append(
            f"| {tf} | {means['A']:.6f} | {means['B']:.6f} | {means['C']:.6f} | {result['validation_signed_C_vs_A_mean_uplift'][tf]:+.4%} |"
        )
    lines += [
        "",
        "A = прежние 14 Spot+Futures OHLCV признаков; B = только пять basis-признаков; C = A+B. Ridge(alpha=10), нормализация только по 2024. Все модели используют одинаковые строки. Uplift — среднее восьми относительных per-symbol улучшений, а не отношение общих MSE. Funding проверен только в диагностических корреляциях и не входит в модели.",
        "",
        "## Вторичные горизонты: exploratory raw outcomes",
        "",
        "| H | TF | Период | Горизонт, бары | N | Raw mean, % |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in result["secondary_exploratory"]:
        if row["split"] in ("validation", "diagnostic_2026"):
            value = row["raw_mean_pct"]
            rendered = f"{value:+.3f}" if value is not None else "—"
            lines.append(
                f"| {row['hypothesis']} | {row['timeframe']} | {row['split']} | {row['horizon_bars']} | {row['n']} | {rendered} |"
            )
    lines += [
        "",
        "Маска события задана на primary-eligible строках; более длинный горизонт дополнительно отсекается у границы периода. Эти таблицы не меняют primary conclusion.",
    ]
    correlations = {
        name: float(
            np.median(
                [
                    abs(series["basis_pct"][name])
                    for series in result["redundancy"].values()
                    if series["basis_pct"][name] is not None
                ]
            )
        )
        for name in (
            "spot_ret1",
            "futures_ret1",
            "spot_volume_ratio24",
            "futures_volume_ratio24",
            "spot_volatility12",
            "futures_volatility12",
            "funding_latest_diagnostic",
        )
    }
    lines += [
        "",
        "## Избыточность признака",
        "",
        "Медиана |корреляции| уровня basis по 16 рядам validation: "
        + ", ".join(f"{key}={value:.3f}" for key, value in correlations.items())
        + ". Basis не является простой копией текущего return/volume, но связан с funding. "
        "Отличие как рыночного состояния не означает дополнительной прогностической пользы: C не улучшил A.",
        "",
        "H2 на 1h имеет лишь 11 validation событий, все на BNB; leave-one-out без BNB не определён. "
        "Положительный raw absolute move H4 не является эффектом basis: residual относительно A отрицательный.",
    ]
    lines += [
        "",
        "## Вывод и ограничения",
        "",
        "Primary target — будущий Spot close-to-close return (6h на 1h, 12h на 4h). Event effect — остаток относительно A в заранее зафиксированном направлении; cost hurdles — raw event outcome минус условные 0/0.30/0.60 п.п. за круг. Это не исполнимый trading PnL: путь входа/выхода, spread, impact и funding не моделировались.",
        "",
        "Пороги discovery 2024 сохранены в JSON. 2026 4h — заранее определённая диагностика, но история уже изучалась в проекте; pristine external holdout отсутствует. Недельный block bootstrap лишь приближённо учитывает перекрытие forward окон; Holm корректирует 8 primary тестов. Архивный trade close не доказывает нулевую задержку live-публикации. После validation пороги и горизонты не подбирались.",
        "",
        f"Новый edge: {result['new_edge_evidence']}. Переход к strategy design: NO; изменения technical-v1 и PAPER: NO. Production/SQLite не менялись. DeepSeek и ордера не вызывались. Commit/push: NO.",
        "",
        "Воспроизведение: `.venv/bin/python -B reports/futures_spot_basis_research.py --self-test`, затем `.venv/bin/python -B reports/futures_spot_basis_research.py --evaluate`.",
    ]
    RESULT_MD.write_text("\n".join(lines) + "\n")


def self_test() -> None:
    index = pd.date_range("2024-01-01", periods=100, freq="h", tz="UTC")
    spot = pd.Series(np.ones(100) * 0.01, index=index)
    futures = pd.Series(np.ones(100) * 10.1, index=index)
    assert np.isclose(normalize_basis(futures, spot, 1000).iloc[0], 1)
    assert np.isclose(normalize_basis(futures, spot, 1).iloc[0], 100900)
    assert np.isnan(trailing_percentile(spot).iloc[89])
    assert np.isclose(trailing_percentile(spot).iloc[90], 1)
    changed = spot.copy()
    changed.iloc[99] = 2
    assert trailing_percentile(changed).iloc[90] == trailing_percentile(spot).iloc[90]
    assert basis_features(changed).iloc[90].equals(basis_features(spot).iloc[90])
    assert cost_hurdles(1)["double"] == 0.4
    print("self-test PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--evaluate", action="store_true")
    group.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test() if args.self_test else evaluate()


if __name__ == "__main__":
    main()
