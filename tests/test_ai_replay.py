from datetime import timedelta

import httpx
import pytest
from ai_backtest import compare_ai
from deepseek_analyzer import AnalysisStore, DeepSeekAnalyzer
from test_deepseek import attach_facts, response, valid_result


@pytest.mark.asyncio
async def test_saved_replay_is_identical_and_holdout_is_separate(tmp_path, candles):
    df = candles(n=184, slope=0.005)
    calls = []

    def handler(req):
        calls.append(1)
        # Deliberately reject all signals: not a model efficacy claim.
        return attach_facts(response(valid_result("HOLD")), req)

    a = DeepSeekAnalyzer(
        store=AnalysisStore(tmp_path / "replay.db"),
        api_key="test-placeholder",
        transport=httpx.MockTransport(handler),
        daily_budget=100,
        clock=lambda: df.close_time.iloc[-1].to_pydatetime() + timedelta(days=1),
    )
    first = await compare_ai(df, "BTCUSDT", "1h", a, retrospective=True, allow_api=True)
    count = len(calls)
    a.key = ""
    replay = await compare_ai(df, "BTCUSDT", "1h", a, retrospective=True)
    assert first == replay
    assert len(calls) == count and count > 0
    assert first["kind"] == "RETROSPECTIVE_AI_EXPERIMENT"
    assert first["complete"]
    assert first["segments"]["holdout"]["hybrid_filter"]["total_trades"] == 0
    assert "no proof" in first["conclusion"] or "did not improve" in first["conclusion"]


@pytest.mark.asyncio
async def test_missing_replay_is_not_evidence(tmp_path, candles):
    df = candles(n=180, slope=0.005)
    a = DeepSeekAnalyzer(store=AnalysisStore(tmp_path / "missing.db"), api_key="")
    report = await compare_ai(df, "BTCUSDT", "1h", a)
    assert not report["complete"]
    assert report["missing_reviews"] > 0
    assert "cannot be assessed" in report["conclusion"]
