import json
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import io


class PredictionHistory:
    def __init__(self):
        self.history_file = 'prediction_history.json'
        self.load_history()

    def load_history(self):
        """Загружает историю из файла"""
        try:
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)
        except:
            self.history = {}

    def save_history(self):
        """Сохраняет историю в файл"""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2, default=str)

    def add_prediction(self, symbol, prediction_data):
        """Добавляет прогноз в историю"""
        if symbol not in self.history:
            self.history[symbol] = []

        self.history[symbol].append({
            'timestamp': datetime.now().isoformat(),
            'prediction': prediction_data['prediction'],
            'confidence': prediction_data['confidence'],
            'actual_price': prediction_data['current_price'],
            'timeframe': prediction_data.get('timeframe', '1h')
        })

        # Ограничиваем историю
        if len(self.history[symbol]) > 50:
            self.history[symbol] = self.history[symbol][-50:]

        self.save_history()

    def get_accuracy(self, symbol):
        """Рассчитывает точность прогнозов"""
        if symbol not in self.history or len(self.history[symbol]) < 5:
            return "Недостаточно данных"

        predictions = self.history[symbol]
        correct = 0

        for i in range(1, len(predictions)):
            prev = predictions[i - 1]
            curr = predictions[i]

            # Простая проверка направления
            if 'РОСТ' in prev['prediction'] and curr['actual_price'] > prev['actual_price']:
                correct += 1
            elif 'ПАДЕНИЕ' in prev['prediction'] and curr['actual_price'] < prev['actual_price']:
                correct += 1

        accuracy = (correct / (len(predictions) - 1)) * 100
        return f"{accuracy:.1f}%"

    def generate_history_chart(self, symbol):
        """Генерирует график истории прогнозов"""
        if symbol not in self.history:
            return None

        df = pd.DataFrame(self.history[symbol])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['actual_price'] = pd.to_numeric(df['actual_price'])

        plt.figure(figsize=(10, 6))
        plt.plot(df['timestamp'], df['actual_price'], marker='o', linewidth=2)
        plt.title(f'История цен и прогнозов для {symbol}')
        plt.ylabel('Цена (USDT)')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=80, bbox_inches='tight')
        buf.seek(0)
        plt.close()

        return buf


# Глобальный экземпляр
prediction_history = PredictionHistory()