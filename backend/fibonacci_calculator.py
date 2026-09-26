# fibonacci_calculator.py
import requests
import numpy as np
from datetime import datetime, timedelta


class FibonacciCalculator:
    def __init__(self):
        self.fib_levels = {
            '0.0': 0.0,
            '0.236': 0.236,
            '0.382': 0.382,
            '0.5': 0.5,
            '0.618': 0.618,
            '0.786': 0.786,
            '1.0': 1.0,
            '1.272': 1.272,
            '1.414': 1.414,
            '1.618': 1.618
        }

    def calculate_fib_levels(self, high, low, direction="LONG"):
        """Расчет уровней Фибоначчи"""
        diff = high - low

        levels = {}
        for name, level in self.fib_levels.items():
            if direction == "LONG":
                price_level = high - (diff * level)
            else:  # SHORT
                price_level = low + (diff * level)
            levels[name] = round(price_level, 4)

        return levels

    def get_support_resistance(self, symbol, period=30):
        """Находит ключевые уровни поддержки/сопротивления"""
        try:
            # Получаем исторические данные
            response = requests.get(
                f"https://api.binance.com/api/v3/klines",
                params={
                    'symbol': symbol,
                    'interval': '1d',
                    'limit': period
                }
            )

            if response.status_code == 200:
                data = response.json()
                highs = [float(candle[2]) for candle in data]  # High prices
                lows = [float(candle[3]) for candle in data]  # Low prices

                # Находим ключевые уровни (округленные)
                key_levels = set()
                for i in range(len(highs)):
                    key_levels.add(round(highs[i], -1))  # Округляем до десятков
                    key_levels.add(round(lows[i], -1))

                return sorted(list(key_levels))

        except Exception as e:
            print(f"Ошибка получения уровней для {symbol}: {e}")

        return []


# Создаем глобальный экземпляр
fib_calculator = FibonacciCalculator()