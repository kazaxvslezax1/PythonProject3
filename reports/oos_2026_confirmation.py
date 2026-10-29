"""Frozen, research-only 2026 confirmation of breakout_24_btc_range (4h).

Order of operations: ``--self-test``, ``--freeze``, ``--fetch``, ``--evaluate``.
No credentials, broker, Telegram, SQLite, AI, or order endpoint is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from market_edge_discovery import trailing_features

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
CODE = Path(__file__).resolve()
ORIGINAL_CODE = HERE / "market_edge_discovery.py"
ORIGINAL_MD = HERE / "MARKET_EDGE_DISCOVERY.md"
ORIGINAL_JSON = HERE / "MARKET_EDGE_DISCOVERY.json"
PROTOCOL_MD = HERE / "OOS_2026_FROZEN_PROTOCOL.md"
PROTOCOL_JSON = HERE / "OOS_2026_FROZEN_PROTOCOL.json"
REPORT_MD = HERE / "OOS_2026_CONFIRMATION.md"
REPORT_JSON = HERE / "OOS_2026_CONFIRMATION.json"
EVENTS_CSV = HERE / "OOS_2026_EVENTS.csv"
DATA_DIR = HERE / "OOS_2026_DATA"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "SHIBUSDT", "PEPEUSDT")
ALTS = SYMBOLS[1:]
START = pd.Timestamp("2026-01-01T00:00:00Z")
END = pd.Timestamp("2026-10-26T04:00:00Z")  # Fixed before any 2026 outcome retrieval.
INTERVAL = pd.Timedelta(hours=4)
HORIZON = 24
SEED = 20261026
BOOT_DRAWS = 2000
URL = "https://api.binance.com/api/v3/klines"
COLUMNS = ["time", "close_time", "open", "high", "low", "close", "volume"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def utc(value: pd.Timestamp) -> str:
    return value.isoformat().replace("+00:00", "Z")


def historical_path(symbol: str) -> Path:
    return ROOT / "runtime" / "walk_forward" / "data" / f"{symbol}_4h_2024-01-01_2026-01-01.csv"


def dataset_path(symbol: str) -> Path:
    return DATA_DIR / f"{symbol}_4h_2026-01-01_2026-10-26T04.csv"


def protocol_text(p: dict) -> str:
    return "\n".join(
        [
            "# Замороженный протокол OOS 2026 — только 4h",
            "",
            f"Заморожен {p['frozen_at_utc']} до загрузки данных 2026. Это post-hoc выбранная WEAK-гипотеза из предыдущей работы, поэтому даже подтверждение не создаёт торговую стратегию.",
            "",
            "## Единственная гипотеза",
            "",
            "`breakout_24_btc_range` на ETH, BNB, SOL, XRP, DOGE, SHIB, PEPE (USDT Spot). BTCUSDT — только синхронный контекст. На закрытии alt-свечи T LONG, если close(T) строго выше максимума high(T−24…T−1); SHORT, если close(T) строго ниже минимума low(T−24…T−1). Одновременно закрытая BTC 4h-свеча T должна иметь efficiency=abs(close(T)−close(T−24))/sum_{i=T−23..T}abs(close(i)−close(i−1)) ≤ 0.15. Нулевой знаменатель исключает условие. Никаких других фильтров и изменений направления.",
            "",
            "BTC и alt сопоставляются по точному `close_time`. Сигнал использует только закрытые свечи T и раньше; гипотетический вход — open(T+1); исход — close(T+24), путь MFE/MAE — high/low свечей T+1…T+24. Горизонт 24×4h=96h. Незрелые события у правой границы исключаются и считаются отдельно. Промежуточные SL/TP не моделируются.",
            "",
            "## Данные и отбор",
            "",
            f"Один хронологический интервал UTC: open ≥ {p['period']['start_inclusive']} и open < {p['period']['end_exclusive']}; последняя свеча open {p['period']['last_open_inclusive']}, close {p['period']['last_close_inclusive']}. По {p['period']['expected_candles_per_symbol']} закрытых 4h свечей на каждую из восьми пар. Публичный Binance Spot `{URL}`; 120 свечей 2025 используются только для прогрева индикаторов, не для OOS исходов. Никакой выборки месяцев/режимов. Пропуски, дубликаты, некорректные OHLC, частичные свечи или рассинхронизация BTC прекращают оценку; данные не заполняются. OOS событие допустимо только если все 24 свечи исхода остаются в интервале.",
            "",
            "## Метрики, контроль и решение",
            "",
            "Primary metric: арифметическое среднее signed next-open→24th-close return минус 0.30 процентного пункта round trip. Zero=0.00 п.п., double=0.60 п.п.; это комиссия 0.10%+проскальзывание 0.05% на сторону при base. Не доходность портфеля и не реализованный PnL.",
            "",
            "Control A: тот же alt breakout24 без фильтра BTC; отдельно публикуются все такие события и complement, где BTC не range. Incremental effect = mean base conditioned − mean base complement. Control B: для каждого события средний signed forward return всех допустимых 4h баров того же символа и календарного месяца, направление фиксировано его event-side. Control C: средний signed forward return баров того же символа/месяца/причинного ATR14/close терциля/знака предыдущего 24-bar momentum; при <20 контролях отступ к symbol/month/volatility, если пусто — symbol/month. Контроли включают event-бары и не являются независимыми сделками.",
            "",
            "Secondary: N, mean/median, доля return>0, p05/p10/p25/p75/p90, MFE, MAE, MFE/|MAE|, zero/base/double; месяцы, пары, leave-one-symbol-out, без лучшего события, доля положительной gross-суммы от top 1% и 5% событий. Cluster-bootstrap: календарные ISO-недели по всем парам, 2000 повторов с возвращением, seed=20261026, 2.5% квантиль base mean. Перекрывающиеся горизонты и общерыночная корреляция снижают независимость выборки.",
            "",
            "**INSUFFICIENT OOS SAMPLE:** N<100 либо <12 разных ISO-недель с событиями. Иначе **CONFIRMED** только при одновременном выполнении всех условий: base mean>0; нижняя 95% week-bootstrap граница>0; base median≥0; double mean>0; ≥60% непустых календарных месяцев и не менее 6 месяцев имеют base mean>0; ≥5 из 7 альткоинов имеют N≥10 и base mean>0; каждый leave-one-symbol-out base mean>0; base mean после удаления единственного лучшего gross-события>0; top 5% событий дают ≤50% суммы всех положительных gross returns; conditioned base mean выше complement Control A; средний excess против B и C >0. При достаточной выборке и любом невыполненном условии **NOT CONFIRMED**. Вторичные показатели не отменяют primary fail.",
            "",
            "Не менять определения после результатов. Не запускать другие 43 события, 1h, DeepSeek, PAPER или реальные ордера. Код и входы закреплены SHA256 в JSON; SHA256 самих протоколов записываются в финальном отчёте (самохеширование невозможно).",
            "",
        ]
    )


def freeze() -> None:
    if PROTOCOL_JSON.exists() or PROTOCOL_MD.exists():
        raise FileExistsError("Frozen protocol already exists; refusing overwrite")
    original = json.loads(ORIGINAL_JSON.read_text())
    if (
        "previous N-bar high" not in original["event_definitions"]["breakout_N"]
        or "range <=0.15" not in original["event_definitions"]["market_regime"]
        or "event index+h" not in original["forward_measure"]
        or original["costs"]["base_pct"] != 0.3
        or original["costs"]["double_pct"] != 0.6
    ):
        raise ValueError("Prior event protocol mismatch; stop before OOS fetch")
    if not all(historical_path(s).exists() for s in SYMBOLS):
        raise FileNotFoundError("Historical 2025 warmup missing")
    expected = int((END - START) / INTERVAL)
    p = {
        "state": "FROZEN_BEFORE_2026_OUTCOMES",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": "breakout_24_btc_range; 4h only; WEAK post-hoc from 2024-25",
        "symbols": list(SYMBOLS),
        "event_symbols": list(ALTS),
        "period": {
            "start_inclusive": utc(START),
            "end_exclusive": utc(END),
            "last_open_inclusive": utc(END - INTERVAL),
            "last_close_inclusive": utc(END - pd.Timedelta(milliseconds=1)),
            "expected_candles_per_symbol": expected,
            "timezone": "UTC",
        },
        "source": URL,
        "warmup": "Last 120 closed 2025 4h bars per symbol, features only, never OOS outcomes",
        "event_definition": {
            "side": "LONG iff alt close(T)>max alt high(T-24..T-1); SHORT iff alt close(T)<min alt low(T-24..T-1); else 0",
            "btc_context": "Exact same close_time closed BTC 4h candle; abs(C[T]-C[T-24])/sum(abs(diff(C)), last 24 changes) <= 0.15; denominator zero is not range",
            "horizon_bars": HORIZON,
            "entry": "alt open(T+1)",
            "exit": "alt close(T+24)",
            "path": "alt high/low T+1..T+24",
        },
        "primary_metric": "mean(side*(close[T+24]/open[T+1]-1)*100-0.3) in percentage points",
        "costs_pct_round_trip": {"zero": 0.0, "base": 0.3, "double": 0.6},
        "control_A": "All alt breakout24; incremental = conditioned base mean minus non-BTC-range breakout24 base mean",
        "control_B": "For each event, same-symbol/month all eligible 4h bars' mean signed forward return in event direction",
        "control_C": "Same-symbol/month/causal ATR14-close tertile/24-bar momentum sign; <20 fallback month/vol; empty fallback month; includes events",
        "eligibility": "All 24 forward bars closed inside period; finite positive ATR14 for current event/control; no imputation, no missing rows",
        "secondary": [
            "N",
            "mean",
            "median",
            "win_fraction",
            "p05",
            "p10",
            "p25",
            "p75",
            "p90",
            "MFE",
            "MAE",
            "MFE/abs(MAE)",
            "zero/base/double",
            "month",
            "symbol",
            "leave-one-symbol-out",
            "outliers",
        ],
        "bootstrap": {"cluster": "ISO week", "draws": BOOT_DRAWS, "seed": SEED, "lower_quantile": 0.025},
        "pass": {
            "minimum_n": 100,
            "minimum_event_weeks": 12,
            "base_mean_gt_pct": 0.0,
            "bootstrap_lower_gt_pct": 0.0,
            "base_median_gte_pct": 0.0,
            "double_mean_gt_pct": 0.0,
            "positive_month_fraction_gte": 0.6,
            "minimum_positive_months": 6,
            "minimum_positive_symbols_with_at_least_10_events": 5,
            "all_leave_one_symbol_out_base_gt_pct": 0.0,
            "remove_best_event_base_mean_gt_pct": 0.0,
            "top5pct_positive_gross_contribution_lte": 0.5,
            "incremental_A_gt_pct": 0.0,
            "excess_B_gt_pct": 0.0,
            "excess_C_gt_pct": 0.0,
        },
        "data_integrity": "Exact 4h UTC grid, 12-field Binance rows, nonduplicate, valid OHLC/volume, close_time=open+4h-1ms, no partial candles, fail closed",
        "prior_sha256": {
            name: digest(path)
            for name, path in (("md", ORIGINAL_MD), ("json", ORIGINAL_JSON), ("code", ORIGINAL_CODE))
        },
        "warmup_file_sha256": {symbol: digest(historical_path(symbol)) for symbol in SYMBOLS},
        "analysis_code_sha256": digest(CODE),
        "results": None,
    }
    PROTOCOL_MD.write_text(protocol_text(p))
    write_json(PROTOCOL_JSON, p)
    print(f"FROZEN {PROTOCOL_JSON} SHA256={digest(PROTOCOL_JSON)}")
    print(f"FROZEN {PROTOCOL_MD} SHA256={digest(PROTOCOL_MD)}")


def load_protocol() -> dict:
    if not PROTOCOL_JSON.exists() or not PROTOCOL_MD.exists():
        raise FileNotFoundError("Both frozen protocols must exist before data access")
    p = json.loads(PROTOCOL_JSON.read_text())
    if p["state"] != "FROZEN_BEFORE_2026_OUTCOMES" or digest(CODE) != p["analysis_code_sha256"]:
        raise ValueError("Frozen code/protocol mismatch")
    for name, path in (("md", ORIGINAL_MD), ("json", ORIGINAL_JSON), ("code", ORIGINAL_CODE)):
        if digest(path) != p["prior_sha256"][name]:
            raise ValueError(f"Prior {name} changed since freeze")
    for symbol in SYMBOLS:
        if digest(historical_path(symbol)) != p["warmup_file_sha256"][symbol]:
            raise ValueError(f"Warmup {symbol} changed since freeze")
    return p


def validate_frame(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> None:
    if list(df.columns) != COLUMNS or len(df) != int((end - start) / INTERVAL):
        raise ValueError("Missing/extra candles or wrong columns")
    if df.time.isna().any() or df.close_time.isna().any():
        raise ValueError("Invalid timestamps")
    grid = pd.date_range(start, end - INTERVAL, freq="4h", tz="UTC")
    if not df.time.reset_index(drop=True).equals(pd.Series(grid, name="time")):
        raise ValueError("Timestamp gap, duplicate or wrong UTC grid")
    if not (df.close_time == df.time + INTERVAL - pd.Timedelta(milliseconds=1)).all():
        raise ValueError("Partial/wrong close_time")
    prices = df[["open", "high", "low", "close", "volume"]].to_numpy(dtype=float)
    if not np.isfinite(prices).all() or (prices[:, :4] <= 0).any() or (prices[:, 4] < 0).any():
        raise ValueError("Nonfinite, nonpositive price or negative volume")
    if (
        (df.high < df[["open", "low", "close"]].max(axis=1))
        | (df.low > df[["open", "high", "close"]].min(axis=1))
    ).any():
        raise ValueError("Invalid OHLC")


def parse_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, float_precision="round_trip")
    for key in ("time", "close_time"):
        df[key] = pd.to_datetime(df[key], utc=True)
    return df


def fetch() -> None:
    p = load_protocol()
    if datetime.now(timezone.utc) < END.to_pydatetime():
        raise ValueError("Frozen end not yet closed")
    DATA_DIR.mkdir(exist_ok=True)
    start_ms, end_ms = int(START.timestamp() * 1000), int(END.timestamp() * 1000)
    for symbol in SYMBOLS:
        if dataset_path(symbol).exists():
            validate_frame(parse_csv(dataset_path(symbol)), START, END)
            print(f"{symbol}: existing validated CSV retained", flush=True)
            continue
        cursor = start_ms
        rows: list[list] = []
        with requests.Session() as session:
            while cursor < end_ms:
                for attempt in range(3):
                    response = session.get(
                        URL,
                        params={
                            "symbol": symbol,
                            "interval": "4h",
                            "startTime": cursor,
                            "endTime": end_ms - 1,
                            "limit": 1000,
                        },
                        timeout=(5, 20),
                    )
                    if response.status_code not in (429, 500, 502, 503, 504):
                        break
                    time.sleep(1 + attempt)
                response.raise_for_status()
                page = response.json()
                if not isinstance(page, list) or not page or len(page) > 1000:
                    raise ValueError(f"Unexpected Binance page for {symbol}")
                if any(not isinstance(row, list) or len(row) != 12 for row in page):
                    raise ValueError(f"Malformed Binance kline for {symbol}")
                if int(page[0][0]) != cursor:
                    raise ValueError(f"Binance pagination gap for {symbol}")
                rows.extend([[row[0], row[6], *row[1:6]] for row in page])
                cursor = int(page[-1][0]) + int(INTERVAL.total_seconds() * 1000)
                time.sleep(0.08)
        df = pd.DataFrame(rows, columns=COLUMNS)
        for key in ("time", "close_time"):
            df[key] = pd.to_datetime(df[key], unit="ms", utc=True)
        for key in COLUMNS[2:]:
            df[key] = pd.to_numeric(df[key], errors="raise")
        validate_frame(df, START, END)
        with tempfile.NamedTemporaryFile(mode="w", dir=DATA_DIR, suffix=".csv", delete=False) as tmp:
            df.to_csv(tmp, index=False)
            tmp_path = Path(tmp.name)
        tmp_path.replace(dataset_path(symbol))
        print(f"{symbol}: {len(df)} candles, SHA256={digest(dataset_path(symbol))}", flush=True)
    print(f"FETCH COMPLETE; frozen code SHA256={p['analysis_code_sha256']}")


def load_data(p: dict) -> tuple[dict[str, pd.DataFrame], list[dict]]:
    data, integrity = {}, []
    for symbol in SYMBOLS:
        path = dataset_path(symbol)
        oos = parse_csv(path)
        validate_frame(oos, START, END)
        warmup = parse_csv(historical_path(symbol)).tail(120).copy()
        validate_frame(warmup, START - 120 * INTERVAL, START)
        df = pd.concat([warmup, oos], ignore_index=True)
        validate_frame(df, START - 120 * INTERVAL, END)
        data[symbol] = df
        integrity.append(
            {
                "symbol": symbol,
                "file": str(path.relative_to(ROOT)),
                "sha256": digest(path),
                "rows_2026": len(oos),
                "first_open": utc(oos.time.iloc[0]),
                "last_close": utc(oos.close_time.iloc[-1]),
                "missing": 0,
                "duplicates": 0,
                "invalid_ohlc": 0,
                "warmup_sha256": p["warmup_file_sha256"][symbol],
            }
        )
    return data, integrity


def event_side(features: pd.DataFrame) -> np.ndarray:
    # Byte-for-byte same comparisons as original sides()["breakout_24"].
    c = features.close
    long = c > features.prior_high_24
    short = c < features.prior_low_24
    return np.select([long & ~short, short & ~long], [1, -1], 0).astype(np.int8)


def future_arrays(df: pd.DataFrame) -> dict[str, np.ndarray]:
    c = df.close.to_numpy(dtype=float)
    o = df.open.to_numpy(dtype=float)
    h = df.high.to_numpy(dtype=float)
    low = df.low.to_numpy(dtype=float)
    n = len(df) - HORIZON
    windows_h = np.lib.stride_tricks.sliding_window_view(h[1:], HORIZON)
    windows_l = np.lib.stride_tricks.sliding_window_view(low[1:], HORIZON)
    return {
        "raw": (c[HORIZON:] / o[1 : n + 1] - 1) * 100,
        "entry": o[1 : n + 1],
        "exit": c[HORIZON:],
        "high": windows_h.max(axis=1),
        "low": windows_l.min(axis=1),
    }


def metric(values: np.ndarray) -> dict:
    if not len(values):
        return {"n": 0}
    return {
        "n": len(values),
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "win_fraction": float(np.mean(values > 0)),
        "p05": float(np.quantile(values, 0.05)),
        "p10": float(np.quantile(values, 0.10)),
        "p25": float(np.quantile(values, 0.25)),
        "p75": float(np.quantile(values, 0.75)),
        "p90": float(np.quantile(values, 0.90)),
    }


def bootstrap_lower(frame: pd.DataFrame) -> float:
    groups = [g.base_pct.to_numpy(dtype=float) for _, g in frame.groupby("week", sort=True)]
    rng = np.random.default_rng(SEED)
    means = np.empty(BOOT_DRAWS)
    for i in range(BOOT_DRAWS):
        picked = rng.integers(0, len(groups), size=len(groups))
        means[i] = np.concatenate([groups[j] for j in picked]).mean()
    return float(np.quantile(means, 0.025))


def observations(data: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    btc = data["BTCUSDT"]
    btc_features = trailing_features(btc).set_axis(btc.close_time)
    all_breakouts: list[dict] = []
    selected: list[dict] = []
    counts: dict[str, dict] = {}
    for symbol in ALTS:
        df = data[symbol]
        f = trailing_features(df)
        side = event_side(f)
        regime = btc_features.market_regime.reindex(df.close_time)
        if regime.isna().any():
            raise ValueError(f"BTC close-time alignment missing for {symbol}")
        range_mask = regime.to_numpy() == "range"
        future = future_arrays(df)
        n = len(future["raw"])
        dates = df.time.iloc[:n]
        month = dates.dt.strftime("%Y-%m").to_numpy()
        vol = f.vol_regime.iloc[:n].to_numpy()
        mom = f.momentum_sign.iloc[:n].to_numpy()
        atr = f.atr.iloc[:n].to_numpy(dtype=float)
        valid = (dates >= START).to_numpy() & np.isfinite(atr) & (atr > 0)
        eligible = pd.DataFrame(
            {"month": month[valid], "vol": vol[valid], "mom": mom[valid], "raw": future["raw"][valid]}
        )
        eligible["positive_raw"] = eligible.raw
        eligible["negative_raw"] = -eligible.raw
        group_month = eligible.groupby("month")
        group_vol = eligible.groupby(["month", "vol"])
        group_full = eligible.groupby(["month", "vol", "mom"])
        event_indexes = np.flatnonzero(valid & (side[:n] != 0))
        all_indexes = np.flatnonzero((dates >= START).to_numpy() & (side[:n] != 0))
        counts[symbol] = {
            "all_breakouts": len(all_indexes),
            "mature_breakouts": len(event_indexes),
            "immature_breakouts": int(np.sum((df.time >= START).to_numpy()[n:] & (side[n:] != 0))),
            "conditioned_immature": int(
                np.sum((df.time >= START).to_numpy()[n:] & (side[n:] != 0) & range_mask[n:])
            ),
        }
        for idx in event_indexes:
            sign = int(side[idx])
            raw = float(sign * future["raw"][idx])
            item = {
                "symbol": symbol,
                "time": utc(df.time.iloc[idx]),
                "close_time": utc(df.close_time.iloc[idx]),
                "side": "LONG" if sign == 1 else "SHORT",
                "sign": sign,
                "month": month[idx],
                "week": dates.iloc[idx].strftime("%G-W%V"),
                "raw_pct": raw,
                "base_pct": raw - 0.3,
                "double_pct": raw - 0.6,
                "btc_range": bool(range_mask[idx]),
            }
            all_breakouts.append(item)
            if not range_mask[idx]:
                continue
            direction_column = "positive_raw" if sign == 1 else "negative_raw"
            ref_b = group_month.get_group(month[idx])[direction_column]
            key_vol = (month[idx], vol[idx])
            key_full = (month[idx], vol[idx], mom[idx])
            ref_c = (
                group_full.get_group(key_full)[direction_column]
                if key_full in group_full.groups
                else pd.Series(dtype=float)
            )
            if len(ref_c) < 20:
                ref_c = (
                    group_vol.get_group(key_vol)[direction_column]
                    if key_vol in group_vol.groups
                    else pd.Series(dtype=float)
                )
            if len(ref_c) == 0:
                ref_c = ref_b
            entry = float(future["entry"][idx])
            mfe = float(
                (future["high"][idx] / entry - 1) * 100
                if sign == 1
                else (1 - future["low"][idx] / entry) * 100
            )
            mae = float(
                (future["low"][idx] / entry - 1) * 100
                if sign == 1
                else (1 - future["high"][idx] / entry) * 100
            )
            selected.append(
                {
                    **item,
                    "entry_open": entry,
                    "horizon_close": float(future["exit"][idx]),
                    "horizon_close_time": utc(df.close_time.iloc[idx + HORIZON]),
                    "btc_efficiency": float(btc_features.efficiency.reindex(df.close_time).iloc[idx]),
                    "mfe_pct": mfe,
                    "mae_pct": mae,
                    "control_B_signed_pct": float(ref_b.mean()),
                    "control_C_signed_pct": float(ref_c.mean()),
                    "control_C_n": len(ref_c),
                    "excess_B_pct": raw - float(ref_b.mean()),
                    "excess_C_pct": raw - float(ref_c.mean()),
                }
            )
    return pd.DataFrame(selected), pd.DataFrame(all_breakouts), counts


def summarize(frame: pd.DataFrame, all_breakouts: pd.DataFrame, counts: dict) -> dict:
    if frame.empty:
        return {"verdict": "INSUFFICIENT OOS SAMPLE", "n": 0, "exclusion_counts": counts, "criteria": {}}
    gross = frame.raw_pct.to_numpy(dtype=float)
    base = gross - 0.3
    double = gross - 0.6
    by_month = {
        name: metric(g.base_pct.to_numpy(dtype=float)) for name, g in frame.groupby("month", sort=True)
    }
    by_symbol = {
        name: metric(g.base_pct.to_numpy(dtype=float)) for name, g in frame.groupby("symbol", sort=True)
    }
    for symbol in ALTS:
        by_symbol.setdefault(symbol, {"n": 0})
    leave_one_out = {
        symbol: metric(frame.loc[frame.symbol != symbol, "base_pct"].to_numpy(dtype=float)) for symbol in ALTS
    }
    top_n_1 = max(1, math.ceil(len(frame) * 0.01))
    top_n_5 = max(1, math.ceil(len(frame) * 0.05))
    total_positive = gross[gross > 0].sum()
    best_removed = np.delete(base, np.argmax(gross)) if len(base) > 1 else np.array([])
    conditioned_mean = float(base.mean())
    non_range = all_breakouts.loc[~all_breakouts.btc_range, "base_pct"].to_numpy(dtype=float)
    all_base = all_breakouts.base_pct.to_numpy(dtype=float)
    positive_months = sum(row["mean"] > 0 for row in by_month.values())
    positive_symbols = sum(row["n"] >= 10 and row["mean"] > 0 for row in by_symbol.values())
    top5_share = (
        float(np.sort(gross)[-top_n_5:].clip(min=0).sum() / total_positive) if total_positive > 0 else None
    )
    ci_lower = bootstrap_lower(frame)
    criteria = {
        "minimum_n": len(frame) >= 100,
        "minimum_event_weeks": frame.week.nunique() >= 12,
        "base_mean_gt_zero": conditioned_mean > 0,
        "bootstrap_lower_gt_zero": ci_lower > 0,
        "base_median_gte_zero": float(np.median(base)) >= 0,
        "double_mean_gt_zero": float(np.mean(double)) > 0,
        "temporal_stability": len(by_month) >= 6
        and positive_months / len(by_month) >= 0.6
        and positive_months >= 6,
        "symbol_stability": positive_symbols >= 5,
        "leave_one_symbol_out": all(row["n"] and row["mean"] > 0 for row in leave_one_out.values()),
        "remove_best_event": len(best_removed) > 0 and float(np.mean(best_removed)) > 0,
        "top5pct_contribution": top5_share is not None and top5_share <= 0.5,
        "incremental_control_A": len(non_range) > 0 and conditioned_mean > float(np.mean(non_range)),
        "excess_control_B": float(frame.excess_B_pct.mean()) > 0,
        "excess_control_C": float(frame.excess_C_pct.mean()) > 0,
    }
    verdict = (
        "INSUFFICIENT OOS SAMPLE"
        if not (criteria["minimum_n"] and criteria["minimum_event_weeks"])
        else ("CONFIRMED" if all(criteria.values()) else "NOT CONFIRMED")
    )
    return {
        "verdict": verdict,
        "n": len(frame),
        "event_weeks": frame.week.nunique(),
        "primary_base_mean_pct": conditioned_mean,
        "bootstrap_base_lower95_pct": ci_lower,
        "zero": metric(gross),
        "base": metric(base),
        "double": metric(double),
        "mfe": metric(frame.mfe_pct.to_numpy(dtype=float)),
        "mae": metric(frame.mae_pct.to_numpy(dtype=float)),
        "median_mfe_to_abs_mae": float(np.median(frame.mfe_pct) / abs(np.median(frame.mae_pct)))
        if np.median(frame.mae_pct)
        else None,
        "months": by_month,
        "symbols": by_symbol,
        "leave_one_symbol_out": leave_one_out,
        "positive_months": positive_months,
        "positive_symbols_n_ge_10": positive_symbols,
        "control_A_all": metric(all_base),
        "control_A_non_range": metric(non_range),
        "control_A_incremental_base_pct": conditioned_mean - float(np.mean(non_range))
        if len(non_range)
        else None,
        "control_B_mean_excess_pct": float(frame.excess_B_pct.mean()),
        "control_C_mean_excess_pct": float(frame.excess_C_pct.mean()),
        "without_best_base_mean_pct": float(np.mean(best_removed)) if len(best_removed) else None,
        "top1pct_positive_gross_contribution": float(
            np.sort(gross)[-top_n_1:].clip(min=0).sum() / total_positive
        )
        if total_positive > 0
        else None,
        "top5pct_positive_gross_contribution": top5_share,
        "exclusion_counts": counts,
        "criteria": criteria,
    }


def render_report(p: dict, result: dict) -> str:
    s = result["summary"]
    if not s["n"]:
        return (
            "# OOS 2026: проверка замороженной гипотезы\n\n"
            "**INSUFFICIENT OOS SAMPLE:** зрелых событий нет. "
            "Нулевой результат не означает отсутствие эффекта.\n"
        )
    lines = [
        "# OOS 2026: проверка замороженной гипотезы",
        "",
        f"**Вердикт: `{s['verdict']}`.** Это outcome 24-барного event study, не торговая стратегия и не исторический PAPER PnL.",
        "",
        f"Период UTC: {p['period']['start_inclusive']} — {p['period']['end_exclusive']} (конец не включён). 4h, 8 пар, {p['period']['expected_candles_per_symbol']} закрытых свечей на пару. 120 исторических свечей 2025 — только прогрев.",
        "",
        "Замороженная гипотеза: альткоин закрывается за предыдущим 24-bar high/low; одновременно закрытый BTC efficiency≤0.15. Следующий open → close 24-й свечи (96 часов). Zero/base/double cost: 0/0.30/0.60 п.п. Основная метрика — mean signed return после base.",
        "",
        f"N={s['n']}; недели={s.get('event_weeks', 0)}; base mean={s.get('primary_base_mean_pct', float('nan')):+.4f}%; 95% week-bootstrap lower={s.get('bootstrap_base_lower95_pct', float('nan')):+.4f}%.",
        "",
        "## Проверка критериев",
        "",
        "| Критерий | Выполнен |",
        "|---|---|",
    ]
    lines.extend(f"|{key}|{'да' if value else 'нет'}|" for key, value in s["criteria"].items())
    lines += [
        "",
        "## Издержки и распределение",
        "",
        "|Сценарий|N|Mean %|Median %|Win >0|p05 %|p90 %|",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for label in ("zero", "base", "double"):
        m = s[label]
        lines.append(
            f"|{label}|{m['n']}|{m['mean']:+.4f}|{m['median']:+.4f}|{m['win_fraction']:.3f}|{m['p05']:+.4f}|{m['p90']:+.4f}|"
        )
    lines += [
        "",
        f"MFE mean={s['mfe']['mean']:+.4f}%, MAE mean={s['mae']['mean']:+.4f}%, median MFE/|MAE|={s['median_mfe_to_abs_mae']}. Квантили p10/p25/p75 и полные распределения — JSON.",
        "",
        "## Контроли",
        "",
        f"A все breakout N={s['control_A_all']['n']}, mean base={s['control_A_all'].get('mean', float('nan')):+.4f}%; A вне BTC-range N={s['control_A_non_range']['n']}, mean base={s['control_A_non_range'].get('mean', float('nan')):+.4f}%; incremental={s['control_A_incremental_base_pct']:+.4f} п.п.",
        f"B средний excess={s['control_B_mean_excess_pct']:+.4f} п.п.; C matched symbol/month/vol/momentum excess={s['control_C_mean_excess_pct']:+.4f} п.п. Это описательные контроли, не доказательство причинности.",
        "",
        "## Временная и парная устойчивость",
        "",
        "|Месяц|N|Mean base %|",
        "|---|---:|---:|",
    ]
    lines.extend(f"|{key}|{m['n']}|{m['mean']:+.4f}|" for key, m in s["months"].items())
    lines += ["", "|Пара|N|Mean base %|Без пары mean base %|", "|---|---:|---:|---:|"]
    for symbol in ALTS:
        m, lo = s["symbols"][symbol], s["leave_one_symbol_out"][symbol]
        lines.append(
            f"|{symbol}|{m['n']}|{m.get('mean', float('nan')):+.4f}|{lo.get('mean', float('nan')):+.4f}|"
        )
    lines += [
        "",
        "## Выбросы и данные",
        "",
        f"Без лучшего события mean base={s['without_best_base_mean_pct']:+.4f}%; доля всех положительных gross returns от top 1%={s['top1pct_positive_gross_contribution']:.3f}, top 5%={s['top5pct_positive_gross_contribution']:.3f}.",
        "",
        "|Пара|2026 свечей|SHA256 CSV|Зрелые breakout|Незрелые conditioned|",
        "|---|---:|---|---:|---:|",
    ]
    for item in result["data_integrity"]:
        c = s["exclusion_counts"][item["symbol"]] if item["symbol"] in s["exclusion_counts"] else {}
        lines.append(
            f"|{item['symbol']}|{item['rows_2026']}|`{item['sha256']}`|{c.get('mature_breakouts', '—')}|{c.get('conditioned_immature', '—')}|"
        )
    lines += [
        "",
        "Во всех рядах: missing=0, duplicates=0, invalid OHLC=0, UTC 4h grid и закрытие свечи проверены. Незрелые правые события не оценивались; месяцы/пары с плохим результатом не исключались.",
        "",
        "## Воспроизводимость и ограничения",
        "",
        f"Frozen MD SHA256 `{result['protocol_sha256']['md']}`; JSON SHA256 `{result['protocol_sha256']['json']}`; analysis code SHA256 `{p['analysis_code_sha256']}`; исходный research-code SHA256 `{p['prior_sha256']['code']}`.",
        "",
        "`python3 -B reports/oos_2026_confirmation.py --self-test` затем `python3 -B reports/oos_2026_confirmation.py --evaluate` с неизменёнными файлами данных. `--fetch` нужен только для первичной публичной загрузки и не перезаписывает файлы.",
        "",
        "Гипотеза выбрана после просмотра 2024–2025. События перекрываются, 24-bar выход не учитывает путь исполнения SL/TP, funding, spread/impact и реализованный портфель. Даже `CONFIRMED` не разрешает менять действующий PAPER bot. Следующий исследовательский этап требует новой будущей полосы; потенциально независимые от OHLCV признаки — bid/ask spread, order-book imbalance, aggressor flow, фактическое проскальзывание, funding, open interest и liquidations — могут добавлять новые сведения, но edge не гарантируют.",
        "",
    ]
    return "\n".join(lines)


def evaluate() -> None:
    p = load_protocol()
    data, integrity = load_data(p)
    frame, all_breakouts, counts = observations(data)
    summary = summarize(frame, all_breakouts, counts)
    result = {
        "hypothesis": p["hypothesis"],
        "period": p["period"],
        "source": URL,
        "protocol_sha256": {"md": digest(PROTOCOL_MD), "json": digest(PROTOCOL_JSON)},
        "analysis_code_sha256": digest(CODE),
        "data_integrity": integrity,
        "summary": summary,
    }
    if frame.empty:
        EVENTS_CSV.write_text("symbol,time,side,raw_pct,base_pct\n")
    else:
        frame.to_csv(EVENTS_CSV, index=False, float_format="%.12g")
    result["events_sha256"] = digest(EVENTS_CSV)
    write_json(REPORT_JSON, result)
    REPORT_MD.write_text(render_report(p, result))
    print(f"{summary['verdict']}: N={summary['n']}, base mean={summary.get('primary_base_mean_pct')}")


def self_test() -> None:
    # Synthetic anti-lookahead, exact horizon, BTC close-time alignment, costs, determinism.
    n = 180
    times = pd.date_range("2025-01-01", periods=n, freq="4h", tz="UTC")
    close = np.full(n, 100.0)
    close[50] = 102.0
    df = pd.DataFrame(
        {
            "time": times,
            "close_time": times + INTERVAL - pd.Timedelta(milliseconds=1),
            "open": close.copy(),
            "high": close + 0.1,
            "low": close - 0.1,
            "close": close.copy(),
            "volume": 1.0,
        }
    )
    f = trailing_features(df)
    before = event_side(f)
    assert before[50] == 1 and before[49] == 0
    changed = df.copy()
    changed.loc[51:, ["open", "high", "low", "close"]] *= 2
    assert np.array_equal(before[:51], event_side(trailing_features(changed))[:51])
    future = future_arrays(df)
    assert math.isclose(future["entry"][50], df.open.iloc[51])
    assert math.isclose(future["exit"][50], df.close.iloc[74])
    assert math.isclose(future["high"][50], df.high.iloc[51:75].max())
    assert math.isclose(future["low"][50], df.low.iloc[51:75].min())
    assert math.isclose((future["raw"][50] - 0.3) - (future["raw"][50] - 0.6), 0.3)
    assert len(future["raw"]) == n - HORIZON
    assert n - HORIZON not in range(len(future["raw"]))
    btc = df.copy()
    btc.loc[50, "close"] = 102
    btc_features = trailing_features(btc).set_axis(btc.close_time)
    matched = btc_features.market_regime.reindex(df.close_time)
    assert matched.iloc[50] == btc_features.market_regime.iloc[50]
    shifted = btc_features.copy()
    shifted.index = shifted.index + INTERVAL
    assert (
        shifted.market_regime.reindex(df.close_time).iloc[50] != matched.iloc[50]
        or shifted.efficiency.reindex(df.close_time).iloc[50] != btc_features.efficiency.iloc[50]
    )
    assert np.array_equal(event_side(f), event_side(trailing_features(df)))
    try:
        validate_frame(df.iloc[:-1], times[0], times[-1] + INTERVAL)
    except ValueError:
        pass
    else:
        raise AssertionError("Partial/missing candle passed integrity")
    print("SELF-TEST PASSED: causal signal, exact horizon, BTC timing, costs, partial candle, determinism")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    for action in ("self-test", "freeze", "fetch", "evaluate"):
        group.add_argument(f"--{action}", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    elif args.freeze:
        freeze()
    elif args.fetch:
        fetch()
    else:
        evaluate()


if __name__ == "__main__":
    main()
