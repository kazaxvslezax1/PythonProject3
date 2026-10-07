"""AI Telegram commands, isolated from the legacy router and paper execution."""

import asyncio
import io
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


class PaperJournalStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    source: Literal["API_SERVER"]
    path: str
    exists: bool
    signals: int
    ai_ok: int
    paired_ai_observations: int


class ScannerStatus(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    enabled: bool
    running: bool
    healthy: bool
    auto_paper_entries: bool = False
    experiment_id: str | None = None
    strategy_version: str
    ai_request_policy: str | None = None
    symbols: list[str]
    timeframes: list[str]
    journal_path: str
    last_success_at: str | None = None
    last_candle_close: str | None = None
    next_scan_at: str | None = None
    observations_today: int = 0
    live_today: int = 0
    backfill_today: int = 0
    ai_calls_today: int = 0
    ai_failures_today: int = 0
    ai_eligible_after_prefilter_today: int = 0
    ai_skipped_by_prefilter_today: int = 0
    ai_skipped_hold_today: int = 0
    ai_requested_today: int = 0
    ai_http_attempts_api_today: int | None = None
    ai_ok_today: int = 0
    ai_validation_failed_today: int = 0
    ai_budget_exhausted_today: int = 0
    inflight_unknown: int = 0
    budget_used_usd: float | None = None
    budget_remaining_usd: float | None = None
    error: str | None = None


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
            lines.append("Для полного перечня сравнений добавьте --details.")
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

    def scanner_status_command(message):
        if not authorized(message):
            return
        try:
            response = remote.get("http://127.0.0.1:8000/paper/scanner/status", timeout=(3, 5))
            response.raise_for_status()
            status = ScannerStatus.model_validate(response.json())
            send(
                message,
                "PAPER Research: "
                f"enabled={status.enabled}; running={status.running}; healthy={status.healthy}; "
                f"auto PAPER entries={status.auto_paper_entries}\n"
                f"Experiment {status.experiment_id}; strategy {status.strategy_version}\n"
                f"Пары: {', '.join(status.symbols)}; TF: {', '.join(status.timeframes)}\n"
                f"Последний успешный scan: {status.last_success_at}; "
                f"последняя свеча: {status.last_candle_close}; следующий scan: {status.next_scan_at}\n"
                f"Сегодня наблюдений {status.observations_today} "
                f"(LIVE {status.live_today}, BACKFILL {status.backfill_today}); "
                f"учётных AI-попыток {status.ai_calls_today} (включая budget отказ), "
                f"ошибок/отказов {status.ai_failures_today}; "
                f"незавершённых {status.inflight_unknown}\n"
                f"AI policy: {status.ai_request_policy}; после prefilter допущено "
                f"{status.ai_eligible_after_prefilter_today}; пропущено prefilter "
                f"{status.ai_skipped_by_prefilter_today}; HOLD "
                f"{status.ai_skipped_hold_today}\n"
                f"AI-заявок по сигналам {status.ai_requested_today}; HTTP attempts в общем API AI-store "
                f"{status.ai_http_attempts_api_today}; OK {status.ai_ok_today}; "
                f"validation failed {status.ai_validation_failed_today}; "
                f"budget exhausted {status.ai_budget_exhausted_today}\n"
                f"Бюджет USD: использовано {status.budget_used_usd}; "
                f"осталось {status.budget_remaining_usd}\n"
                f"SQLite: {status.journal_path}"
                + (f"\nОшибка запуска: {status.error}" if status.error else ""),
            )
        except Exception:
            send(message, "PAPER scanner: статус API недоступен; проверьте запуск API.")

    def bridge_status_command(message):
        if not authorized(message):
            return
        import telegram_handlers as handlers
        from paper_journal import journal_path

        bridge = getattr(handlers, "paper_execution_bridge", None)
        legacy = handlers.auto_trading_scanner.status()
        if bridge is None:
            send(
                message,
                "PAPER bridge: enabled=False; running=False; healthy=не применимо\n"
                f"Experiment: {os.environ.get('PAPER_EXPERIMENT_ID', 'paper-baseline-v1')}; "
                f"SQLite: {journal_path()}\n"
                f"Legacy Telegram scanner: enabled={legacy['enabled']}; "
                f"running={legacy['running']}; last_scan={legacy['last_scan_at']}; "
                "source=LEGACY_TELEGRAM_SCANNER; PAPER-only",
            )
            return
        status = bridge.status()
        send(
            message,
            f"PAPER bridge: enabled={status['enabled']}; running={status['running']}; "
            f"healthy={status['healthy']}\n"
            f"Experiment: {status['experiment_id']}; SQLite: {status['journal_path']}\n"
            f"Last successful cycle: {status['last_successful_cycle']}; "
            f"last claimed observation: {status['last_claimed_observation']}; "
            f"last result: {status['last_execution_result']}; "
            f"next poll ≈ {status['next_poll_at']}; last error: {status['last_error']}\n"
            f"Legacy Telegram scanner: enabled={legacy['enabled']}; "
            f"running={legacy['running']}; last_scan={legacy['last_scan_at']}; "
            "source=LEGACY_TELEGRAM_SCANNER; PAPER-only",
        )

    def paper_errors_command(message):
        if not authorized(message):
            return
        try:
            response = remote.get("http://127.0.0.1:8000/paper/scanner/errors", timeout=(3, 5))
            response.raise_for_status()
            records = response.json().get("errors", [])
            if not isinstance(records, list):
                raise ValueError("Invalid scanner errors")
            lines = ["Последние ошибки PAPER scanner:"]
            for item in records[:10]:
                if not isinstance(item, dict):
                    continue
                lines.append(
                    f"{str(item.get('occurred_at', ''))[:32]} "
                    f"{str(item.get('stage', ''))[:24]} "
                    f"{str(item.get('error_type', ''))[:40]} "
                    f"{str(item.get('symbol') or '')[:20]} {str(item.get('timeframe') or '')[:4]}"
                )
            send(message, "\n".join(lines) if len(lines) > 1 else "Ошибок PAPER scanner нет.")
        except Exception:
            send(message, "PAPER scanner: ошибки API недоступны.")

    def paper_command(message):
        if not authorized(message):
            return
        from paper_journal import PaperJournal, journal_path

        try:
            local_path = journal_path()
            local_existed = local_path.is_file()
            experiment_id = os.environ.get("PAPER_EXPERIMENT_ID", "paper-baseline-v1")
            r = PaperJournal().report(experiment_id=experiment_id)
            lines = [
                f"PAPER-журнал: {r['period_start']} — {r['period_end']}",
                f"Research experiment: {experiment_id}; вне эксперимента PAPER-позиций "
                f"{r['outside_experiment_positions']} "
                f"(без подтверждённого источника: {r['unattributed_legacy_positions']})",
                f"Telegram SQLite: {local_path}; существует={local_existed or local_path.is_file()}",
                f"Сигналы/наблюдения {r['signals']} (LONG {r['signal_directions']['LONG']}, "
                f"SHORT {r['signal_directions']['SHORT']}, HOLD {r['hold']}); "
                f"отклонённые входы {r['rejected_entries']}",
                f"Фактические PAPER-позиции {r['paper_positions']}; закрыты {r['closed_positions']}",
                f"Net PnL закрытых: {r['net_pnl_usd_closed']:.2f} USD; "
                f"реализованная просадка {r['realized_max_drawdown_pct']:.2f}%",
                f"DeepSeek: первый ответ OK {r['ai_ok']}; недоступен {r['ai_unavailable']}; "
                f"успешные повторы {r['ai_retry_ok']}; "
                f"без проверки {r['ai_not_reviewed']}; ответов AI {r['ai_observations']}; "
                f"проверенных пар сигнал/AI {r['paired_ai_observations']}",
                f"Research: LIVE {r['research_origins'].get('LIVE', 0)}; "
                f"BACKFILL {r['research_origins'].get('BACKFILL_TECHNICAL', 0)}; "
                f"AI не запрашивался {r['ai_not_requested']}",
                f"AI пропущен prefilter: {r['ai_skipped_by_prefilter']}; "
                "политики запросов: "
                + ", ".join(
                    f"{policy}={count}" for policy, count in sorted(r["ai_request_policies"].items())
                ),
            ]
            if not local_existed:
                lines.append("Telegram SQLite создан при первом чтении отчёта; прежних записей в нём нет.")
            try:
                response = remote.get("http://127.0.0.1:8000/paper/journal/status", timeout=(3, 5))
                response.raise_for_status()
                api = PaperJournalStatus.model_validate(response.json())
                lines.append(
                    f"API SQLite: {api.path}; существует={api.exists}; "
                    f"сигналы={api.signals}; AI OK={api.ai_ok}; пары={api.paired_ai_observations}"
                )
                if api.path != str(local_path):
                    lines.append("ВНИМАНИЕ: API и Telegram читают разные PAPER-журналы.")
                else:
                    lines.append(
                        "API-счётчики охватывают весь журнал; Research-отчёт ограничен experiment ID."
                    )
            except Exception:
                lines.append("API SQLite: диагностика недоступна; путь и счётчики сервера неизвестны.")
            if message.text.split()[0].split("@")[0] == "/paper_report":
                lines.append("Пары/TF (закрытые сделки, net USD):")
                for pair, item in sorted(r["by_pair_timeframe"].items()):
                    lines.append(f"{pair}: {item['closed']}, {item['net_pnl_usd']:.2f}")
                c = r["control_decisions"]
                lines.append(f"Решения AI к моменту попытки входа: {r['entry_aligned_ai_decisions']}.")
                lines.append(
                    f"Контроль A/B: технически допущено {c['technical_allow']}; "
                    f"AI подтвердил {c['ai_allow']}, отклонил {c['ai_veto']}, "
                    f"недоступен {c['ai_unknown']}"
                )
                if c["actual_vs_global_model_mismatch"]:
                    lines.append(
                        "Внимание: фактический менеджер открыл "
                        f"{c['actual_vs_global_model_mismatch']} входов вне общего контрольного лимита."
                    )
                if r["ai_error_reasons"]:
                    lines.append(
                        "Ошибки DeepSeek: "
                        + ", ".join(f"{key}={value}" for key, value in sorted(r["ai_error_reasons"].items()))
                    )
                if r["rejected_reasons"]:
                    lines.append(
                        "Причины пропуска: "
                        + ", ".join(f"{key}={value}" for key, value in sorted(r["rejected_reasons"].items()))
                    )
                if r["research_outcomes"]:
                    lines.append(
                        "Исходы research-сигналов по OHLCV: "
                        + ", ".join(f"{key}={value}" for key, value in sorted(r["research_outcomes"].items()))
                    )
                    lines.append("AMBIGUOUS_INTRABAR означает неизвестный порядок касаний внутри свечи.")
                state = r["current_portfolio_model"]
                available = state["available_lower_bound_usd"]
                available_text = f"{available:.2f} USD" if available is not None else "неизвестно"
                lines.append(
                    f"Контрольный капитал, нижняя оценка доступного: "
                    f"{available_text}; "
                    f"занятые слоты {state['active_slots_global']}/{state['slot_limit']}"
                )
                model = r["modeled_same_fills_costs"]
                lines.append(
                    f"Те же fills, модель base/double: {model['base_usd']:.2f}/"
                    f"{model['double_usd']:.2f} USD; покрыто {model['covered_positions']} закрытий"
                )
                lines.append("Просадка только по реализованным закрытиям; внутрисвечной риск неизвестен.")
                if r["sampled_max_position_drawdown_pct"] is not None:
                    lines.append(
                        "Максимальная просадка отдельной позиции по ticker-отметкам: "
                        f"{r['sampled_max_position_drawdown_pct']:.2f}% (выборка раз в пять минут)."
                    )
            if r["sample_warning"]:
                lines.append("Выборка закрытых сделок мала (<30); выводы о качестве преждевременны.")
            send(message, "\n".join(lines))
        except Exception as exc:
            send(message, "PAPER-журнал недоступен: " + type(exc).__name__)

    def paper_export_command(message):
        if not authorized(message):
            return
        from paper_journal import PaperJournal

        try:
            parts = message.text.split()
            kind = parts[1].lower() if len(parts) > 1 else "csv"
            payload = PaperJournal().export(kind).encode("utf-8")
            document = io.BytesIO(payload)
            document.name = "paper_journal." + kind
            bot.send_document(message.chat.id, document)
        except Exception as exc:
            send(message, "PAPER-экспорт недоступен: " + type(exc).__name__)

    bot.message_handler(commands=["deepseek", "ai_signal"])(analyze_command)
    bot.message_handler(commands=["ai_status"])(status_command)
    bot.message_handler(commands=["ai_performance"])(performance_command)
    bot.message_handler(commands=["paper_scanner_status"])(scanner_status_command)
    bot.message_handler(commands=["paper_bridge_status"])(bridge_status_command)
    bot.message_handler(commands=["paper_errors"])(paper_errors_command)
    bot.message_handler(commands=["paper_journal", "paper_report"])(paper_command)
    bot.message_handler(commands=["paper_export"])(paper_export_command)
    return state
