"""AI Telegram commands, isolated from the legacy router and paper execution."""

import asyncio
import json
import os
import threading
from concurrent.futures import TimeoutError as FutureTimeout
from typing import Literal

import requests
from ai_backtest import load_comparison
from ai_facts import FactExplanationError, explain_facts, format_facts
from deepseek_analyzer import DeepSeekAnalyzer
from hybrid_strategy import AIMode, hybrid_signal
from market_snapshot import live_snapshot
from pydantic import BaseModel, ConfigDict


class APIStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    source: Literal["API_SERVER"]
    mode: Literal["OFF", "ADVISORY", "FILTER", "INVALID_CONFIGURATION"]
    configured: bool
    model: Literal["deepseek-flash", "deepseek-v4-pro", "INVALID_CONFIGURATION"]
    last_status: str
    connectivity: Literal["NOT_PROBED_STATUS_ONLY"]


class AsyncWorker:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True, name="ai-worker")
        self.thread.start()

    def run(self, coroutine, timeout=100):
        future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        try:
            return future.result(timeout)
        except FutureTimeout:
            future.cancel()
            raise

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(timeout=2)
        self.loop.close()


def format_decision(snapshot, decision, detailed=False):
    s = decision.technical
    explanation = None
    error = None
    if decision.ai is not None and decision.ai.status == "OK":
        try:
            explanation = explain_facts(decision.ai.result.facts, snapshot)
        except FactExplanationError as exc:
            error = str(exc)
    final = "HOLD" if error and decision.mode == AIMode.FILTER else decision.final.direction.value
    lines = [
        f"{s.symbol} {s.timeframe} | {decision.mode.value} | PAPER",
        f"Технический сигнал: {s.direction.value}; итоговый: {final}",
        f"Качество: {s.quality:.1f}/10 — эвристика, не вероятность",
        f"Закрытая свеча: {s.timestamp.isoformat()}",
    ]
    if s.plan:
        p = s.plan
        lines.append(
            f"Entry {p.entry:.10g}; SL {p.stop_loss:.10g}; TP "
            + ", ".join(f"{v:.10g}" for v in p.take_profits)
            + f"; R/R {p.rr:.2f}"
        )
    if decision.veto_reason:
        lines.append("Отклонено: " + decision.veto_reason)
    if decision.ai is None:
        lines.append("AI OFF; техническая стратегия")
    elif decision.ai.status != "OK" or error:
        lines.append("AI_UNAVAILABLE: " + str(error or decision.ai.reason))
    elif explanation:
        lines.append("Проверенные факты и их интерпретация по фиксированным правилам:")
        for title, key in [
            ("Что поддерживает рост", "up"),
            ("Что поддерживает снижение или препятствует росту", "down"),
            ("Ключевые риски и ограничения", "risks"),
        ]:
            lines.append("\n" + title + ":")
            lines.extend("• " + text for text in explanation[key])
            if not explanation[key]:
                lines.append("В выбранных факторах отдельного подтверждения нет.")
        lines.extend(
            [
                "\nУсловия возможного роста и снижения (не прогноз):",
                f"Рост: выход цены выше сопротивления {snapshot.resistance:.10g}; сам пробой не гарантирует продолжения.",
                f"Снижение: уход цены ниже поддержки {snapshot.support:.10g}; сам пробой не гарантирует продолжения.",
                "\nУсловия отмены сценария:",
            ]
        )
        if s.plan:
            side = "ниже или равна" if s.direction.value == "LONG" else "выше или равна"
            lines.append(f"Исходный {s.direction.value}-план: цена {side} SL {s.plan.stop_loss:.10g}.")
        else:
            lines.append("Активного технического плана нет — торговые уровни отмены не рассчитаны.")
        lines.append("\nКраткое заключение: " + explanation["conclusion"])
        if detailed:
            lines.append("\nВсе проверенные сравнения: " + format_facts(decision.ai.result.facts, snapshot))
        else:
            lines.append("Все сравнения: /deepseek " + s.symbol + " " + s.timeframe + " --details")
    lines.append("Реальные ордера отключены.")
    return "\n".join(lines)


def register_ai_handlers(
    bot, authorized=lambda message: True, analyzer=None, snapshot_loader=None, runner=None, api_client=None
):
    # Lazy initialization: importing or registering handlers makes no network calls.
    state = {}
    remote = api_client or requests
    use_api = analyzer is None and snapshot_loader is None and runner is None
    snapshot_loader = snapshot_loader or live_snapshot
    mode = None if use_api else AIMode(os.environ.get("AI_MODE", "ADVISORY").upper())

    def get_analyzer():
        if "analyzer" not in state:
            state["analyzer"] = analyzer or DeepSeekAnalyzer()
        return state["analyzer"]

    def run(coro):
        if runner:
            return runner(coro)
        if "worker" not in state:
            state["worker"] = AsyncWorker()
        return state["worker"].run(coro)

    def send(message, text):
        for start in range(0, len(text), 3900):
            bot.reply_to(message, text[start : start + 3900], parse_mode=None)

    def analyze_command(message):
        if not authorized(message):
            return
        parts = message.text.split()
        if len(parts) < 2:
            send(message, "Используйте /deepseek BTCUSDT 1h или /ai_signal BTCUSDT 1h")
            return
        try:
            if use_api:
                response = remote.post(
                    "http://127.0.0.1:8000/ai/review",
                    params={
                        "symbol": parts[1].upper(),
                        "timeframe": parts[2] if len(parts) > 2 else "1h",
                        "advisory": parts[0].split("@")[0] == "/deepseek",
                        "detailed": "--details" in parts[3:],
                    },
                    timeout=(3, 100),
                )
                response.raise_for_status()
                send(message, response.json()["text"])
                return
            snapshot = snapshot_loader(parts[1].upper(), parts[2] if len(parts) > 2 else "1h")
            selected = AIMode.ADVISORY if parts[0].split("@")[0] == "/deepseek" else mode
            decision = run(
                hybrid_signal(snapshot, get_analyzer() if selected != AIMode.OFF else None, selected)
            )
            send(message, format_decision(snapshot, decision, detailed="--details" in parts[3:]))
        except Exception as exc:
            send(message, "AI_UNAVAILABLE: " + type(exc).__name__ + "; торговое действие не создано")

    def status_command(message):
        if not authorized(message):
            return
        local_mode = os.environ.get("AI_MODE", "ADVISORY").upper()
        if local_mode not in ("OFF", "ADVISORY", "FILTER"):
            local_mode = "INVALID_CONFIGURATION"
        local_key = bool(os.environ.get("DEEPSEEK_API_KEY"))
        lines = [
            f"Telegram (локально): AI_MODE={local_mode}; configured={local_key}",
            "AI-команды используют API-сервер; локальный ключ Telegram не требуется.",
        ]
        try:
            response = remote.get("http://127.0.0.1:8000/ai/status", timeout=(3, 5))
            response.raise_for_status()
            status = APIStatus.model_validate(response.json())
            lines.append(
                f"API-сервер: доступен; AI_MODE={status.mode}; configured={status.configured}; "
                f"model={status.model}; last_status={status.last_status if status.last_status in ('OK', 'CACHED', 'NOT_CHECKED', 'MISSING_API_KEY', 'AI_FACT_CHECK_FAILED') else 'AI_UNAVAILABLE'}"
            )
            lines.append(
                "Доступность DeepSeek сейчас не проверялась; статус основан на состоянии API-процесса."
            )
        except Exception:
            lines.append("API-сервер: статус недоступен. Состояние DeepSeek на сервере неизвестно.")
        send(message, "\n".join(lines))

    def performance_command(message):
        if authorized(message):
            send(message, json.dumps(load_comparison(), ensure_ascii=False, indent=2))

    bot.message_handler(commands=["deepseek", "ai_signal"])(analyze_command)
    bot.message_handler(commands=["ai_status"])(status_command)
    bot.message_handler(commands=["ai_performance"])(performance_command)
    return state
