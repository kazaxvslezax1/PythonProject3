"""AI Telegram commands, isolated from the legacy router and paper execution."""

import asyncio
import json
import os
import threading
from concurrent.futures import TimeoutError as FutureTimeout

from ai_backtest import load_comparison
from deepseek_analyzer import DeepSeekAnalyzer
from hybrid_strategy import AIMode, hybrid_signal
from market_snapshot import live_snapshot


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


def format_decision(snapshot, decision):
    s = decision.technical
    values = snapshot.indicators
    lines = [
        f"{s.symbol} {s.timeframe} | {decision.mode.value}",
        f"Technical: {s.direction.value}; final: {decision.final.direction.value}",
        f"Quality: {s.quality:.1f}/10 (эвристический балл, не вероятность)",
        "Причины: " + "; ".join(s.reasons),
        "Показатели: "
        + ", ".join(
            f"{k}={values[k]:.6g}"
            for k in ("RSI", "MACD", "SMA_20", "SMA_50", "EMA_12", "EMA_26", "ATR", "ADX")
        ),
        f"BB: {values['BB_Lower']:.6g} / {values['BB_Middle']:.6g} / {values['BB_Upper']:.6g}",
        f"Объём: {values['Volume_Ratio']:.2f}x; изменение {snapshot.volume_change_pct:.2f}%",
        f"Поддержка {snapshot.support:.10g}; сопротивление {snapshot.resistance:.10g}",
        f"Свеча закрыта: {s.timestamp.isoformat()}",
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
    elif decision.ai.status != "OK":
        lines.append("AI_UNAVAILABLE: " + str(decision.ai.reason))
    else:
        result = decision.ai.result
        refs = snapshot.references()

        def explain(item):
            return f"{item.explanation} [{item.reference}={refs[item.reference]:.6g}]"

        lines.extend(
            [
                "DeepSeek: " + result.direction + " / " + result.confirmation,
                "За: " + "; ".join(map(explain, result.factors_for)),
                "Против: " + "; ".join(map(explain, result.factors_against)),
                "Риски: " + "; ".join(map(explain, result.risks)),
                "Рост: " + result.bullish_scenario.relation + " " + explain(result.bullish_scenario),
                "Падение: " + result.bearish_scenario.relation + " " + explain(result.bearish_scenario),
                "Отмена: " + "; ".join(v.relation + " " + explain(v) for v in result.invalidation_conditions),
                "Заключение: " + result.conclusion,
            ]
        )
    lines.append("Только анализ / PAPER. Реальные ордера отключены.")
    return "\n".join(lines)


def register_ai_handlers(
    bot, authorized=lambda message: True, analyzer=None, snapshot_loader=None, runner=None
):
    # Lazy initialization: importing or registering handlers makes no network calls.
    state = {}
    snapshot_loader = snapshot_loader or live_snapshot
    mode = AIMode(os.environ.get("AI_MODE", "ADVISORY").upper())

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
            snapshot = snapshot_loader(parts[1].upper(), parts[2] if len(parts) > 2 else "1h")
            selected = AIMode.ADVISORY if parts[0].split("@")[0] == "/deepseek" else mode
            decision = run(
                hybrid_signal(snapshot, get_analyzer() if selected != AIMode.OFF else None, selected)
            )
            send(message, format_decision(snapshot, decision))
        except Exception as exc:
            send(message, "AI_UNAVAILABLE: " + type(exc).__name__ + "; торговое действие не создано")

    def status_command(message):
        if authorized(message):
            try:
                send(
                    message,
                    "AI_MODE="
                    + mode.value
                    + "\n"
                    + json.dumps(run(get_analyzer().check_status()), ensure_ascii=False, indent=2),
                )
            except Exception:
                send(message, "AI_UNAVAILABLE: configuration/storage error")

    def performance_command(message):
        if authorized(message):
            send(message, json.dumps(load_comparison(), ensure_ascii=False, indent=2))

    bot.message_handler(commands=["deepseek", "ai_signal"])(analyze_command)
    bot.message_handler(commands=["ai_status"])(status_command)
    bot.message_handler(commands=["ai_performance"])(performance_command)
    return state
