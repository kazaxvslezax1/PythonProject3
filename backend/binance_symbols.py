import requests
import json
from datetime import datetime


def get_all_usdt_pairs():
    """Получает все доступные пары USDT с Binance"""
    try:
        print("🔄 Получаю список всех пар с Binance...")
        response = requests.get('https://api.binance.com/api/v3/exchangeInfo', timeout=10)

        if response.status_code == 200:
            data = response.json()
            usdt_pairs = []

            for symbol_info in data['symbols']:
                symbol = symbol_info['symbol']
                status = symbol_info['status']

                # Берем только USDT пары которые сейчас торгуются
                if symbol.endswith('USDT') and status == 'TRADING':
                    usdt_pairs.append(symbol)

            print(f"✅ Найдено {len(usdt_pairs)} торговых пар USDT")
            return sorted(usdt_pairs)

        else:
            print(f"❌ Ошибка: {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []


# Запускаем получение символов
if __name__ == "__main__":
    symbols = get_all_usdt_pairs()
    if symbols:
        print(f"📊 Примеры: {symbols[:10]}...")
        print(f"💾 Сохраняю в файл...")

        # Сохраняем в файл
        with open("all_usdt_pairs.json", "w") as f:
            json.dump(symbols, f)
        print("✅ Готово! Файл all_usdt_pairs.json создан")