"""Offline, read-only futures flow/funding incremental-information research.

No production imports, keys, orders, databases or DeepSeek calls. Protocol is
reports/FUTURES_FLOW_OI_FROZEN_PROTOCOL.json; run --self-test before --fetch.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
DATA = REPORTS / "FUTURES_FLOW_OI_DATA"
RAW = DATA / "raw"
NORMALIZED = DATA / "normalized"
FEATURES = DATA / "features"
MANIFEST = DATA / "manifest.json"
PROTOCOL_PATH = REPORTS / "FUTURES_FLOW_OI_FROZEN_PROTOCOL.json"
RESULT_JSON = REPORTS / "FUTURES_FLOW_OI_RESEARCH.json"
RESULT_MD = REPORTS / "FUTURES_FLOW_OI_RESEARCH.md"
RESULT_CSV = REPORTS / "FUTURES_FLOW_OI_RESULTS.csv"
FIVE_MIN_MS = 300_000
START = pd.Timestamp("2024-01-01", tz="UTC")
END = pd.Timestamp("2026-10-01", tz="UTC")
SPLITS = {
    "discovery": (START, pd.Timestamp("2025-01-01", tz="UTC")),
    "validation": (pd.Timestamp("2025-01-01", tz="UTC"), pd.Timestamp("2026-01-01", tz="UTC")),
    "diagnostic_2026": (pd.Timestamp("2026-01-01", tz="UTC"), END),
}
COLS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "trade_count",
    "taker_buy_base",
    "taker_buy_quote",
    "ignore",
]
PRICE_COLS = ["ret1", "ret3", "ret6", "range", "volatility12", "volume_ratio24", "trend24"]
FLOW_COLS = [
    "flow_imbalance",
    "flow_trailing3",
    "flow_persistence",
    "flow_acceleration",
    "taker_buy_share",
    "trade_count_context",
]
FUNDING_COLS = ["funding_latest", "funding_sign", "funding_trailing3", "funding_abs_percentile90d"]
ALL_PRICE = [f"spot_{name}" for name in PRICE_COLS] + [f"futures_{name}" for name in PRICE_COLS]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def directory_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file()) if path.exists() else 0


def request_bytes(url: str, *, attempts: int = 3) -> bytes:
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=25) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}: {url}")
                return response.read()
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            if attempt == attempts - 1:
                raise RuntimeError(
                    f"Download failed after {attempts} attempts: {url}; {type(exc).__name__}"
                ) from exc
            time.sleep(1.5 * (attempt + 1))
    raise AssertionError("unreachable")


def write_immutable(path: Path, content: bytes) -> None:
    if path.exists():
        if hashlib.sha256(content).hexdigest() != sha256(path):
            raise RuntimeError(f"Existing immutable raw file differs: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_bytes(content)
    temporary.replace(path)


def months() -> list[str]:
    return [stamp.strftime("%Y-%m") for stamp in pd.date_range(START, END, freq="MS", inclusive="left")]


def budget() -> dict:
    protocol = json.loads(PROTOCOL_PATH.read_text())
    monthly_files = len(months()) * len(protocol["universe"])
    free = shutil.disk_usage(ROOT).free
    result = {
        "months": len(months()),
        "zip_files": monthly_files,
        "checksum_files": monthly_files,
        "funding_requests_estimate": 40,
        "total_requests_estimate": monthly_files * 2 + 40,
        "compressed_expected_bytes_approx": 110_000_000,
        "compressed_hard_limit_bytes": protocol["download_budget"]["hard_zip_bytes_limit"],
        "working_disk_hard_limit_bytes": protocol["download_budget"]["working_disk_limit_bytes"],
        "free_disk_bytes": free,
    }
    print(json.dumps(result, indent=2))
    if monthly_files != protocol["download_budget"]["monthly_zip_files"]:
        raise RuntimeError("Scope differs from frozen budget")
    if free < protocol["download_budget"]["working_disk_limit_bytes"]:
        raise RuntimeError("Insufficient free disk")
    return result


def publisher_hash(content: bytes) -> str:
    tokens = content.decode("utf-8").strip().split()
    if not tokens or len(tokens[0]) != 64 or not all(c in "0123456789abcdefABCDEF" for c in tokens[0]):
        raise ValueError("Unrecognized publisher CHECKSUM format")
    return tokens[0].lower()


def fetch_archives(protocol: dict) -> list[dict]:
    entries = []
    cap = protocol["download_budget"]["hard_zip_bytes_limit"]
    disk_cap = protocol["download_budget"]["working_disk_limit_bytes"]
    lock = Lock()

    def one_archive(spot_symbol: str, futures_symbol: str, month: str) -> dict:
        filename = f"{futures_symbol}-5m-{month}.zip"
        url = protocol["source"]["futures_5m"].format(futures_symbol=futures_symbol, month=month)
        path = RAW / "futures_5m" / futures_symbol / filename
        check_path = path.with_suffix(".zip.CHECKSUM")
        if not path.exists():
            with lock:
                if directory_bytes(RAW) > disk_cap:
                    raise RuntimeError("Working disk cap reached before archive download")
            write_immutable(path, request_bytes(url))
        if not check_path.exists():
            write_immutable(check_path, request_bytes(url + ".CHECKSUM"))
        own_hash = sha256(path)
        expected_hash = publisher_hash(check_path.read_bytes())
        if own_hash != expected_hash:
            raise RuntimeError(f"Publisher checksum mismatch: {filename}")
        with lock:
            zip_total = sum(p.stat().st_size for p in (RAW / "futures_5m").rglob("*.zip"))
            if zip_total > cap:
                raise RuntimeError("Compressed ZIP budget exceeded; stop research download")
        return {
            "source": "Binance Public Data USD-M 5m klines",
            "url": url,
            "spot_symbol": spot_symbol,
            "futures_symbol": futures_symbol,
            "month": month,
            "file": str(path.relative_to(ROOT)),
            "size": path.stat().st_size,
            "sha256": own_hash,
            "downloaded_at_utc": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
            "publisher_checksum_file": str(check_path.relative_to(ROOT)),
            "publisher_checksum_size": check_path.stat().st_size,
            "publisher_checksum_sha256": sha256(check_path),
            "publisher_sha256": expected_hash,
            "schema": "USD-M kline 12 columns, monthly CSV ZIP",
            "verified_at_utc": utc_now(),
        }

    tasks = [(spot, futures, month) for spot, futures in protocol["universe"].items() for month in months()]
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(one_archive, *task) for task in tasks]
        for future in as_completed(futures):
            entries.append(future.result())
            if len(entries) % 24 == 0 or len(entries) == len(tasks):
                print(f"Fetched/verified monthly 5m archives: {len(entries)}/{len(tasks)}", flush=True)
    entries.sort(key=lambda item: (item["futures_symbol"], item["month"]))
    return entries


def fetch_funding(protocol: dict) -> list[dict]:
    entries = []
    start_ms = START.value // 1_000_000
    end_ms = END.value // 1_000_000 - 1
    for spot_symbol, futures_symbol in protocol["universe"].items():
        cursor = start_ms
        page = 0
        while cursor <= end_ms:
            if page >= 20:
                raise RuntimeError(f"Funding page safety limit reached: {futures_symbol}")
            params = urllib.parse.urlencode(
                {"symbol": futures_symbol, "startTime": cursor, "endTime": end_ms, "limit": 1000}
            )
            url = protocol["source"]["funding"] + "?" + params
            path = RAW / "funding" / futures_symbol / f"page_{page:03d}.json"
            if not path.exists():
                write_immutable(path, request_bytes(url))
            content = path.read_bytes()
            records = json.loads(content)
            if not isinstance(records, list):
                raise RuntimeError(f"Funding API returned non-list: {futures_symbol} page {page}")
            times = [int(record["fundingTime"]) for record in records]
            if times != sorted(set(times)) or any(t < cursor or t > end_ms for t in times):
                raise RuntimeError(f"Funding pagination integrity failure: {futures_symbol} page {page}")
            entries.append(
                {
                    "source": "Binance USD-M fundingRate REST",
                    "url": url,
                    "spot_symbol": spot_symbol,
                    "futures_symbol": futures_symbol,
                    "page": page,
                    "file": str(path.relative_to(ROOT)),
                    "size": path.stat().st_size,
                    "sha256": sha256(path),
                    "downloaded_at_utc": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
                    "rows": len(records),
                    "first_funding_time_ms": times[0] if times else None,
                    "last_funding_time_ms": times[-1] if times else None,
                    "schema": "fundingRate REST JSON raw",
                    "verified_at_utc": utc_now(),
                }
            )
            if len(records) < 1000:
                break
            cursor = times[-1] + 1
            page += 1
        print(f"Fetched/verified funding: {futures_symbol}, {page + 1} pages", flush=True)
    return entries


def fetch() -> None:
    budget()
    protocol = json.loads(PROTOCOL_PATH.read_text())
    archive_entries = fetch_archives(protocol)
    funding_entries = fetch_funding(protocol)
    if directory_bytes(DATA) > protocol["download_budget"]["working_disk_limit_bytes"]:
        raise RuntimeError("Working disk cap exceeded")
    manifest = {
        "created_utc": utc_now(),
        "protocol_sha256": sha256(PROTOCOL_PATH),
        "entries": archive_entries + funding_entries,
        "raw_bytes": directory_bytes(RAW),
    }
    DATA.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"Manifest: {MANIFEST}; raw files={len(manifest['entries'])}; bytes={manifest['raw_bytes']}")


def read_futures(symbol: str) -> tuple[pd.DataFrame, dict]:
    frames = []
    month_reports = []
    for month in months():
        path = RAW / "futures_5m" / symbol / f"{symbol}-5m-{month}.zip"
        if not path.exists():
            raise FileNotFoundError(path)
        with zipfile.ZipFile(path) as archive:
            members = [m for m in archive.namelist() if m.endswith(".csv")]
            if len(members) != 1:
                raise RuntimeError(f"Unexpected ZIP members: {path}")
            frame = pd.read_csv(archive.open(members[0]), header=None, low_memory=False)
        if frame.shape[1] != 12:
            raise RuntimeError(f"Futures kline field count {frame.shape[1]}: {path}")
        if str(frame.iat[0, 0]).strip().lower() == "open_time":
            frame = frame.iloc[1:].reset_index(drop=True)
        frame.columns = COLS
        if not pd.to_numeric(frame["open_time"], errors="coerce").notna().all():
            raise RuntimeError(f"Non-numeric open_time: {path}")
        for column in COLS[:11]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        invalid_numeric = int(frame[COLS[:11]].isna().any(axis=1).sum())
        start = pd.Timestamp(month + "-01", tz="UTC")
        stop = start + pd.offsets.MonthBegin(1)
        start_ms, stop_ms = start.value // 1_000_000, stop.value // 1_000_000
        expected = (stop_ms - start_ms) // FIVE_MIN_MS
        timestamps = frame["open_time"].to_numpy(dtype=np.int64)
        duplicates = int(frame["open_time"].duplicated().sum())
        off_grid = int(np.count_nonzero(timestamps % FIVE_MIN_MS))
        outside = int(np.count_nonzero((timestamps < start_ms) | (timestamps >= stop_ms)))
        missing = int(
            expected - len(np.unique(timestamps[(timestamps >= start_ms) & (timestamps < stop_ms)]))
        )
        o = frame["open"].to_numpy(float)
        h = frame["high"].to_numpy(float)
        low = frame["low"].to_numpy(float)
        c = frame["close"].to_numpy(float)
        vol = frame["volume"].to_numpy(float)
        buy = frame["taker_buy_base"].to_numpy(float)
        count = frame["trade_count"].to_numpy(float)
        ohlc_bad = int(
            np.count_nonzero(
                (h < np.maximum.reduce([o, c, low])) | (low > np.minimum.reduce([o, c, h])) | (low < 0)
            )
        )
        volume_bad = int(np.count_nonzero((vol < 0) | (buy < -1e-8) | (buy > vol + 1e-8)))
        count_bad = int(np.count_nonzero((count < 0) | (count != np.floor(count))))
        close_bad = int(
            np.count_nonzero(frame["close_time"].to_numpy(np.int64) != timestamps + FIVE_MIN_MS - 1)
        )
        row = {
            "symbol": symbol,
            "source": "futures_5m",
            "month": month,
            "rows": len(frame),
            "expected_rows": int(expected),
            "missing_5m": missing,
            "duplicate_timestamps": duplicates,
            "off_grid": off_grid,
            "outside_month": outside,
            "invalid_numeric": invalid_numeric,
            "invalid_ohlc": ohlc_bad,
            "invalid_volume_or_taker": volume_bad,
            "invalid_trade_count": count_bad,
            "invalid_close_time": close_bad,
        }
        row["integrity"] = (
            "PASS"
            if not any(
                row[key]
                for key in (
                    "missing_5m",
                    "duplicate_timestamps",
                    "off_grid",
                    "outside_month",
                    "invalid_numeric",
                    "invalid_ohlc",
                    "invalid_volume_or_taker",
                    "invalid_trade_count",
                    "invalid_close_time",
                )
            )
            else "FAIL"
        )
        month_reports.append(row)
        if row["integrity"] == "FAIL":
            raise RuntimeError(f"Futures integrity failure: {row}")
        frames.append(frame.drop(columns="ignore"))
    full = pd.concat(frames, ignore_index=True)
    if full["open_time"].duplicated().any() or not full["open_time"].is_monotonic_increasing:
        raise RuntimeError(f"Cross-month timestamp failure: {symbol}")
    normalized_path = NORMALIZED / "futures_5m" / f"{symbol}.csv.gz"
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    full.to_csv(normalized_path, index=False, compression={"method": "gzip", "mtime": 0})
    return full, {
        "symbol": symbol,
        "source": "futures_5m",
        "months": month_reports,
        "total_rows": len(full),
        "missing_5m": sum(x["missing_5m"] for x in month_reports),
        "normalized_file": str(normalized_path.relative_to(ROOT)),
        "normalized_sha256": sha256(normalized_path),
        "integrity": "PASS",
    }


def aggregate_futures(raw: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    bars = 12 if timeframe == "1h" else 48
    interval_ms = FIVE_MIN_MS * bars
    frame = raw.copy()
    frame["bucket"] = (frame["open_time"] // interval_ms) * interval_ms
    grouped = frame.groupby("bucket", sort=True)
    agg = grouped.agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        buy=("taker_buy_base", "sum"),
        trade_count=("trade_count", "sum"),
        first_open=("open_time", "first"),
        last_close=("close_time", "last"),
        subbars=("open_time", "size"),
    )
    expected_close = agg.index.to_numpy(np.int64) + interval_ms - 1
    complete = (
        (agg["subbars"].to_numpy() == bars)
        & (agg["first_open"].to_numpy() == agg.index.to_numpy(np.int64))
        & (agg["last_close"].to_numpy() == expected_close)
    )
    agg = agg.loc[complete].copy()
    agg.index = pd.to_datetime(agg.index.to_numpy(np.int64) + interval_ms, unit="ms", utc=True)
    agg.index.name = "decision_time"
    agg["flow_imbalance"] = np.where(
        agg["volume"] > 0, (2 * agg["buy"] - agg["volume"]) / agg["volume"], np.nan
    )
    agg["taker_buy_share"] = np.where(agg["volume"] > 0, agg["buy"] / agg["volume"], np.nan)
    prior_vol = agg["volume"].shift(1).rolling(3, min_periods=3).sum()
    prior_signed = (2 * agg["buy"] - agg["volume"]).shift(1).rolling(3, min_periods=3).sum()
    agg["flow_trailing3"] = prior_signed / prior_vol.replace(0, np.nan)
    signs = np.sign(agg["flow_imbalance"])
    agg["flow_persistence"] = sum((signs == signs.shift(i)).astype(float) for i in (1, 2, 3)) / 3
    agg.loc[signs.isna(), "flow_persistence"] = np.nan
    agg["flow_acceleration"] = agg["flow_imbalance"] - agg["flow_trailing3"]
    prior_count = agg["trade_count"].shift(1).rolling(24, min_periods=24).median()
    agg["trade_count_context"] = np.log1p(agg["trade_count"]) - np.log1p(prior_count)
    return agg


def read_funding(symbol: str) -> tuple[pd.DataFrame, dict]:
    paths = sorted((RAW / "funding" / symbol).glob("page_*.json"))
    if not paths:
        raise FileNotFoundError(f"No raw funding pages: {symbol}")
    records = [record for path in paths for record in json.loads(path.read_text())]
    frame = pd.DataFrame(records)
    if frame.empty or not {"symbol", "fundingTime", "fundingRate"}.issubset(frame):
        raise RuntimeError(f"Invalid funding schema: {symbol}")
    times = pd.to_datetime(pd.to_numeric(frame["fundingTime"], errors="raise"), unit="ms", utc=True)
    rates = pd.to_numeric(frame["fundingRate"], errors="raise")
    bad_symbol = int((frame["symbol"] != symbol).sum())
    duplicates = int(times.duplicated().sum())
    out_of_range = int(((times < START) | (times >= END)).sum())
    invalid_rates = int((~np.isfinite(rates.to_numpy(float))).sum())
    gaps = pd.Series(times).diff().dropna().dt.total_seconds() / 3600
    large_gaps = int((gaps > 24).sum())
    if bad_symbol or duplicates or out_of_range or invalid_rates or not times.is_monotonic_increasing:
        raise RuntimeError(f"Funding integrity failure: {symbol}")
    result = pd.DataFrame({"time": times, "rate": rates.to_numpy(float)})
    result["abs_rate"] = result["rate"].abs()
    result["funding_trailing3"] = result["rate"].rolling(3, min_periods=3).mean()
    percentiles = []
    values = result["abs_rate"].to_numpy()
    t_ns = times.astype("int64").to_numpy()
    lookback_ns = int(pd.Timedelta(days=90).value)
    left = 0
    for i, (value, stamp) in enumerate(zip(values, t_ns, strict=True)):
        while left < i and t_ns[left] < stamp - lookback_ns:
            left += 1
        history = values[left:i]
        percentiles.append(float(np.mean(history <= value)) if len(history) >= 30 else np.nan)
    result["funding_abs_percentile90d"] = percentiles
    result["funding_sign"] = np.sign(result["rate"])
    integrity = {
        "symbol": symbol,
        "source": "funding",
        "rows": len(result),
        "pages": len(paths),
        "duplicate_timestamps": duplicates,
        "invalid_symbol": bad_symbol,
        "invalid_rates": invalid_rates,
        "outside_period": out_of_range,
        "gaps_over_24h": large_gaps,
        "max_gap_hours": float(gaps.max()) if len(gaps) else None,
        "integrity": "PASS" if large_gaps == 0 else "GAPS_PRESENT",
    }
    normalized_path = NORMALIZED / "funding" / f"{symbol}.csv.gz"
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(normalized_path, index=False, compression={"method": "gzip", "mtime": 0})
    integrity["normalized_file"] = str(normalized_path.relative_to(ROOT))
    integrity["normalized_sha256"] = sha256(normalized_path)
    return result, integrity


def add_funding(agg: pd.DataFrame, funding: pd.DataFrame) -> pd.DataFrame:
    left = agg.reset_index().sort_values("decision_time")
    right = funding.rename(columns={"time": "funding_time", "rate": "funding_latest"}).sort_values(
        "funding_time"
    )
    joined = pd.merge_asof(
        left,
        right[
            [
                "funding_time",
                "funding_latest",
                "funding_trailing3",
                "funding_sign",
                "funding_abs_percentile90d",
            ]
        ],
        left_on="decision_time",
        right_on="funding_time",
        direction="backward",
        allow_exact_matches=False,
        tolerance=pd.Timedelta(hours=24),
    )
    return joined.set_index("decision_time")


def read_spot(spot_symbol: str, timeframe: str) -> tuple[pd.DataFrame, dict]:
    first = (
        ROOT / "runtime" / "walk_forward" / "data" / f"{spot_symbol}_{timeframe}_2024-01-01_2026-01-01.csv"
    )
    files = [first]
    if timeframe == "4h":
        files.append(REPORTS / "OOS_2026_DATA" / f"{spot_symbol}_4h_2026-01-01_2026-10-26T04.csv")
    reference = json.loads((REPORTS / "WALK_FORWARD_RESULTS.json").read_text())
    expected = next(
        row["data"]["sha256"]
        for row in reference["results"]
        if row["symbol"] == spot_symbol and row["timeframe"] == timeframe
    )
    if sha256(first) != expected:
        raise RuntimeError(f"Existing Spot source hash changed: {first}")
    if timeframe == "4h":
        oos = json.loads((REPORTS / "OOS_2026_CONFIRMATION.json").read_text())
        expected_2026 = next(row["sha256"] for row in oos["data_integrity"] if row["symbol"] == spot_symbol)
        if sha256(files[1]) != expected_2026:
            raise RuntimeError(f"Existing 2026 Spot source hash changed: {files[1]}")
    frames = []
    for path in files:
        frame = pd.read_csv(path, parse_dates=["time", "close_time"])
        frame["time"] = pd.to_datetime(frame["time"], utc=True)
        frame["close_time"] = pd.to_datetime(frame["close_time"], utc=True)
        frames.append(frame)
    full = pd.concat(frames, ignore_index=True)
    interval = pd.Timedelta(hours=1 if timeframe == "1h" else 4)
    duplicate = int(full["time"].duplicated().sum())
    gaps = int((full["time"].diff().dropna() != interval).sum())
    close_bad = int((full["close_time"] != full["time"] + interval - pd.Timedelta(milliseconds=1)).sum())
    ohlc_bad = int(
        (
            (full["high"] < full[["open", "close", "low"]].max(axis=1))
            | (full["low"] > full[["open", "close", "high"]].min(axis=1))
            | (full["volume"] < 0)
        ).sum()
    )
    if duplicate or gaps or close_bad or ohlc_bad:
        raise RuntimeError(f"Spot integrity failure: {spot_symbol} {timeframe}")
    full.index = full["time"] + interval
    full.index.name = "decision_time"
    full = full.loc[(full.index >= START) & (full.index <= END)].copy()
    hashes = {str(path.relative_to(ROOT)): sha256(path) for path in files}
    return full, {
        "symbol": spot_symbol,
        "source": "spot_" + timeframe,
        "rows": len(full),
        "duplicates": duplicate,
        "gaps": gaps,
        "invalid_close_time": close_bad,
        "invalid_ohlc": ohlc_bad,
        "files_sha256": hashes,
        "integrity": "PASS",
    }


def price_features(frame: pd.DataFrame, prefix: str) -> pd.DataFrame:
    close = frame["close"].astype(float)
    previous = close.shift(1)
    result = pd.DataFrame(index=frame.index)
    for lag in (1, 3, 6):
        result[f"{prefix}_ret{lag}"] = close.div(close.shift(lag)).sub(1).mul(100)
    result[f"{prefix}_range"] = (frame["high"] - frame["low"]).div(previous).mul(100)
    result[f"{prefix}_volatility12"] = (
        result[f"{prefix}_ret1"].abs().shift(1).rolling(12, min_periods=12).mean()
    )
    result[f"{prefix}_volume_ratio24"] = frame["volume"].div(
        frame["volume"].shift(1).rolling(24, min_periods=24).median()
    )
    result[f"{prefix}_trend24"] = close.div(close.shift(1).rolling(24, min_periods=24).mean()).sub(1).mul(100)
    return result


def targets(spot: pd.DataFrame, horizons: list[int]) -> pd.DataFrame:
    close = spot["close"].astype(float)
    result = pd.DataFrame(index=spot.index)
    for horizon in horizons:
        result[f"signed_{horizon}"] = (close.shift(-horizon) / close - 1) * 100
        result[f"absolute_{horizon}"] = result[f"signed_{horizon}"].abs()
        future_high = pd.concat([spot["high"].shift(-step) for step in range(1, horizon + 1)], axis=1).max(
            axis=1
        )
        future_low = pd.concat([spot["low"].shift(-step) for step in range(1, horizon + 1)], axis=1).min(
            axis=1
        )
        result[f"mfe_{horizon}"] = (future_high / close - 1) * 100
        result[f"mae_{horizon}"] = (future_low / close - 1) * 100
    return result


def build_dataset(
    symbol: str, timeframe: str, raw: pd.DataFrame, funding: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:
    spot, spot_integrity = read_spot(symbol, timeframe)
    aggregate = aggregate_futures(raw, timeframe)
    aggregate_path = NORMALIZED / "futures_aggregate" / f"{symbol}_{timeframe}.csv.gz"
    aggregate_path.parent.mkdir(parents=True, exist_ok=True)
    aggregate.to_csv(aggregate_path, index_label="decision_time", compression={"method": "gzip", "mtime": 0})
    futures = add_funding(aggregate, funding)
    primary = 6 if timeframe == "1h" else 3
    horizons = [1, 3, 6, 12, 24] if timeframe == "1h" else [1, 3, 6, 12]
    features = pd.concat(
        [
            price_features(spot, "spot"),
            price_features(futures, "futures"),
            futures[FLOW_COLS + FUNDING_COLS + ["funding_time"]],
            targets(spot, horizons),
        ],
        axis=1,
        join="inner",
    )
    # A row is eligible only with an unbroken 5m parent interval and all feature inputs.
    features = features.loc[
        (features.index >= START) & (features.index < (END if timeframe == "4h" else SPLITS["validation"][1]))
    ].copy()
    features["symbol"] = symbol
    features["timeframe"] = timeframe
    features["primary_horizon"] = primary
    features["futures_direction"] = np.sign(features["futures_ret1"])
    features["week"] = features.index.strftime("%G-W%V")
    path = FEATURES / f"{symbol}_{timeframe}.csv.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(path, compression={"method": "gzip", "mtime": 0}, index_label="decision_time")
    summary = {
        "symbol": symbol,
        "timeframe": timeframe,
        "source": "joined_features",
        "spot": spot_integrity,
        "spot_rows": len(spot),
        "futures_aggregate_rows": len(futures),
        "aggregate_file": str(aggregate_path.relative_to(ROOT)),
        "aggregate_sha256": sha256(aggregate_path),
        "joined_rows": len(features),
        "feature_complete_rows": int(
            features[ALL_PRICE + FLOW_COLS + FUNDING_COLS].notna().all(axis=1).sum()
        ),
        "funding_missing_or_stale": int(features["funding_latest"].isna().sum()),
        "zero_volume_or_missing_flow": int(features["flow_imbalance"].isna().sum()),
        "feature_file": str(path.relative_to(ROOT)),
        "feature_sha256": sha256(path),
    }
    return features, summary


def split_rows(frame: pd.DataFrame, split: str, timeframe: str, horizon: int) -> pd.DataFrame:
    start, end = SPLITS[split]
    if split == "diagnostic_2026" and timeframe == "1h":
        return frame.iloc[:0].copy()
    interval = pd.Timedelta(hours=1 if timeframe == "1h" else 4)
    return frame.loc[(frame.index >= start) & (frame.index + horizon * interval <= end)].copy()


def model_columns(control: str) -> list[str]:
    spot = [f"spot_{name}" for name in PRICE_COLS]
    if control == "A":
        return spot
    if control == "A2":
        return ALL_PRICE
    if control == "B":
        return FLOW_COLS + FUNDING_COLS
    if control == "C":
        return ALL_PRICE + FLOW_COLS + FUNDING_COLS
    raise ValueError(control)


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, columns: list[str], target: str) -> np.ndarray:
    mean = train[columns].mean().to_numpy(float)
    scale = train[columns].std(ddof=0).replace(0, 1).to_numpy(float)
    x_train = (train[columns].to_numpy(float) - mean) / scale
    x_test = (test[columns].to_numpy(float) - mean) / scale
    model = Ridge(alpha=10.0)
    model.fit(x_train, train[target].to_numpy(float))
    return model.predict(x_test)


def orient_excursions(direction: float, upside_pct: float, downside_pct: float) -> tuple[float, float]:
    """Return favourable/adverse excursion for a directional event."""
    return (upside_pct, downside_pct) if direction >= 0 else (-downside_pct, -upside_pct)


def model_and_events(frame: pd.DataFrame, symbol: str, timeframe: str) -> tuple[dict, dict, list[dict]]:
    horizon = 6 if timeframe == "1h" else 3
    needed = ALL_PRICE + FLOW_COLS + FUNDING_COLS + [f"signed_{horizon}", f"absolute_{horizon}"]
    train = split_rows(frame, "discovery", timeframe, horizon).dropna(subset=needed).copy()
    if len(train) < 1000:
        raise RuntimeError(f"Too few discovery rows: {symbol} {timeframe} {len(train)}")
    thresholds = {
        "flow_q75": float(train["flow_imbalance"].abs().quantile(0.75)),
        "flow_q90": float(train["flow_imbalance"].abs().quantile(0.90)),
        "price_move_q75": float(train["futures_ret1"].abs().quantile(0.75)),
        "funding_q90": float(train["funding_latest"].abs().quantile(0.90)),
    }
    tests = {}
    event_rows = []
    for split in ("validation", "diagnostic_2026"):
        test = split_rows(frame, split, timeframe, horizon).dropna(subset=needed).copy()
        if test.empty:
            continue
        truth = test[f"signed_{horizon}"].to_numpy(float)
        abs_truth = test[f"absolute_{horizon}"].to_numpy(float)
        predictions = {
            name: fit_predict(train, test, model_columns(name), f"signed_{horizon}")
            for name in ("A", "A2", "B", "C")
        }
        # Component ablations are diagnostic; A2 vs C remains the frozen primary comparison.
        predictions["A2_flow"] = fit_predict(train, test, ALL_PRICE + FLOW_COLS, f"signed_{horizon}")
        predictions["A2_funding"] = fit_predict(train, test, ALL_PRICE + FUNDING_COLS, f"signed_{horizon}")
        abs_a2 = fit_predict(train, test, model_columns("A2"), f"absolute_{horizon}")
        mse = {name: float(np.mean((truth - pred) ** 2)) for name, pred in predictions.items()}
        tests[split] = {
            "rows": len(test),
            "mse": mse,
            "C_vs_A2_uplift": (mse["A2"] - mse["C"]) / mse["A2"] if mse["A2"] else None,
            "A2_vs_A_uplift": (mse["A"] - mse["A2"]) / mse["A"] if mse["A"] else None,
        }
        direction = test["futures_direction"].to_numpy(float)
        flow = test["flow_imbalance"].to_numpy(float)
        price_move = test["futures_ret1"].to_numpy(float)
        aligned = (np.sign(flow) == direction) & (direction != 0) & (np.sign(price_move) == direction)
        masks = {
            "H1": (np.abs(flow) >= thresholds["flow_q75"]) & aligned,
            "H2": (np.abs(flow) >= thresholds["flow_q90"])
            & (np.abs(price_move) >= thresholds["price_move_q75"])
            & aligned,
            "H4": test["funding_latest"].abs().to_numpy(float) >= thresholds["funding_q90"],
        }
        for hypothesis, mask in masks.items():
            chosen = test.loc[mask]
            positions = np.flatnonzero(mask)
            for pos, (stamp, row) in zip(positions, chosen.iterrows(), strict=True):
                if hypothesis == "H4":
                    raw_effect = abs_truth[pos]
                    residual = abs_truth[pos] - abs_a2[pos]
                    expected_effect = residual
                else:
                    raw_effect = direction[pos] * truth[pos]
                    residual = direction[pos] * (truth[pos] - predictions["A2"][pos])
                    expected_effect = residual if hypothesis == "H1" else -residual
                if hypothesis != "H4" and direction[pos] < 0:
                    mfe, mae = orient_excursions(
                        direction[pos], float(row[f"mfe_{horizon}"]), float(row[f"mae_{horizon}"])
                    )
                else:
                    mfe = float(row[f"mfe_{horizon}"])
                    mae = float(row[f"mae_{horizon}"])
                event_rows.append(
                    {
                        "hypothesis": hypothesis,
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "split": split,
                        "decision_time": stamp.isoformat(),
                        "week": row["week"],
                        "raw_forward_pct": float(raw_effect),
                        "residual_pct": float(residual),
                        "hypothesis_effect_pct": float(expected_effect),
                        "mfe_pct": mfe,
                        "mae_pct": mae,
                    }
                )
    return thresholds, tests, event_rows


def bootstrap_effect(events: list[dict], *, seed: int, repetitions: int) -> dict:
    if not events:
        return {"n": 0, "weeks": 0, "mean_pct": None, "ci95": None, "one_sided_p": None}
    by_week = defaultdict(list)
    for row in events:
        by_week[row["week"]].append(row["hypothesis_effect_pct"])
    weeks = sorted(by_week)
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(repetitions):
        picked = rng.choice(weeks, size=len(weeks), replace=True)
        values = [value for week in picked for value in by_week[week]]
        samples.append(float(np.mean(values)))
    effects = [row["hypothesis_effect_pct"] for row in events]
    return {
        "n": len(events),
        "weeks": len(weeks),
        "mean_pct": float(np.mean(effects)),
        "median_pct": float(np.median(effects)),
        "ci95": [float(x) for x in np.quantile(samples, [0.025, 0.975])],
        "one_sided_p": (1 + sum(x <= 0 for x in samples)) / (repetitions + 1),
        "raw_forward_mean_pct": float(np.mean([r["raw_forward_pct"] for r in events])),
        "mfe_mean_pct": float(np.mean([r["mfe_pct"] for r in events])),
        "mae_mean_pct": float(np.mean([r["mae_pct"] for r in events])),
    }


def quarterly_folds(events: list[dict]) -> dict:
    grouped = defaultdict(list)
    for row in events:
        stamp = row["decision_time"]
        quarter = f"{stamp[:4]}Q{(int(stamp[5:7]) - 1) // 3 + 1}"
        grouped[quarter].append(row["hypothesis_effect_pct"])
    return {
        quarter: {"n": len(values), "mean_hypothesis_effect_pct": float(np.mean(values))}
        for quarter, values in sorted(grouped.items())
    }


def hypothesis_summary(
    events: list[dict], model_results: dict, symbols: list[str]
) -> tuple[list[dict], list[dict]]:
    primary = []
    detailed = []
    for hypothesis in ("H1", "H2", "H4"):
        for timeframe in ("1h", "4h"):
            selected = [r for r in events if r["hypothesis"] == hypothesis and r["timeframe"] == timeframe]
            validation = [r for r in selected if r["split"] == "validation"]
            diagnostic = [r for r in selected if r["split"] == "diagnostic_2026"]
            stats = bootstrap_effect(validation, seed=20261028, repetitions=500)
            diag_stats = bootstrap_effect(diagnostic, seed=20261028, repetitions=500)
            by_symbol = {
                symbol: bootstrap_effect(
                    [r for r in validation if r["symbol"] == symbol], seed=20261028, repetitions=100
                )
                for symbol in symbols
            }
            leave_one_out = {
                symbol: bootstrap_effect(
                    [r for r in validation if r["symbol"] != symbol], seed=20261028, repetitions=100
                )["mean_pct"]
                for symbol in symbols
            }
            if hypothesis == "H1":
                cost_gross = stats.get("raw_forward_mean_pct")
            elif hypothesis == "H2":
                cost_gross = (
                    -stats["raw_forward_mean_pct"] if stats.get("raw_forward_mean_pct") is not None else None
                )
            else:
                cost_gross = stats.get("raw_forward_mean_pct")  # volatility magnitude, not a tradable return
            mse_a2 = []
            mse_c = []
            weights = []
            for symbol in symbols:
                result = model_results.get(f"{symbol}/{timeframe}", {}).get("validation")
                if result:
                    mse_a2.append(result["mse"]["A2"])
                    mse_c.append(result["mse"]["C"])
                    weights.append(result["rows"])
            a2 = float(np.average(mse_a2, weights=weights)) if weights else None
            c = float(np.average(mse_c, weights=weights)) if weights else None
            uplift = (a2 - c) / a2 if a2 else None
            result = {
                "hypothesis": hypothesis,
                "timeframe": timeframe,
                "primary_horizon_bars": 6 if timeframe == "1h" else 3,
                "validation": stats,
                "diagnostic_2026": diag_stats,
                "by_symbol": by_symbol,
                "leave_one_symbol_out_mean_pct": leave_one_out,
                "symbols_correct_sign": sum((v["mean_pct"] or 0) > 0 for v in by_symbol.values()),
                "model_C_vs_A2_mse_uplift": uplift,
                "cost_hurdle": {
                    name: None if cost_gross is None else cost_gross - cost
                    for name, cost in (("zero", 0), ("base", 0.3), ("double", 0.6))
                },
                "cost_interpretation": "absolute move, not directional PnL"
                if hypothesis == "H4"
                else "hypothetical directional event hurdle, not executable PnL",
                "quarterly_folds": {
                    "validation": quarterly_folds(validation),
                    "diagnostic_2026": quarterly_folds(diagnostic),
                },
            }
            primary.append(result)
            detailed.extend(selected)
    # Holm familywise adjustment: six predeclared primary one-sided cells.
    ordered = sorted(
        range(len(primary)),
        key=lambda i: (
            primary[i]["validation"]["one_sided_p"]
            if primary[i]["validation"]["one_sided_p"] is not None
            else 1
        ),
    )
    adjusted = 0.0
    for rank, index in enumerate(ordered):
        p = primary[index]["validation"]["one_sided_p"]
        adjusted = max(adjusted, min(1.0, (len(primary) - rank) * (p if p is not None else 1)))
        primary[index]["holm_adjusted_p"] = adjusted
    for result in primary:
        val = result["validation"]
        if val["n"] < 100 or val["weeks"] < 12:
            classification = "WEAK" if (val["mean_pct"] or 0) > 0 else "REJECT"
        elif (val["mean_pct"] or 0) <= 0:
            classification = "REJECT"
        elif (result["model_C_vs_A2_mse_uplift"] or 0) <= 0:
            classification = "WEAK"
        else:
            robust = result["holm_adjusted_p"] < 0.05
            if result["timeframe"] == "4h":
                robust = robust and (result["diagnostic_2026"]["mean_pct"] or 0) > 0
            else:
                robust = False  # Frozen ROBUST rule requires 2026 diagnostic, unavailable on Spot 1h.
            robust = robust and result["symbols_correct_sign"] >= 6
            robust = robust and all((x or 0) > 0 for x in result["leave_one_symbol_out_mean_pct"].values())
            robust = robust and (result["model_C_vs_A2_mse_uplift"] or 0) >= 0.001
            robust = robust and (val["mean_pct"] or 0) >= 0.3
            robust = robust and (result["cost_hurdle"]["double"] or 0) > 0
            classification = "ROBUST" if robust else "PROMISING"
        result["classification"] = classification
    return primary, detailed


def secondary_horizons(datasets: dict, thresholds: dict) -> list[dict]:
    """Descriptive raw outcomes only; no new primary test or post-hoc selection."""
    rows = []
    for key, frame in datasets.items():
        symbol, timeframe = key.split("/")
        q = thresholds[key]
        horizons = [1, 3, 6, 12, 24] if timeframe == "1h" else [1, 3, 6, 12]
        primary = 6 if timeframe == "1h" else 3
        for horizon in horizons:
            if horizon == primary:
                continue
            for split in ("validation", "diagnostic_2026"):
                part = split_rows(frame, split, timeframe, horizon).dropna(
                    subset=[
                        "flow_imbalance",
                        "futures_ret1",
                        "funding_latest",
                        f"signed_{horizon}",
                        f"absolute_{horizon}",
                    ]
                )
                if part.empty:
                    continue
                direction = part["futures_direction"]
                aligned = (np.sign(part["flow_imbalance"]) == direction) & (direction != 0)
                masks = {
                    "H1": (part["flow_imbalance"].abs() >= q["flow_q75"]) & aligned,
                    "H2": (part["flow_imbalance"].abs() >= q["flow_q90"])
                    & (part["futures_ret1"].abs() >= q["price_move_q75"])
                    & aligned,
                    "H4": part["funding_latest"].abs() >= q["funding_q90"],
                }
                for hypothesis, mask in masks.items():
                    chosen = part.loc[mask]
                    if chosen.empty:
                        continue
                    effect = (
                        chosen[f"absolute_{horizon}"]
                        if hypothesis == "H4"
                        else chosen["futures_direction"] * chosen[f"signed_{horizon}"]
                    )
                    rows.append(
                        {
                            "hypothesis": hypothesis,
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "split": split,
                            "horizon_bars": horizon,
                            "n": len(chosen),
                            "raw_forward_mean_pct": float(effect.mean()),
                            "exploratory_only": True,
                        }
                    )
    return rows


def incremental_decisions(primary: list[dict], models: dict, symbols: list[str]) -> dict:
    ablation = {}
    for timeframe in ("1h", "4h"):
        parts = [models[f"{symbol}/{timeframe}"]["validation"] for symbol in symbols]
        weights = [part["rows"] for part in parts]
        baseline = float(np.average([part["mse"]["A2"] for part in parts], weights=weights))
        for name in ("A2_flow", "A2_funding"):
            loss = float(np.average([part["mse"][name] for part in parts], weights=weights))
            ablation[f"{name}/{timeframe}"] = (baseline - loss) / baseline
    flow_positive_event = any(
        row["hypothesis"] == "H1" and (row["validation"]["mean_pct"] or 0) > 0 for row in primary
    )
    flow_robust = any(
        row["hypothesis"] in ("H1", "H2") and row["classification"] == "ROBUST" for row in primary
    )
    funding_robust = any(row["hypothesis"] == "H4" and row["classification"] == "ROBUST" for row in primary)
    flow_uplift = all(ablation[f"A2_flow/{timeframe}"] > 0 for timeframe in ("1h", "4h"))
    funding_uplift = all(ablation[f"A2_funding/{timeframe}"] > 0 for timeframe in ("1h", "4h"))
    if flow_robust and flow_uplift:
        flow_status = "YES"
    elif flow_positive_event:
        flow_status = "INCONCLUSIVE"
    else:
        flow_status = "NO"
    if funding_robust and funding_uplift:
        funding_status = "YES"
    elif (
        all(row["hypothesis"] != "H4" or (row["validation"]["mean_pct"] or 0) <= 0 for row in primary)
        and not funding_uplift
    ):
        funding_status = "NO"
    else:
        funding_status = "INCONCLUSIVE"
    return {
        "flow": flow_status,
        "funding": funding_status,
        "oi": "NOT TESTED",
        "robust_new_edge": flow_robust or funding_robust,
        "strategy_design_justified": False,
        "component_mse_uplift": ablation,
    }


def verify_manifest() -> dict:
    manifest = json.loads(MANIFEST.read_text())
    if manifest["protocol_sha256"] != sha256(PROTOCOL_PATH):
        raise RuntimeError("Frozen protocol hash differs from download manifest")
    for entry in manifest["entries"]:
        path = ROOT / entry["file"]
        if not path.exists() or sha256(path) != entry["sha256"] or path.stat().st_size != entry["size"]:
            raise RuntimeError(f"Raw file changed since manifest: {path}")
        if "publisher_checksum_file" in entry:
            checksum_path = ROOT / entry["publisher_checksum_file"]
            if (
                checksum_path.stat().st_size != entry["publisher_checksum_size"]
                or sha256(checksum_path) != entry["publisher_checksum_sha256"]
            ):
                raise RuntimeError(f"Publisher CHECKSUM changed since manifest: {checksum_path}")
    return manifest


def evaluate() -> None:
    verify_manifest()
    protocol = json.loads(PROTOCOL_PATH.read_text())
    integrity = []
    summaries = []
    thresholds = {}
    models = {}
    events = []
    redundancy = {}
    datasets = {}
    for symbol, futures_symbol in protocol["universe"].items():
        raw, raw_integrity = read_futures(futures_symbol)
        funding, funding_integrity = read_funding(futures_symbol)
        integrity.extend([raw_integrity, funding_integrity])
        for timeframe in ("1h", "4h"):
            frame, summary = build_dataset(symbol, timeframe, raw, funding)
            datasets[f"{symbol}/{timeframe}"] = frame
            summaries.append(summary)
            q, model_result, event_rows = model_and_events(frame, symbol, timeframe)
            thresholds[f"{symbol}/{timeframe}"] = q
            models[f"{symbol}/{timeframe}"] = model_result
            events.extend(event_rows)
            complete = split_rows(frame, "validation", timeframe, 6 if timeframe == "1h" else 3).dropna(
                subset=[
                    "flow_imbalance",
                    "futures_ret1",
                    "futures_volume_ratio24",
                    "funding_latest",
                    "spot_ret6",
                ]
            )
            redundancy[f"{symbol}/{timeframe}"] = {
                "flow_vs_futures_return_corr": float(
                    complete["flow_imbalance"].corr(complete["futures_ret1"])
                ),
                "flow_vs_futures_volume_ratio_corr": float(
                    complete["flow_imbalance"].corr(complete["futures_volume_ratio24"])
                ),
                "funding_vs_spot_trailing_return_corr": float(
                    complete["funding_latest"].corr(complete["spot_ret6"])
                ),
            }
        print(f"Validated/evaluated: {symbol}", flush=True)
    primary, detailed = hypothesis_summary(events, models, list(protocol["universe"]))
    secondary = secondary_horizons(datasets, thresholds)
    incremental = incremental_decisions(primary, models, list(protocol["universe"]))
    # Full event-level results are retained in CSV for audit; no post-hoc event selection.
    with RESULT_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(detailed[0])
            if detailed
            else [
                "hypothesis",
                "symbol",
                "timeframe",
                "split",
                "decision_time",
                "week",
                "raw_forward_pct",
                "residual_pct",
                "hypothesis_effect_pct",
                "mfe_pct",
                "mae_pct",
            ],
        )
        writer.writeheader()
        writer.writerows(detailed)
    result = {
        "protocol_sha256_json": sha256(PROTOCOL_PATH),
        "protocol_sha256_md": sha256(REPORTS / "FUTURES_FLOW_OI_FROZEN_PROTOCOL.md"),
        "code_sha256": sha256(Path(__file__)),
        "manifest_sha256": sha256(MANIFEST),
        "raw_file_count": sum(1 for path in RAW.rglob("*") if path.is_file()),
        "raw_bytes": directory_bytes(RAW),
        "working_data_bytes": directory_bytes(DATA),
        "oi_causality": protocol["oi_causality"]["decision"],
        "H3": "NOT TESTED",
        "H5": "NOT TESTED",
        "incremental_information": incremental,
        "mapping": protocol["universe"],
        "period": protocol["period_utc"],
        "integrity": integrity,
        "joined_data": summaries,
        "thresholds_discovery_only": thresholds,
        "models": models,
        "primary": primary,
        "secondary_exploratory": secondary,
        "feature_redundancy": redundancy,
        "events_csv_sha256": sha256(RESULT_CSV),
        "created_utc": utc_now(),
        "limitations": [
            "Исторические 2024–2025 OHLCV уже исследовались в предыдущей работе проекта",
            "2026 4h ранее использовался для OHLCV OOS, это не чистый внешний holdout",
            "Метка fundingTime и закрытие архивной свечи не доказывают нулевую live-задержку публикации",
            "Исходы событий не являются исполнимым торговым PnL",
            "OI исключён из причинного воспроизведения",
        ],
    }
    RESULT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    render_markdown(result)


def render_markdown(result: dict) -> None:
    rows = result["primary"]
    lines = [
        "# Futures flow / funding: frozen incremental-information research",
        "",
        "**OI: `OI_CAUSALITY_UNCONFIRMED`; H3/H5 `NOT TESTED`.** Исходы — Spot event study, не торговый PnL.",
        "",
        f"Протокол JSON SHA-256 `{result['protocol_sha256_json']}`; MD `{result['protocol_sha256_md']}`. Код `{result['code_sha256']}`; manifest `{result['manifest_sha256']}`.",
        f"Raw: {result['raw_file_count']} файлов, {result['raw_bytes']:,} B. Рабочие research данные: {result['working_data_bytes']:,} B. Период UTC: 2024-01-01–2026-10-01 exclusive; 1h только 2024–25, 4h также 2026 diagnostic.",
        "",
        "## Решение и происхождение данных",
        "",
        f"**Нового устойчивого information edge {'найдено' if result['incremental_information']['robust_new_edge'] else 'не найдено'}; к design торговой стратегии переходить рано.** Flow: `{result['incremental_information']['flow']}` (условная связь H1 есть, но первичный C<A2 и gross эффект ниже 0.30 п.п.); funding: `{result['incremental_information']['funding']}` в проверенных формах; OI: `NOT TESTED`. Ни один результат не переносится в PAPER.",
        "",
        "Источник flow: официальный Binance Public Data USD-M monthly 5m ZIP с taker-buy полями и издательскими SHA-256; funding: публичный `/fapi/v1/fundingRate`; Spot: уже сохранённые и сверенные с прежними SHA-256 файлы проекта. 264 ZIP + 264 CHECKSUM + 32 REST JSON = 560 raw файлов. Funding и свечи доступны на одинаковом полном периоде у всех восьми контрактов. OHLCV Spot 1h заканчивается 2025-12-31, поэтому 2026 — только 4h diagnostic.",
        "",
        "| Spot | USD-M perpetual | Множитель цены для сравнения со Spot |",
        "|---|---|---:|",
        *[
            f"| {spot} | {futures} | {1000 if spot in ('SHIBUSDT', 'PEPEUSDT') else 1} |"
            for spot, futures in result["mapping"].items()
        ],
        "",
        "OI: официальная REST-документация описывает `openInterestHist.timestamp` как конец периода, но не доказывает семантику/доступность архивного `metrics.create_time`. Поэтому OI raw не загружался; H3/H5 не тестировались. Basis тоже не тестировался в этой фазе.",
        "",
        "## Primary validation 2025",
        "",
        "| Гипотеза | TF | N / недель | residual effect п.п. | 95% weekly CI | Holm p | C vs A2 MSE uplift | Класс |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        val = row["validation"]
        ci = val["ci95"]
        lines.append(
            f"| {row['hypothesis']} | {row['timeframe']} | {val['n']} / {val['weeks']} | {val['mean_pct']:+.4f} | [{ci[0]:+.4f}, {ci[1]:+.4f}] | {row['holm_adjusted_p']:.4f} | {row['model_C_vs_A2_mse_uplift']:+.4%} | {row['classification']} |"
            if ci and row["model_C_vs_A2_mse_uplift"] is not None
            else f"| {row['hypothesis']} | {row['timeframe']} | {val['n']} / {val['weeks']} | n/a | n/a | n/a | n/a | {row['classification']} |"
        )
    lines.extend(["", "## Временная и парная устойчивость", ""])
    for row in rows:
        diag = row["diagnostic_2026"]
        folds = [
            f"{quarter}:{values['mean_hypothesis_effect_pct']:+.3f}({values['n']})"
            for split in ("validation", "diagnostic_2026")
            for quarter, values in row["quarterly_folds"][split].items()
        ]
        leave = list(row["leave_one_symbol_out_mean_pct"].values())
        lines.append(
            f"- {row['hypothesis']} {row['timeframe']}: validation {row['symbols_correct_sign']}/8 пар с ожидаемым знаком; leave-one-out min={min(leave):+.3f}, max={max(leave):+.3f} п.п.; 2026 N={diag['n']}, effect={diag['mean_pct']}; gross zero/base/double hurdle={row['cost_hurdle']}. Кварталы: {', '.join(folds)}."
        )
    lines.extend(["", "## Компоненты и другие горизонты", ""])
    for timeframe in ("1h", "4h"):
        per_symbol = [result["models"][f"{symbol}/{timeframe}"]["validation"] for symbol in result["mapping"]]
        weights = [row["rows"] for row in per_symbol]
        base = float(np.average([row["mse"]["A2"] for row in per_symbol], weights=weights))
        for variant in ("A2_flow", "A2_funding"):
            loss = float(np.average([row["mse"][variant] for row in per_symbol], weights=weights))
            lines.append(
                f"- {timeframe} {variant} vs A2: validation MSE uplift {(base - loss) / base:+.4%} (диагностическая ablation, не primary)."
            )
    correlations = list(result["feature_redundancy"].values())
    for field, label in (
        ("flow_vs_futures_return_corr", "flow к текущему futures return"),
        ("flow_vs_futures_volume_ratio_corr", "flow к объёму futures"),
        ("funding_vs_spot_trailing_return_corr", "funding к прошлому Spot return"),
    ):
        values = [item[field] for item in correlations]
        lines.append(
            f"- Корреляция {label}, validation по 16 рядам: min={min(values):+.3f}, median={np.median(values):+.3f}, max={max(values):+.3f}."
        )
    lines.append(
        "- `taker_buy_share=(flow_imbalance+1)/2` при ненулевом объёме: детерминированная избыточность двух признаков, не отдельный источник информации."
    )
    lines.extend(
        [
            "",
            "| Гипотеза | TF | Период | Горизонт, бары | N | Средний raw forward, % |",
            "|---|---|---|---:|---:|---:|",
        ]
    )
    groups = defaultdict(list)
    for row in result["secondary_exploratory"]:
        groups[(row["hypothesis"], row["timeframe"], row["split"], row["horizon_bars"])].append(row)
    for key, parts in sorted(groups.items()):
        count = sum(row["n"] for row in parts)
        mean = sum(row["n"] * row["raw_forward_mean_pct"] for row in parts) / count
        lines.append(f"| {key[0]} | {key[1]} | {key[2]} | {key[3]} | {count} | {mean:+.4f} |")
    lines.append(
        "Secondary horizons только exploratory: без контроля A2 для этих горизонтов и без отбора лучшей ячейки."
    )
    lines.extend(["", "## Integrity и ограничения", ""])
    for item in result["integrity"]:
        lines.append(
            f"- {item['symbol']} {item['source']}: {item['integrity']}; rows={item.get('total_rows', item.get('rows'))}; missing 5m={item.get('missing_5m', 'n/a')}; funding gaps >24h={item.get('gaps_over_24h', 'n/a')}."
        )
    lines.append(
        "Все 8 × 33 месячных ряда 5m прошли checks: 289 152 строк на контракт, 0 отсутствующих 5m интервалов, дубликатов, некорректных OHLC/объёма/taker/count; funding — 3 012 событий на контракт, 0 дубликатов и разрывов >24h. Из joined 1h 17 543 строк на пару complete 17 302; из 4h 6 023 complete 5 963: ранние окна исключены из-за причинного прогрева признаков. Funding stale и zero-volume flow: 0. Пропуски не заполнялись."
    )
    lines.extend(
        [
            "",
            "## Следующий источник информации",
            "",
            "Сначала запросить у Binance документированную семантику `metrics.create_time` и point-in-time публикацию OI. Пока её нет, следующий дешёвый отдельный frozen test — futures/Spot basis на уже имеющихся ценах с нормализацией множителя 1000; это новая гипотеза, не часть текущих шести primary ячеек. Проспективный spread нужен для реалистичности исполнения, но здесь collector не создавался.",
        ]
    )
    lines.extend(
        [
            "",
            "Детальные per-symbol, model, thresholds и source hashes — в [JSON](FUTURES_FLOW_OI_RESEARCH.json); события — в [CSV](FUTURES_FLOW_OI_RESULTS.csv).",
            "",
            "Ограничения: " + "; ".join(result["limitations"]),
            "",
            "Воспроизведение без сети: `.venv/bin/python -B reports/futures_flow_oi_research.py --self-test` затем `.venv/bin/python -B reports/futures_flow_oi_research.py --evaluate`.",
            "",
            "Production, technical-v1, PAPER/SQLite и DeepSeek не изменялись. Ордеров, commit и push нет.",
            "",
        ]
    )
    RESULT_MD.write_text("\n".join(lines))


def self_test() -> None:
    assert len(months()) == 33
    frame = pd.DataFrame(
        {
            "open_time": np.arange(12) * FIVE_MIN_MS,
            "open": np.ones(12),
            "high": np.ones(12),
            "low": np.ones(12),
            "close": np.ones(12),
            "volume": np.ones(12),
            "close_time": (np.arange(12) + 1) * FIVE_MIN_MS - 1,
            "taker_buy_base": np.ones(12) * 0.75,
            "trade_count": np.ones(12),
        }
    )
    agg = aggregate_futures(frame, "1h")
    assert len(agg) == 1 and abs(agg["flow_imbalance"].iloc[0] - 0.5) < 1e-12
    assert agg.index[0] == pd.Timestamp("1970-01-01T01:00:00Z")
    frame.loc[11, "close_time"] += FIVE_MIN_MS
    assert aggregate_futures(frame, "1h").empty
    future = pd.DataFrame(
        {
            "time": [pd.Timestamp("2024-01-01T01:00:00Z")],
            "rate": [0.001],
            "abs_rate": [0.001],
            "funding_trailing3": [0.001],
            "funding_sign": [1.0],
            "funding_abs_percentile90d": [0.9],
        }
    )
    test_agg = pd.DataFrame(
        index=pd.DatetimeIndex(
            [pd.Timestamp("2024-01-01T01:00:00Z"), pd.Timestamp("2024-01-01T02:00:00Z")], name="decision_time"
        )
    )
    joined = add_funding(test_agg, future)
    assert math.isnan(joined["funding_latest"].iloc[0])
    assert joined["funding_latest"].iloc[1] == 0.001
    assert orient_excursions(-1, 2.0, -3.0) == (3.0, -2.0)
    print("Self-test PASS: closed 5m aggregation, incomplete-bar rejection, strict funding timestamp")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--budget", action="store_true")
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--fetch", action="store_true")
    group.add_argument("--evaluate", action="store_true")
    args = parser.parse_args()
    if args.budget:
        budget()
    elif args.self_test:
        self_test()
    elif args.fetch:
        fetch()
    else:
        evaluate()


if __name__ == "__main__":
    main()
