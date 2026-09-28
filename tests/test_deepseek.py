import json
from datetime import timedelta

import httpx
import pytest
from deepseek_analyzer import AIAnalysisResult, AnalysisStore, DeepSeekAnalyzer
from hybrid_strategy import AIMode, hybrid_signal


def valid_result(direction="LONG"):
    evidence = {"reference": "RSI", "explanation": "Подтверждение импульса"}
    return dict(
        direction=direction,
        factors_for=[evidence],
        factors_against=[],
        risks=[evidence],
        bullish_scenario=dict(reference="resistance", relation="above", explanation="Пробой вверх"),
        bearish_scenario=dict(reference="support", relation="below", explanation="Пробой вниз"),
        invalidation_conditions=[dict(reference="support", relation="below", explanation="Отмена идеи")],
        confirmation="SUFFICIENT" if direction != "HOLD" else "INSUFFICIENT",
        conclusion="Технический сценарий",
    )


def response(data=None, status=200):
    return httpx.Response(
        status,
        json={
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": json.dumps(
                            data if data is not None else valid_result(), ensure_ascii=False
                        )
                    },
                }
            ],
            "usage": {"prompt_tokens": 100, "completion_tokens": 100},
        },
    )


def analyzer(tmp_path, snapshot, handler, **kwargs):
    return DeepSeekAnalyzer(
        store=AnalysisStore(tmp_path / "ai.db"),
        api_key="test-placeholder",
        clock=lambda: snapshot.as_of,
        transport=httpx.MockTransport(handler),
        **kwargs,
    )


@pytest.mark.asyncio
async def test_json_contract_cache_budget_and_replay(tmp_path, snapshot):
    calls = []

    def handler(req):
        body = json.loads(req.content)
        assert str(req.url) == "https://api.deepseek.com/chat/completions"
        assert body["response_format"] == {"type": "json_object"}
        assert "confidence" not in json.dumps(AIAnalysisResult.model_json_schema())
        calls.append(body)
        return response()

    a = analyzer(tmp_path, snapshot, handler)
    first = await a.analyze(snapshot)
    assert first.status == "OK"
    second = await a.analyze(snapshot)
    assert second.cached and len(calls) == 1
    assert a.status()["reserved_usd"] > 0
    a.key = ""
    assert (await a.analyze(snapshot, replay=True)).status == "OK"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kind", ["json", "schema", "invented", "number", "incomplete", "http401", "http402", "timeout", "http429"]
)
async def test_errors(tmp_path, snapshot, kind):
    calls = []

    def handler(req):
        calls.append(1)
        if kind == "timeout":
            raise httpx.ReadTimeout("redacted")
        if kind.startswith("http"):
            return httpx.Response(int(kind[4:]))
        if kind == "json":
            return httpx.Response(
                200, json={"choices": [{"finish_reason": "stop", "message": {"content": "not json"}}]}
            )
        data = valid_result()
        if kind == "schema":
            data["confidence"] = 99
        if kind == "invented":
            data["risks"][0]["reference"] = "invented_news"
        if kind == "number":
            data["conclusion"] = "Price 999"
        out = response(data)
        if kind == "incomplete":
            payload = json.loads(out.content)
            payload["choices"][0]["finish_reason"] = "length"
            return httpx.Response(200, json=payload)
        return out

    a = analyzer(tmp_path, snapshot, handler, attempts=2)
    result = await a.analyze(snapshot)
    assert result.status == "AI_UNAVAILABLE"
    assert len(calls) == (2 if kind in ("timeout", "http429") else 1)


@pytest.mark.asyncio
async def test_budget_stale_and_invalid_input(tmp_path, snapshot):
    def never(req):
        raise AssertionError("No request expected")

    a = analyzer(tmp_path, snapshot, never, daily_budget=0)
    assert (await a.analyze(snapshot)).reason == "BUDGET_EXHAUSTED"
    a.clock = lambda: snapshot.as_of + timedelta(days=1)
    assert (await a.analyze(snapshot)).reason == "STALE_MARKET_DATA"
    data = snapshot.model_dump()
    data["indicators"]["RSI"] = 999
    assert (await a.analyze(data)).reason == "INVALID_MARKET_DATA"


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", list(AIMode))
@pytest.mark.parametrize("ai_side", ["LONG", "SHORT", "HOLD", "UNAVAILABLE"])
async def test_all_modes_conflicting_and_unavailable(tmp_path, snapshot, mode, ai_side):
    calls = []

    def handler(req):
        calls.append(1)
        return response(valid_result(ai_side)) if ai_side != "UNAVAILABLE" else httpx.Response(401)

    a = analyzer(tmp_path, snapshot, handler)
    decision = await hybrid_signal(snapshot, a, mode)
    if mode == AIMode.OFF:
        assert not calls
    expected = "HOLD" if mode == AIMode.FILTER and ai_side != "LONG" else "LONG"
    assert decision.final.direction.value == expected
    if decision.final.plan:
        assert decision.final.plan == snapshot.technical.plan
    risk = await hybrid_signal(snapshot, a, mode, risk_allowed=False)
    assert risk.final.direction.value == "HOLD" and risk.veto_reason == "RISK_VETO"


@pytest.mark.asyncio
async def test_retrospective_replay_separation(tmp_path, snapshot):
    a = analyzer(tmp_path, snapshot, lambda req: response())
    a.clock = lambda: snapshot.as_of + timedelta(days=100)
    saved = await a.analyze(snapshot, retrospective=True)
    assert saved.status == "OK" and saved.retrospective
    assert (await a.analyze(snapshot, replay=True)).reason == "REPLAY_MISS"
    replay = await a.analyze(snapshot, replay=True, retrospective=True)
    assert replay.status == "OK" and replay.retrospective


@pytest.mark.asyncio
async def test_ai_cannot_create_trade_from_hold(tmp_path, candles):
    from market_snapshot import build_snapshot

    df = candles(slope=0.1)
    df["close"] = [100 + i for i in range(len(df))]
    df["open"] = df.close
    df["high"] = df.close + 0.5
    df["low"] = df.close - 0.5
    snap = build_snapshot(
        df, "BTCUSDT", "1h", df.close_time.iloc[-1].to_pydatetime() + timedelta(milliseconds=1)
    )
    assert snap.technical.direction.value == "HOLD"
    a = analyzer(tmp_path, snap, lambda req: response())
    result = await hybrid_signal(snap, a, AIMode.FILTER)
    assert result.final.direction.value == "HOLD" and result.final.plan is None


@pytest.mark.asyncio
async def test_same_candles_reused_at_later_poll(tmp_path, snapshot):
    calls = []

    def handler(req):
        calls.append(1)
        return response()

    a = analyzer(tmp_path, snapshot, handler)
    assert (await a.analyze(snapshot)).status == "OK"
    later = snapshot.model_copy(update={"as_of": snapshot.as_of + timedelta(minutes=2)})
    a.clock = lambda: later.as_of
    assert (await a.analyze(later)).cached
    assert len(calls) == 1
