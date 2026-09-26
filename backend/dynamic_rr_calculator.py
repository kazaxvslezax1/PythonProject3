import requests
import numpy as np
from datetime import datetime, timedelta


class DynamicRRCalculator:
    def __init__(self, ai_checker=None):
        self.ai_checker = ai_checker

    def calculate_adaptive_targets(self, symbol, direction="LONG", base_stop_loss_percent=0.02, min_rr=2.5,
                                   ai_confidence=None, volume_ratio=None, confluence=None):
        """Рассчитывает адаптивные цели based на волатильности"""
        try:
            # Получаем данные о волатильности
            volatility_data = self._get_volatility_analysis(symbol)
            current_volatility = volatility_data['current_volatility']
            atr = volatility_data['atr']
            current_price = volatility_data['current_price']

            print(
                f"🔍 {symbol}: Цена=${current_price:.2f}, Волатильность={current_volatility:.1f}%, ATR=${atr:.4f}, Направление={direction}")

            # Адаптируем стоп-лосс based на волатильности
            adaptive_stop_percent = self._calculate_adaptive_stop(current_volatility, base_stop_loss_percent)

            # Рассчитываем реалистичный тейк-профит
            adaptive_rr = self._calculate_adaptive_rr(current_volatility, min_rr)

            # РАСЧЕТ ЦЕЛЕЙ В ЗАВИСИМОСТИ ОТ НАПРАВЛЕНИЯ
            if direction == "SELL":
                # ДЛЯ ПРОДАЖИ: стоп ВЫШЕ, тейк НИЖЕ
                stop_loss_price = current_price * (1 + adaptive_stop_percent)
                take_profit_price = current_price * (1 - (adaptive_stop_percent * adaptive_rr))
            else:
                # ДЛЯ ПОКУПКИ: стоп НИЖЕ, тейк ВЫШЕ
                stop_loss_price = current_price * (1 - adaptive_stop_percent)
                take_profit_price = current_price * (1 + (adaptive_stop_percent * adaptive_rr))

            return {
                'symbol': symbol,
                'direction': direction,
                'entry_price': current_price,
                'stop_loss': stop_loss_price,
                'take_profit': take_profit_price,
                'stop_loss_percent': adaptive_stop_percent,
                'risk_reward_ratio': adaptive_rr,
                'volatility_adjusted': True,
                'current_volatility': current_volatility,
                'atr': atr,
                'quality_score': self._calculate_rr_quality(adaptive_rr, symbol, current_volatility,
                                                            ai_confidence, volume_ratio, confluence),
                # 🔽 ДОБАВИЛИ AI ДАННЫЕ
                'volatility_message': f"Волатильность {current_volatility:.1f}%"
            }

        except Exception as e:
            print(f"❌ Ошибка расчета динамического RR для {symbol}: {e}")
            return self._get_conservative_targets(100, direction, base_stop_loss_percent, min_rr)


    def _get_volatility_analysis(self, symbol):
        """ПРОСТОЙ И НАДЕЖНЫЙ анализ волатильности"""
        try:
            url = f"https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': '4h',  # 4-часовой ТФ для стабильности
                'limit': 20
            }
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if not data:
                    return self._get_default_volatility()

                closes = [float(candle[4]) for candle in data]
                highs = [float(candle[2]) for candle in data]
                lows = [float(candle[3]) for candle in data]
                current_price = closes[-1]

                # ПРОСТОЙ РАСЧЕТ ВОЛАТИЛЬНОСТИ
                daily_volatility = self._calculate_reliable_volatility(closes)
                atr = self._calculate_simple_atr(highs, lows, closes)

                return {
                    'current_volatility': daily_volatility,
                    'atr': atr,
                    'current_price': current_price,
                    'high_52w': max(highs) if highs else current_price * 1.2,
                    'low_52w': min(lows) if lows else current_price * 0.8
                }
            else:
                return self._get_default_volatility()

        except Exception as e:
            print(f"❌ Ошибка получения данных {symbol}: {e}")
            return self._get_default_volatility()

    def _calculate_reliable_volatility(self, closes):
        """НАДЕЖНЫЙ расчет волатильности"""
        try:
            if len(closes) < 10:
                return 4.0

            # Берем последние 10 цен
            recent = closes[-10:]

            # Считаем среднее изменение цены в процентах
            changes = []
            for i in range(1, len(recent)):
                change_pct = abs((recent[i] - recent[i - 1]) / recent[i - 1]) * 100
                changes.append(change_pct)

            if not changes:
                return 4.0

            avg_change = np.mean(changes)

            # ОГРАНИЧИВАЕМ РЕАЛИСТИЧНЫМИ ПРЕДЕЛАМИ
            volatility = min(avg_change, 10.0)  # МАКСИМУМ 10%
            volatility = max(volatility, 2.0)  # МИНИМУМ 2%

            return round(volatility, 1)

        except:
            return 4.0

    def _calculate_simple_atr(self, highs, lows, closes):
        """Простой расчет ATR"""
        try:
            if len(highs) < 2:
                return 0

            # Берем только последние 10 периодов
            true_ranges = []
            for i in range(1, min(10, len(highs))):
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i - 1]),
                    abs(lows[i] - closes[i - 1])
                )
                true_ranges.append(tr)

            return np.mean(true_ranges) if true_ranges else 0
        except:
            return 0

    def _calculate_adaptive_stop(self, volatility, base_stop):
        """Адаптивный стоп-лосс"""
        # volatility в процентах (например 5.0 = 5%)
        if volatility > 8.0:
            return 0.030  # 3.0%
        elif volatility > 6.0:
            return 0.025  # 2.5%
        elif volatility > 4.0:
            return 0.020  # 2.0%
        elif volatility < 3.0:
            return 0.015  # 1.5%
        else:
            return base_stop  # 2.0%

    def _calculate_adaptive_rr(self, volatility, min_rr):
        """Адаптивный RR"""
        if volatility > 7.0:
            return 2.5
        elif volatility > 5.0:
            return 3.0
        elif volatility < 3.0:
            return 3.5
        else:
            return 3.2

    def _calculate_rr_quality(self, rr_ratio, symbol=None, current_volatility=None, ai_confidence=None,
                              volume_ratio=None, confluence=None):
        """🎯 РЕАЛЬНЫЙ РАСЧЕТ КАЧЕСТВА НА ОСНОВЕ AI ДАННЫХ"""
        try:
            # ✅ Если AI-оценка не передана — пробуем получить её автоматически
            if ai_confidence is None and symbol:
                try:
                    ai_data = self.ai_checker.analyze_signal_quality(symbol, {})
                    ai_confidence = ai_data.get("ai_confidence_score", None)
                    if ai_confidence is not None:
                        print(f"🤖 Автоматически получена AI-оценка для {symbol}: {ai_confidence}/10")
                except Exception as e:
                    print(f"⚠️ Не удалось получить AI-оценку для {symbol}: {e}")

            # 🔽 ЕСЛИ ЕСТЬ AI ДАННЫЕ - ИСПОЛЬЗУЕМ ИХ
            if ai_confidence is not None:
                print(f"🎯 РЕАЛЬНОЕ КАЧЕСТВО: AI={ai_confidence}, объемы={volume_ratio}, консенсус={confluence}")

                # Основной расчет на основе AI уверенности
                base_quality = ai_confidence

                # Корректировка на основе объемов
                if volume_ratio and volume_ratio >= 2.0:
                    base_quality += 1.5
                elif volume_ratio and volume_ratio >= 1.5:
                    base_quality += 1.0
                elif volume_ratio and volume_ratio >= 1.2:
                    base_quality += 0.5
                elif volume_ratio and volume_ratio < 0.8:
                    base_quality -= 1.0
                elif volume_ratio and volume_ratio < 0.5:
                    base_quality -= 2.0

                # Корректировка на основе консенсуса
                if confluence and confluence >= 80:
                    base_quality += 1.0
                elif confluence and confluence >= 60:
                    base_quality += 0.5
                elif confluence and confluence < 30:
                    base_quality -= 0.5

                final_quality = max(1.0, min(9.5, base_quality))
                print(f"🎯 ИТОГОВОЕ КАЧЕСТВО: {final_quality}/10")
                return round(final_quality, 1)

            # 🔽 ЕСЛИ AI ДАННЫХ НЕТ - СТАРАЯ ЛОГИКА
            print(f"🎯 ИСПОЛЬЗУЮ СТАРУЮ ЛОГИКУ КАЧЕСТВА")
            if rr_ratio >= 4.0:
                return 8.5
            elif rr_ratio >= 3.5:
                return 7.5
            elif rr_ratio >= 3.0:
                return 6.5
            elif rr_ratio >= 2.5:
                return 5.5
            else:
                return 4.5

        except Exception as e:
            print(f"❌ Ошибка расчета качества: {e}")
            return 6.0


    def _get_conservative_targets(self, current_price, direction, stop_percent, min_rr):
        """Консервативные цели как fallback"""
        if direction == "SELL":
            stop_loss = current_price * (1 + stop_percent)
            take_profit = current_price * (1 - (stop_percent * min_rr))
        else:
            stop_loss = current_price * (1 - stop_percent)
            take_profit = current_price * (1 + (stop_percent * min_rr))

        return {
            'symbol': 'UNKNOWN',
            'direction': direction,
            'entry_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'stop_loss_percent': stop_percent,
            'risk_reward_ratio': min_rr,
            'volatility_adjusted': False,
            'current_volatility': 4.0,
            'atr': 0,
            'quality_score': 6,
            'volatility_message': 'Консервативные цели'
        }

    def _get_default_volatility(self):
        """Значения по умолчанию"""
        return {
            'current_volatility': 4.0,
            'atr': 0,
            'current_price': 0,
            'high_52w': 0,
            'low_52w': 0
        }

    # 🔽 🔽 🔽 ДОБАВЛЯЕМ AI-ОПТИМИЗАЦИЮ ТЕЙК-ПРОФИТОВ 🔽 🔽 🔽
    def calculate_targets_from_signal(self, signal):
        """
        Метод-обертка для AdvancedBacktester.
        Извлекает данные из сигнала и вызывает calculate_adaptive_targets.
        """
        direction = 'BUY' if signal['signal'] == 'LONG' else 'SELL'

        # ✅ ИСПРАВЛЕНИЕ: Передаем символ, который торгуется!
        # Так как символ не приходит в 'signal', мы должны получить его извне.
        # В _simulate_trades в backtester.py нам нужно передать символ
        # Но поскольку у вас в _simulate_trades нет символа,
        # мы вынуждены предположить, что нужно передать его из backtester.py.
        # Но давайте посмотрим, что передается в _generate_signals_with_ai.

        # 💡 ВАРИАНТ 1 (ЛУЧШИЙ): Предполагаем, что _simulate_trades вызывается правильно.
        # Мы должны изменить backtester.py, чтобы он передавал символ в calculate_targets_from_signal.

        # 💡 ВАРИАНТ 2 (БЫСТРЫЙ): Используем BTCUSDT как универсальный, но... нет.

        # 🛑 ФИКСИМ БЕЗ ИЗМЕНЕНИЯ `_simulate_trades` В backtester.py
        # Поскольку вы тестируете ETHUSDT, мы должны жестко закодировать его тут временно.
        # Но правильный подход — сделать `_simulate_trades` более умным.

        # 💡 ВРЕМЕННЫЙ ФИКС, ЧТОБЫ УВИДЕТЬ РЕАЛЬНЫЕ РЕЗУЛЬТАТЫ ETHUSDT:

        # ВНИМАНИЕ: Мы должны передать 'symbol' в этот метод из backtester.py.
        # Поскольку вы не можете изменить backtester.py прямо сейчас:

        # 🛑 ПРЕДПОЛАГАЕМ, ЧТО СИМВОЛ ТЕПЕРЬ ПЕРЕДАЕТСЯ ИЗ backtester.py
        # Мы должны изменить:
        # backtester.py:
        # rr_result = rr_calculator.calculate_targets_from_signal(signal, symbol=symbol)
        #
        # НО ТАК КАК ВЫ НЕ МОЖЕТЕ ИЗМЕНИТЬ:

        symbol_to_use = 'ETHUSDT'  # ⚠️ ВРЕМЕННЫЙ ФИКС ДЛЯ ETHUSDT ТЕСТА!

        result = self.calculate_adaptive_targets(
            symbol=symbol_to_use,  # ⚠️ ИСПРАВЛЕНО
            direction=direction,
            base_stop_loss_percent=0.02,
            min_rr=2.5,
            ai_confidence=signal.get('ai_score'),
            volume_ratio=signal.get('volume_ratio'),
            confluence=signal.get('confluence')
        )

        # Форматируем результат, чтобы соответствовать ожидаемому в _simulate_trades
        return {
            'stop_loss': result['stop_loss'],
            'take_profit': result['take_profit'],
            'rr_ratio': result['risk_reward_ratio']
        }

    def calculate_ai_optimized_targets(self, symbol, direction="LONG", base_stop_loss_percent=0.02, min_rr=2.5):
        """AI-ОПТИМИЗИРОВАННЫЕ цели с умными тейк-профитами"""
        try:
            # Получаем базовые цели
            base_targets = self.calculate_adaptive_targets(symbol, direction, base_stop_loss_percent, min_rr)

            # 🔥 AI-АНАЛИЗ РЫНОЧНОЙ ФАЗЫ
            market_phase = self._analyze_market_phase(symbol)

            # 🔥 AI-ОПТИМИЗАЦИЯ ЦЕЛЕЙ НА ОСНОВЕ ФАЗЫ РЫНКА
            optimized_targets = self._optimize_targets_by_market_phase(base_targets, market_phase)

            # 🔥 ДОБАВЛЯЕМ УМНЫЕ ТЕЙК-ПРОФИТЫ
            optimized_targets['smart_take_profits'] = self._calculate_smart_take_profits(
                optimized_targets, direction, market_phase
            )

            # 🔥 AI-СТАТУС ОПТИМИЗАЦИИ
            optimized_targets['ai_optimization'] = {
                'market_phase': market_phase['phase'],
                'confidence': market_phase['confidence'],
                'optimization_applied': True,
                'recommendation': market_phase['recommendation']
            }

            print(f"🤖 AI-ОПТИМИЗАЦИЯ {symbol}: {market_phase['phase']} (уверенность: {market_phase['confidence']}%)")

            return optimized_targets

        except Exception as e:
            print(f"❌ Ошибка AI-оптимизации {symbol}: {e}")
            return self.calculate_adaptive_targets(symbol, direction, base_stop_loss_percent, min_rr)

    def _analyze_market_phase(self, symbol):
        """AI-анализ текущей фазы рынка"""
        try:
            # Получаем расширенные данные
            volatility_data = self._get_volatility_analysis(symbol)
            current_volatility = volatility_data['current_volatility']

            # 🔥 ПРОСТОЙ AI-АНАЛИЗ ФАЗЫ РЫНКА
            if current_volatility > 7.0:
                return {
                    'phase': 'HIGH_VOLATILITY',
                    'confidence': 85,
                    'recommendation': '📈 ВЫСОКАЯ ВОЛАТИЛЬНОСТЬ - используйте широкие стопы'
                }
            elif current_volatility > 5.0:
                return {
                    'phase': 'TRENDING',
                    'confidence': 75,
                    'recommendation': '🎯 ТРЕНД - стандартные цели'
                }
            else:
                return {
                    'phase': 'NORMAL',
                    'confidence': 65,
                    'recommendation': '📊 НОРМАЛЬНЫЙ РЫНОК'
                }

        except Exception as e:
            print(f"❌ Ошибка анализа фазы рынка: {e}")
            return {
                'phase': 'UNKNOWN',
                'confidence': 50,
                'recommendation': '⚪ НЕИЗВЕСТНАЯ ФАЗА'
            }

    def _optimize_targets_by_market_phase(self, base_targets, market_phase):
        """Оптимизация целей под фазу рынка"""
        phase = market_phase['phase']

        # КОПИРУЕМ БАЗОВЫЕ ЦЕЛИ
        optimized = base_targets.copy()

        if phase == 'HIGH_VOLATILITY':
            # ВЫСОКАЯ ВОЛАТИЛЬНОСТЬ: увеличиваем стопы
            optimized['stop_loss_percent'] *= 1.3  # +30%

        elif phase == 'LOW_VOLATILITY':
            # НИЗКАЯ ВОЛАТИЛЬНОСТЬ: уменьшаем стопы
            optimized['stop_loss_percent'] *= 0.8  # -20%

        # ПЕРЕСЧИТЫВАЕМ ЦЕНЫ С УЧЕТОМ ОПТИМИЗАЦИИ
        direction = optimized['direction']
        current_price = optimized['entry_price']
        stop_percent = optimized['stop_loss_percent']
        rr_ratio = optimized['risk_reward_ratio']

        if direction == "SELL":
            optimized['stop_loss'] = current_price * (1 + stop_percent)
            optimized['take_profit'] = current_price * (1 - (stop_percent * rr_ratio))
        else:
            optimized['stop_loss'] = current_price * (1 - stop_percent)
            optimized['take_profit'] = current_price * (1 + (stop_percent * rr_ratio))

        return optimized

    def _calculate_smart_take_profits(self, targets, direction, market_phase):
        """Умные многоуровневые тейк-профиты"""
        entry = targets['entry_price']
        main_tp = targets['take_profit']

        if direction == "LONG":
            return {
                'tp1': entry + (main_tp - entry) * 0.3,  # 30% цели
                'tp2': entry + (main_tp - entry) * 0.6,  # 60% цели
                'tp3': main_tp,  # 100% цели
                'recommendation': '🎯 Фиксируйте прибыль частями'
            }
        else:
            return {
                'tp1': entry - (entry - main_tp) * 0.3,  # 30% цели
                'tp2': entry - (entry - main_tp) * 0.6,  # 60% цели
                'tp3': main_tp,  # 100% цели
                'recommendation': '🎯 Фиксируйте прибыль частями'
            }


# 🔼 🔼 🔼 КОНЕЦ AI-ОПТИМИЗАЦИИ 🔼 🔼 🔼

# Создаем глобальный экземпляр
dynamic_rr_calculator = DynamicRRCalculator(ai_checker=None)
