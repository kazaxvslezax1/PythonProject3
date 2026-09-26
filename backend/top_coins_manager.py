# top_coins_manager.py
import requests
import json
from datetime import datetime, timedelta


class TopCoinsManager:
    def __init__(self):
        self.top_symbols = []
        self.last_update = None
        self.update_interval = timedelta(hours=6)

    def get_top_coins_by_marketcap(self, limit=100):
        """Получает топ монет по рыночной капитализации + мемкоины с Bybit"""
        try:
            if (self.last_update and
                    datetime.now() - self.last_update < self.update_interval and
                    self.top_symbols):
                return self.top_symbols[:limit]

            print("🔄 Обновляю список топ-монет...")

            # 1. Получаем монеты с CoinGecko
            response = requests.get(
                "https://api.coingecko.com/api/v3/coins/markets",
                params={
                    'vs_currency': 'usd',
                    'order': 'market_cap_desc',
                    'per_page': limit,
                    'page': 1,
                    'sparkline': 'false'
                },
                timeout=10
            )

            top_symbols = []

            if response.status_code == 200:
                coins_data = response.json()
                for coin in coins_data:
                    symbol = coin['symbol'].upper() + 'USDT'
                    top_symbols.append(symbol)

            # 2. 🔽 🔽 🔽 ДОБАВЛЯЕМ МЕМКОИНЫ С BYBIT 🔽 🔽 🔽
            try:
                print("🔍 Добавляю мемкоины с Bybit...")
                bybit_response = requests.get(
                    "https://api.bybit.com/v5/market/tickers?category=spot",
                    timeout=10
                )

                if bybit_response.status_code == 200:
                    bybit_data = bybit_response.json()

                    # 🔽 🔽 🔽 ИСПРАВЛЕННЫЙ СПИСОК МЕМКОИНОВ 🔽 🔽 🔽
                    # Проверяем реальные названия на Bybit
                    memecoins_to_check = [
                        'PEPE', 'FLOKI', 'BONK', 'WIF', 'BOME', 'MEME',
                        'LUNC', 'LUNA', 'DOGE', 'SHIB'
                    ]

                    # Получаем все символы с Bybit
                    all_bybit_symbols = [item['symbol'] for item in bybit_data['result']['list']]
                    print(f"📊 Найдено символов на Bybit: {len(all_bybit_symbols)}")

                    # Ищем реальные названия мемкоинов
                    added_memecoins = []
                    for memecoin in memecoins_to_check:
                        # Пробуем разные варианты названий
                        possible_names = [
                            f"{memecoin}USDT",  # PEPEUSDT
                            f"{memecoin}USDT",  # DOGEUSDT
                        ]

                        for name in possible_names:
                            if name in all_bybit_symbols and name not in top_symbols:
                                top_symbols.append(name)
                                added_memecoins.append(name)
                                print(f"✅ Добавлен мемкоин: {name}")
                                break

                    print(f"🎯 Добавлено мемкоинов: {len(added_memecoins)}")

            except Exception as bybit_error:
                print(f"⚠️ Не удалось добавить мемкоины с Bybit: {bybit_error}")



            # 3. 🔽 🔽 🔽 ДОБАВЛЯЕМ ПОПУЛЯРНЫЕ АЛЬТКОИНЫ 🔽 🔽 🔽
            popular_altcoins = [
                'ADAUSDT', 'DOTUSDT', 'LINKUSDT', 'MATICUSDT', 'AVAXUSDT',
                'ATOMUSDT', 'NEARUSDT', 'ALGOUSDT', 'ETCUSDT', 'XLMUSDT',
                'ARBUSDT', 'OPUSDT', 'SUIUSDT', 'SEIUSDT', 'APTUSDT'
            ]

            for altcoin in popular_altcoins:
                if altcoin not in top_symbols:
                    top_symbols.append(altcoin)

            # Сохраняем обновленный список
            self.top_symbols = top_symbols
            self.last_update = datetime.now()

            print(f"✅ Обновлен список монет: {len(top_symbols)} монет (включая мемкоины)")
            return top_symbols[:limit]

        except Exception as e:
            print(f"❌ Ошибка получения топ-монет: {e}")
            return self._get_fallback_top_coins(limit)



    def _get_fallback_top_coins(self, limit=100):
        """Запасной список топ-монет если API не работает"""
        fallback_top = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT",
            "AVAXUSDT", "DOGEUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT", "LINKUSDT",
            "ATOMUSDT", "UNIUSDT", "XLMUSDT", "ALGOUSDT", "TRXUSDT", "XMRUSDT",
            "ETCUSDT", "FILUSDT", "AAVEUSDT", "EOSUSDT", "XTZUSDT", "SANDUSDT",
            "MANAUSDT", "THETAUSDT", "EGLDUSDT", "FTMUSDT", "NEARUSDT", "GRTUSDT"
        ]
        return fallback_top[:limit]

    def get_popular_trading_pairs(self, limit=50):
        """Получает популярные торговые пары"""
        return self.get_top_coins_by_marketcap(limit)


# Создаем глобальный экземпляр
top_coins_manager = TopCoinsManager()