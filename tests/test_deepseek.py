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
        facts=[],
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


def attach_facts(out, request):
    from ai_facts import relation

    try:
        envelope = json.loads(out.content)
        result = json.loads(envelope["choices"][0]["message"]["content"])
        if result.get("facts") == []:
            inputs = json.loads(json.loads(request.content)["messages"][1]["content"])
            result["facts"] = [
                {"fact_id": key, "relation": relation(fact)} for key, fact in inputs["fact_catalog"].items()
            ]
            envelope["choices"][0]["message"]["content"] = json.dumps(result)
            return httpx.Response(out.status_code, json=envelope, headers=out.headers)
    except (KeyError, ValueError, IndexError, TypeError):
        pass
    return out


def analyzer(tmp_path, snapshot, handler, **kwargs):
    return DeepSeekAnalyzer(
        store=AnalysisStore(tmp_path / "ai.db"),
        api_key="test-placeholder",
        clock=lambda: snapshot.as_of,
        transport=httpx.MockTransport(lambda req: attach_facts(handler(req), req)),
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kind,expected",
    [
        ("valid", None),
        ("json", "INVALID_CONTENT_JSON"),
        ("schema", "AI_SCHEMA_VALIDATION_FAILED"),
        ("reference", "AI_REFERENCE_VALIDATION_FAILED"),
        ("empty", "EMPTY_API_CONTENT"),
        ("envelope", "INVALID_RESPONSE_ENVELOPE"),
        ("html", "INVALID_ENVELOPE_JSON"),
        ("provider_error", "API_ERROR_RESPONSE"),
        ("unauthorized", "API_HTTP_401"),
        ("bad_request", "API_HTTP_400"),
    ],
)
async def test_response_diagnostics(tmp_path, snapshot, caplog, kind, expected):
    marker = "private-response-marker"
    data = valid_result()
    if kind == "schema":
        data[marker] = "private-field-value"
    if kind == "reference":
        data["risks"][0]["reference"] = marker
    payload = json.loads(response(data).content)
    payload["usage"] = None  # Optional provider metadata must not invalidate valid analysis.
    if kind in ("json", "empty"):
        payload["choices"][0]["message"]["content"] = marker if kind == "json" else ""
    if kind == "envelope":
        payload = {"choices": []}
    if kind in ("provider_error", "unauthorized", "bad_request"):
        payload = {"error": {"message": marker, "type": "authentication_error"}}
    code = 401 if kind == "unauthorized" else 400 if kind == "bad_request" else 200
    out = httpx.Response(code, json=payload, headers={"x-request-id": "req-regression-123"})
    if kind == "html":
        out = httpx.Response(200, text="<html>" + marker, headers={"x-request-id": "req-regression-123"})
    a = analyzer(tmp_path, snapshot, lambda request: out)
    result = await a.analyze(snapshot)
    assert result.reason == expected
    assert result.status == ("OK" if expected is None else "AI_UNAVAILABLE")
    if expected:
        assert result.http_status == code and result.request_id == "req-regression-123"
        assert expected in caplog.text
    if kind == "schema":
        assert result.validation_errors == ["extra_forbidden:<field>"]
    assert marker not in caplog.text
    assert "test-placeholder" not in caplog.text
    assert "Authorization" not in caplog.text


@pytest.mark.asyncio
async def test_non_ascii_key_reproduces_pre_response_error(tmp_path, snapshot):
    # Previous catch(ValueError) misclassified this as INVALID_API_RESPONSE before HTTP.
    with pytest.raises(UnicodeEncodeError):
        httpx.Request(
            "POST", "https://api.deepseek.com/chat/completions", headers={"Authorization": "Bearer пример"}
        )
    a = analyzer(tmp_path, snapshot, lambda req: pytest.fail("No request expected"))
    a.key = "пример"
    assert (await a.analyze(snapshot)).reason == "INVALID_API_KEY_FORMAT"
    assert a.store.spent(snapshot.as_of.date().isoformat()) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("model", ["deepseek-flash", "deepseek-v4-pro"])
async def test_supported_model_request_contract(tmp_path, snapshot, model):
    def transport(request):
        body = json.loads(request.content)
        assert body["model"] == model
        assert body["thinking"] == {"type": "disabled"}
        assert body["response_format"] == {"type": "json_object"}
        assert body["stream"] is False
        assert "json" in body["messages"][0]["content"]
        return response()

    assert (await analyzer(tmp_path, snapshot, transport, model=model).analyze(snapshot)).status == "OK"


@pytest.mark.parametrize("mode", ["ADVISORY", "FILTER"])
def test_analyze_endpoint_preserves_ai_failure_diagnostics(tmp_path, snapshot, monkeypatch, mode):
    import asyncio
    from types import SimpleNamespace

    import ai_runtime
    import app
    import pandas as pd
    from fastapi.testclient import TestClient

    frame = pd.DataFrame([c.model_dump() for c in snapshot.candles])
    from strategy_engine import legacy_result

    analysis = {
        **legacy_result(snapshot.technical, frame),
        "frame": frame,
        "technical_signal": snapshot.technical,
        "symbol": snapshot.symbol,
        "timeframe": snapshot.timeframe,
        "as_of": snapshot.as_of,
    }
    a = analyzer(
        tmp_path,
        snapshot,
        lambda req: httpx.Response(
            401, json={"error": {"message": "never log this"}}, headers={"x-request-id": "req-api-123"}
        ),
    )
    monkeypatch.setattr(app, "analyze_market", lambda *args: dict(analysis))
    monkeypatch.setattr(ai_runtime, "_analyzer", a)
    monkeypatch.setattr(ai_runtime, "_worker", SimpleNamespace(run=asyncio.run))
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("AI_MODE", mode)
    with TestClient(app.app) as client:
        out = client.post("/analyze").json()
    assert out["deepseek"]["reason"] == "API_HTTP_401"
    assert out["deepseek"]["http_status"] == 401
    assert out["deepseek"]["request_id"] == "req-api-123"
    assert out["action"] == ("BUY" if mode == "ADVISORY" else "HOLD")


@pytest.mark.asyncio
@pytest.mark.parametrize("explanation", ["RSI выше 70", "Цена ниже SMA20", "Таймфрейм 1h", "Уровень ٧٠"])
async def test_factors_against_explanation_rejects_digits(tmp_path, snapshot, caplog, explanation):
    data = valid_result()
    data["factors_against"] = [{"reference": "RSI", "explanation": explanation}]
    result = await analyzer(tmp_path, snapshot, lambda req: response(data)).analyze(snapshot)
    assert result.status == "AI_UNAVAILABLE"
    assert result.reason == "AI_SCHEMA_VALIDATION_FAILED"
    assert result.http_status == 200
    assert result.validation_errors == ["digits_in_explanation:factors_against.0.explanation"]
    assert "digits_in_explanation:factors_against.0.explanation" in caplog.text
    assert explanation not in caplog.text


@pytest.mark.asyncio
async def test_qualitative_explanation_matches_schema_and_prompt(tmp_path, snapshot):
    from deepseek_analyzer import PROMPT_VERSION

    text = "Импульс не подтверждает направление технического сигнала"
    data = valid_result()
    data["factors_against"] = [{"reference": "RSI", "explanation": text}]

    def transport(request):
        body = json.loads(request.content)
        prompt = body["messages"][0]["content"]
        assert "factors_against[].explanation" in prompt
        assert "indicator names" in prompt
        assert "never spell out numerical market claims" in prompt
        return response(data)

    result = await analyzer(tmp_path, snapshot, transport).analyze(snapshot)
    assert result.status == "OK"
    assert result.result.factors_against[0].explanation == text
    assert result.prompt_version == PROMPT_VERSION == "market-review-v3"
    schema = AIAnalysisResult.model_json_schema()
    for definition in ("Evidence", "Scenario"):
        field = schema["$defs"][definition]["properties"]["explanation"]
        assert field["pattern"] == r"^\D*$"
        assert field["minLength"] == 1 and field["maxLength"] == 350
    assert schema["properties"]["conclusion"]["pattern"] == r"^[^\d%]*$"
