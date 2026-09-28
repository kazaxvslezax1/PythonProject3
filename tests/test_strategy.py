import pandas as pd
import pytest
from analysis_service import analyze_market, consensus_from_analysis
from signal_models import TradePlan
from strategy_engine import generate_signal


@pytest.mark.parametrize("side,stop,tps", [("LONG", 99, [101, 102, 103]), ("SHORT", 101, [99, 98, 97])])
def test_plans(side, stop, tps):
    assert TradePlan(direction=side, entry=100, stop_loss=stop, take_profits=tps).rr == 3
    with pytest.raises(ValueError):
        TradePlan(direction=side, entry=100, stop_loss=stop, take_profits=tps[::-1])


def test_same_signal_and_no_future(candles):
    df = candles()
    cut = df.close_time.iloc[99] + pd.Timedelta(milliseconds=1)
    a = generate_signal(df.iloc[:100], "BTCUSDT", "1h", cut)
    b = generate_signal(df, "BTCUSDT", "1h", cut)
    assert a == b
    analysis = analyze_market("BTCUSDT", "1h", cut, loader=lambda *a, **kw: df.iloc[:100])
    assert analysis["technical_signal"] == a
    consensus = consensus_from_analysis(analysis)
    assert consensus["systems_checked"] == 3
    assert consensus["final_direction"] == a.direction.value
    assert 0 <= consensus["confidence"] <= 100


def test_threshold_reachable(candles):
    df = candles(n=84, slope=0.005)
    df.loc[len(df) - 1, "volume"] = 400
    a = generate_signal(df, "BTCUSDT", "1h", df.close_time.iloc[-1] + pd.Timedelta(milliseconds=1))
    assert a.quality >= 7.5
