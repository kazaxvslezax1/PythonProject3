from types import SimpleNamespace

import pytest
from ai_facts import FactClaim, FactExplanationError, explain_facts, fact_catalog, relation
from hybrid_strategy import AIMode, hybrid_signal
from telegram_ai import format_decision
from test_deepseek import analyzer, response


def source(snapshot, **changes):
    refs = {**snapshot.references(), **changes}
    return SimpleNamespace(references=lambda: refs)


def claims(snapshot):
    return [FactClaim(fact_id=key, relation=relation(value)) for key, value in fact_catalog(snapshot).items()]


def joined(explanation):
    return "\n".join(
        [*explanation["up"], *explanation["down"], *explanation["risks"], explanation["conclusion"]]
    )


@pytest.mark.parametrize("up", [True, False])
def test_directional_explanations_follow_values(snapshot, up):
    data = source(
        snapshot,
        close=110 if up else 90,
        SMA_20=105 if up else 95,
        SMA_50=100,
        MACD=2 if up else -2,
        MACD_Signal=0,
        ADX=30,
        Volume_Ratio=1.5,
        RSI=50,
    )
    result = explain_facts(claims(data), data)
    expected, opposite = ("up", "down") if up else ("down", "up")
    assert len(result[expected]) == 2 and not result[opposite]
    text = joined(result)
    assert ("положительный импульс" if up else "отрицательный импульс") in text
    assert ("Цена (110) выше SMA20 (105)" if up else "Цена (90) ниже SMA20 (95)") in text
    assert "тренд недостаточно выражен" not in text
    assert "движение не сопровождается повышенной" not in text
    assert "не прогноз" in text


def test_mixed_picture_and_low_activity(snapshot):
    data = source(
        snapshot,
        close=110,
        SMA_20=105,
        SMA_50=120,
        MACD=2,
        MACD_Signal=1,
        ADX=19.2917,
        Volume_Ratio=0.871472,
        RSI=60.8393,
    )
    result = explain_facts(claims(data), data)
    text = joined(result)
    assert "Цена (110) выше SMA20 (105); SMA20 ниже SMA50 (120)" in text
    assert "Смешанная картина" in text
    assert "ADX=19.2917 ниже 25" in text
    assert "Объём=0.871472× среднего" in text
    assert "однозначного вывода о направлении нет" in result["conclusion"]
    assert sum(len(result[k]) for k in ("up", "down", "risks")) == 4


def test_equal_values_and_rsi_boundaries_do_not_invent_strength(snapshot):
    data = source(
        snapshot, close=100, SMA_20=100, SMA_50=100, MACD=0, MACD_Signal=0, ADX=25, Volume_Ratio=1, RSI=70
    )
    result = explain_facts(claims(data), data)
    assert not result["up"] and not result["down"]
    text = joined(result)
    assert "на уровне SMA20" in text and "пограничное значение" in text
    assert "перекупленности" not in text and "повышена" not in text


@pytest.mark.parametrize("rsi,expected", [(80, "перекупленности"), (20, "перепроданности")])
def test_at_most_five_factors_even_with_extreme_rsi(snapshot, rsi, expected):
    data = source(snapshot, RSI=rsi)
    result = explain_facts(claims(data), data)
    assert expected in joined(result)
    assert sum(len(result[k]) for k in ("up", "down", "risks")) == 5


@pytest.mark.parametrize("missing", ["SMA_20", "MACD_Signal", "ADX", "Volume_Ratio", "RSI"])
def test_missing_indicators_never_produce_fabricated_explanations(snapshot, missing):
    verified = claims(snapshot)
    refs = snapshot.references()
    refs.pop(missing)
    with pytest.raises(FactExplanationError, match="INVALID_MARKET_DATA"):
        explain_facts(verified, SimpleNamespace(references=lambda: refs))


def test_contradictory_claim_is_not_rewritten_into_plausible_text(snapshot):
    facts = claims(snapshot)
    facts[0].relation = "above" if facts[0].relation != "above" else "below"
    with pytest.raises(FactExplanationError, match="AI_FACT_CHECK_FAILED"):
        explain_facts(facts, snapshot)


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", [AIMode.ADVISORY, AIMode.FILTER])
async def test_compact_and_detailed_rendering_preserve_all_facts_and_plan(tmp_path, snapshot, mode):
    a = analyzer(tmp_path, snapshot, lambda req: response())
    decision = await hybrid_signal(snapshot, a, mode)
    original = decision.model_dump()
    text = format_decision(snapshot, decision)
    detailed = format_decision(snapshot, decision, detailed=True)
    assert "Технический сигнал: LONG; итоговый: LONG" in text
    assert "Что поддерживает рост" in text and "Ключевые риски" in text
    assert "Условия возможного роста и снижения (не прогноз)" in text
    assert f"SL {snapshot.technical.plan.stop_loss:.10g}" in text
    assert "Краткое заключение" in text
    assert "Все проверенные сравнения" not in text
    assert "Все проверенные сравнения" in detailed
    assert 3 <= text.count("• ") <= 5
    assert len(text) < 3900
    assert "Технический сценарий" not in text  # Model conclusion stays hidden.
    assert decision.model_dump() == original
    assert len(decision.ai.result.facts) == len(fact_catalog(snapshot))


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", [AIMode.ADVISORY, AIMode.FILTER])
async def test_formatter_defends_against_mutated_claims(tmp_path, snapshot, mode):
    a = analyzer(tmp_path, snapshot, lambda req: response())
    decision = await hybrid_signal(snapshot, a, mode)
    fact = decision.ai.result.facts[0]
    fact.relation = "above" if fact.relation != "above" else "below"
    text = format_decision(snapshot, decision)
    assert "AI_FACT_CHECK_FAILED" in text
    assert "Что поддерживает рост" not in text
    assert ("итоговый: LONG" if mode == AIMode.ADVISORY else "итоговый: HOLD") in text


def test_details_command_forwards_flag_without_local_analysis(monkeypatch):
    from unittest.mock import Mock

    from telegram_ai import register_ai_handlers
    from test_telegram_ai import Bot

    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    client = Mock()
    client.post.return_value.json.return_value = {"text": "Все проверенные сравнения"}
    bot = Bot()
    state = register_ai_handlers(bot, api_client=client)
    bot.handlers["deepseek"](SimpleNamespace(text="/deepseek BTCUSDT 1h --details"))
    assert client.post.call_args.kwargs["params"]["detailed"] is True
    assert state == {}  # Formatting doesn't create a second model client.
    assert bot.messages == ["Все проверенные сравнения"]
