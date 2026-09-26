import matplotlib.pyplot as plt
import pandas as pd
import io
import os
from datetime import datetime
import mplfinance as mpf


def generate_price_chart(df, symbol, timeframe):
    """Генерирует красивый график цен"""
    try:
        # Создаем временную папку для графиков
        if not os.path.exists('charts'):
            os.makedirs('charts')

        # Настраиваем стиль
        plt.style.use('dark_background')

        # Создаем свечной график
        fig, axes = plt.subplots(2, 1, figsize=(12, 10),
                                 gridspec_kw={'height_ratios': [3, 1]})

        # Верхний график - свечи
        dates = pd.to_datetime(df['time'])
        prices = df[['open', 'high', 'low', 'close']].astype(float)

        # Рисуем свечи
        for i in range(len(df)):
            open_price = prices['open'].iloc[i]
            close_price = prices['close'].iloc[i]
            high_price = prices['high'].iloc[i]
            low_price = prices['low'].iloc[i]
            date = dates.iloc[i]

            # Цвет свечи
            color = 'green' if close_price > open_price else 'red'

            # Тело свечи
            axes[0].plot([date, date], [open_price, close_price],
                         color=color, linewidth=6, solid_capstyle='round')

            # Тени
            axes[0].plot([date, date], [high_price, low_price],
                         color=color, linewidth=1)

        # Добавляем скользящие средние
        df['SMA_20'] = df['close'].rolling(window=20).mean()
        df['SMA_50'] = df['close'].rolling(window=50).mean()

        axes[0].plot(dates, df['SMA_20'], 'orange', linewidth=1, label='SMA 20')
        axes[0].plot(dates, df['SMA_50'], 'purple', linewidth=1, label='SMA 50')

        # Настройки верхнего графика
        axes[0].set_title(f'{symbol.upper()} Price Chart - {timeframe.upper()}',
                          fontsize=16, fontweight='bold', color='white')
        axes[0].set_ylabel('Price (USDT)', fontsize=12)
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Нижний график - объемы
        volumes = df['volume'].astype(float)
        colors = ['green' if prices['close'].iloc[i] > prices['open'].iloc[i]
                  else 'red' for i in range(len(df))]

        axes[1].bar(dates, volumes, color=colors, alpha=0.7)
        axes[1].set_ylabel('Volume', fontsize=12)
        axes[1].grid(True, alpha=0.3)

        # Форматируем даты
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Сохраняем график
        filename = f'charts/{symbol}_{timeframe}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        plt.savefig(filename, dpi=100, bbox_inches='tight')
        plt.close()

        return filename

    except Exception as e:
        print(f"❌ Ошибка создания графика: {e}")
        return None


def generate_simple_chart(df, symbol, timeframe):
    """Простой график для быстрого отображения"""
    try:
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(10, 6))

        # Линия цены
        ax.plot(df['time'], df['close'].astype(float),
                linewidth=2, color='blue', label='Price')

        # Заполнение под графиком
        ax.fill_between(df['time'], df['close'].astype(float),
                        alpha=0.3, color='blue')

        ax.set_title(f'{symbol.upper()} - {timeframe.upper()}',
                     fontsize=14, fontweight='bold')
        ax.set_ylabel('Price (USDT)')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Сохраняем в буфер
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=80, bbox_inches='tight')
        buf.seek(0)
        plt.close()

        return buf

    except Exception as e:
        print(f"❌ Ошибка простого графика: {e}")
        return None