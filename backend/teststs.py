class AutoTradeManager:
    """Автоматическое управление торговыми позициями"""

    def __init__(self, bot):
        self.bot = bot
        self.active_positions = {}  # Храним все активные позиции
        self.trade_history = []  # История всех сделок
        self.monitoring_active = False
        self.monitoring_thread = None

    def create_auto_trade(self, chat_id, symbol, entry_price, stop_loss, take_profits, direction="LONG"):
        """Создает автоматическую сделку"""
        try:
            position_id = f"{symbol}_{int(time.time())}"

            position_data = {
                'position_id': position_id,
                'symbol': symbol,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profits': take_profits,  # [tp1, tp2, tp3]
                'direction': direction,
                'status': 'ACTIVE',
                'current_size': 100,  # Начальный размер позиции %
                'chat_id': chat_id,
                'created_at': datetime.now(),
                'executed_tps': []  # Какие ТП уже выполнены
            }

            self.active_positions[position_id] = position_data

            # Запускаем мониторинг если еще не запущен
            if not self.monitoring_active:
                self.start_monitoring()

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
        """Исполнение стоп-лосса или ручного закрытия"""
        try:
            position_id = position['position_id']
            symbol = position['symbol']

            # Рассчитываем результат
            entry = position['entry_price']
            if position['direction'] == "LONG":
                pnl_pct = (current_price - entry) / entry * 100
            else:
                pnl_pct = (entry - current_price) / entry * 100

            # Закрываем позицию
            position['status'] = 'CLOSED'
            position['closed_at'] = datetime.now()
            position['close_price'] = current_price

            if is_manual_close:
                position['close_reason'] = 'MANUAL_CLOSE'
                close_emoji = "👤"
                close_reason = "РУЧНОЕ ЗАКРЫТИЕ"
            else:
                position['close_reason'] = 'STOP_LOSS'
                close_emoji = "🛑"
                close_reason = "СТОП-ЛОСС"

            # Сохраняем в историю
            self.trade_history.append(position.copy())

            # Отправляем уведомление
            message = f"""
    {close_emoji} {close_reason}!

    📊 {symbol} - {position['direction']}
    💰 Вход: {format_price(entry)}
    🛑 Стоп: {format_price(position['stop_loss'])}
    📉 Текущая: {format_price(current_price)}
    💸 Результат: {pnl_pct:+.2f}%

    💡 Позиция закрыта {"вручную" if is_manual_close else "автоматически"}
    📊 Анализ: /analyze_smart {symbol}
    """
            self.bot.send_message(position['chat_id'], message)
            print(f"🔴 {close_reason.lower()}: {symbol} ({pnl_pct:+.2f}%)")

        except Exception as e:
            print(f"❌ Ошибка исполнения закрытия: {e}")

    def close_position_manually(self, position_id, current_price):
        """Ручное закрытие позиции"""
        position = self.active_positions.get(position_id)
        if position and position['status'] == 'ACTIVE':
            self._execute_stop_loss(position, current_price, is_manual_close=True)
            return True
        return False



    def _execute_take_profit(self, position, tp_id, tp_price, current_price):
        """Исполнение тейк-профита"""
        try:
            symbol = position['symbol']
            executed_tps = position['executed_tps']

            # Определяем размер позиции для этого ТП
            if tp_id == "TP1":
                size_to_close = 30  # 30% позиции
                new_stop = position['entry_price']  # Безубыток
            elif tp_id == "TP2":
                size_to_close = 30  # еще 30% позиции
                # Стоп перемещаем для защиты прибыли
                if position['direction'] == "LONG":
                    new_stop = position['entry_price'] + (tp_price - position['entry_price']) * 0.5
                else:
                    new_stop = position['entry_price'] - (position['entry_price'] - tp_price) * 0.5
            else:  # TP3
                size_to_close = 40  # оставшиеся 40%
                new_stop = tp_price  # Закрываем всю позицию

            # Обновляем позицию
            position['current_size'] -= size_to_close
            executed_tps.append(tp_id)

            if tp_id == "TP3" or position['current_size'] <= 0:
                # Закрываем всю позицию
                position['status'] = 'CLOSED'
                position['closed_at'] = datetime.now()
                position['close_price'] = current_price
                position['close_reason'] = 'TAKE_PROFIT'
                self.trade_history.append(position.copy())
            else:
                # Обновляем стоп-лосс
                position['stop_loss'] = new_stop

            # Отправляем уведомление
            message = self._create_tp_message(position, tp_id, tp_price, current_price, size_to_close, new_stop)
            self.bot.send_message(position['chat_id'], message)
            print(f"🟢 Тейк-профит исполнен: {symbol} {tp_id}")

        except Exception as e:
            print(f"❌ Ошибка исполнения тейк-профита: {e}")

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
        """Рассчитывает общую прибыль/убыток"""
        # Упрощенный расчет для демонстрации
        entry = position['entry_price']
        close = position.get('close_price', entry)

        if position['direction'] == "LONG":
            return (close - entry) / entry * 100
        else:
            return (entry - close) / entry * 100

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
        """Рассчитывает PnL для одной сделки"""
        try:
            entry = trade['entry_price']
            close = trade.get('close_price', entry)

            if trade['direction'] == "LONG":
                return (close - entry) / entry * 100
            else:
                return (entry - close) / entry * 100
        except:
            return 0

    def can_create_auto_trade(self, chat_id, symbol):
        """Проверяет можно ли создать новую авто-сделку"""
        try:
            # Максимум 3 активные позиции
            active_positions = self.get_active_positions(chat_id)
            if len(active_positions) >= 3:
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
        """Сохраняет все данные в файл"""
        try:
            # Подготовка данных для сохранения
            data_to_save = {
                'active_positions': {},
                'trade_history': []
            }

            # Конвертируем активные позиции
            for position_id, position in self.active_positions.items():
                # Создаем копию позиции без объектов datetime
                position_copy = position.copy()

                # Конвертируем datetime в строки
                if 'created_at' in position_copy and position_copy['created_at']:
                    position_copy['created_at'] = position_copy['created_at'].isoformat()
                if 'closed_at' in position_copy and position_copy['closed_at']:
                    position_copy['closed_at'] = position_copy['closed_at'].isoformat()

                data_to_save['active_positions'][position_id] = position_copy

            # Конвертируем историю сделок
            for trade in self.trade_history:
                trade_copy = trade.copy()

                # Конвертируем datetime в строки
                if 'created_at' in trade_copy and trade_copy['created_at']:
                    trade_copy['created_at'] = trade_copy['created_at'].isoformat()
                if 'closed_at' in trade_copy and trade_copy['closed_at']:
                    trade_copy['closed_at'] = trade_copy['closed_at'].isoformat()

                data_to_save['trade_history'].append(trade_copy)

            # Сохраняем в файл
            with open('trading_data.json', 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)

            print("💾 Данные успешно сохранены")
            print(
                f"📊 Сохранено: {len(data_to_save['active_positions'])} активных позиций, {len(data_to_save['trade_history'])} сделок в истории")
            return True

        except Exception as e:
            print(f"❌ Ошибка сохранения данных: {e}")
            return False

    def load_data(self):
        """Загружает данные из файла"""
        try:
            # Проверяем существует ли файл
            if not os.path.exists('trading_data.json'):
                print("📂 Файл данных не найден, начинаем с чистого листа")
                return True

            # Читаем файл
            with open('trading_data.json', 'r', encoding='utf-8') as f:
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


# Создаем глобальный экземпляр менеджера торговли
auto_trade_manager = AutoTradeManager(bot)
# 🔼 🔼 🔼 КОНЕЦ СИСТЕМЫ АВТОМАТИЧЕСКОЙ ТОРГОВЛИ 🔼 🔼 🔼

# 🔽 🔽 🔽 ЗАГРУЖАЕМ ДАННЫЕ ПРИ ЗАПУСКЕ 🔽 🔽 🔽
auto_trade_manager.load_data()