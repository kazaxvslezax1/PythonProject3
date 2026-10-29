"""Read-only, frozen higher-timeframe Spot event research.

The optional --fetch command accesses only public Binance Spot klines. --evaluate
is entirely offline. Neither path imports production bot code or uses credentials.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
DATA = REPORTS / "HIGHER_TIMEFRAME_EDGE_DATA"
RAW = DATA / "raw_spot_4h"
NORMALIZED = DATA / "normalized_spot_4h"
MANIFEST = DATA / "manifest.json"
PROTOCOL = REPORTS / "HIGHER_TIMEFRAME_EDGE_PROTOCOL.json"
RESULT_JSON = REPORTS / "HIGHER_TIMEFRAME_EDGE_RESEARCH.json"
RESULT_MD = REPORTS / "HIGHER_TIMEFRAME_EDGE_RESEARCH.md"
RESULT_CSV = REPORTS / "HIGHER_TIMEFRAME_EDGE_EVENTS.csv"
PROTOCOL_SHA = "0322a2af725cea7ca44c1e34d2604992f05c39376dd54414b1dc7fa6ed837a46"
START = pd.Timestamp("2020-01-01", tz="UTC")
NEW_END = pd.Timestamp("2024-01-01", tz="UTC")
END = pd.Timestamp("2026-10-26", tz="UTC")
BAR = pd.Timedelta(hours=4)
BAR_MS = 14_400_000
SPLITS = {
    "discovery": (START, pd.Timestamp("2023-01-01", tz="UTC")),
    "validation": (pd.Timestamp("2023-01-01", tz="UTC"), pd.Timestamp("2026-01-01", tz="UTC")),
    "diagnostic_2026": (pd.Timestamp("2026-01-01", tz="UTC"), END),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_protocol() -> dict:
    if sha256(PROTOCOL) != PROTOCOL_SHA:
        raise RuntimeError("Frozen higher-timeframe protocol changed")
    return json.loads(PROTOCOL.read_text())


def request_public_klines(symbol: str, cursor: int, end_ms: int) -> tuple[bytes, str]:
    query = urllib.parse.urlencode(
        {"symbol": symbol, "interval": "4h", "startTime": cursor, "endTime": end_ms - 1, "limit": 1000}
    )
    url = f"https://data-api.binance.vision/api/v3/klines?{query}"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                if response.status != 200:
                    raise RuntimeError(f"Binance HTTP {response.status}: {symbol}")
                return response.read(), url
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == 2:
                raise RuntimeError(
                    f"Binance data request unavailable: {symbol}: {type(exc).__name__}"
                ) from exc
            time.sleep(1 + attempt)
    raise AssertionError("unreachable")


def immutable_write(path: Path, content: bytes) -> None:
    if path.exists():
        if path.read_bytes() != content:
            raise RuntimeError(f"Raw page unexpectedly changed: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(content)
    temporary.replace(path)


def parse_page(content: bytes, symbol: str) -> list[list]:
    rows = json.loads(content)
    if not isinstance(rows, list) or any(not isinstance(row, list) or len(row) != 12 for row in rows):
        raise RuntimeError(f"Unexpected Binance Spot kline schema: {symbol}")
    return rows


def normalize_rows(rows: list[list], symbol: str) -> pd.DataFrame:
    frame = pd.DataFrame(
        rows,
        columns=[
            "open_ms",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_ms",
            "quote_volume",
            "trade_count",
            "taker_base",
            "taker_quote",
            "ignore",
        ],
    )
    if frame.empty:
        raise RuntimeError(f"No historical Spot data: {symbol}")
    for name in ("open", "high", "low", "close", "volume"):
        frame[name] = pd.to_numeric(frame[name], errors="raise")
    frame["open_ms"] = pd.to_numeric(frame["open_ms"], errors="raise").astype("int64")
    frame["close_ms"] = pd.to_numeric(frame["close_ms"], errors="raise").astype("int64")
    gaps = frame["open_ms"].diff().dropna()
    if frame["open_ms"].duplicated().any() or (gaps <= 0).any() or (gaps % BAR_MS != 0).any():
        raise RuntimeError(f"Historical Spot duplicate/order/grid error: {symbol}")
    partial = frame["close_ms"] != frame["open_ms"] + BAR_MS - 1
    if (frame.loc[partial, "close_ms"] < frame.loc[partial, "open_ms"]).any() or (
        frame.loc[partial, "close_ms"] > frame.loc[partial, "open_ms"] + BAR_MS - 1
    ).any():
        raise RuntimeError(f"Historical Spot invalid close timestamp: {symbol}")
    frame = frame.loc[~partial].copy()
    if (
        (frame["open_ms"] % BAR_MS != 0)
        | (frame["high"] < frame[["open", "close", "low"]].max(axis=1))
        | (frame["low"] > frame[["open", "close", "high"]].min(axis=1))
        | (frame["volume"] < 0)
        | (frame[["open", "high", "low", "close"]] <= 0).any(axis=1)
    ).any():
        raise RuntimeError(f"Historical Spot invalid OHLC/time/volume: {symbol}")
    out = frame[["open", "high", "low", "close", "volume"]].copy()
    out.index = pd.to_datetime(frame["open_ms"], unit="ms", utc=True)
    out.index.name = "time"
    out["close_time"] = pd.to_datetime(frame["close_ms"], unit="ms", utc=True).to_numpy()
    return out


def fetch() -> None:
    config = check_protocol()
    RAW.mkdir(parents=True, exist_ok=True)
    NORMALIZED.mkdir(parents=True, exist_ok=True)
    all_entries, series, total_pages, total_bytes, total_rows = [], {}, 0, 0, 0
    start_ms = START.value // 1_000_000
    end_ms = NEW_END.value // 1_000_000
    reused_pages = 0
    for symbol in config["universe"]:
        cursor, pages, rows_all = start_ms, 0, []
        while cursor < end_ms:
            cached = list(RAW.glob(f"{symbol}_{cursor}_*.json"))
            if len(cached) > 1:
                raise RuntimeError(f"Ambiguous cached page: {symbol} {cursor}")
            if cached:
                content = cached[0].read_bytes()
                query = urllib.parse.urlencode(
                    {
                        "symbol": symbol,
                        "interval": "4h",
                        "startTime": cursor,
                        "endTime": end_ms - 1,
                        "limit": 1000,
                    }
                )
                url = f"https://data-api.binance.vision/api/v3/klines?{query}"
                reused_pages += 1
            else:
                content, url = request_public_klines(symbol, cursor, end_ms)
            rows = parse_page(content, symbol)
            total_pages += 1
            total_bytes += len(content)
            if total_pages > 90 or total_bytes > 30 * 1024 * 1024:
                raise RuntimeError("Predeclared download budget exceeded")
            if not rows:
                break
            first_open, last_open = int(rows[0][0]), int(rows[-1][0])
            if first_open < cursor or last_open >= end_ms or last_open < first_open:
                raise RuntimeError(f"Unexpected Binance pagination: {symbol}")
            path = RAW / f"{symbol}_{first_open}_{last_open}.json"
            immutable_write(path, content)
            all_entries.append(
                {
                    "symbol": symbol,
                    "file": str(path.relative_to(ROOT)),
                    "url": url,
                    "http_status": 200,
                    "sha256": sha256(path),
                    "bytes": len(content),
                    "rows": len(rows),
                    "first_open_ms": first_open,
                    "last_open_ms": last_open,
                    "retrieved_utc": datetime.now(UTC).isoformat(),
                }
            )
            rows_all.extend(rows)
            pages += 1
            cursor = last_open + BAR_MS
            time.sleep(0.05)
        out = normalize_rows(rows_all, symbol)
        total_rows += len(out)
        if total_rows > 80_000:
            raise RuntimeError("Predeclared candle budget exceeded")
        output = NORMALIZED / f"{symbol}_4h_2020_2023.csv.gz"
        out.to_csv(output, compression={"method": "gzip", "mtime": 0}, index_label="time")
        series[symbol] = {
            "file": str(output.relative_to(ROOT)),
            "sha256": sha256(output),
            "rows": len(out),
            "first_open": out.index.min().isoformat(),
            "last_open": out.index.max().isoformat(),
            "pages": pages,
            "partial_4h_excluded": sum(int(row[6]) - int(row[0]) != BAR_MS - 1 for row in rows_all),
            "gap_count": int((out.index.to_series().diff().dropna() > BAR).sum()),
            "missing_4h_bars": int(((out.index.to_series().diff().dropna() / BAR) - 1).sum()),
        }
        print(
            f"{symbol}: {len(out)} verified 4h bars, {pages} public pages, first={out.index.min().isoformat()}, missing={series[symbol]['missing_4h_bars']}",
            flush=True,
        )
    manifest = {
        "protocol_sha256": PROTOCOL_SHA,
        "source": "official Binance Spot public REST /api/v3/klines",
        "source_documentation": "https://developers.binance.com/en/docs/products/spot/rest-api",
        "download_utc": datetime.now(UTC).isoformat(),
        "pages": all_entries,
        "series": series,
        "total_pages": total_pages,
        "total_raw_bytes": total_bytes,
        "total_new_rows": total_rows,
        "reused_pages": reused_pages,
        "schema": ["time", "open", "high", "low", "close", "volume", "close_time"],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"fetch complete: pages={total_pages}, raw_bytes={total_bytes}, rows={total_rows}")


def verify_manifest() -> dict:
    config = check_protocol()
    manifest = json.loads(MANIFEST.read_text())
    if manifest["protocol_sha256"] != PROTOCOL_SHA or set(manifest["series"]) != set(config["universe"]):
        raise RuntimeError("Higher-timeframe data manifest mismatch")
    for entry in manifest["pages"]:
        path = ROOT / entry["file"]
        if not path.exists() or sha256(path) != entry["sha256"] or path.stat().st_size != entry["bytes"]:
            raise RuntimeError(f"Raw Spot page changed: {path}")
    for entry in manifest["series"].values():
        path = ROOT / entry["file"]
        if not path.exists() or sha256(path) != entry["sha256"]:
            raise RuntimeError(f"Normalized Spot history changed: {path}")
    return manifest


def read_spot_4h(symbol: str, manifest: dict) -> tuple[pd.DataFrame, dict]:
    history = ROOT / manifest["series"][symbol]["file"]
    middle = ROOT / "runtime" / "walk_forward" / "data" / f"{symbol}_4h_2024-01-01_2026-01-01.csv"
    recent = REPORTS / "OOS_2026_DATA" / f"{symbol}_4h_2026-01-01_2026-10-26T04.csv"
    walk = json.loads((REPORTS / "WALK_FORWARD_RESULTS.json").read_text())
    expected_middle = next(
        row["data"]["sha256"]
        for row in walk["results"]
        if row["symbol"] == symbol and row["timeframe"] == "4h"
    )
    oos = json.loads((REPORTS / "OOS_2026_CONFIRMATION.json").read_text())
    expected_recent = next(row["sha256"] for row in oos["data_integrity"] if row["symbol"] == symbol)
    if sha256(middle) != expected_middle or sha256(recent) != expected_recent:
        raise RuntimeError(f"Existing Spot source hash changed: {symbol}")
    paths = [history, middle, recent]
    frames = []
    for path, start, end in zip(
        paths,
        (START, NEW_END, pd.Timestamp("2026-01-01", tz="UTC")),
        (NEW_END, pd.Timestamp("2026-01-01", tz="UTC"), END),
        strict=True,
    ):
        part = pd.read_csv(path, parse_dates=["time", "close_time"])
        part["time"] = pd.to_datetime(part["time"], utc=True)
        part["close_time"] = pd.to_datetime(part["close_time"], utc=True)
        frames.append(
            part.loc[
                (part["time"] >= start) & (part["time"] < end),
                ["time", "open", "high", "low", "close", "volume", "close_time"],
            ]
        )
    full = pd.concat(frames, ignore_index=True).sort_values("time").set_index("time")
    if full.empty or full.index.duplicated().any() or not full.index.is_monotonic_increasing:
        raise RuntimeError(f"Spot duplicate/order/empty: {symbol}")
    gaps = full.index.to_series().diff().dropna()
    if (gaps <= pd.Timedelta(0)).any() or (gaps % BAR != pd.Timedelta(0)).any():
        raise RuntimeError(f"Spot 4h timestamp grid broken: {symbol}")
    if ((full.index.asi8 // 1_000_000) % BAR_MS != 0).any():
        raise RuntimeError(f"Spot 4h UTC alignment broken: {symbol}")
    if not (full["close_time"] == full.index + BAR - pd.Timedelta(milliseconds=1)).all():
        raise RuntimeError(f"Spot close time broken: {symbol}")
    invalid = (
        (full["high"] < full[["open", "close", "low"]].max(axis=1))
        | (full["low"] > full[["open", "close", "high"]].min(axis=1))
        | (full["volume"] < 0)
        | (full[["open", "high", "low", "close"]] <= 0).any(axis=1)
    )
    if invalid.any() or not np.isfinite(full[["open", "high", "low", "close", "volume"]]).all().all():
        raise RuntimeError(f"Spot OHLC invalid: {symbol}")
    grid = pd.date_range(full.index.min(), full.index.max(), freq="4h", tz="UTC", name="time")
    padded = full.reindex(grid)
    info = {
        "symbol": symbol,
        "first_open": full.index.min().isoformat(),
        "last_open": full.index.max().isoformat(),
        "observed_4h": len(full),
        "missing_4h": int(padded["close"].isna().sum()),
        "gaps": int((gaps > BAR).sum()),
        "duplicates": 0,
        "invalid_ohlc": 0,
        "source_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in paths},
    }
    return padded, info


def aggregate_daily(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    daily = frame.groupby(pd.Grouper(freq="1D", label="left", closed="left"))
    counts = daily["close"].count()
    complete = counts == 6
    result = pd.DataFrame(
        {
            "open": daily["open"].first(),
            "high": daily["high"].max(),
            "low": daily["low"].min(),
            "close": daily["close"].last(),
            "volume": daily["volume"].sum(min_count=6),
        }
    )
    result.loc[~complete, ["open", "high", "low", "close", "volume"]] = np.nan
    result.index.name = "time"
    result["close_time"] = result.index + pd.Timedelta(days=1) - pd.Timedelta(milliseconds=1)
    return result, int((~complete).sum())


def trailing_percentile(values: pd.Series, window: int) -> pd.Series:
    array = values.to_numpy(float)
    result = np.full(len(array), np.nan)
    for i in range(window, len(array)):
        prior = array[i - window : i]
        if np.isfinite(array[i]) and np.isfinite(prior).all():
            result[i] = np.mean(prior <= array[i])
    return pd.Series(result, index=values.index)


def price_features(frame: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    bars_per_day = 6 if timeframe == "4h" else 1
    close = frame["close"]
    log_return = np.log(close / close.shift(1))
    sigma = log_return.rolling(30 * bars_per_day, min_periods=30 * bars_per_day).std(ddof=0) * math.sqrt(
        bars_per_day
    )
    result = pd.DataFrame(index=frame.index + (BAR if timeframe == "4h" else pd.Timedelta(days=1)))
    result.index.name = "decision_time"
    result["sigma_daily"] = sigma.to_numpy()
    result["vol_percentile"] = trailing_percentile(sigma, 180 * bars_per_day).to_numpy()
    result["z7"] = (np.log(close / close.shift(7 * bars_per_day)) / (sigma * math.sqrt(7))).to_numpy()
    result["z30"] = (np.log(close / close.shift(30 * bars_per_day)) / (sigma * math.sqrt(30))).to_numpy()
    pre_high = frame["high"].shift(1).rolling(30 * bars_per_day, min_periods=30 * bars_per_day).max()
    pre_low = frame["low"].shift(1).rolling(30 * bars_per_day, min_periods=30 * bars_per_day).min()
    pre_range = (pre_high - pre_low) / close.shift(1)
    result["pre_high"] = pre_high.to_numpy()
    result["pre_low"] = pre_low.to_numpy()
    result["range_percentile"] = trailing_percentile(pre_range, 180 * bars_per_day).to_numpy()
    pre_sigma = sigma.shift(3 * bars_per_day)
    result["pre_trend_z"] = (
        np.log(close.shift(3 * bars_per_day) / close.shift(33 * bars_per_day)) / (pre_sigma * math.sqrt(30))
    ).to_numpy()
    result["pullback_z"] = (
        np.log(close / close.shift(3 * bars_per_day)) / (pre_sigma * math.sqrt(3))
    ).to_numpy()
    result["close"] = close.to_numpy()
    result["vol_state"] = np.select(
        [result["vol_percentile"] < 1 / 3, result["vol_percentile"] > 2 / 3],
        ["low", "high"],
        default="normal",
    )
    result.loc[result["vol_percentile"].isna(), "vol_state"] = None
    return result


def forward_outcomes(frame: pd.DataFrame, horizon: int, timeframe: str) -> pd.DataFrame:
    interval = BAR if timeframe == "4h" else pd.Timedelta(days=1)
    entry = frame["open"].shift(-1)
    future_close = frame["close"].shift(-horizon)
    highs = pd.concat([frame["high"].shift(-step) for step in range(1, horizon + 1)], axis=1)
    lows = pd.concat([frame["low"].shift(-step) for step in range(1, horizon + 1)], axis=1)
    result = pd.DataFrame(index=frame.index + interval)
    result.index.name = "decision_time"
    result["entry_open"] = entry.to_numpy()
    result["signed_pct"] = ((future_close / entry - 1) * 100).to_numpy()
    result["absolute_pct"] = result["signed_pct"].abs()
    result["mfe_pct"] = ((highs.max(axis=1, skipna=False) / entry - 1) * 100).to_numpy()
    result["mae_pct"] = ((lows.min(axis=1, skipna=False) / entry - 1) * 100).to_numpy()
    return result


def cost_hurdles(value: float) -> dict[str, float]:
    return {"zero": value, "base": value - 0.3, "double": value - 0.6}


def cooldown(events: pd.DataFrame, days: int = 14) -> pd.DataFrame:
    if events.empty:
        return events
    chosen, last = [], None
    for stamp in events.sort_index().index:
        if last is None or stamp - last >= pd.Timedelta(days=days):
            chosen.append(stamp)
            last = stamp
    return events.loc[chosen]


def select_family(frame: pd.DataFrame, family: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    if family == "H1_H2":
        direction = np.sign(frame["z7"])
        event = frame["z7"].abs() >= 2
        control = frame["z7"].abs().between(0.5, 1.5, inclusive="left")
    elif family == "H3":
        direction = pd.Series(
            np.select(
                [frame["close"] > frame["pre_high"], frame["close"] < frame["pre_low"]], [1, -1], default=0
            ),
            index=frame.index,
        )
        breakout = direction != 0
        event = breakout & (frame["range_percentile"] <= 0.25)
        control = breakout & (frame["range_percentile"] > 0.25)
    elif family == "H4":
        direction = np.sign(frame["pre_trend_z"])
        signed_pullback = direction * frame["pullback_z"]
        trend = frame["pre_trend_z"].abs() >= 1.5
        event = trend & signed_pullback.between(-1.5, -0.5, inclusive="both")
        control = trend & signed_pullback.between(-0.5, 0.5, inclusive="neither")
    else:
        raise ValueError(family)
    eligible = frame["vol_state"].notna() & np.isfinite(direction) & (direction != 0)
    events = frame.loc[event & eligible].copy()
    controls = frame.loc[control & eligible].copy()
    events["direction"] = direction.loc[events.index]
    controls["direction"] = direction.loc[controls.index]
    return cooldown(events), controls


def eligible_segment(frame: pd.DataFrame, split: str, timeframe: str, horizon: int) -> pd.DataFrame:
    start, end = SPLITS[split]
    interval = BAR if timeframe == "4h" else pd.Timedelta(days=1)
    return frame.loc[(frame.index >= start) & (frame.index + interval * horizon < end)].copy()


def orient_excursions(direction: float, mfe: float, mae: float) -> tuple[float, float]:
    return (mfe, mae) if direction > 0 else (-mae, -mfe)


def family_events(frame: pd.DataFrame, symbol: str, timeframe: str, split: str, family: str) -> list[dict]:
    events, controls = select_family(frame, family)
    if events.empty:
        return []
    controls = controls.loc[
        np.isfinite(controls[["signed_pct", "entry_open", "mfe_pct", "mae_pct"]]).all(axis=1)
    ].copy()
    controls["directed_pct"] = controls["direction"] * controls["signed_pct"]
    controls["year"] = controls.index.year
    control_means = controls.groupby(["year", "vol_state", "direction"])["directed_pct"].mean()
    records = []
    for stamp, event in events.iterrows():
        direction = float(event["direction"])
        key = (stamp.year, event["vol_state"], direction)
        outcome_available = bool(
            np.isfinite(event[["signed_pct", "entry_open", "mfe_pct", "mae_pct"]].to_numpy(dtype=float)).all()
        )
        matched = outcome_available and key in control_means.index
        control = float(control_means[key]) if matched else None
        raw = direction * float(event["signed_pct"]) if outcome_available else None
        mfe, mae = (
            orient_excursions(direction, float(event["mfe_pct"]), float(event["mae_pct"]))
            if outcome_available
            else (None, None)
        )
        base = {
            "family": family,
            "symbol": symbol,
            "timeframe": timeframe,
            "split": split,
            "decision_time": stamp.isoformat(),
            "year": stamp.year,
            "month": stamp.strftime("%Y-%m"),
            "direction": int(direction),
            "vol_state": event["vol_state"],
            "btc_regime": event["btc_regime"],
            "entry_open": float(event["entry_open"]) if outcome_available else None,
            "signed_forward_pct": float(event["signed_pct"]) if outcome_available else None,
            "mfe_pct": mfe,
            "mae_pct": mae,
            "outcome_available": outcome_available,
            "matched": matched,
            "matched_control_pct": control,
            "raw_directed_pct": raw,
            "excess_pct": raw - control if matched else None,
            "active_symbols": None,
            "top_symbols": None,
            "bottom_symbols": None,
            "middle_forward_pct": None,
        }
        if family == "H1_H2":
            records.append(
                base
                | {
                    "hypothesis": "H1",
                    "raw_hypothesis_pct": raw,
                    "effect_pct": raw - control if matched else None,
                }
            )
            records.append(
                base
                | {
                    "hypothesis": "H2",
                    "raw_hypothesis_pct": -raw if raw is not None else None,
                    "effect_pct": control - raw if matched else None,
                }
            )
        else:
            records.append(
                base
                | {
                    "hypothesis": family,
                    "raw_hypothesis_pct": raw,
                    "effect_pct": raw - control if matched else None,
                }
            )
    return records


def rank_cross_section(
    candidates: list[dict],
) -> tuple[float, list[str], list[str], float, float, float, float]:
    ranked = sorted(candidates, key=lambda row: (-row["z30"], row["symbol"]))
    top, bottom, middle = ranked[:2], ranked[-2:], ranked[2:-2]
    top_return = float(np.mean([row["forward_pct"] for row in top]))
    bottom_return = float(np.mean([row["forward_pct"] for row in bottom]))
    middle_return = float(np.mean([row["forward_pct"] for row in middle])) if middle else float("nan")
    raw = (top_return - bottom_return) / 2
    mfe = (
        float(np.mean([row["mfe_pct"] for row in top])) - float(np.mean([row["mae_pct"] for row in bottom]))
    ) / 2
    mae = (
        float(np.mean([row["mae_pct"] for row in top])) - float(np.mean([row["mfe_pct"] for row in bottom]))
    ) / 2
    return (
        raw,
        [row["symbol"] for row in top],
        [row["symbol"] for row in bottom],
        middle_return,
        mfe,
        mae,
        top_return,
    )


def cross_section_events(series: dict, timeframe: str, split: str) -> tuple[list[dict], list[dict]]:
    start, end = SPLITS[split]
    interval = BAR if timeframe == "4h" else pd.Timedelta(days=1)
    horizon = 42 if timeframe == "4h" else 7
    records, snapshots = [], []
    for stamp in pd.date_range(START, END, freq="14D", tz="UTC"):
        if not (start <= stamp and stamp + interval * horizon < end):
            continue
        candidates = []
        for symbol, frame in series.items():
            if stamp not in frame.index:
                continue
            row = frame.loc[stamp]
            if not np.isfinite(row["z30"]):
                continue
            candidates.append(
                {
                    "symbol": symbol,
                    "z30": float(row["z30"]),
                    "forward_pct": float(row["signed_pct"]),
                    "mfe_pct": float(row["mfe_pct"]),
                    "mae_pct": float(row["mae_pct"]),
                }
            )
        if len(candidates) < 5:
            continue
        ranked = sorted(candidates, key=lambda item: (-item["z30"], item["symbol"]))
        outcome_available = all(
            np.isfinite(item["forward_pct"]) and np.isfinite(item["mfe_pct"]) and np.isfinite(item["mae_pct"])
            for item in ranked
        )
        if not outcome_available:
            records.append(
                {
                    "family": "H5",
                    "hypothesis": "H5",
                    "symbol": "CROSS_SECTION",
                    "timeframe": timeframe,
                    "split": split,
                    "decision_time": stamp.isoformat(),
                    "year": stamp.year,
                    "month": stamp.strftime("%Y-%m"),
                    "direction": 1,
                    "vol_state": None,
                    "btc_regime": None,
                    "entry_open": None,
                    "signed_forward_pct": None,
                    "mfe_pct": None,
                    "mae_pct": None,
                    "matched": False,
                    "outcome_available": False,
                    "matched_control_pct": None,
                    "raw_directed_pct": None,
                    "raw_hypothesis_pct": None,
                    "excess_pct": None,
                    "effect_pct": None,
                    "active_symbols": len(candidates),
                    "top_symbols": ",".join(item["symbol"] for item in ranked[:2]),
                    "bottom_symbols": ",".join(item["symbol"] for item in ranked[-2:]),
                    "middle_forward_pct": None,
                    "top_forward_pct": None,
                }
            )
            continue
        raw, top, bottom, middle_return, mfe, mae, top_return = rank_cross_section(candidates)
        btc_row = series["BTCUSDT"].loc[stamp] if stamp in series["BTCUSDT"].index else None
        btc_regime = btc_row["btc_regime"] if btc_row is not None else None
        records.append(
            {
                "family": "H5",
                "hypothesis": "H5",
                "symbol": "CROSS_SECTION",
                "timeframe": timeframe,
                "split": split,
                "decision_time": stamp.isoformat(),
                "year": stamp.year,
                "month": stamp.strftime("%Y-%m"),
                "direction": 1,
                "vol_state": None,
                "btc_regime": btc_regime,
                "entry_open": None,
                "signed_forward_pct": None,
                "mfe_pct": mfe,
                "mae_pct": mae,
                "matched": True,
                "outcome_available": True,
                "matched_control_pct": 0.0,
                "raw_directed_pct": raw,
                "raw_hypothesis_pct": raw,
                "excess_pct": raw,
                "effect_pct": raw,
                "active_symbols": len(candidates),
                "top_symbols": ",".join(top),
                "bottom_symbols": ",".join(bottom),
                "middle_forward_pct": middle_return,
                "top_forward_pct": top_return,
            }
        )
        snapshots.append(
            {
                "timeframe": timeframe,
                "split": split,
                "decision_time": stamp.isoformat(),
                "candidates": candidates,
            }
        )
    return records, snapshots


def block_bootstrap(events: pd.DataFrame, hypothesis: str, timeframe: str) -> dict:
    if events.empty:
        return {"n": 0, "months": 0, "mean_pct": None, "ci95_pct": None, "p": None}
    blocks = events.groupby("month")["effect_pct"].agg(["sum", "count"])
    sums, counts = blocks["sum"].to_numpy(float), blocks["count"].to_numpy(float)
    family_number = {"H1": 0, "H2": 0, "H3": 1, "H4": 2, "H5": 3}[hypothesis]
    rng = np.random.default_rng(20261028 + family_number * 10 + (timeframe == "1d"))
    draw = rng.integers(0, len(blocks), size=(1000, len(blocks)))
    sampled = sums[draw].sum(axis=1) / counts[draw].sum(axis=1)
    mean = float(events["effect_pct"].mean())
    null_sampled = ((sums - mean * counts)[draw]).sum(axis=1) / counts[draw].sum(axis=1)
    if hypothesis in ("H1", "H2"):
        p = float((np.count_nonzero(np.abs(null_sampled) >= abs(mean)) + 1) / 1001)
    else:
        p = float((np.count_nonzero(null_sampled >= mean) + 1) / 1001)
    return {
        "n": len(events),
        "months": len(blocks),
        "mean_pct": mean,
        "ci95_pct": [float(np.quantile(sampled, 0.025)), float(np.quantile(sampled, 0.975))],
        "p": p,
    }


def summarize(
    events: pd.DataFrame, hypothesis: str, timeframe: str, h5_snapshots: list[dict], symbols: list[str]
) -> dict:
    matched = events.loc[events["matched"] & events["effect_pct"].notna()].copy()
    stats = block_bootstrap(matched, hypothesis, timeframe)
    unavailable = int((~events["outcome_available"]).sum()) if not events.empty else 0
    result = {
        **stats,
        "total_events": len(events),
        "unmatched": len(events) - len(matched),
        "outcome_unavailable": unavailable,
        "unmatched_control": len(events) - len(matched) - unavailable,
    }
    if matched.empty:
        return result
    effects = matched["effect_pct"].to_numpy(float)
    raw = matched["raw_hypothesis_pct"].to_numpy(float)
    years = matched.groupby("year")["effect_pct"].agg(["count", "mean"]).to_dict("index")
    per_symbol = matched.groupby("symbol")["effect_pct"].agg(["count", "mean"]).to_dict("index")
    if hypothesis == "H5":
        split = matched["split"].iloc[0]
        valid_stamps = set(matched["decision_time"])
        current = [
            item
            for item in h5_snapshots
            if item["timeframe"] == timeframe
            and item["split"] == split
            and item["decision_time"] in valid_stamps
        ]
        loo = {}
        for excluded in symbols:
            values = [
                rank_cross_section([row for row in item["candidates"] if row["symbol"] != excluded])[0]
                for item in current
                if len(item["candidates"]) >= 6
            ]
            loo[excluded] = float(np.mean(values)) if values else None
        participation = {
            symbol: {
                "top": int(matched["top_symbols"].str.contains(symbol).sum()),
                "bottom": int(matched["bottom_symbols"].str.contains(symbol).sum()),
            }
            for symbol in symbols
        }
        h5_groups = {
            "top_mean_pct": float(matched["top_forward_pct"].mean()),
            "middle_mean_pct": float(matched["middle_forward_pct"].mean()),
            "bottom_mean_pct": float((matched["top_forward_pct"] - 2 * matched["raw_hypothesis_pct"]).mean()),
        }
    else:
        loo = {
            symbol: float(matched.loc[matched.symbol != symbol, "effect_pct"].mean())
            if (matched.symbol != symbol).any()
            else None
            for symbol in symbols
        }
        participation = None
        h5_groups = None
    positive = np.sort(effects[effects > 0])[::-1]
    top_n = max(1, math.ceil(len(effects) * 0.01))
    gaps = []
    for _, group in matched.groupby("symbol"):
        stamp = pd.to_datetime(group["decision_time"], utc=True).sort_values()
        gaps.extend((stamp.diff().dropna() / pd.Timedelta(days=1)).tolist())
    btc_sample = matched if hypothesis == "H5" else matched.loc[matched.symbol != "BTCUSDT"]
    return result | {
        "effect_median_pct": float(np.median(effects)),
        "raw_mean_pct": float(np.mean(raw)),
        "cost_hurdle_pct": cost_hurdles(float(np.mean(raw))),
        "effect_to_base_cost": float(stats["mean_pct"] / 0.3),
        "by_year": years,
        "by_symbol": per_symbol,
        "h5_participation": participation,
        "h5_group_forward_pct": h5_groups,
        "leave_one_symbol_out": loo,
        "without_best_pct": float((effects.sum() - effects.max()) / (len(effects) - 1))
        if len(effects) > 1
        else None,
        "top1_positive_contribution": float(positive[:top_n].sum() / positive.sum())
        if positive.size
        else None,
        "mfe_median_pct": float(matched["mfe_pct"].median()),
        "mae_median_pct": float(matched["mae_pct"].median()),
        "mfe_q10_q90": [float(matched["mfe_pct"].quantile(0.1)), float(matched["mfe_pct"].quantile(0.9))],
        "mae_q10_q90": [float(matched["mae_pct"].quantile(0.1)), float(matched["mae_pct"].quantile(0.9))],
        "btc_regime": btc_sample.groupby("btc_regime")["effect_pct"].agg(["count", "mean"]).to_dict("index"),
        "median_days_between_events": float(np.median(gaps)) if gaps else None,
    }


def safe_json(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): safe_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [safe_json(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    return value


def holm_adjust(rows: list[dict]) -> None:
    unique = {}
    for row in rows:
        key = ("H1_H2" if row["hypothesis"] in ("H1", "H2") else row["hypothesis"], row["timeframe"])
        unique[key] = row["validation"]["p"] if key not in unique else unique[key]
    ordered = sorted(unique.items(), key=lambda item: item[1] if item[1] is not None else 1.0)
    adjusted, maximum = {}, 0.0
    for i, (key, p) in enumerate(ordered):
        maximum = max(maximum, min(1.0, (p if p is not None else 1.0) * (len(ordered) - i)))
        adjusted[key] = maximum
    for row in rows:
        key = ("H1_H2" if row["hypothesis"] in ("H1", "H2") else row["hypothesis"], row["timeframe"])
        row["holm_p"] = adjusted[key]


def classify(row: dict, symbols: list[str]) -> str:
    val = row["validation"]
    if val["n"] == 0 or val["mean_pct"] <= 0:
        return "REJECT"
    minimum = 50 if row["hypothesis"] == "H5" else 100
    if val["n"] < minimum or val["months"] < 18:
        return "REJECT"
    symbol_ok = (
        all(
            val["leave_one_symbol_out"].get(symbol) is not None and val["leave_one_symbol_out"][symbol] > 0
            for symbol in symbols
        )
        if row["hypothesis"] == "H5"
        else sum(item["mean"] > 0 for item in val["by_symbol"].values()) >= 5
    )
    btc = val["btc_regime"]
    btc_ok = all(
        item["mean"] > 0 for key, item in btc.items() if key in ("up", "down") and item["count"] >= 30
    )
    robust_internal = (
        val["mean_pct"] >= 0.6
        and val["cost_hurdle_pct"]["base"] > 0
        and val["ci95_pct"][0] > 0
        and row["holm_p"] < 0.05
        and len(val["by_year"]) >= 3
        and sum(item["mean"] > 0 for item in val["by_year"].values()) >= 2
        and symbol_ok
        and all(value is not None and value > 0 for value in val["leave_one_symbol_out"].values())
        and val["without_best_pct"] > 0
        and btc_ok
    )
    return "PROMISING" if robust_internal else "WEAK"


def secondary_diagnostics(events: pd.DataFrame, prices: dict, config: dict) -> list[dict]:
    rows = []
    for timeframe in ("4h", "1d"):
        interval = BAR if timeframe == "4h" else pd.Timedelta(days=1)
        horizons = (6, 18) if timeframe == "4h" else (1, 3, 14)
        outcomes = {
            symbol: {h: forward_outcomes(frame, h, timeframe) for h in horizons}
            for symbol, frame in prices[timeframe].items()
        }
        for split in ("validation", "diagnostic_2026"):
            end = SPLITS[split][1]
            for hypothesis in ("H1", "H2", "H3", "H4", "H5"):
                subset = events.loc[
                    (events.timeframe == timeframe)
                    & (events.split == split)
                    & (events.hypothesis == hypothesis)
                    & events.matched
                ]
                for horizon in horizons:
                    values = []
                    for event in subset.itertuples():
                        stamp = pd.Timestamp(event.decision_time)
                        if stamp + horizon * interval >= end:
                            continue
                        if hypothesis == "H5":
                            top = event.top_symbols.split(",")
                            bottom = event.bottom_symbols.split(",")
                            try:
                                top_forward = [
                                    float(outcomes[s][horizon].loc[stamp, "signed_pct"]) for s in top
                                ]
                                bottom_forward = [
                                    float(outcomes[s][horizon].loc[stamp, "signed_pct"]) for s in bottom
                                ]
                            except KeyError:
                                continue
                            value = (np.mean(top_forward) - np.mean(bottom_forward)) / 2
                        else:
                            try:
                                forward = float(outcomes[event.symbol][horizon].loc[stamp, "signed_pct"])
                            except KeyError:
                                continue
                            value = event.direction * forward * (-1 if hypothesis == "H2" else 1)
                        if np.isfinite(value):
                            values.append(float(value))
                    rows.append(
                        {
                            "hypothesis": hypothesis,
                            "timeframe": timeframe,
                            "split": split,
                            "horizon_bars": horizon,
                            "n": len(values),
                            "raw_mean_pct": float(np.mean(values)) if values else None,
                        }
                    )
    return rows


def evaluate() -> None:
    config = check_protocol()
    manifest = verify_manifest()
    prices, features, integrity = {"4h": {}, "1d": {}}, {"4h": {}, "1d": {}}, []
    for symbol in config["universe"]:
        spot_4h, info = read_spot_4h(symbol, manifest)
        daily, incomplete_days = aggregate_daily(spot_4h)
        info["observed_1d"] = int(daily["close"].notna().sum())
        info["incomplete_1d_excluded"] = incomplete_days
        info["new_history"] = manifest["series"][symbol]
        integrity.append(info)
        for timeframe, bars in (("4h", spot_4h), ("1d", daily)):
            prices[timeframe][symbol] = bars
            horizon = 42 if timeframe == "4h" else 7
            features[timeframe][symbol] = price_features(bars, timeframe).join(
                forward_outcomes(bars, horizon, timeframe)
            )
    for timeframe in ("4h", "1d"):
        btc = features[timeframe]["BTCUSDT"]["z30"]
        regime = pd.Series(
            np.select([btc > 0.5, btc < -0.5], ["up", "down"], default="neutral"), index=btc.index
        )
        regime.loc[btc.isna()] = None
        for frame in features[timeframe].values():
            frame["btc_regime"] = regime.reindex(frame.index)
    all_events, h5_snapshots = [], []
    for timeframe in ("4h", "1d"):
        horizon = 42 if timeframe == "4h" else 7
        for split in SPLITS:
            segmented = {
                symbol: eligible_segment(frame, split, timeframe, horizon)
                for symbol, frame in features[timeframe].items()
            }
            for symbol, frame in segmented.items():
                for family in ("H1_H2", "H3", "H4"):
                    all_events.extend(family_events(frame, symbol, timeframe, split, family))
            records, snapshots = cross_section_events(segmented, timeframe, split)
            all_events.extend(records)
            h5_snapshots.extend(snapshots)
    events = pd.DataFrame(all_events).sort_values(
        ["hypothesis", "timeframe", "split", "symbol", "decision_time"]
    )
    events.to_csv(RESULT_CSV, index=False)
    common_start = {}
    for timeframe in ("4h", "1d"):
        starts = []
        for frame in features[timeframe].values():
            complete = frame.loc[
                frame[["z7", "z30", "vol_percentile", "range_percentile", "pre_trend_z", "pullback_z"]]
                .notna()
                .all(axis=1)
            ]
            starts.append(complete.index.min())
        common_start[timeframe] = max(starts).isoformat()
    primary = []
    for hypothesis in ("H1", "H2", "H3", "H4", "H5"):
        for timeframe in ("4h", "1d"):
            subset = events.loc[(events.hypothesis == hypothesis) & (events.timeframe == timeframe)]
            summaries = {
                split: summarize(
                    subset.loc[subset.split == split], hypothesis, timeframe, h5_snapshots, config["universe"]
                )
                for split in SPLITS
            }
            common = subset.loc[
                (subset.split == "validation")
                & (pd.to_datetime(subset.decision_time, utc=True) >= pd.Timestamp(common_start[timeframe]))
            ]
            summaries["common_period"] = summarize(
                common, hypothesis, timeframe, h5_snapshots, config["universe"]
            )
            row = {
                "hypothesis": hypothesis,
                "timeframe": timeframe,
                **summaries,
                "validation_events_per_year_universe": summaries["validation"]["total_events"] / 3,
                "validation_events_per_year_per_symbol": summaries["validation"]["total_events"] / 24
                if hypothesis != "H5"
                else None,
            }
            primary.append(row)
    holm_adjust(primary)
    for row in primary:
        row["class"] = classify(row, config["universe"])
    classes = {row["class"] for row in primary}
    verdict = (
        "PROMISING_HIGHER_TIMEFRAME_HYPOTHESIS_FOUND"
        if "PROMISING" in classes
        else "WEAK_HIGHER_TIMEFRAME_EFFECTS_ONLY"
        if "WEAK" in classes
        else "NO_HIGHER_TIMEFRAME_EDGE_FOUND"
    )
    secondary = secondary_diagnostics(events, prices, config)
    result = {
        "protocol_sha256": PROTOCOL_SHA,
        "code_sha256": sha256(Path(__file__)),
        "data_manifest_sha256": sha256(MANIFEST),
        "events_sha256": sha256(RESULT_CSV),
        "source": config["source"],
        "integrity": integrity,
        "common_start": common_start,
        "primary": primary,
        "secondary_exploratory": secondary,
        "overall_verdict": verdict,
        "strategy_design": "YES_FOR_SEPARATE_PROSPECTIVE_PROTOCOL" if "PROMISING" in classes else "NO",
        "technical_v1_change": "NO",
        "PAPER_change": "NO",
        "limitations": "2024-2026 previously analyzed; no pristine external holdout; event outcomes and cost hurdles are not strategy PnL",
    }
    result = safe_json(result)
    RESULT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    render_report(result)


def render_report(result: dict) -> None:
    rows = result["primary"]
    lines = [
        "# Higher-timeframe Spot edge: frozen 4h / 1d research",
        "",
        f"**Вердикт: `{result['overall_verdict']}`.** Это event study, не стратегия и не торговый PnL.",
        "",
        f"Замороженный JSON-протокол SHA-256 `{result['protocol_sha256']}`; код `{result['code_sha256']}`; data manifest `{result['data_manifest_sha256']}`; события `{result['events_sha256']}`.",
        "",
        "Источники: официальный публичный Binance Spot REST `/api/v3/klines` 4h за 2020–2023 и ранее сохранённые SHA-проверенные Spot 4h файлы проекта за 2024–2026. Новых Futures/AI данных нет. Daily — ровно шесть завершённых UTC 4h-свечей; неполные дни не используются. До первой наблюдаемой свечи каждой пары данные не достраивались; для старых пар это начало запрошенного диапазона, не дата листинга.",
        "",
        "Discovery 2020–2022; validation 2023–2025 с годовыми folds; 2026 до 2026-10-26 UTC — диагностический период. История 2024–2026 ранее исследовалась, чистого внешнего holdout нет. Основной результат — Spot next-open → close через 7 дней: 42×4h либо 7×1d. H1/H2 используют один и тот же набор сильных 7-дневных движений и считаются одним двусторонним тестом.",
        "",
        "## Основные результаты validation 2023–2025",
        "",
        "| H | TF | Matched N / всего | Эффект к контролю, % | 95% CI по месяцам | Holm p | Raw 0 / −0.30 / −0.60%, % | Effect / 0.30 | Класс |",
        "|---|---|---:|---:|---|---:|---|---:|---|",
    ]
    for row in rows:
        val = row["validation"]
        if val["n"]:
            cost = val["cost_hurdle_pct"]
            lines.append(
                f"| {row['hypothesis']} | {row['timeframe']} | {val['n']} / {val['total_events']} | {val['mean_pct']:+.3f} | [{val['ci95_pct'][0]:+.3f}, {val['ci95_pct'][1]:+.3f}] | {row['holm_p']:.3f} | {cost['zero']:+.3f}/{cost['base']:+.3f}/{cost['double']:+.3f} | {val['effect_to_base_cost']:+.2f} | {row['class']} |"
            )
        else:
            lines.append(
                f"| {row['hypothesis']} | {row['timeframe']} | 0 / {val['total_events']} | — | — | — | — | — | {row['class']} |"
            )
    lines += [
        "",
        "H1/H2: одинаковое событие, противоположная интерпретация. H3: breakout после 30-дневного сжатия; H4: откат в предшествующем 30-дневном тренде; H5: половина 7-дневного spread сильнейших и слабейших двух активов. H1–H4 сравниваются с заранее определёнными наблюдениями той же пары, года, волатильностного режима и направления; unmatched события не входят в excess. H5 ранжирует только доступные к тому моменту активы. Часть направленных сценариев H1–H4 и нижняя сторона H5 требуют short exposure, которого обычный Spot не предоставляет: это диагностические распределения, не исполнимые Spot-сделки. Все cost values — пороги интерпретации, не реализованный PnL.",
        "",
        "## Данные и целостность",
        "",
        "| Пара | Первый 4h open UTC | Последний 4h open UTC | 4h наблюд. | Пропусков 4h | Полных 1d | Исключено 1d |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for info in result["integrity"]:
        lines.append(
            f"| {info['symbol']} | {info['first_open']} | {info['last_open']} | {info['observed_4h']} | {info['missing_4h']} | {info['observed_1d']} | {info['incomplete_1d_excluded']} |"
        )
    lines += [
        "",
        "SHA каждого исходного файла и расширенного ряда, число ранних частичных 4h-свечей и metadata публичных запросов находятся в data manifest и JSON. Пропуски не заполнялись; rolling features требуют полных окон. Daily соответствует Binance UTC day. Из-за ранних пропусков и обязательной 180-дневной непрерывной истории H1–H4 дают discovery-события только в 2022 году; H5, которому этот percentile не нужен, охватывает 2020–2022. Общий период с созревшими признаками всех восьми пар начинается: 4h `"
        + result["common_start"]["4h"]
        + "`, 1d `"
        + result["common_start"]["1d"]
        + "`; отдельный common-period результат есть в JSON.",
        "",
        "## Временная, парная и режимная устойчивость",
        "",
        "| H | TF | Discovery N / excess | 2023 / 2024 / 2025 excess, % | 2026 N / excess | Пар с плюсом | LOO min/max, % | BTC up/down, % | Без лучшего, % |",
        "|---|---|---|---|---|---:|---|---|---:|",
    ]
    for row in rows:
        val, disc, diag = row["validation"], row["discovery"], row["diagnostic_2026"]
        yearly = (
            "/".join(
                f"{val.get('by_year', {}).get(str(year), {}).get('mean', float('nan')):+.2f}"
                for year in (2023, 2024, 2025)
            )
            if val["n"]
            else "—"
        )
        disctxt = f"{disc['n']}/{disc['mean_pct']:+.2f}" if disc["n"] else "0/—"
        diagtxt = f"{diag['n']}/{diag['mean_pct']:+.2f}" if diag["n"] else "0/—"
        symbol_pos = (
            sum(item["mean"] > 0 for item in val.get("by_symbol", {}).values())
            if row["hypothesis"] != "H5"
            else "H5"
        )
        loo_values = [x for x in val.get("leave_one_symbol_out", {}).values() if x is not None]
        loo = f"{min(loo_values):+.2f}/{max(loo_values):+.2f}" if loo_values else "—"
        btc = val.get("btc_regime", {})
        btc_text = "/".join(
            f"{btc.get(state, {}).get('mean', float('nan')):+.2f}" for state in ("up", "down")
        )
        best = f"{val['without_best_pct']:+.2f}" if val["n"] else "—"
        lines.append(
            f"| {row['hypothesis']} | {row['timeframe']} | {disctxt} | {yearly} | {diagtxt} | {symbol_pos} | {loo} | {btc_text} | {best} |"
        )
    lines += [
        "",
        "В JSON: N по каждому году/символу/BTC regime, leave-one-symbol-out, top-1% вклад, медиана и квантили MFE/MAE. Для H1–H4 BTC regime рассчитывается только на альткоин-событиях; H5 — на уровне всего cross-section timestamp. H5 LOO пересчитывает ранги после исключения пары, а не только удаляет её сделки. Одновременные альткоин-события объединены в месячные bootstrap-блоки (1000 повторов, seed 20261028); p оценивается из bootstrap-выборки с центрированным нулевым эффектом, Holm корректирует восемь первичных family×TF тестов. Это приближение, не точное независимое испытание. Вторичные горизонты описательные и не меняют класс.",
        "",
        "## H5: сильные, средние и слабые активы",
        "",
        "| TF | Top-2 forward, % | Middle forward, % | Bottom-2 forward, % | Половина top−bottom, % |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        if row["hypothesis"] == "H5":
            groups = row["validation"]["h5_group_forward_pct"]
            lines.append(
                f"| {row['timeframe']} | {groups['top_mean_pct']:+.3f} | {groups['middle_mean_pct']:+.3f} | {groups['bottom_mean_pct']:+.3f} | {row['validation']['raw_mean_pct']:+.3f} |"
            )
    lines += [
        "",
        "Группы формируются только по прошлым 30-дневным движениям. Их forward returns показаны описательно; нижняя группа — не разрешение открыть short на Spot.",
        "",
        "## Частота и горизонт",
        "",
        "| H | TF | Событий в год на universe | На пару в год | Медиана дней между событиями | MFE/MAE медиана, % |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in rows:
        val = row["validation"]
        per_symbol = row["validation_events_per_year_per_symbol"]
        period = (
            f"{val['median_days_between_events']:.1f}"
            if val.get("median_days_between_events") is not None
            else "—"
        )
        excursion = f"{val['mfe_median_pct']:+.2f}/{val['mae_median_pct']:+.2f}" if val["n"] else "—"
        lines.append(
            f"| {row['hypothesis']} | {row['timeframe']} | {row['validation_events_per_year_universe']:.1f} | {per_symbol:.1f} | {period} | {excursion} |"
            if per_symbol is not None
            else f"| {row['hypothesis']} | {row['timeframe']} | {row['validation_events_per_year_universe']:.1f} | — | {period} | {excursion} |"
        )
    lines += [
        "",
        "Частота — число исследовательских эпизодов, не реализованный оборот портфеля. Набор H1/H2 один и тот же, поэтому две строки не суммируются. Cooldown 14 дней задан до результата. MFE/MAE не используются для подбора SL/TP.",
        "",
        "## Ограничения и решение",
        "",
        "Оценка эффектов зависит от выбранного до результата matched control; она не доказывает причинность или исполнимость. 2024–2026 уже рассматривались в других исследованиях; даже PROMISING потребует будущего prospective confirmation. Блочный bootstrap приближённо учитывает перекрывающиеся горизонты и общерыночную зависимость, но не делает наблюдения независимыми.",
        "",
        f"Основание проектировать отдельную low-turnover стратегию: `{result['strategy_design']}`. Изменять technical-v1: NO. Изменять PAPER: NO. Production/SQLite не менялись; DeepSeek и ордера не вызывались. Commit/push: NO.",
        "",
        "Повтор: `.venv/bin/python -B reports/higher_timeframe_edge_research.py --self-test`, затем `.venv/bin/python -B reports/higher_timeframe_edge_research.py --evaluate`. `--fetch` нужен только для первоначальной ограниченной загрузки; повторный анализ полностью offline.",
    ]
    RESULT_MD.write_text("\n".join(lines) + "\n")


def self_test() -> None:
    index = pd.date_range("2020-01-01", periods=12, freq="4h", tz="UTC", name="time")
    frame = pd.DataFrame(
        {
            "open": np.arange(12) + 100,
            "high": np.arange(12) + 101,
            "low": np.arange(12) + 99,
            "close": np.arange(12) + 100.5,
            "volume": np.ones(12),
        },
        index=index,
    )
    daily, missing = aggregate_daily(frame)
    assert missing == 0 and len(daily) == 2 and daily.iloc[0]["open"] == 100
    assert daily.iloc[0]["high"] == 106 and daily.iloc[0]["volume"] == 6
    outcome = forward_outcomes(frame, 2, "4h")
    assert outcome.iloc[0]["entry_open"] == 101
    assert outcome.iloc[0]["signed_pct"] == (102.5 / 101 - 1) * 100
    values = pd.Series(np.arange(10.0), index=range(10))
    assert np.isnan(trailing_percentile(values, 5).iloc[4])
    changed = values.copy()
    changed.iloc[7:] = -100
    assert trailing_percentile(changed, 5).iloc[6] == trailing_percentile(values, 5).iloc[6]
    assert cost_hurdles(0.5)["double"] == -0.09999999999999998
    assert (
        rank_cross_section(
            [
                {
                    "symbol": str(i),
                    "z30": float(i),
                    "forward_pct": float(i),
                    "mfe_pct": float(i) + 1,
                    "mae_pct": float(i) - 1,
                }
                for i in range(5)
            ]
        )[0]
        == 1.5
    )
    print("self-test PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--fetch", action="store_true")
    action.add_argument("--evaluate", action="store_true")
    action.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.fetch:
        fetch()
    elif args.evaluate:
        evaluate()
    else:
        self_test()


if __name__ == "__main__":
    main()
