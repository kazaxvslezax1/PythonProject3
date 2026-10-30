import pandas as pd
import pytest
from backtester import AdvancedBacktester, signals_for, simulate, statistics
from execution import PaperPosition
from signal_models import TradePlan, TradingSignal
from walk_forward import COSTS, folds, metrics, regime, signal_counts


def signal(df, index=59, side="LONG"):
    return TradingSignal(
        symbol="BTCUSDT",
        timeframe="1h",
        timestamp=df.close_time.iloc[index],
        direction=side,
        quality=8,
        strength=4 if side == "LONG" else -4,
        reasons=["fixture"],
        plan=TradePlan(
            direction=side,
            entry=100,
            stop_loss=99 if side == "LONG" else 101,
            take_profits=[101, 102, 103] if side == "LONG" else [99, 98, 97],
        ),
    )


def flat(candles, n=65):
    df = candles(n=n, slope=0)
    df[["open", "close"]] = 100.0
    df["high"], df["low"] = 100.2, 99.8
    return df


def test_empty_and_breakeven():
    run = simulate(pd.DataFrame(), {})
    assert run["stats"]["final_capital"] == 10000
    assert run["stats"]["total_trades"] == 0
    assert statistics([{"pnl": 0}], [10000], 10000)["losing_trades"] == 0
    assert statistics([], [], 10000)["max_drawdown"] == 0
    with pytest.raises(ValueError, match="Empty"):
        AdvancedBacktester().compare(pd.DataFrame(), "BTCUSDT", "1h")


def test_future_signal_is_rejected(candles):
    df = flat(candles)
    with pytest.raises(ValueError, match="Future signal"):
        simulate(df, {59: signal(df, 62)})


def test_warmup_and_future_mutation_do_not_change_signals(candles):
    df = candles(130, slope=0.005)
    first = signals_for(df, "BTCUSDT", "1h")
    changed = df.copy()
    changed.loc[125:, ["open", "high", "low", "close"]] *= 2
    second = signals_for(changed, "BTCUSDT", "1h")
    assert min(first) == 119
    assert all(first[i] == second[i] for i in range(119, 125))


@pytest.mark.parametrize("side", ["LONG", "SHORT"])
def test_round_trip_fee_slippage_and_fixed_size(candles, side):
    df = flat(candles)
    clean = simulate(df, {59: signal(df, side=side)}, fee=0, slippage=0, fixed_notional=1000)
    paid = simulate(df, {59: signal(df, side=side)}, fee=0.001, slippage=0.0005, fixed_notional=1000)
    assert clean["stats"]["net_pnl"] == 0
    assert paid["stats"]["net_pnl"] < -2.9
    assert paid["fills"][0]["price"] == pytest.approx(100 * (1.0005 if side == "LONG" else 0.9995))
    assert paid["fills"][0]["quantity"] * paid["fills"][0]["price"] == pytest.approx(1000)
    assert paid["stats"]["net_pnl"] == pytest.approx(sum(f["pnl"] for f in paid["fills"]))
    assert sum(f["fee"] for f in paid["fills"]) == pytest.approx(2, abs=0.002)


def test_ambiguous_bar_stop_first_and_hold_exit(candles):
    df = flat(candles)
    df.loc[61, ["high", "low"]] = [104, 98]
    run = simulate(df, {59: signal(df)}, fee=0, slippage=0)
    assert run["fills"][1]["reason"] == "STOP_LOSS"
    assert run["ambiguous_bars"] == 1
    assert run["stats"]["net_pnl"] == pytest.approx(-10)


def test_gap_stop_and_no_retroactive_breakeven():
    p = PaperPosition(
        TradePlan(direction="LONG", entry=100, stop_loss=99, take_profits=[101, 102, 103]), 10, 0, 0
    )
    p.enter("start")
    p.on_bar(pd.Series(dict(open=100, low=99.5, high=101.5, close_time="one")))
    assert p.remaining == pytest.approx(0.7)  # Low below newly moved stop must not close retroactively.
    p.on_bar(pd.Series(dict(open=98, low=97, high=100, close_time="two")))
    assert p.fills[-1]["price"] == 98
    assert p.realized_pnl == pytest.approx(3 - 14)


def test_proxy_limits_and_loss_streak(candles):
    df = flat(candles)
    df.loc[60:, "low"] = 98
    signals = {i: signal(df, i) for i in range(59, len(df) - 1)}
    run = simulate(df, signals, fee=0, slippage=0, fixed_notional=1000, max_daily_entries=2)
    assert run["stats"]["total_trades"] == 2
    assert metrics(run)["max_loss_streak"] == 2
    assert metrics(run)["expectancy"] == -10
    assert metrics(run)["sample_warning"] == "LESS_THAN_30_TRADES"


def test_folds_are_chronological_disjoint_and_frozen():
    windows = folds("2024-01-01T00:00Z", "2026-01-01T00:00Z")
    assert len(windows) == 5
    for i, w in enumerate(windows):
        assert w["train_start"] < w["validation_start"] < w["test_start"] < w["test_end"]
        if i:
            assert windows[i - 1]["test_end"] == w["test_start"]
    assert COSTS["base"] == (0.001, 0.0005)
    assert folds("2024-01-01", "2024-03-01") == []


def test_regime_is_based_only_on_signal_bar_values():
    base = {"ATR": 1, "close": 100, "ADX": 30, "SMA_20": 110, "SMA_50": 100}
    assert regime(base) == "trend_up"
    assert regime({**base, "ATR": 2}) == "high_volatility"
    assert regime({**base, "ADX": 24}) == "sideways"
    assert regime({**base, "SMA_20": 90}) == "trend_down"


def test_signal_counts_exclude_terminal_unfillable_signal(candles):
    df = flat(candles)
    signals = {59: signal(df), 64: signal(df, 64)}
    assert signal_counts(signals, 60, 65)["total"] == 1


def research_cli():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "scripts/run_walk_forward.py"
    spec = importlib.util.spec_from_file_location("research_cli", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_offline_missing_data_never_downloads(tmp_path, monkeypatch):
    cli = research_cli()

    def forbidden(*args):
        pytest.fail("Offline mode attempted a download")

    monkeypatch.setattr(cli, "download", forbidden)
    with pytest.raises(ValueError, match="Missing offline dataset"):
        cli.job(("BTCUSDT", "1h", "2024-01-01T00:00Z", "2026-01-01T00:00Z", str(tmp_path), True))


def test_public_candle_pagination_and_round_trip(candles, tmp_path, monkeypatch):
    cli = research_cli()
    frame = candles(n=121)
    rows = [
        [
            int(row.time.timestamp() * 1000),
            *[str(row[k]) for k in ("open", "high", "low", "close", "volume")],
            int(row.close_time.timestamp() * 1000),
        ]
        for _, row in frame.iterrows()
    ]
    calls = []

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, url, *, params, timeout, allow_redirects):
            calls.append(params)
            assert url == "https://api.binance.com/api/v3/klines"
            assert timeout == (5, 20)
            assert allow_redirects is False
            page = [r for r in rows if params["startTime"] <= r[0] <= params["endTime"]][:100]

            class Response:
                status_code = 200

                def raise_for_status(self):
                    pass

                def json(self):
                    return page

            return Response()

    import binance_http

    monkeypatch.setattr(binance_http, "_new_session", Session)
    monkeypatch.setattr(cli.time, "sleep", lambda _: None)
    path = tmp_path / "candles.csv"
    result = cli.download(
        "BTCUSDT", "1h", frame.time.iloc[0], frame.close_time.iloc[-1] + pd.Timedelta(milliseconds=1), path
    )
    assert len(calls) == 2
    assert calls[1]["startTime"] == rows[100][0]
    pd.testing.assert_frame_equal(result, frame)
    restored = pd.read_csv(path, float_precision="round_trip")
    assert restored.close.tolist() == result.close.tolist()
