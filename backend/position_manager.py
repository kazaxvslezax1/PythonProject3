"""Paper position bookkeeping only; no exchange order APIs."""

import copy
import json
import logging
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

import requests


def format_price(value):
    return f"{value:.10g}"


class AutoTradeManager:
    """Автоматическое управление торговыми позициями"""

    def __init__(self, bot, rules_loader=None):
        self.bot = bot
        from exchange_rules import get_exchange_rules

        self.rules_loader = rules_loader or get_exchange_rules
        self.paper_notional = 1000.0
        self._lock = threading.RLock()
        self.data_path = Path(__file__).resolve().parent.parent / "runtime" / "paper_positions.json"
        self.active_positions = {}  # Храним все активные позиции
        self.trade_history = []  # История всех сделок
        self.monitoring_active = False
        self.monitoring_thread = None
        self.last_trade_time = None

        # 🔽 🔽 🔽 ДОБАВЛЯЕМ НОВЫЕ НАСТРОЙКИ 🔽 🔽 🔽
        self.trading_config = {
            # 🎯 ФИЛЬТРЫ КАЧЕСТВА:
            "MIN_AI_CONFIDENCE": 7.0,  # Только высокие уверенности
            "MIN_VOLUME_RATIO": 1.5,  # Хорошие объемы!!!!!!!!!!!!!!!!
            # 📊 ЛИМИТЫ АКТИВНОСТИ:
            "MAX_ACTIVE_POSITIONS": 5,  # Макс 5 активных сделок
            "MAX_TRADES_PER_DAY": 6,  # До 6 сделок в день
            "MIN_TIME_BETWEEN_TRADES": 30,  # 30 минут между сделками
            # 🛡️ УПРАВЛЕНИЕ РИСКАМИ:
            "MAX_STOP_LOSS_PERCENT": 10.0,  # Reject excessive risk; do not tighten levels
        }

    def should_open_trade(self, chat_id, symbol, ai_confidence, volume_ratio):
        import math

        config = self.trading_config
        if not all(math.isfinite(x) for x in (ai_confidence, volume_ratio)):
            return False, "Invalid quality or volume"
        if ai_confidence < config["MIN_AI_CONFIDENCE"] or volume_ratio < config["MIN_VOLUME_RATIO"]:
            return False, "Quality or volume filter rejected"
        positions = self.get_active_positions(chat_id)
        if len(positions) >= config["MAX_ACTIVE_POSITIONS"]:
            return False, "Active position limit"
        if any(p["symbol"] == symbol for p in positions.values()):
            return False, "Symbol already open"
        records = {
            t["position_id"]: t
            for t in [*self.trade_history, *self.active_positions.values()]
            if t.get("chat_id") == chat_id
        }
        created = [t["created_at"] for t in records.values() if t.get("created_at")]
        now = datetime.now()
        if created and (now - max(created)).total_seconds() < config["MIN_TIME_BETWEEN_TRADES"] * 60:
            return False, "Trade cooldown"
        if sum(t.date() == now.date() for t in created) >= config["MAX_TRADES_PER_DAY"]:
            return False, "Daily entry limit"
        return True, "Paper entry allowed"

    def create_auto_trade(
        self,
        chat_id,
        symbol,
        entry_price,
        stop_loss,
        take_profits,
        direction="LONG",
        ai_confidence=5.0,
        volume_ratio=1.0,
    ):
        """Создает автоматическую сделку с проверками"""
        try:
            # 🔽 🔽 🔽 ВКЛЮЧАЕМ ПРОВЕРКИ ОБРАТНО 🔽 🔽 🔽
            can_open, reason = self.should_open_trade(chat_id, symbol, ai_confidence, volume_ratio)
            if not can_open:
                print(f"🚫 Сделка {symbol} отклонена: {reason}")
                # Отправляем уведомление в телеграм
                try:
                    self.bot.send_message(chat_id, f"🚫 {reason}")
                except Exception:
                    pass
                return None

            # 🔽 УБИРАЕМ СТАРУЮ ДИАГНОСТИКУ (она больше не нужна)
            # print(f"🎯 СОЗДАЮ СДЕЛКУ {symbol} (проверки отключены)")
            # print(f"   AI: {ai_confidence}/10, Объемы: {volume_ratio}x")

            # 🔽 ДАЛЕЕ ИДЕТ ОСТАЛЬНОЙ КОД БЕЗ ИЗМЕНЕНИЙ:
            from signal_models import TradePlan
            from signal_models import direction as normalize_direction

            direction = normalize_direction(direction).value
            plan = TradePlan(
                direction=direction, entry=entry_price, stop_loss=stop_loss, take_profits=take_profits
            )
            if plan.rr < 2:
                return None
            if (
                abs(stop_loss - entry_price) / entry_price
                > self.trading_config["MAX_STOP_LOSS_PERCENT"] / 100
            ):
                return None

            current_price = self._get_current_price(symbol)
            if not current_price:
                return None
            fill = current_price * (1.0005 if direction == "LONG" else 0.9995)
            rules = self.rules_loader(symbol)
            plan = rules.plan(
                TradePlan(direction=direction, entry=fill, stop_loss=stop_loss, take_profits=take_profits)
            )
            if plan.rr < 2 or abs(plan.entry - plan.stop_loss) / plan.entry > 0.10:
                return None
            quantity = rules.quantity(self.paper_notional, plan.entry)
            entry_price, stop_loss, take_profits = plan.entry, plan.stop_loss, plan.take_profits
            position_id = f"{symbol}_{uuid.uuid4().hex}"

            position_data = {
                "position_id": position_id,
                "symbol": symbol,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profits": take_profits,
                "direction": direction,
                "status": "ACTIVE",
                "current_size": 100,
                "quantity": quantity,
                "paper_notional": quantity * entry_price,
                "chat_id": chat_id,
                "created_at": datetime.now(),
                "executed_tps": [],
                "fills": [],
                "realized_pnl_pct": -0.1,
                "pnl_verified": True,
                # 🔽 ДОБАВЛЯЕМ ДАННЫЕ ДЛЯ АНАЛИТИКИ
                "ai_confidence": ai_confidence,
                "volume_ratio": volume_ratio,
            }

            self.active_positions[position_id] = position_data
            try:
                self.save_data()
            except OSError:
                self.active_positions.pop(position_id, None)
                raise
            self.last_trade_time = datetime.now()  # 🔽 ОБНОВЛЯЕМ ВРЕМЯ ПОСЛЕДНЕЙ СДЕЛКИ

            # Запускаем мониторинг если еще не запущен
            if not self.monitoring_active:
                self.start_monitoring()

            print(f"✅ Создана авто-сделка {symbol}: AI {ai_confidence}/10, объемы {volume_ratio}x")

            # Отправляем уведомление о создании сделки
            try:
                self.bot.send_message(
                    chat_id,
                    f"✅ АВТО-СДЕЛКА СОЗДАНА!\n\n"
                    f"📊 {symbol} - {direction}\n"
                    f"💰 Вход: {format_price(entry_price)}\n"
                    f"🎯 Цели: {', '.join([format_price(tp) for tp in take_profits])}\n"
                    f"🛑 Стоп: {format_price(stop_loss)}\n\n"
                    f"🤖 AI: {ai_confidence}/10 📊 Объемы: {volume_ratio}x",
                )
            except Exception:
                pass

            return position_id

        except Exception as e:
            print(f"❌ Ошибка создания авто-сделки: {e}")
            return None

    def start_monitoring(self):
        """Запуск автоматического мониторинга позиций"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return
        self.monitoring_active = True

        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        print("🔍 Автоматический мониторинг позиций запущен")

    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.monitoring_active = False
        print("⏹️ Автоматический мониторинг позиций остановлен")

    def _monitoring_loop(self):
        """Основной цикл мониторинга позиций"""
        check_interval = 30  # Проверка каждые 30 секунд

        while self.monitoring_active:
            try:
                self._check_all_positions()
                time.sleep(check_interval)
            except Exception as e:
                print(f"❌ Ошибка в мониторинге позиций: {e}")
                time.sleep(60)

    def _check_all_positions(self):
        """Проверяет все активные позиции"""
        if not self.active_positions:
            return

        for position_id, position in list(self.active_positions.items()):
            if position["status"] != "ACTIVE":
                continue

            try:
                current_price = self._get_current_price(position["symbol"])
                if not current_price:
                    continue

                self._check_position_triggers(position, current_price)

            except Exception as e:
                print(f"❌ Ошибка проверки позиции {position_id}: {e}")

    def _get_current_price(self, symbol):
        """Получает текущую цену символа"""
        try:
            # Используем упрощенный метод получения цены
            url = "https://api.binance.com/api/v3/ticker/price"
            params = {"symbol": symbol}
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return float(data["price"])
            return None

        except Exception as e:
            print(f"❌ Ошибка получения цены {symbol}: {e}")
            return None

    def _check_position_triggers(self, position, current_price):
        """Проверяет срабатывание триггеров позиции"""
        direction = position["direction"]

        # Проверяем стоп-лосс
        if self._check_stop_loss(position, current_price, direction):
            self._execute_stop_loss(position, current_price)
            return

        # Проверяем тейк-профиты
        self._check_take_profits(position, current_price, direction)

    def _check_stop_loss(self, position, current_price, direction):
        """Проверяет срабатывание стоп-лосса"""
        stop_loss = position["stop_loss"]

        if direction == "LONG":
            return current_price <= stop_loss
        else:  # SHORT
            return current_price >= stop_loss

    def _check_take_profits(self, position, current_price, direction):
        """Проверяет срабатывание тейк-профитов"""
        take_profits = position["take_profits"]
        executed_tps = position["executed_tps"]

        for i, tp_price in enumerate(take_profits):
            tp_id = f"TP{i + 1}"

            # Если этот ТП еще не выполнен
            if tp_id not in executed_tps:
                tp_triggered = False

                if direction == "LONG":
                    tp_triggered = current_price >= tp_price
                else:  # SHORT
                    tp_triggered = current_price <= tp_price

                if tp_triggered:
                    self._execute_take_profit(position, tp_id, tp_price, current_price)
                    if position["status"] != "ACTIVE":
                        break

    def _execute_stop_loss(self, position, current_price, is_manual_close=False):
        if position["status"] != "ACTIVE":
            return
        self._record_fill(
            position,
            current_price,
            position["current_size"],
            "MANUAL_CLOSE" if is_manual_close else "STOP_LOSS",
        )
        position.update(
            status="CLOSED",
            closed_at=datetime.now(),
            close_price=current_price,
            close_reason="MANUAL_CLOSE" if is_manual_close else "STOP_LOSS",
        )
        self.trade_history.append(copy.deepcopy(position))
        self.save_data()
        self._notify(
            position["chat_id"],
            f"PAPER {position['symbol']}: {position['close_reason']}; net PnL {position['realized_pnl_pct']:.3f}%",
        )

    def close_position_manually(self, position_id, current_price):
        """Ручное закрытие позиции"""
        position = self.active_positions.get(position_id)
        if position and position["status"] == "ACTIVE":
            self._execute_stop_loss(position, current_price, is_manual_close=True)
            return True
        return False

    def _execute_take_profit(self, position, tp_id, tp_price, current_price):
        if position["status"] != "ACTIVE" or tp_id in position["executed_tps"]:
            return
        size = {"TP1": 30, "TP2": 30, "TP3": 40}[tp_id]
        self._record_fill(position, tp_price, size, tp_id)
        position["executed_tps"].append(tp_id)
        if position["current_size"] <= 0:
            position.update(
                status="CLOSED", closed_at=datetime.now(), close_price=tp_price, close_reason="TAKE_PROFIT"
            )
            self.trade_history.append(copy.deepcopy(position))
        else:
            position["stop_loss"] = (
                position["entry_price"]
                if tp_id == "TP1"
                else position["entry_price"] + (tp_price - position["entry_price"]) * 0.5
            )
        self.save_data()
        self._notify(
            position["chat_id"],
            f"PAPER {position['symbol']}: {tp_id}; realized net {position['realized_pnl_pct']:.3f}%",
        )

    def _create_tp_message(self, position, tp_id, tp_price, current_price, size_closed, new_stop):
        """Создает сообщение о исполнении тейк-профита"""
        symbol = position["symbol"]

        if tp_id == "TP3" or position["current_size"] <= 0:
            return f"""
🎉 СДЕЛКА ЗАВЕРШЕНА!

💰 {symbol} достиг финальной цели
📈 Цена: {format_price(current_price)}
✅ Позиция полностью закрыта

📊 Итоговый результат: +{self._calculate_total_pnl(position):.2f}%
💡 Сделка завершена успешно!
"""
        else:
            return f"""
🔔 ЧАСТИЧНОЕ ЗАКРЫТИЕ ПОЗИЦИИ!

🎯 {symbol} достиг {tp_id}
💰 Цена: {format_price(current_price)}
📊 Продано: {size_closed}% позиции

🛑 Стоп перемещен: {format_price(new_stop)}
✅ Остаток позиции: {position["current_size"]}%

💡 Следующая цель: {position["take_profits"][len(position["executed_tps"])]}
"""

    def _calculate_total_pnl(self, position):
        return self._calculate_trade_pnl(position)

    def get_active_positions(self, chat_id=None):
        """Возвращает активные позиции"""
        if chat_id:
            return {
                pid: pos
                for pid, pos in self.active_positions.items()
                if pos["chat_id"] == chat_id and pos["status"] == "ACTIVE"
            }
        return {pid: pos for pid, pos in self.active_positions.items() if pos["status"] == "ACTIVE"}

    def get_position_status(self, position_id):
        """Возвращает статус позиции"""
        return self.active_positions.get(position_id)

    def get_trading_statistics(self, chat_id=None, days=7):
        """Собирает статистику по сделкам"""
        try:
            # Фильтруем сделки по пользователю и дате
            user_trades = [
                t
                for t in self.trade_history
                if (chat_id is None or t.get("chat_id") == chat_id)
                and t.get("pnl_verified", False)
                and t.get("closed_at")
                and (datetime.now() - t["closed_at"]).total_seconds() <= days * 86400
            ]

            if not user_trades:
                return None

            # Статистика по сделкам
            total_trades = len(user_trades)
            profitable_trades = [t for t in user_trades if self._calculate_trade_pnl(t) > 0]
            losing_trades = [t for t in user_trades if self._calculate_trade_pnl(t) <= 0]

            # Общая доходность
            total_pnl = sum(self._calculate_trade_pnl(t) for t in user_trades)
            avg_pnl = total_pnl / total_trades if total_trades > 0 else 0

            # Статистика по AI уверенности
            ai_confident_trades = [t for t in user_trades if t.get("ai_confidence", 0) >= 7.0]
            ai_high_confident_trades = [t for t in user_trades if t.get("ai_confidence", 0) >= 8.0]

            # Лучшие/худшие символы
            symbol_stats = {}
            for trade in user_trades:
                symbol = trade["symbol"]
                pnl = self._calculate_trade_pnl(trade)
                if symbol not in symbol_stats:
                    symbol_stats[symbol] = {"trades": 0, "total_pnl": 0, "profitable": 0}
                symbol_stats[symbol]["trades"] += 1
                symbol_stats[symbol]["total_pnl"] += pnl
                if pnl > 0:
                    symbol_stats[symbol]["profitable"] += 1

            # Сортируем символы по доходности
            best_symbols = sorted(symbol_stats.items(), key=lambda x: x[1]["total_pnl"], reverse=True)[:5]
            worst_symbols = sorted(symbol_stats.items(), key=lambda x: x[1]["total_pnl"])[:5]

            return {
                "total_trades": total_trades,
                "profitable_trades": len(profitable_trades),
                "losing_trades": len(losing_trades),
                "win_rate": (len(profitable_trades) / total_trades * 100) if total_trades > 0 else 0,
                "total_pnl": total_pnl,
                "avg_pnl": avg_pnl,
                "ai_confident_trades": len(ai_confident_trades),
                "ai_high_confident_trades": len(ai_high_confident_trades),
                "best_symbols": best_symbols,
                "worst_symbols": worst_symbols,
                "symbol_stats": symbol_stats,
            }

        except Exception as e:
            print(f"❌ Ошибка сбора статистики: {e}")
            return None

    def _calculate_trade_pnl(self, trade):
        return float(trade.get("realized_pnl_pct", 0))

    def can_create_auto_trade(self, chat_id, symbol):
        """Проверяет можно ли создать новую авто-сделку"""
        try:
            # Максимум 3 активные позиции
            active_positions = self.get_active_positions(chat_id)
            if len(active_positions) >= self.trading_config["MAX_ACTIVE_POSITIONS"]:
                return False, "❌ Достигнут лимит: макс. 3 активные позиции"

            # Проверяем не торгуем ли уже этот символ
            for pos_id, position in active_positions.items():
                if position["symbol"] == symbol:
                    return False, f"❌ Активная позиция {symbol} уже существует"

            # Проверяем лимит 3 сделки в час
            recent_trades = self._get_recent_trades(chat_id, hours=1)
            if len(recent_trades) >= 3:
                return False, "❌ Лимит: не более 3 сделок в час"

            return True, "✅ Можно создать сделку"

        except Exception as e:
            print(f"❌ Ошибка проверки лимитов: {e}")
            return False, "❌ Ошибка проверки лимитов"

    def _get_recent_trades(self, chat_id, hours=1):
        """Возвращает сделки за последние N часов"""
        try:
            from datetime import datetime, timedelta

            time_threshold = datetime.now() - timedelta(hours=hours)

            recent_trades = []
            for trade in self.trade_history:
                if (
                    trade.get("chat_id") == chat_id
                    and trade.get("created_at")
                    and trade["created_at"] >= time_threshold
                ):
                    recent_trades.append(trade)

            return recent_trades
        except Exception as e:
            print(f"❌ Ошибка получения recent trades: {e}")
            return []

    def save_data(self):
        from storage import atomic_json

        with self._lock:
            atomic_json(
                self.data_path,
                {"active_positions": self.active_positions, "trade_history": self.trade_history},
            )
        return True

    def load_data(self):
        source = self.data_path
        legacy = Path(__file__).resolve().parent / "trading_data.json"
        if not source.exists():
            if source.name == "paper_positions.json" and legacy.exists():
                source = legacy
            else:
                return True
        try:
            data = json.loads(source.read_text())
            positions = data.get("active_positions", {})
            history = data.get("trade_history", [])
            if not isinstance(positions, dict) or not isinstance(history, list):
                raise ValueError("Invalid storage shape")
            for record in [*positions.values(), *history]:
                for key in ("created_at", "closed_at"):
                    if record.get(key):
                        record[key] = datetime.fromisoformat(record[key])
                record.setdefault("fills", [])
                if "realized_pnl_pct" not in record:
                    record["pnl_verified"] = False
                    record["realized_pnl_pct"] = 0.0
                else:
                    record.setdefault("pnl_verified", True)
            with self._lock:
                self.active_positions = positions
                self.trade_history = history
            if source != self.data_path:
                self.save_data()  # preserve original legacy file unchanged
            return True
        except Exception as exc:
            logging.getLogger(__name__).error("Position restore failed: %s", type(exc).__name__)
            return False

    def _record_fill(self, position, price, size, reason):
        size = min(size, position["current_size"])
        sign = 1 if position["direction"] == "LONG" else -1
        fill = price * (1 - sign * 0.0005)
        net = (
            (
                sign * (fill - position["entry_price"]) / position["entry_price"] * 100
                - 0.1 * fill / position["entry_price"]
            )
            * size
            / 100
        )
        position["realized_pnl_pct"] = position.get("realized_pnl_pct", -0.1) + net
        position["current_size"] -= size
        position.setdefault("fills", []).append(
            {
                "price": fill,
                "size": size,
                "reason": reason,
                "net_pnl_pct": net,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def _notify(self, chat_id, text):
        try:
            self.bot.send_message(chat_id, text)
        except Exception:
            logging.getLogger(__name__).warning("Paper notification failed")


# Serialize compound position mutations across scanner, Telegram and monitor threads.
def _synchronized(method):
    def call(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)

    return call


for _name in (
    "create_auto_trade",
    "_check_all_positions",
    "close_position_manually",
    "_execute_stop_loss",
    "_execute_take_profit",
    "get_active_positions",
    "get_trading_statistics",
):
    setattr(AutoTradeManager, _name, _synchronized(getattr(AutoTradeManager, _name)))


class SmartTakeProfitAdapter:
    """Legacy smart_tp commands share the same positions and fill ledger."""

    def __init__(self, manager):
        self._manager = manager
        self.chat_id = None

    @property
    def monitoring_active(self):
        return self._manager().monitoring_active

    @property
    def active_positions(self):
        return {
            key: {**value, "current_stop_loss": value["stop_loss"]}
            for key, value in self._manager().get_active_positions(self.chat_id).items()
        }

    def start_takeprofit_monitoring(self, chat_id):
        self.chat_id = chat_id
        self._manager().start_monitoring()
        return "PAPER monitoring started; shared position ledger"

    def stop_takeprofit_monitoring(self):
        self._manager().stop_monitoring()
        return "PAPER monitoring stopped"

    def add_position(self, symbol, entry_price, stop_loss, take_profits, direction, position_size=100):
        from ai_runtime import review_analysis
        from analysis_service import analyze_market
        from signal_models import direction as normalize_direction

        if self.chat_id is None:
            return None
        data = analyze_market(symbol)
        signal = data["technical_signal"]
        review = review_analysis(data)
        if review is not None:
            signal = review.final
        if signal.direction != normalize_direction(direction) or signal.plan is None:
            return None
        return self._manager().create_auto_trade(
            self.chat_id,
            symbol,
            entry_price,
            stop_loss,
            take_profits,
            signal.direction.value,
            signal.quality,
            data["volume_ratio"],
        )
