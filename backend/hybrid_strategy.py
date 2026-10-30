"""AI may veto a technical entry; it never invents an entry or overrides risk."""

from enum import Enum

from deepseek_analyzer import AIResponse
from pydantic import BaseModel
from signal_models import Direction, TradingSignal


class AIMode(str, Enum):
    OFF = "OFF"
    ADVISORY = "ADVISORY"
    FILTER = "FILTER"


class HybridDecision(BaseModel):
    technical: TradingSignal
    final: TradingSignal
    mode: AIMode
    ai: AIResponse | None = None
    veto_reason: str | None = None


def hold(signal, reason):
    return signal.model_copy(
        update={"direction": Direction.HOLD, "plan": None, "reasons": [*signal.reasons, reason]}
    )


async def hybrid_signal(
    snapshot, analyzer, mode=AIMode.ADVISORY, risk_allowed=True, retrospective=False, replay=False
):
    mode = AIMode(mode)
    technical = snapshot.technical
    final = technical
    veto = None
    ai = None
    if not risk_allowed:
        veto = "RISK_VETO"
        final = hold(technical, veto)
    elif mode != AIMode.OFF:
        ai = await analyzer.analyze(snapshot, retrospective=retrospective, replay=replay)
        if mode == AIMode.FILTER and technical.direction != Direction.HOLD:
            if ai.status != "OK":
                veto = "AI_UNAVAILABLE"
            elif ai.result.direction != technical.direction.value or ai.result.confirmation != "SUFFICIENT":
                veto = "AI_VETO"
            if veto:
                final = hold(technical, veto)
    return HybridDecision(technical=technical, final=final, mode=mode, ai=ai, veto_reason=veto)
