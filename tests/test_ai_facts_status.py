import asyncio
import json
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from ai_facts import FactClaim, check_facts, fact_catalog, format_facts, relation
from deepseek_analyzer import AIAnalysisResult
from hybrid_strategy import AIMode, hybrid_signal
from pydantic import ValidationError
from telegram_ai import format_decision, register_ai_handlers
from test_deepseek import analyzer, response, valid_result
from test_telegram_ai import Bot


def claims(snapshot):
    return [dict(fact_id=k, relation=relation(v)) for k, v in fact_catalog(snapshot).items()]


def test_fact_catalog_user_example_and_indicator_coverage(snapshot):
    refs = {**snapshot.references(), "close": 83723.1, "SMA_20": 83487.9}
    source = SimpleNamespace(references=lambda: refs)
    facts = [FactClaim(**v) for v in claims(source)]
    assert check_facts(facts, source) == []
    assert next(c.relation for c in facts if c.fact_id == "close_vs_SMA_20") == "above"
    assert "close=83723.1 > SMA_20=83487.9" in format_facts(facts, source)
    for key in (
        "SMA_20_vs_SMA_50",
        "EMA_12_vs_EMA_26",
        "RSI_vs_30",
        "RSI_vs_70",
        "MACD_vs_MACD_Signal",
        "ADX_vs_25",
        "Volume_Ratio_vs_1",
        "volume_change_pct_vs_0",
        "close_vs_support",
        "close_vs_resistance",
    ):
        assert key in fact_catalog(source)
    next(c for c in facts if c.fact_id == "close_vs_SMA_20").relation = "below"
    assert check_facts(facts, source) == ["close_vs_SMA_20"]


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", [AIMode.ADVISORY, AIMode.FILTER])
async def test_conflicting_fact_veto_and_safe_display(tmp_path, snapshot, mode, caplog):
    data = valid_result()
    data["facts"] = claims(snapshot)
    fact = data["facts"][0]
    fact["relation"] = "below" if fact["relation"] != "below" else "above"
    data["conclusion"] = "Недостоверный текст модели"
    data["factors_against"] = [{"reference": "SMA_20", "explanation": "Цена ниже скользящей средней"}]
    a = analyzer(tmp_path, snapshot, lambda req: response(data))
    decision = await hybrid_signal(snapshot, a, mode)
    assert decision.ai.reason == "AI_FACT_CHECK_FAILED"
    assert decision.ai.fact_check_status == "FAILED"
    assert decision.ai.result is None
    assert decision.final.direction.value == ("LONG" if mode == AIMode.ADVISORY else "HOLD")
    if mode == AIMode.ADVISORY:
        assert decision.final == snapshot.technical
    assert "Недостоверный текст" not in format_decision(snapshot, decision)
    assert "Недостоверный текст" not in caplog.text
    assert "test-placeholder" not in caplog.text
    assert "AI_FACT_CHECK_FAILED" in caplog.text


@pytest.mark.asyncio
async def test_correct_facts_opinions_and_same_input_values(tmp_path, snapshot):
    data = valid_result()
    data["facts"] = claims(snapshot)
    data["factors_against"] = [{"reference": "SMA_20", "explanation": "Нужна осторожность при оценке тренда"}]
    data["conclusion"] = "Альтернативный сценарий заслуживает внимания"

    def transport(request):
        inputs = json.loads(json.loads(request.content)["messages"][1]["content"])
        assert inputs["references"] == snapshot.references()
        assert inputs["fact_catalog"] == fact_catalog(snapshot)
        return response(data)

    a = analyzer(tmp_path, snapshot, transport)
    decision = await hybrid_signal(snapshot, a, AIMode.ADVISORY)
    assert decision.ai.status == "OK" and decision.ai.fact_check_status == "PASSED"
    text = format_decision(snapshot, decision)
    assert "Проверенные факты" in text
    assert "Все проверенные сравнения:" not in text
    assert "Все проверенные сравнения:" in format_decision(snapshot, decision, detailed=True)
    assert "Альтернативный сценарий" not in text
    assert decision.ai.interpretation_status == "UNVERIFIED"
    assert (await a.analyze(snapshot)).cached


@pytest.mark.parametrize(
    "bad",
    [None, [{"fact_id": "close_vs_SMA_20", "relation": "maybe"}], [{"fact_id": 3, "relation": "above"}]],
)
def test_strict_fact_schema(bad):
    data = valid_result()
    if bad is None:
        data.pop("facts")
    else:
        data["facts"] = bad
    with pytest.raises(ValidationError):
        AIAnalysisResult.model_validate(data, strict=True)


def test_missing_duplicate_and_unknown_facts(snapshot):
    facts = [FactClaim(**v) for v in claims(snapshot)]
    assert check_facts(facts[:-1], snapshot) == ["FACT_COVERAGE_MISMATCH"]
    assert check_facts(facts + facts[:1], snapshot) == ["FACT_COVERAGE_MISMATCH"]
    facts[0].fact_id = "secret-invented-reference"
    assert check_facts(facts, snapshot) == ["FACT_COVERAGE_MISMATCH"]


@pytest.mark.parametrize("configured,available", [(True, True), (False, True), (False, False)])
def test_status_separates_processes_without_provider_calls(monkeypatch, configured, available):
    import ai_runtime
    import app
    from fastapi.testclient import TestClient

    monkeypatch.setattr(ai_runtime, "_analyzer", None)
    monkeypatch.setenv("AI_MODE", "ADVISORY")
    if configured:
        monkeypatch.setenv("DEEPSEEK_API_KEY", "api-process-only-placeholder")
    else:
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with TestClient(app.app) as client:
        server_payload = client.get("/ai/status").json()
    assert server_payload["configured"] is configured
    assert "api-process-only-placeholder" not in json.dumps(server_payload)
    assert ai_runtime._analyzer is None  # Status never creates a client or sends a completion.
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("AI_MODE", "OFF")
    remote = Mock()
    if available:
        remote.get.return_value.json.return_value = server_payload
    else:
        remote.get.side_effect = httpx.ConnectError("private provider detail")
    bot = Bot()
    register_ai_handlers(bot, api_client=remote)
    bot.handlers["ai_status"](SimpleNamespace(text="/ai_status"))
    text = bot.messages[-1]
    assert "Telegram (локально): AI_MODE=OFF; configured=False" in text
    if available:
        assert f"API-сервер: доступен; AI_MODE=ADVISORY; configured={configured}" in text
    else:
        assert "Состояние DeepSeek на сервере неизвестно" in text
    assert "private provider detail" not in text
    remote.post.assert_not_called()


def test_deepseek_command_delegates_to_api_without_local_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("AI_MODE", "OFF")
    remote = Mock()
    remote.post.return_value.json.return_value = {"text": "API analysis"}
    bot = Bot()
    state = register_ai_handlers(bot, api_client=remote)
    bot.handlers["deepseek"](SimpleNamespace(text="/deepseek BTCUSDT 1h"))
    assert bot.messages == ["API analysis"]
    assert state == {}
    assert remote.post.call_args.kwargs["params"]["advisory"] is True


def test_api_review_uses_shared_analyzer_and_reports_its_status(tmp_path, snapshot, monkeypatch):
    import ai_runtime
    import app
    import pandas as pd
    from fastapi.testclient import TestClient
    from strategy_engine import legacy_result

    frame = pd.DataFrame([c.model_dump() for c in snapshot.candles])
    data = {
        **legacy_result(snapshot.technical, frame),
        "frame": frame,
        "technical_signal": snapshot.technical,
        "symbol": snapshot.symbol,
        "timeframe": snapshot.timeframe,
        "as_of": snapshot.as_of,
    }
    a = analyzer(tmp_path, snapshot, lambda req: response())
    monkeypatch.setattr(ai_runtime, "_analyzer", a)
    monkeypatch.setattr(ai_runtime, "_worker", SimpleNamespace(run=asyncio.run))
    monkeypatch.setattr(app, "analyze_market", lambda *args: dict(data))
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("AI_MODE", "OFF")
    with TestClient(app.app) as client:
        result = client.post("/ai/review", params={"advisory": True}).json()
        status = client.get("/ai/status").json()
    assert "Проверенные факты" in result["text"]
    assert status["last_status"] == "OK" and status["configured"] is True
    assert status["mode"] == "OFF"  # Explicit /deepseek review doesn't change strategy mode.


def test_status_does_not_echo_invalid_configuration(monkeypatch):
    import ai_runtime

    monkeypatch.setattr(ai_runtime, "_analyzer", None)
    monkeypatch.setenv("DEEPSEEK_MODEL", "private-configuration-value")
    monkeypatch.setenv("AI_MODE", "private-mode-value")
    status = ai_runtime.api_status()
    assert status["model"] == status["mode"] == "INVALID_CONFIGURATION"
    assert "private-" not in json.dumps(status)


@pytest.mark.asyncio
async def test_cached_facts_are_rechecked(tmp_path, snapshot):
    a = analyzer(tmp_path, snapshot, lambda req: response())
    saved = await a.analyze(snapshot)
    saved.result.facts[0].relation = "below" if saved.result.facts[0].relation != "below" else "above"
    a.store.save(a.identity(snapshot), snapshot, saved, "", {})
    result = await a.analyze(snapshot, replay=True)
    assert result.reason == "AI_FACT_CHECK_FAILED" and result.result is None
