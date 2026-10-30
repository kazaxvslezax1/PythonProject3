"""Run offline replay by default. CSV must contain time and close_time in UTC."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import pandas as pd
from ai_backtest import compare_ai, save_comparison
from deepseek_analyzer import DeepSeekAnalyzer
from market_data import validate_candles


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candles", type=Path)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--retrospective", action="store_true")
    parser.add_argument(
        "--allow-api",
        action="store_true",
        help="Explicit paid retrospective experiment; requires --retrospective",
    )
    args = parser.parse_args()
    if args.allow_api and not args.retrospective:
        parser.error("Modern historical API calls require --retrospective")
    df = pd.read_csv(args.candles)
    df["time"] = pd.to_datetime(df.time, utc=True)
    df["close_time"] = pd.to_datetime(df.close_time, utc=True)
    df = validate_candles(
        df, args.timeframe, df.close_time.iloc[-1] + pd.Timedelta(milliseconds=1), min_bars=180
    )
    report = asyncio.run(
        compare_ai(
            df,
            args.symbol,
            args.timeframe,
            DeepSeekAnalyzer(),
            retrospective=args.retrospective,
            allow_api=args.allow_api,
        )
    )
    save_comparison(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
