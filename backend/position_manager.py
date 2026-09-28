"""Paper position bookkeeping only; no exchange order APIs."""
import copy
import json
import logging
import os
import threading
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import requests


def format_price(value):
    return f"{value:.10g}"


class AutoTradeManager:
    """Автоматическое управление торговыми позициями"""

    def __init__(self, bot):
        self.bot = bot
        self._lock = threading.RLock()
        self.data_path = Path(__file__).resolve().parent.parent / 'runtime' / 'paper_positions.json'
        self.active_positions = {}  # Храним все активные позиции
        self.trade_history = []  # История всех сделок
        self.monitoring_active = False
        self.monitoring_thread = None
        self.last_trade_time = None

        # 🔽 🔽 🔽 ДОБАВЛЯЕМ НОВЫЕ НАСТРОЙКИ 🔽 🔽 🔽
        self.trading_config = {
            # 🎯 ФИЛЬТРЫ КАЧЕСТВА:
            'MIN_AI_CONFIDENCE': 7.0,  # Только высокие уверенности
            'MIN_VOLUME_RATIO': 1.5,  # Хорошие объемы!!!!!!!!!!!!!!!!

            # 📊 ЛИМИТЫ АКТИВНОСТИ:
            'MAX_ACTIVE_POSITIONS': 5,  # Макс 5 активных сделок
            'MAX_TRADES_PER_DAY': 6,  # До 6 сделок в день
            'MIN_TIME_BETWEEN_TRADES': 30,  # 30 минут между сделками

            # 🛡️ УПРАВЛЕНИЕ РИСКАМИ:
            'MAX_STOP_LOSS_PERCENT': 0.8,  # Стоп-лосс 0.8%
        }

    def should_open_trade(self, chat_id, symbol, ai_confidence, volume_ratio):
        """Проверяет можно ли открывать сделку"""
        try:
            config = self.trading_config

            # 1. 🎯 Проверка AI уверенности
            if ai_confidence < config['MIN_AI_CONFIDENCE']:
                return False, f"❌ AI уверенность {ai_confidence:.1f}/10 < {config['MIN_AI_CONFIDENCE']:.1f}/10"
            # 2. 📊 Проверка объемов
            if volume_ratio < config['MIN_VOLUME_RATIO']:
                return False, f"❌ Объемы {volume_ratio:.1f}x < {config['MIN_VOLUME_RATIO']:.1f}x"



            # 3. 🚫 Проверка лимита активных позиций
            active_count = len(self.get_active_positions(chat_id))
            if active_count >= config['MAX_ACTIVE_POSITIONS']:
                return False, f"❌ Достигнут лимит {config['MAX_ACTIVE_POSITIONS']} активных позиций"

            # 4. ⏰ Проверка времени между сделками
            if self.last_trade_time:
                time_since_last = (datetime.now() - self.last_trade_time).total_seconds() / 60
                if time_since_last < config['MIN_TIME_BETWEEN_TRADES']:
                    wait_time = config['MIN_TIME_BETWEEN_TRADES'] - time_since_last
                    return False, f"⏳ Ждите {wait_time:.0f} мин. между сделками"

            # 5. 📈 Проверка лимита сделок за день
            today_trades = [t for t in self.trade_history
                            if t.get('chat_id') == chat_id
                            and t.get('created_at') and t['created_at'].date() == datetime.now().date()]
            if len(today_trades) >= config['MAX_TRADES_PER_DAY']:
                return False, f"❌ Достигнут лимит {config['MAX_TRADES_PER_DAY']} сделок в день"

            return True, "✅ Можно открывать сделку"

        except Exception as e:
            return False, f"❌ Ошибка проверки: {str(e)}"

    def create_auto_trade(self, chat_id, symbol, entry_price, stop_loss, take_profits, direction="LONG",
                          ai_confidence=5.0, volume_ratio=1.0):
        """Создает автоматическую сделку с проверками"""
        try:
            # 🔽 🔽 🔽 ВКЛЮЧАЕМ ПРОВЕРКИ ОБРАТНО 🔽 🔽 🔽
            can_open, reason = self.should_open_trade(chat_id, symbol, ai_confidence, volume_ratio)
            if not can_open:
                print(f"🚫 Сделка {symbol} отклонена: {reason}")
                # Отправляем уведомление в телеграм
                try:
                    self.bot.send_message(chat_id, f"🚫 {reason}")
                except:
                    pass
                return None

            # 🔽 УБИРАЕМ СТАРУЮ ДИАГНОСТИКУ (она больше не нужна)
            # print(f"🎯 СОЗДАЮ СДЕЛКУ {symbol} (проверки отключены)")
            # print(f"   AI: {ai_confidence}/10, Объемы: {volume_ratio}x")

            # 🔽 ДАЛЕЕ ИДЕТ ОСТАЛЬНОЙ КОД БЕЗ ИЗМЕНЕНИЙ:
            from signal_models import TradePlan, direction as normalize_direction
            direction = normalize_direction(direction).value
            TradePlan(direction=direction, entry=entry_price, stop_loss=stop_loss,
                      take_profits=take_profits)
            if abs(stop_loss-entry_price)/entry_price > 0.10:
                return None

            position_id = f"{symbol}_{uuid.uuid4().hex}"

            position_data = {
                'position_id': position_id,
                'symbol': symbol,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profits': take_profits,
                'direction': direction,
                'status': 'ACTIVE',
                'current_size': 100,
                'chat_id': chat_id,
                'created_at': datetime.now(),
                'executed_tps': [],
                'fills': [],
                'realized_pnl_pct': -0.1,
                # 🔽 ДОБАВЛЯЕМ ДАННЫЕ ДЛЯ АНАЛИТИКИ
                'ai_confidence': ai_confidence,
                'volume_ratio': volume_ratio
            }

            self.active_positions[position_id] = position_data
            self.save_data()
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
                    f"🤖 AI: {ai_confidence}/10 📊 Объемы: {volume_ratio}x"
                )
            except:
                pass

            return position_id

        except Exception as e:
            print(f"❌ Ошибка создания авто-сделки: {e}")
            return None

    def start_monitoring(self):
        """Запуск автоматического мониторинга позиций"""
        self.monitoring_active = True

        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
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
            if position['status'] != 'ACTIVE':
                continue

            try:
                current_price = self._get_current_price(position['symbol'])
                if not current_price:
                    continue

                self._check_position_triggers(position, current_price)

            except Exception as e:
                print(f"❌ Ошибка проверки позиции {position_id}: {e}")

    def _get_current_price(self, symbol):
        """Получает текущую цену символа"""
        try:
            # Используем упрощенный метод получения цены
            url = f"https://api.binance.com/api/v3/ticker/price"
            params = {'symbol': symbol}
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return float(data['price'])
            return None

        except Exception as e:
            print(f"❌ Ошибка получения цены {symbol}: {e}")
            return None

    def _check_position_triggers(self, position, current_price):
        """Проверяет срабатывание триггеров позиции"""
        symbol = position['symbol']
        direction = position['direction']

        # Проверяем стоп-лосс
        if self._check_stop_loss(position, current_price, direction):
            self._execute_stop_loss(position, current_price)
            return

        # Проверяем тейк-профиты
        self._check_take_profits(position, current_price, direction)

    def _check_stop_loss(self, position, current_price, direction):
        """Проверяет срабатывание стоп-лосса"""
        stop_loss = position['stop_loss']

        if direction == "LONG":
            return current_price <= stop_loss
        else:  # SHORT
            return current_price >= stop_loss

    def _check_take_profits(self, position, current_price, direction):
        """Проверяет срабатывание тейк-профитов"""
        take_profits = position['take_profits']
        executed_tps = position['executed_tps']

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
                    break

    def _execute_stop_loss(self, position, current_price, is_manual_close=False):
        if position['status'] != 'ACTIVE':
            return
        self._record_fill(position,current_price,position['current_size'],'MANUAL_CLOSE' if is_manual_close else 'STOP_LOSS')
        position.update(status='CLOSED',closed_at=datetime.now(),close_price=current_price,
                        close_reason='MANUAL_CLOSE' if is_manual_close else 'STOP_LOSS')
        self.trade_history.append(copy.deepcopy(position))
        self.save_data()
        self._notify(position['chat_id'],f"PAPER {position['symbol']}: {position['close_reason']}; net PnL {position['realized_pnl_pct']:.3f}%")

    def close_position_manually(self, position_id, current_price):
        """Ручное закрытие позиции"""
        position = self.active_positions.get(position_id)
        if position and position['status'] == 'ACTIVE':
            self._execute_stop_loss(position, current_price, is_manual_close=True)
            return True
        return False



    def _execute_take_profit(self, position, tp_id, tp_price, current_price):
        if position['status'] != 'ACTIVE' or tp_id in position['executed_tps']:
            return
        size={'TP1':30,'TP2':30,'TP3':40}[tp_id]
        self._record_fill(position,tp_price,size,tp_id)
        position['executed_tps'].append(tp_id)
        if position['current_size']<=0:
            position.update(status='CLOSED',closed_at=datetime.now(),close_price=tp_price,close_reason='TAKE_PROFIT')
            self.trade_history.append(copy.deepcopy(position))
        else:
            position['stop_loss']=position['entry_price'] if tp_id=='TP1' else position['entry_price']+(tp_price-position['entry_price'])*.5
        self.save_data()
        self._notify(position['chat_id'],f"PAPER {position['symbol']}: {tp_id}; realized net {position['realized_pnl_pct']:.3f}%")

    def _create_tp_message(self, position, tp_id, tp_price, current_price, size_closed, new_stop):
        """Создает сообщение о исполнении тейк-профита"""
        symbol = position['symbol']

        if tp_id == "TP3" or position['current_size'] <= 0:
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
✅ Остаток позиции: {position['current_size']}%

💡 Следующая цель: {position['take_profits'][len(position['executed_tps'])]}
"""

    def _calculate_total_pnl(self, position):
        return self._calculate_trade_pnl(position)

    def get_active_positions(self, chat_id=None):
        """Возвращает активные позиции"""
        if chat_id:
            return {pid: pos for pid, pos in self.active_positions.items()
                    if pos['chat_id'] == chat_id and pos['status'] == 'ACTIVE'}
        return {pid: pos for pid, pos in self.active_positions.items()
                if pos['status'] == 'ACTIVE'}

    def get_position_status(self, position_id):
        """Возвращает статус позиции"""
        return self.active_positions.get(position_id)

    def get_trading_statistics(self, chat_id=None, days=7):
        """Собирает статистику по сделкам"""
        try:
            # Фильтруем сделки по пользователю и дате
            user_trades = [t for t in self.trade_history
                           if (chat_id is None or t.get('chat_id') == chat_id)]

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
            ai_confident_trades = [t for t in user_trades if t.get('ai_confidence', 0) >= 7.0]
            ai_high_confident_trades = [t for t in user_trades if t.get('ai_confidence', 0) >= 8.0]

            # Лучшие/худшие символы
            symbol_stats = {}
            for trade in user_trades:
                symbol = trade['symbol']
                pnl = self._calculate_trade_pnl(trade)
                if symbol not in symbol_stats:
                    symbol_stats[symbol] = {'trades': 0, 'total_pnl': 0, 'profitable': 0}
                symbol_stats[symbol]['trades'] += 1
                symbol_stats[symbol]['total_pnl'] += pnl
                if pnl > 0:
                    symbol_stats[symbol]['profitable'] += 1

            # Сортируем символы по доходности
            best_symbols = sorted(symbol_stats.items(), key=lambda x: x[1]['total_pnl'], reverse=True)[:5]
            worst_symbols = sorted(symbol_stats.items(), key=lambda x: x[1]['total_pnl'])[:5]

            return {
                'total_trades': total_trades,
                'profitable_trades': len(profitable_trades),
                'losing_trades': len(losing_trades),
                'win_rate': (len(profitable_trades) / total_trades * 100) if total_trades > 0 else 0,
                'total_pnl': total_pnl,
                'avg_pnl': avg_pnl,
                'ai_confident_trades': len(ai_confident_trades),
                'ai_high_confident_trades': len(ai_high_confident_trades),
                'best_symbols': best_symbols,
                'worst_symbols': worst_symbols,
                'symbol_stats': symbol_stats
            }

        except Exception as e:
            print(f"❌ Ошибка сбора статистики: {e}")
            return None

    def _calculate_trade_pnl(self, trade):
        return float(trade.get('realized_pnl_pct', 0))

    def can_create_auto_trade(self, chat_id, symbol):
        """Проверяет можно ли создать новую авто-сделку"""
        try:
            # Максимум 3 активные позиции
            active_positions = self.get_active_positions(chat_id)
            if len(active_positions) >= self.trading_config['MAX_ACTIVE_POSITIONS']:
                return False, "❌ Достигнут лимит: макс. 3 активные позиции"

            # Проверяем не торгуем ли уже этот символ
            for pos_id, position in active_positions.items():
                if position['symbol'] == symbol:
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
                if (trade.get('chat_id') == chat_id and
                        trade.get('created_at') and
                        trade['created_at'] >= time_threshold):
                    recent_trades.append(trade)

            return recent_trades
        except Exception as e:
            print(f"❌ Ошибка получения recent trades: {e}")
            return []

    def save_data(self):
        from storage import atomic_json
        with self._lock:
            atomic_json(self.data_path,{'active_positions':self.active_positions,'trade_history':self.trade_history})
        return True

    def load_data(self):
        """Загружает данные из файла"""
        try:
            # Проверяем существует ли файл
            if not os.path.exists(self.data_path):
                print("📂 Файл данных не найден, начинаем с чистого листа")
                return True

            # Читаем файл
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Восстанавливаем активные позиции
            self.active_positions = {}
            for position_id, position_data in data.get('active_positions', {}).items():
                # Конвертируем строки обратно в datetime
                if 'created_at' in position_data and position_data['created_at']:
                    position_data['created_at'] = datetime.fromisoformat(position_data['created_at'])
                if 'closed_at' in position_data and position_data['closed_at']:
                    position_data['closed_at'] = datetime.fromisoformat(position_data['closed_at'])

                self.active_positions[position_id] = position_data
            self.save_data()

            # Восстанавливаем историю сделок
            self.trade_history = []
            for trade_data in data.get('trade_history', []):
                # Конвертируем строки обратно в datetime
                if 'created_at' in trade_data and trade_data['created_at']:
                    trade_data['created_at'] = datetime.fromisoformat(trade_data['created_at'])
                if 'closed_at' in trade_data and trade_data['closed_at']:
                    trade_data['closed_at'] = datetime.fromisoformat(trade_data['closed_at'])

                self.trade_history.append(trade_data)

            print(
                f"📂 Загружено: {len(self.active_positions)} активных позиций, {len(self.trade_history)} сделок в истории")
            return True

        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            return False

    def _record_fill(self, position, price, size, reason):
        size=min(size,position['current_size'])
        sign=1 if position['direction']=='LONG' else -1
        fill=price*(1-sign*.0005)
        net=(sign*(fill-position['entry_price'])/position['entry_price']*100-.1*fill/position['entry_price'])*size/100
        position['realized_pnl_pct']=position.get('realized_pnl_pct',-.1)+net
        position['current_size']-=size
        position.setdefault('fills',[]).append({'price':fill,'size':size,'reason':reason,'net_pnl_pct':net,'timestamp':datetime.now().isoformat()})

    def _notify(self,chat_id,text):
        try:
            self.bot.send_message(chat_id,text)
        except Exception:
            logging.getLogger(__name__).warning('Paper notification failed')


# Serialize compound position mutations across scanner, Telegram and monitor threads.
def _synchronized(method):
    def call(self,*args,**kwargs):
        with self._lock:
            return method(self,*args,**kwargs)
    return call


for _name in ('create_auto_trade','_check_all_positions','close_position_manually',
              '_execute_stop_loss','_execute_take_profit','get_active_positions','get_trading_statistics'):
    setattr(AutoTradeManager,_name,_synchronized(getattr(AutoTradeManager,_name)))
