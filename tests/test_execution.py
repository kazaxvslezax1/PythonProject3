import pandas as pd
import pytest
from backtester import simulate, statistics
from execution import PaperPosition
from signal_models import TradePlan, TradingSignal


def test_stop_on_hold_and_next_bar_entry(candles):
    df = candles(65, slope=0)
    df.loc[60, ["open", "high", "low", "close"]] = [100, 100.5, 99.5, 100]
    df.loc[61, ["open", "high", "low", "close"]] = [100, 100.5, 98, 99]
    sig = TradingSignal(
        symbol="BTCUSDT",
        timeframe="1h",
        timestamp=df.close_time.iloc[59],
        direction="LONG",
        quality=8,
        strength=4,
        reasons=["test"],
        plan=TradePlan(direction="LONG", entry=100, stop_loss=99, take_profits=[101, 102, 103]),
    )
    result = simulate(df, {59: sig, 60: sig}, fee=0, slippage=0)
    # signal at close 60 enters at open 61, hits SL even without signal at 61.
    assert result["fills"][0]["time"] == str(df.time.iloc[60])
    assert result["fills"][1]["reason"] == "STOP_LOSS"
    assert result["stats"]["max_drawdown"] > 0


def test_partial_pnl_and_stop_priority():
    p = PaperPosition(
        TradePlan(direction="LONG", entry=100, stop_loss=99, take_profits=[101, 102, 103]), 10, 0, 0
    )
    p.enter("start")
    p.on_bar(pd.Series(dict(open=100, low=99.5, high=101.5, close_time="a")))
    assert p.remaining == pytest.approx(0.7)
    assert p.realized_pnl == pytest.approx(3)
    assert p.plan.stop_loss == 100
    p.on_bar(pd.Series(dict(open=100, low=99, high=104, close_time="b")))
    assert p.remaining == 0
    assert p.realized_pnl == pytest.approx(3)


def test_short_commissions_and_all_targets():
    p = PaperPosition(
        TradePlan(direction="SHORT", entry=100, stop_loss=101, take_profits=[99, 98, 97]), 10, 0.001, 0
    )
    p.enter("start")
    p.on_bar(pd.Series(dict(open=100, low=96, high=100.5, close_time="a")))
    assert p.remaining == pytest.approx(0)
    assert p.realized_pnl == pytest.approx(21 - 1 - 0.979)


def test_first_loss_drawdown():
    assert statistics([{"pnl": -100}], [10000, 9900], 10000)["max_drawdown"] == pytest.approx(1)
