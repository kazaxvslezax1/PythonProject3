import pandas as pd
import numpy as np
from datetime import datetime, timedelta
# Импортируем нашу функцию для расчета индикаторов
from technical_indicators import calculate_all_indicators
import math  # Для проверки на NaN, если потребуется


class AdvancedBacktester:
    def __init__(self):
        self.results = {}
        print("✅ Улучшенный бэктестер с AI фильтрами инициализирован!")

    def backtest_with_ai_filters(self, symbol, timeframe, days, min_ai_confidence, min_volume_ratio):
        """🎯 Бэктестинг с AI фильтрами - сравниваем с обычной торговлей"""
        try:
            from data import get_candles
            # Импортируем AI тут, чтобы избежать циклического импорта
            from ai_confidence_checker import ai_checker

            # 1. Рассчитываем лимит свечей в зависимости от таймфрейма
            # Карта: (Таймфрейм: Свечи в сутки)
            timeframe_map = {'15m': 96, '1h': 24, '4h': 6, '1d': 1}
            # Используем timeframe, переданный в функцию
            candles_per_day = timeframe_map.get(timeframe, 96)
            limit = days * candles_per_day

            # Получаем исторические данные
            df = get_candles(symbol, timeframe, limit=limit)

            if len(df) < 100:
                return {"error": f"Недостаточно данных для {symbol}"}
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    # errors='coerce' заменит любые нечисловые значения на NaN
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            # Добавляем индикаторы
            df = calculate_all_indicators(df)

            # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Удаляем строки, только если отсутствуют базовые данные (close) или RSI
            # Удостоверимся, что у нас есть RSI и SMA_50, так как они нужны для _simple_strategy
            required_cols = ['close', 'RSI', 'SMA_50', 'ADX']
            df = df.dropna(subset=required_cols)  # <-- НОВЫЙ МЕТОД ОЧИСТКИ

            # 🔽 ТЕСТИРУЕМ 2 ВАРИАНТА:
            # 1. Обычная торговля (без AI)
            normal_signals = self._generate_signals(df)
            normal_trades = self._simulate_trades(df, normal_signals)
            normal_stats = self._calculate_stats(normal_trades, df)

            # 2. Торговля с AI фильтрами
            # 🛑 ВНИМАНИЕ: min_ai_confidence и min_volume_ratio теперь должны быть
            # переданы при вызове backtester.backtest_with_ai_filters('ETHUSDT', '15m', 10, 5.0, 1.0)
            ai_signals = self._generate_signals_with_ai(
                df,
                symbol,
                min_ai_confidence,  # ✅ ПЕРЕДАЕМ ПАРАМЕТР AI
                min_volume_ratio  # ✅ ПЕРЕДАЕМ ПАРАМЕТР ОБЪЕМА
            )
            ai_trades = self._simulate_trades(df, ai_signals)
            ai_stats = self._calculate_stats(ai_trades, df)

            # 🔽 СТАТИСТИКА ЭФФЕКТИВНОСТИ AI
            ai_efficiency = self._calculate_ai_efficiency(normal_signals, ai_signals, df)

            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'period_days': days,

                # 📊 СРАВНЕНИЕ РЕЗУЛЬТАТОВ
                'comparison': {
                    'normal_trading': {
                        'total_trades': len(normal_trades),
                        'winning_trades': len([t for t in normal_trades if t['profit'] > 0]),
                        'losing_trades': len([t for t in normal_trades if t['profit'] <= 0]),
                        'win_rate': normal_stats['win_rate'],
                        'total_profit': normal_stats['total_profit'],
                        'avg_profit': normal_stats['avg_profit'],
                        'max_drawdown': normal_stats['max_drawdown']
                    },
                    'ai_trading': {
                        'total_trades': len(ai_trades),
                        'winning_trades': len([t for t in ai_trades if t['profit'] > 0]),
                        'losing_trades': len([t for t in ai_trades if t['profit'] <= 0]),
                        'win_rate': ai_stats['win_rate'],
                        'total_profit': ai_stats['total_profit'],
                        'avg_profit': ai_stats['avg_profit'],
                        'max_drawdown': ai_stats['max_drawdown']
                    }
                },

                # 🎯 ЭФФЕКТИВНОСТЬ AI ФИЛЬТРОВ
                'ai_efficiency': ai_efficiency,

                # 📈 ОБЩАЯ СТАТИСТИКА
                'improvement': {
                    'profit_improvement': ai_stats['total_profit'] - normal_stats['total_profit'],
                    'win_rate_improvement': ai_stats['win_rate'] - normal_stats['win_rate'],
                    'risk_reduction': normal_stats['max_drawdown'] - ai_stats['max_drawdown'],
                    'trades_filtered': len(normal_signals) - len(ai_signals)
                },

                'summary': self._generate_ai_summary(normal_stats, ai_stats, ai_efficiency)
            }

        except Exception as e:
            return {"error": f"Ошибка бэктестинга: {str(e)}"}

    def _generate_signals_with_ai(self, df, symbol, min_ai_confidence, min_volume_ratio):
        """Генерация сигналов с AI фильтрами (Использует абсолютный индекс)"""
        # Импортируем AI здесь, так как он используется только в этой функции
        try:
            from ai_confidence_checker import ai_checker
        except ImportError:
            # Если не можем импортировать, будем считать AI выключенным
            print("❌ AI_CONFIDENCE_CHECKER не найден. AI-фильтр будет выключен (min_ai_confidence=0).")
            ai_checker = None
            min_ai_confidence = 0.0

        signals = []

        # Начинаем с 1, чтобы гарантировать, что для current_index - 1 существует prev_data
        for i in range(1, len(df)):

            current_data = df.iloc[i]

            # 🔽 ОБЫЧНЫЙ СИГНАЛ
            signal = self._simple_strategy(df, i)

            if signal != 'HOLD':
                # 🔽 AI АНАЛИЗ КАЧЕСТВА СИГНАЛА

                # Безопасный расчет метрик
                volume_ratio_raw = self._calculate_volume_ratio(df, i)
                confluence_raw = self._calculate_confluence(current_data)

                # 🛑 ФИКС NAN: Заменяем NaN на безопасные значения
                volume_ratio = volume_ratio_raw if not (
                            isinstance(volume_ratio_raw, float) and math.isnan(volume_ratio_raw)) else 1.0
                confluence = confluence_raw if not (
                            isinstance(confluence_raw, float) and math.isnan(confluence_raw)) else 50.0

                ai_score = 0.0
                ai_status = signal  # Изначально статус - это сам сигнал (LONG/SHORT)

                if ai_checker:
                    ai_data = {
                        'volume_ratio': volume_ratio,
                        'confluence': confluence,
                        'current_price': float(current_data['close'])
                    }
                    try:
                        ai_result = ai_checker.analyze_signal_quality(symbol, ai_data)
                        ai_score = ai_result.get('ai_confidence_score', 0.0)
                    except Exception as e:
                        # Если AI упал (например, из-за проблем с сервером), ставим минимальный скор
                        print(f"❌ Ошибка вызова AI в {symbol} (индекс {i}): {e}. Игнорируем AI.")
                        ai_score = 0.0
                        ai_status = 'AI_ERROR'

                # 🔽 ФИЛЬТРУЕМ СИГНАЛЫ С НИЗКИМ AI или ошибкой
                if ai_score >= min_ai_confidence and volume_ratio >= min_volume_ratio and ai_status != 'AI_ERROR':

                    signals.append({
                        'index': i,
                        'timestamp': current_data.name if hasattr(current_data, 'name') else i,
                        'signal': signal,
                        'price': float(current_data['close']),
                        'ai_score': ai_score,
                        'volume_ratio': volume_ratio,
                        'confluence': confluence
                    })
                else:
                    # Сигнал отфильтрован по AI, Объему или из-за Ошибки AI
                    signals.append({
                        'index': i,
                        'timestamp': current_data.name if hasattr(current_data, 'name') else i,
                        'signal': 'FILTERED',
                        'price': float(current_data['close']),
                        'ai_score': ai_score,
                        'volume_ratio': volume_ratio,
                        'confluence': confluence
                    })

        # Возвращаем только те сигналы, которые не были FILTERED, или весь список, если вызывалось для обычного бэктеста
        return [s for s in signals if
                s['signal'] != 'FILTERED'] if min_ai_confidence > 0.0 or min_volume_ratio > 0.0 else signals

    def _calculate_volume_ratio(self, df, current_index):
        """Расчет отношения объема к среднему"""
        try:
            current_volume = float(df.iloc[current_index]['volume'])
            # Усредняем по 20 предыдущим свечам
            avg_volume = float(df.iloc[max(0, current_index - 20):current_index]['volume'].mean())
            return current_volume / avg_volume if avg_volume > 0 else 1.0
        except Exception:
            # Возвращаем np.nan при ошибке
            return np.nan

    def _calculate_confluence(self, current_data):
        """Расчет конфлюэнса индикаторов"""
        try:
            confluence_score = 0
            indicators_checked = 0

            # RSI
            if 'RSI' in current_data and not pd.isna(current_data['RSI']):
                rsi = current_data['RSI']
                if rsi < 30 or rsi > 70:  # Сильные зоны
                    confluence_score += 25
                indicators_checked += 1

            # MACD
            if ('MACD' in current_data and 'MACD_Signal' in current_data and
                    not pd.isna(current_data['MACD']) and not pd.isna(current_data['MACD_Signal'])):
                macd = current_data['MACD']
                signal = current_data['MACD_Signal']
                if (macd > signal and macd > 0) or (macd < signal and macd < 0):
                    confluence_score += 25
                indicators_checked += 1

            # Тренд
            if ('SMA_20' in current_data and 'SMA_50' in current_data and
                    not pd.isna(current_data['SMA_20']) and not pd.isna(current_data['SMA_50'])):
                sma20 = current_data['SMA_20']
                sma50 = current_data['SMA_50']
                if (sma20 > sma50 and current_data['close'] > sma20) or (
                        sma20 < sma50 and current_data['close'] < sma20):
                    confluence_score += 25
                indicators_checked += 1

            # Волатильность
            if ('BB_Upper' in current_data and 'BB_Lower' in current_data and
                    not pd.isna(current_data['BB_Upper']) and not pd.isna(current_data['BB_Lower'])):
                price = current_data['close']
                bb_upper = current_data['BB_Upper']
                bb_lower = current_data['BB_Lower']
                if price >= bb_upper or price <= bb_lower:
                    confluence_score += 25
                indicators_checked += 1

            return confluence_score if indicators_checked > 0 else 50
        except Exception:
            # Возвращаем np.nan при ошибке
            return np.nan

    def _calculate_ai_efficiency(self, normal_signals, ai_signals, df):
        """Расчет эффективности AI фильтров"""
        try:
            # Сигналы, которые AI отфильтровал (должны быть помечены как 'FILTERED')
            all_generated_signals = []

            # Находим оригинальный список сигналов (из ai_signals с учетом 'FILTERED')
            for s_norm in normal_signals:
                # В normal_signals уже нет 'FILTERED', так как _generate_signals использует ai_signals с min_ai_confidence=0,
                # но затем отфильтровывает 'FILTERED' (см. конец _generate_signals_with_ai)
                # Для корректного сравнения, нам нужно найти оригинальный список сигналов, прежде чем _generate_signals его почистит.
                # Это сложно. Лучше просто сравнить списки сделок, которые должны пройти.

                # Упрощаем: Сравниваем фактическое количество сигналов
                pass

            # Используем упрощенный подход: сравниваем количество сигналов
            signals_before_filtering = len([s for s in normal_signals if s['signal'] != 'HOLD'])
            signals_after_filtering = len([s for s in ai_signals if s['signal'] != 'HOLD'])

            # Находим общее количество отфильтрованных сигналов (за счет AI и объема)
            total_filtered = signals_before_filtering - signals_after_filtering

            # 🛑 НОВОЕ ВРЕМЕННОЕ РЕШЕНИЕ: Возвращаем более простые, но надежные метрики
            return {
                'signals_before_filtering': signals_before_filtering,
                'signals_after_filtering': signals_after_filtering,
                'signals_filtered': total_filtered,
                'bad_signals_caught': 0,  # Не можем надежно посчитать
                'filter_efficiency': 0,  # Не можем надежно посчитать
                'risk_reduction_percent': (
                            total_filtered / signals_before_filtering * 100) if signals_before_filtering > 0 else 0
            }
        except Exception as e:
            return {'error': f'AI efficiency calculation: {str(e)}'}

    def _generate_ai_summary(self, normal_stats, ai_stats, ai_efficiency):
        """Генерация сводки с AI анализом"""

        profit_improvement = ai_stats['total_profit'] - normal_stats['total_profit']
        win_rate_improvement = ai_stats['win_rate'] - normal_stats['win_rate']

        # Временное использование 0 для 'filter_efficiency', так как она была отключена
        filter_efficiency_score = ai_efficiency.get('filter_efficiency', 0)

        if profit_improvement > 10 and win_rate_improvement > 10:
            return "🚀 AI УЛУЧШАЕТ РЕЗУЛЬТАТЫ - значительное улучшение прибыли и точности!"
        elif profit_improvement > 5:
            return "✅ AI ЭФФЕКТИВЕН - улучшает прибыль и фильтрует риски"
        elif profit_improvement > 0:
            return "⚪ AI НЕМНОГО ПОМОГАЕТ - небольшое улучшение"
        else:
            return "🔴 AI НЕ ЭФФЕКТИВЕН - требует настройки"

    # 🔽 СУЩЕСТВУЮЩИЕ ФУНКЦИИ (оставляем без изменений)
    # ВНУТРИ backtester.py, в классе AdvancedBacktester

    def _generate_signals(self, df):
        """
        Унифицированный генератор сигналов для ОБЫЧНОЙ ТОРГОВЛИ.
        Вызывает _generate_signals_with_ai с НЕАКТИВНЫМИ фильтрами.
        """
        # 🛑 ВЫЗЫВАЕМ НОВЫЙ МЕТОД С ФИЛЬТРАМИ 0.0 (НЕАКТИВНЫ)
        # Используем BTCUSDT как символ по умолчанию
        return self._generate_signals_with_ai(
            df,
            'BTCUSDT',
            min_ai_confidence=0.0,  # AI отключен
            min_volume_ratio=0.0  # Объем отключен
        )

    # ВНУТРИ backtester.py, в классе AdvancedBacktester

    # ПРИБЫЛЬНАЯ СТРАТЕГИЯ: MA Crossover (10/50) - Оптимизирована для 4h.
    def _simple_strategy(self, df, current_index):
        """
        ФИНАЛЬНАЯ АВТОРСКАЯ СТРАТЕГИЯ V2: RSI Momentum Breakout + ADX Trend Filter
        """
        signal = 'HOLD'

        # Требуется: 50 периодов для SMA 50 и 14 для ADX
        if current_index < 50:
            return 'HOLD'

        current = df.iloc[current_index]
        prev = df.iloc[current_index - 1]

        # Проверяем наличие SMA_50, RSI, ADX
        required = ['SMA_50', 'RSI', 'ADX']

        if not all(ind in df.columns for ind in required) or df.iloc[current_index][required].isnull().any():
            return 'HOLD'

        # 1. ФИЛЬТР ПОЛОЖЕНИЯ: Цена не должна быть дальше 2% от SMA 50
        price_limit = current['close'] * 0.02
        is_not_far = abs(current['close'] - current['SMA_50']) < price_limit

        # 2. ТРИГГЕР: Сильный пробой импульса (RSI)
        is_rsi_breakout_long = current['RSI'] > 60 and prev['RSI'] <= 60
        is_rsi_breakout_short = current['RSI'] < 40 and prev['RSI'] >= 40

        # 3. НОВЫЙ ФИЛЬТР: Сила тренда
        is_strong_trend = current['ADX'] > 20

        # ЛОГИКА LONG: Пробой RSI И недалеко от SMA 50 И сильный АКТИВНЫЙ тренд вверх
        if (current['close'] > current['SMA_50'] and
                is_rsi_breakout_long and
                is_not_far and
                is_strong_trend):  # <--- НОВОЕ УСЛОВИЕ

            signal = 'LONG'

        # ЛОГИКА SHORT: Пробой RSI И недалеко от SMA 50 И сильный АКТИВНЫЙ тренд вниз
        elif (current['close'] < current['SMA_50'] and
              is_rsi_breakout_short and
              is_not_far and
              is_strong_trend):  # <--- НОВОЕ УСЛОВИЕ

            signal = 'SHORT'

        return signal

    def _simulate_trades(self, df, signals):
        """
        Симуляция торгов.
        ✅ ИСПРАВЛЕНИЕ 1: Добавлена проверка на NoneType при расчете RR.
        ✅ ИСПРАВЛЕНИЕ 2: Корректный расчет P&L для SHORT-сделок.
        """

        # Мы не можем импортировать DynamicRRCalculator, так как его нет в предоставленном коде,
        # поэтому я создам заглушку, чтобы код был runnable.
        class DynamicRRCalculator:
            def calculate_targets_from_signal(self, signal):
                # Заглушка: SL - 1%, TP - 2%
                entry = signal['price']
                if signal['signal'] == 'LONG':
                    stop_loss = entry * 0.99
                    take_profit = entry * 1.02
                else:  # SHORT
                    stop_loss = entry * 1.01
                    take_profit = entry * 0.98

                return {
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'rr_ratio': 2.0
                }

        # 🛑 ВРЕМЕННО ОТКЛЮЧАЕМ ФИЛЬТР RR (чтобы увидеть сделки)
        MIN_RR_RATIO = 0.01

        trades = []
        position = None

        rr_calculator = DynamicRRCalculator()

        for i, signal in enumerate(signals):
            if signal.get('signal') == 'FILTERED' or signal.get('signal') == 'AI_ERROR':
                continue

            current_idx = signal['index']
            current_price = signal['price']

            # 1. Логика открытия (включает LONG и SHORT)
            if position is None and (signal.get('signal') == 'LONG' or signal.get('signal') == 'SHORT'):

                rr_result = rr_calculator.calculate_targets_from_signal(signal)

                # ✅ НОВОЕ ИСПРАВЛЕНИЕ: Проверяем, что rr_result не None
                if rr_result is None:
                    continue  # Пропускаем сигнал, если RR-расчет не удался

                # Проверяем, соответствует ли сделка минимальному RR
                if rr_result.get('rr_ratio', 0) >= MIN_RR_RATIO:
                    position = {
                        'entry_index': current_idx,
                        'entry_price': current_price,
                        'entry_time': signal['timestamp'],
                        'stop_loss': rr_result['stop_loss'],
                        'take_profit': rr_result['take_profit'],
                        'type': signal['signal'],  # LONG или SHORT
                        'rr_ratio': rr_result['rr_ratio']
                    }

            elif position is not None:
                current_low = float(df.iloc[current_idx]['low'])
                current_high = float(df.iloc[current_idx]['high'])
                exit_reason = None
                exit_price = None
                profit = 0

                # 2. Логика выхода (унифицированная)
                if position['type'] == 'LONG':
                    if current_low <= position['stop_loss']:
                        # LONG SL: (Цена SL - Entry) / Entry * 100. Должно быть отрицательно.
                        profit = (position['stop_loss'] - position['entry_price']) / position['entry_price'] * 100
                        exit_reason = 'STOP_LOSS'
                        exit_price = position['stop_loss']
                    elif current_high >= position['take_profit']:
                        # LONG TP: (Цена TP - Entry) / Entry * 100. Должно быть положительно.
                        profit = (position['take_profit'] - position['entry_price']) / position['entry_price'] * 100
                        exit_reason = 'TAKE_PROFIT'
                        exit_price = position['take_profit']

                elif position['type'] == 'SHORT':
                    if current_high >= position['stop_loss']:  # Цена поднялась до SL
                        # SHORT SL: (Entry - Цена SL) / Entry * 100. Результат должен быть отрицательным.
                        profit = (position['entry_price'] - position['stop_loss']) / position['entry_price'] * 100

                        # ✅ ИСПРАВЛЕНИЕ P&L: Гарантируем, что убыток отрицателен
                        profit = -abs(profit)

                        exit_reason = 'STOP_LOSS'
                        exit_price = position['stop_loss']
                    elif current_low <= position['take_profit']:  # Цена упала до TP
                        # SHORT TP: (Entry - Цена TP) / Entry * 100. Результат должен быть положительным.
                        profit = (position['entry_price'] - position['take_profit']) / position['entry_price'] * 100

                        # ✅ ИСПРАВЛЕНИЕ P&L: Гарантируем, что прибыль положительна
                        profit = abs(profit)

                        exit_reason = 'TAKE_PROFIT'
                        exit_price = position['take_profit']

                # 3. Закрытие сделки, если SL/TP сработал
                if exit_reason is not None:
                    # В этом блоке оставляем ТОЛЬКО append
                    trades.append({
                        **position,
                        'exit_index': current_idx,
                        'exit_price': exit_price,
                        'exit_time': signal['timestamp'],
                        'exit_reason': exit_reason,
                        'profit': profit,
                        'bars_held': current_idx - position['entry_index']
                    })
                    position = None

                # Принудительное закрытие через 50 баров
                elif (current_idx - position['entry_index']) >= 50:
                    if position['type'] == 'LONG':
                        profit = (current_price - position['entry_price']) / position['entry_price'] * 100
                    else:  # SHORT
                        profit = (position['entry_price'] - current_price) / position['entry_price'] * 100

                    trades.append({
                        **position,
                        'exit_index': current_idx,
                        'exit_price': current_price,
                        'exit_time': signal['timestamp'],
                        'exit_reason': 'TIME_EXIT',
                        'profit': profit,
                        'bars_held': current_idx - position['entry_index']
                    })
                    position = None

        return trades

    def _calculate_stats(self, trades, df):
        """Расчет статистики (безопасный фикс для Max Drawdown)"""
        if not trades:
            return {
                'win_rate': 0,
                'total_profit': 0,
                'avg_profit': 0,
                'max_drawdown': 0,
                'profit_factor': 0,
                'sharpe_ratio': 0
            }

        profits = [t['profit'] for t in trades]
        winning_trades = [p for p in profits if p > 0]
        losing_trades = [p for p in profits if p <= 0]

        total_profit = sum(profits)
        win_rate = len(winning_trades) / len(profits) * 100

        # 🛑 ИСПРАВЛЕНИЕ MAX DRAWDOWN (Безопасный расчет на основе абсолютного капитала)
        equity_curve = np.cumsum(profits)

        # 1. Преобразуем кумулятивную % прибыль в абсолютный капитал (начиная с 1.0)
        # Если прибыль = 10%, капитал = 1.10. Если прибыль = -10%, капитал = 0.90.
        equity_curve_abs = 1.0 + (equity_curve / 100)

        # 2. Находим максимально достигнутое значение капитала
        running_max = np.maximum.accumulate(equity_curve_abs)

        # 3. Просадка: разница между максимумом и текущим капиталом, выраженная в % от максимума
        # Формула: (Макс. Капитал - Текущий Капитал) / Макс. Капитал * 100
        drawdowns = (running_max - equity_curve_abs) / running_max * 100
        max_drawdown = abs(max(drawdowns)) if len(drawdowns) > 0 else 0

        # Оставляем остальные расчеты как есть
        gross_profit = sum(winning_trades) if winning_trades else 0
        gross_loss = abs(sum(losing_trades)) if losing_trades else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        avg_profit = np.mean(profits) if profits else 0
        std_profit = np.std(profits) if profits else 1
        sharpe_ratio = avg_profit / std_profit if std_profit > 0 else 0

        return {
            'win_rate': round(win_rate, 1),
            'total_profit': round(total_profit, 2),
            'avg_profit': round(avg_profit, 2),
            'max_drawdown': round(max_drawdown, 2),  # Теперь это правильное значение
            'profit_factor': round(profit_factor, 2),
            'sharpe_ratio': round(sharpe_ratio, 2)
        }


# 🔽 ОБНОВЛЯЕМ ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
backtester = AdvancedBacktester()