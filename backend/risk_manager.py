import requests

class RiskManager:
    def __init__(self):
        self.max_risk_per_trade = 0.02  # 2% максимальный риск на сделку
        self.risk_levels = {
            1: 0.05,  # 5% для низкого риска
            2: 0.03,  # 3% для среднего риска
            3: 0.02,  # 2% для высокого риска
            4: 0.01,  # 1% для очень высокого риска
            5: 0.005  # 0.5% для экстремального риска
        }

    def calculate_position_size(self, symbol_data, account_balance, stop_loss_percent):
        """Расчет размера позиции"""
        risk_score = symbol_data.get('risk_score', 3)
        risk_percent = self.risk_levels.get(risk_score, 0.02)

        # Ограничиваем риск
        risk_percent = min(risk_percent, self.max_risk_per_trade)

        # Расчет размера позиции
        risk_amount = account_balance * risk_percent
        position_size = risk_amount / (stop_loss_percent / 100)

        return {
            'position_size_usd': round(position_size, 2),
            'risk_amount_usd': round(risk_amount, 2),
            'risk_percent': risk_percent * 100,
            'leverage_suggestion': self._suggest_leverage(stop_loss_percent)
        }

    def _suggest_leverage(self, stop_loss_percent):
        """Рекомендация по кредитному плечу"""
        if stop_loss_percent <= 1:
            return "10x-20x"
        elif stop_loss_percent <= 2:
            return "5x-10x"
        elif stop_loss_percent <= 5:
            return "3x-5x"
        else:
            return "1x-3x"

    def get_latest_price(self, symbol):
        """Получает последнюю цену монеты с биржи Binance"""
        try:
            # ИСПОЛЬЗУЕМ API БИНАНСА (самый распространенный)
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()  # Вызывает исключение для плохих ответов
            data = response.json()

            # Возвращаем цену в виде числа (float)
            return float(data['price'])

        except requests.exceptions.RequestException as e:
            # Если запрос не удался (нет интернета, таймаут и т.п.)
            print(f"❌ Ошибка получения цены для {symbol}: {e}")
            return 0.0  # Возвращаем 0.0, чтобы не сломать бота
        except Exception as e:
            print(f"❌ Неизвестная ошибка получения цены: {e}")
            return 0.0


    def portfolio_risk_assessment(self, positions):
        """Оценка риска портфеля"""
        total_risk = sum(pos.get('risk_percent', 0) for pos in positions)

        if total_risk > 10:
            risk_status = "🔴 ВЫСОКИЙ РИСК"
        elif total_risk > 5:
            risk_status = "🟡 СРЕДНИЙ РИСК"
        else:
            risk_status = "🟢 НИЗКИЙ РИСК"

        return {
            'total_risk_percent': round(total_risk, 2),
            'risk_status': risk_status,
            'recommendation': self._get_portfolio_recommendation(total_risk)
        }

    def _get_portfolio_recommendation(self, total_risk):
        """Рекомендации по управлению портфелем"""
        if total_risk > 15:
            return "СРОЧНО УМЕНЬШИТЕ ПОЗИЦИИ! Риск слишком высок"
        elif total_risk > 10:
            return "Рассмотрите уменьшение позиций"
        elif total_risk > 5:
            return "Риск в допустимых пределах"
        else:
            return "Риск оптимальный"

    def calculate_drawdown_limits(self, account_balance):
        """Расчет лимитов просадки"""
        return {
            'warning_level': account_balance * 0.9,  # -10%
            'stop_level': account_balance * 0.8,  # -20%
            'max_drawdown_percent': 20
        }


# Глобальный экземпляр
risk_manager = RiskManager()

