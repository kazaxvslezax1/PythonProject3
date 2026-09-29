"""Reproducible public-data research. No credentials, AI completions or order endpoints."""

# ruff: noqa: E402 -- CLI adds the repository backend to sys.path before local imports.

import argparse
import concurrent.futures
import gzip
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
import pandas as pd
import requests
from market_data import INTERVALS, normalize_symbol, validate_candles
from signal_models import TradingSignal
from storage import atomic_json
from walk_forward import COSTS, ai_archive_coverage, digest, evaluate, features_and_signals


def download(symbol, timeframe, start, end, path):
    cursor = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    rows = []
    with requests.Session() as session:
        while cursor < end_ms:
            response = None
            for attempt in range(3):
                response = session.get(
                    "https://api.binance.com/api/v3/klines",
                    params={
                        "symbol": symbol,
                        "interval": timeframe,
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
            if not page:
                break
            if not isinstance(page, list) or int(page[0][0]) < cursor:
                raise ValueError("Invalid Binance pagination")
            rows.extend([[r[0], r[6], *r[1:6]] for r in page])
            cursor = int(page[-1][0]) + INTERVALS[timeframe] * 1000
            time.sleep(0.08)
    frame = pd.DataFrame(rows, columns=["time", "close_time", "open", "high", "low", "close", "volume"])
    for key in ("time", "close_time"):
        frame[key] = pd.to_datetime(frame[key], unit="ms", utc=True)
    frame = validate_candles(frame, timeframe, end, min_bars=121, require_fresh=False)
    frame.to_csv(path, index=False)
    return frame


def job(args):
    symbol, tf, start_s, end_s, directory, offline = args
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    start, end = pd.Timestamp(start_s), pd.Timestamp(end_s)
    data = root / f"{symbol}_{tf}_{start.date()}_{end.date()}.csv"
    if data.exists():
        frame = pd.read_csv(data, float_precision="round_trip")
        for key in ("time", "close_time"):
            frame[key] = pd.to_datetime(frame[key], utc=True)
        frame = validate_candles(frame, tf, end, min_bars=121, require_fresh=False)
    elif offline:
        raise ValueError("Missing offline dataset")
    else:
        frame = download(symbol, tf, start - pd.Timedelta(seconds=120 * INTERVALS[tf]), end, data)
    effective_start = max(start, (frame.time.iloc[0] + pd.Timedelta(seconds=120 * INTERVALS[tf])).ceil("D"))
    effective_end = min(end, (frame.close_time.iloc[-1] + pd.Timedelta(milliseconds=1)).floor("D"))
    metadata = {
        "source": "https://api.binance.com/api/v3/klines",
        "sha256": digest(data),
        "file": str(data.relative_to(ROOT)),
        "rows": len(frame),
        "first_open": str(frame.time.iloc[0]),
        "last_close": str(frame.close_time.iloc[-1]),
        "duplicates": int(frame.time.duplicated().sum()),
        "missing_internal": int(
            ((frame.time.diff().dropna().dt.total_seconds() / INTERVALS[tf]) - 1).clip(lower=0).sum()
        ),
        "effective_start": str(effective_start),
        "effective_end": str(effective_end),
        "requested_start": start_s,
        "requested_end": end_s,
    }
    code = hashlib.sha256(
        b"".join(
            (ROOT / "backend" / f).read_bytes()
            for f in (
                "strategy_engine.py",
                "technical_indicators.py",
                "market_data.py",
                "signal_models.py",
                "walk_forward.py",
            )
        )
    ).hexdigest()
    cache = data.with_suffix(".signals.json.gz")
    cached = None
    if cache.exists():
        with gzip.open(cache, "rt") as handle:
            candidate = json.load(handle)
        if candidate["data_hash"] == metadata["sha256"] and candidate["code_hash"] == code:
            cached = candidate
    print(
        f"{symbol} {tf}: validated {len(frame)} candles; signals {'cache' if cached else 'compute'}",
        flush=True,
    )
    if cached:
        signals = {int(i): TradingSignal.model_validate(s) for i, s in cached["signals"].items()}
        features = {int(i): f for i, f in cached["features"].items()}
    else:
        signals, features = features_and_signals(frame, symbol, tf)
        with gzip.open(cache, "wt") as handle:
            json.dump(
                {
                    "data_hash": metadata["sha256"],
                    "code_hash": code,
                    "signals": {i: s.model_dump(mode="json") for i, s in signals.items()},
                    "features": features,
                },
                handle,
            )
    result = evaluate(frame, signals, features, symbol, tf, effective_start, effective_end)
    result["data"] = metadata
    result["signal_code_hash"] = code
    atomic_json(root / f"{symbol}_{tf}.result.json", result)
    print(f"{symbol} {tf}: complete, {len(result['folds'])} test folds", flush=True)
    return result


def write_report(results, failures, config, path, archive):
    lines = [
        "# Walk-forward: реальные данные Binance",
        "",
        "Параметры стратегии не подбирались. Все результаты — PAPER-модель, не доказательство будущей доходности.",
        "",
        "Первый train — 180 дней; следующие 90 дней — validation; test — неперекрывающиеся окна по 90 дней. Train расширяется; параметры остаются неизменными. Validation не используется для выбора победителя. Хвост короче полного окна исключается.",
        "",
        "Техническая модель: 10% текущего капитала на позицию. PAPER proxy: фиксированные 1000, качество ≥7, объём ≥1.5, до 6 входов/сутки на пару, cooldown 30 минут. Это не общий портфельный лимит реального менеджера. Начальный капитал каждого ряда 10000; капитал переносится между test-окнами, позиции закрываются на границах.",
        "",
        "Издержки на каждую сторону: base комиссия 0.10%, slippage 0.05%; double 0.20%/0.10%; stress 0.30%/0.20%; zero 0/0. Это сценарии чувствительности, а не восстановленные исторические тарифы.",
        "",
        "## Данные",
        "",
        "|Пара|TF|Свечей|Период данных UTC|Пропуски|",
        "|---|---|---:|---|---:|",
    ]
    if results:
        positive = {
            profile: sum(r["aggregate"][f"{profile}:base"]["total_profit"] > 0 for r in results)
            for profile in ("technical", "paper_proxy")
        }
        lines[4:4] = [
            f"Завершено {len(results)} рядов; положительный итог после базовых издержек: technical {positive['technical']}/{len(results)}, paper_proxy {positive['paper_proxy']}/{len(results)}. Положительный отдельный итог не доказывает устойчивость; см. окна, число сделок и стресс затрат ниже.",
            "",
        ]
    for r in results:
        d = r["data"]
        lines.append(
            f"|{r['symbol']}|{r['timeframe']}|{d['rows']}|{d['first_open']} — {d['last_close']}|{d['missing_internal']}|"
        )
    for profile in ("technical", "paper_proxy"):
        lines += [
            "",
            f"## Вне периода настройки: {profile}",
            "",
            "|Пара|TF|Сделок|WR %|PF|Expectancy USD|Средняя прибыль/убыток|DD %|Net %|Zero %|Double %|Stress %|Макс серия потерь|",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for r in results:
            a = r["aggregate"]
            m = a[f"{profile}:base"]

            def fmt(v):
                return "—" if v is None else f"{v:.2f}"

            lines.append(
                f"|{r['symbol']}|{r['timeframe']}|{m['total_trades']}|{fmt(m['win_rate'])}|{fmt(m['profit_factor'])}|{fmt(m['expectancy'])}|{fmt(m['payoff_ratio'])}|{fmt(m['max_drawdown'])}|{fmt(m['total_profit'])}|{fmt(a[f'{profile}:zero']['total_profit'])}|{fmt(a[f'{profile}:double']['total_profit'])}|{fmt(a[f'{profile}:stress']['total_profit'])}|{m['max_loss_streak']}|"
            )
        lines += [
            "",
            "### Последовательные test-периоды",
            "",
            "|Пара|TF|Окно UTC|Сделок|Net %|DD %|Выборка|",
            "|---|---|---|---:|---:|---:|---|",
        ]
        for r in results:
            for row in r["out_of_sample"]:
                if row["profile"] == profile and row["cost"] == "base":
                    m = row["metrics"]
                    lines.append(
                        f"|{r['symbol']}|{r['timeframe']}|{row['test_start'][:10]} — {row['test_end'][:10]}|{m['total_trades']}|{m['total_profit']:.2f}|{m['max_drawdown']:.2f}|{'малая (<30)' if m['sample_warning'] else '≥30, не гарантия'}|"
                    )
        lines += [
            "",
            "### Стабильность между test-периодами (base)",
            "",
            "|Пара|TF|Положительных окон|Худшее окно %|Лучшее окно %|",
            "|---|---|---:|---:|---:|",
        ]
        for r in results:
            returns = r["aggregate"][f"{profile}:base"]["fold_returns"]
            lines.append(
                f"|{r['symbol']}|{r['timeframe']}|{sum(v > 0 for v in returns)}/{len(returns)}|{min(returns):.2f}|{max(returns):.2f}|"
            )
    lines += [
        "",
        "## Validation перед первым test (technical, base)",
        "",
        "Настройка параметров не выполнялась. Эти результаты не включены в итог test; последующие validation-окна и метрики сохранены в JSON.",
        "",
        "|Пара|TF|Период UTC|Сделок|Net %|",
        "|---|---|---|---:|---:|",
    ]
    for r in results:
        v = r["validation"][0]
        lines.append(
            f"|{r['symbol']}|{r['timeframe']}|{v['start'][:10]} — {v['end'][:10]}|{v['metrics']['total_trades']}|{v['metrics']['total_profit']:.2f}|"
        )
    lines += [
        "",
        "## Сигналы технической стратегии на test-периодах",
        "",
        "|Пара|TF|LONG|SHORT|HOLD|Доли L/S/H %|",
        "|---|---|---:|---:|---:|---|",
    ]
    for r in results:
        rows = [x for x in r["out_of_sample"] if x["profile"] == "technical" and x["cost"] == "base"]
        counts = {k: sum(x["signals"]["counts"][k] for x in rows) for k in ("LONG", "SHORT", "HOLD")}
        total = sum(counts.values())
        lines.append(
            f"|{r['symbol']}|{r['timeframe']}|{counts['LONG']}|{counts['SHORT']}|{counts['HOLD']}|"
            + "/".join(f"{100 * v / total:.1f}" for v in counts.values())
            + "|"
        )
    lines += [
        "",
        "## Режимы рынка (на свече формирования входа, base)",
        "",
        "High volatility: ATR/close ≥2% на бар; иначе ADX≥25 означает trend_up/down по SMA20/SMA50, иначе sideways. Правила зафиксированы до результатов. Группы не являются отдельными портфелями; здесь только атрибуция PnL по режиму входа.",
        "",
        "|Пара|TF|Модель|Режим|Сделок|Net USD|",
        "|---|---|---|---|---:|---:|",
    ]
    for r in results:
        for profile in ("technical", "paper_proxy"):
            groups = {}
            for row in r["out_of_sample"]:
                if row["profile"] == profile and row["cost"] == "base":
                    for name, m in row["regimes"].items():
                        g = groups.setdefault(name, [0, 0])
                        g[0] += m["trades"]
                        g[1] += m["net_pnl"]
            for name, (n, pnl) in groups.items():
                lines.append(f"|{r['symbol']}|{r['timeframe']}|{profile}|{name}|{n}|{pnl:.2f}|")
    lines += [
        "",
        "## DeepSeek",
        "",
        json.dumps(archive, ensure_ascii=False),
        "",
        "ADVISORY не изменяет торговое решение по определению. Без своевременных исторических ответов эмпирическое сравнение AI не проводится; нулевую разницу не выдаём за доказательство качества AI. FILTER не включался; новых AI-запросов нет.",
        "",
        "## Ограничения",
        "",
        "SHORT на спотовых свечах — математическая модель, не доступная спотовая продажа без займа. Не учтены funding, заём, стакан, задержки, исторические tick/lot ограничения. SL исполняется первым при неоднозначной свече; перенос стопа после TP действует со следующего бара. Просадка считается по отметкам close, не по внутрисвечному худшему пути. Живой монитор опрашивает ticker и не тождественен OHLC replay. Zero/double/stress — отдельные прогоны: издержки могут изменить допустимость входа и набор сделок. Выборка текущих поддерживаемых монет имеет survivorship bias. Параметры стратегии созданы до этого исследования, но нет доказательства, что автор ранее не видел эти периоды: это chronological OOS относительно нашего протокола, не слепой prospective test.",
        "",
        "Конфигурация, SHA256 CSV, средние выигрыши/потери, комиссии, validation, распределение сигналов и окна сохранены в соседнем WALK_FORWARD_RESULTS.json. CSV и кэш находятся в runtime/walk_forward/data; исходные свечи не заменялись синтетикой.",
        "",
        "Ошибки загрузки/истории: " + json.dumps(failures, ensure_ascii=False),
    ]
    Path(path).write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "SHIBUSDT", "PEPEUSDT"],
    )
    parser.add_argument("--timeframes", nargs="+", default=["1h", "4h"])
    parser.add_argument("--start", default="2024-01-01")
    parser.add_argument("--end", default="2026-01-01")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    start, end = pd.Timestamp(args.start, tz="UTC"), pd.Timestamp(args.end, tz="UTC")
    if start >= end or end > pd.Timestamp.now(tz="UTC").floor("D"):
        parser.error("Need a closed historical UTC range")
    directory = ROOT / "runtime/walk_forward/data"
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    config = {
        "symbols": [normalize_symbol(s) for s in args.symbols],
        "timeframes": args.timeframes,
        "start": str(start),
        "end": str(end),
        "costs": COSTS,
        "train_days": 180,
        "validation_days": 90,
        "test_days": 90,
        "parameter_search": False,
        "regime_ATR_fraction": 0.02,
        "regime_ADX": 25,
    }
    atomic_json(reports / "WALK_FORWARD_PROTOCOL.json", config)
    tasks = [
        (s, tf, str(start), str(end), str(directory), args.offline)
        for s in config["symbols"]
        for tf in args.timeframes
    ]
    results, failures = [], []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        jobs = {pool.submit(job, task): task for task in tasks}
        for future in concurrent.futures.as_completed(jobs):
            task = jobs[future]
            try:
                results.append(future.result())
            except Exception as exc:
                failure = {"symbol": task[0], "timeframe": task[1], "error_type": type(exc).__name__}
                failures.append(failure)
                print(f"FAILED {task[0]} {task[1]} {type(exc).__name__}", flush=True)
    results.sort(key=lambda r: (config["symbols"].index(r["symbol"]), r["timeframe"]))
    archive = ai_archive_coverage(ROOT / "runtime/ai.sqlite3", start, end)
    atomic_json(
        reports / "WALK_FORWARD_RESULTS.json",
        {"config": config, "results": results, "failures": failures, "ai_archive": archive},
    )
    write_report(results, failures, config, reports / "WALK_FORWARD_RESULTS.md", archive)
    print(f"Completed {len(results)}/{len(tasks)} datasets; reports/WALK_FORWARD_RESULTS.md", flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
