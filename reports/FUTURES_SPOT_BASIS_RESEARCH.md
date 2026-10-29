# Futures / Spot basis: исследование дополнительной информации

**BASIS_INCREMENTAL_INFORMATION = NO**. Стратегия и PAPER не менялись.

Protocol SHA-256 `1c3314be00b463c2567463b671f06d96224eddb22bf6313a48ac75f21a7de142`; code `ceb63156aebf5493e1b52181cd10521cc0d9b70bff664e42c83d38221b95f05e`; source manifest `2b21b433ab80fdbe106f1048570eb1b22d27629b3598290b7d2af42687c8f241`. No downloads.

Basis = 100 × ((USD-M perpetual **trade close** / multiplier) / Spot trade close − 1). Для SHIB/PEPE множитель 1000; остальные шесть пар напрямую. Это не mark/index/premium-index basis. Оба close относятся к одному закрытому интервалу [T−TF,T) UTC и известны на границе T. 1h: 2024-01-01…2025-12-31; 4h: 2024-01-01…2026-09-30. Данные уже сохранены, новых загрузок нет.

## Основная валидация 2025

| H | TF | N | Effect vs A, pp | 95% weekly CI, pp | Holm p | C vs A MSE | Cost zero/base/double, % | Class |
|---|---|---:|---:|---|---:|---:|---|---|
| H1 | 1h | 157 | -0.0156 | [-0.3978, +0.3350] | 1.0000 | -0.1453% | +0.042/-0.258/-0.558 | REJECT |
| H1 | 4h | 69 | -0.3912 | [-1.1579, +0.3422] | 1.0000 | -0.4758% | -0.159/-0.459/-0.759 | REJECT |
| H2 | 1h | 11 | -0.3086 | [-0.8575, +0.6519] | 1.0000 | -0.1453% | -0.404/-0.704/-1.004 | REJECT |
| H2 | 4h | 6 | -0.3351 | [-1.0652, +1.1251] | 1.0000 | -0.4758% | -0.907/-1.207/-1.507 | REJECT |
| H3 | 1h | 9975 | +0.0283 | [-0.0781, +0.1313] | 1.0000 | -0.1453% | -0.016/-0.316/-0.616 | WEAK |
| H3 | 4h | 2351 | +0.1051 | [-0.1041, +0.3441] | 1.0000 | -0.4758% | -0.033/-0.333/-0.633 | WEAK |
| H4 | 1h | 1555 | -0.0284 | [-0.1278, +0.0868] | 1.0000 | +0.0294% | +1.538/+1.238/+0.938 | REJECT |
| H4 | 4h | 491 | -0.1166 | [-0.3812, +0.2064] | 1.0000 | -0.5375% | +2.207/+1.907/+1.607 | REJECT |

## Integrity and sample

- BTCUSDT 1h: PASS; aligned=17544; basis=[-0.175%, +0.289%]; |basis|>5%=0; |Δbasis|>2pp=0.
- BTCUSDT 4h: PASS; aligned=6024; basis=[-0.098%, +0.287%]; |basis|>5%=0; |Δbasis|>2pp=0.
- ETHUSDT 1h: PASS; aligned=17544; basis=[-0.523%, +0.299%]; |basis|>5%=0; |Δbasis|>2pp=0.
- ETHUSDT 4h: PASS; aligned=6024; basis=[-0.254%, +0.299%]; |basis|>5%=0; |Δbasis|>2pp=0.
- BNBUSDT 1h: PASS; aligned=17544; basis=[-1.352%, +0.231%]; |basis|>5%=0; |Δbasis|>2pp=0.
- BNBUSDT 4h: PASS; aligned=6024; basis=[-1.352%, +0.171%]; |basis|>5%=0; |Δbasis|>2pp=0.
- SOLUSDT 1h: PASS; aligned=17544; basis=[-1.401%, +0.332%]; |basis|>5%=0; |Δbasis|>2pp=0.
- SOLUSDT 4h: PASS; aligned=6024; basis=[-0.460%, +0.332%]; |basis|>5%=0; |Δbasis|>2pp=0.
- XRPUSDT 1h: PASS; aligned=17544; basis=[-0.212%, +0.287%]; |basis|>5%=0; |Δbasis|>2pp=0.
- XRPUSDT 4h: PASS; aligned=6024; basis=[-0.160%, +0.287%]; |basis|>5%=0; |Δbasis|>2pp=0.
- DOGEUSDT 1h: PASS; aligned=17544; basis=[-0.551%, +0.394%]; |basis|>5%=0; |Δbasis|>2pp=0.
- DOGEUSDT 4h: PASS; aligned=6024; basis=[-0.191%, +0.254%]; |basis|>5%=0; |Δbasis|>2pp=0.
- SHIBUSDT 1h: PASS; aligned=17544; basis=[-1.276%, +0.494%]; |basis|>5%=0; |Δbasis|>2pp=0.
- SHIBUSDT 4h: PASS; aligned=6024; basis=[-0.332%, +0.494%]; |basis|>5%=0; |Δbasis|>2pp=0.
- PEPEUSDT 1h: PASS; aligned=17544; basis=[-1.021%, +1.023%]; |basis|>5%=0; |Δbasis|>2pp=0.
- PEPEUSDT 4h: PASS; aligned=6024; basis=[-0.927%, +1.023%]; |basis|>5%=0; |Δbasis|>2pp=0.
Spot/Futures дубликаты и внутренние пропуски: 0; OHLC, объём, закрытие в T−1ms и 12/48 исходных 5m баров проверены. Сумма 188 544 выровненных строк включает отдельно 1h и 4h наблюдения одних и тех же рынков. Первая Spot свеча прогрева 2024-01-01T00:00Z не имеет парной Futures свечи и не оценивалась.

## Хронология, устойчивость и выбросы

| H | TF | 2024 discovery N/эффект | 2025 validation N/эффект | 2026 diagnostic N/эффект | Кварталы + | Пары + | LOO min/max, п.п. | Без лучшего, п.п. | MFE/MAE медиана, % |
|---|---|---|---|---|---:|---:|---|---:|---|
| H1 | 1h | 3265/-0.082 | 157/-0.016 | — | 3/4 | 2/8 | -0.251/+0.438 | -0.067 | +1.129/-0.889 |
| H1 | 4h | 895/+0.012 | 69/-0.391 | 196/+0.392 | 1/4 | 1/8 | -0.733/-0.065 | -0.552 | +1.692/-1.532 |
| H2 | 1h | 565/+0.162 | 11/-0.309 | — | 1/2 | 0/8 | — | -0.626 | +1.507/-0.801 |
| H2 | 4h | 165/-0.359 | 6/-0.335 | 5/+0.278 | 0/1 | 1/8 | -0.669/+1.336 | -0.796 | +2.420/-1.308 |
| H3 | 1h | 6952/+0.014 | 9975/+0.028 | — | 2/4 | 6/8 | +0.013/+0.046 | +0.026 | +0.997/-1.070 |
| H3 | 4h | 1689/-0.015 | 2351/+0.105 | 3014/-0.044 | 3/4 | 5/8 | +0.089/+0.128 | +0.096 | +1.421/-1.554 |
| H4 | 1h | 3476/+0.057 | 1555/-0.028 | — | 2/4 | 3/8 | -0.049/-0.007 | -0.037 | +1.031/-1.145 |
| H4 | 4h | 842/+0.008 | 491/-0.117 | 783/-0.329 | 2/4 | 2/8 | -0.198/-0.063 | -0.146 | +1.410/-1.746 |

2024 discovery effect рассчитан на обучающих данных и является in-sample описанием. Нулевые символы в per-symbol CSV не появляются как события. Полные квартальные, парные, top-1%, MFE/MAE quantile и redundancy данные — в JSON. MFE/MAE не переориентированы как short-сделка.

## Модели A / B / C

| TF | Средний A MSE | B MSE | C MSE | Средний uplift C против A |
|---|---:|---:|---:|---:|
| 1h | 4.515156 | 4.465522 | 4.521596 | -0.1453% |
| 4h | 8.972410 | 8.827533 | 9.027532 | -0.4758% |

A = прежние 14 Spot+Futures OHLCV признаков; B = только пять basis-признаков; C = A+B. Ridge(alpha=10), нормализация только по 2024. Все модели используют одинаковые строки. Uplift — среднее восьми относительных per-symbol улучшений, а не отношение общих MSE. Funding проверен только в диагностических корреляциях и не входит в модели.

## Вторичные горизонты: exploratory raw outcomes

| H | TF | Период | Горизонт, бары | N | Raw mean, % |
|---|---|---|---:|---:|---:|
| H1 | 1h | validation | 1 | 157 | +0.155 |
| H1 | 1h | validation | 3 | 157 | +0.141 |
| H1 | 1h | validation | 12 | 157 | -0.260 |
| H1 | 1h | validation | 24 | 157 | -0.556 |
| H1 | 4h | diagnostic_2026 | 1 | 196 | +0.475 |
| H1 | 4h | diagnostic_2026 | 6 | 193 | +0.717 |
| H1 | 4h | diagnostic_2026 | 12 | 193 | +1.195 |
| H1 | 4h | validation | 1 | 69 | -0.040 |
| H1 | 4h | validation | 6 | 69 | -0.498 |
| H1 | 4h | validation | 12 | 69 | -0.255 |
| H2 | 1h | validation | 1 | 11 | -0.147 |
| H2 | 1h | validation | 3 | 11 | -0.264 |
| H2 | 1h | validation | 12 | 11 | -0.523 |
| H2 | 1h | validation | 24 | 11 | +0.838 |
| H2 | 4h | diagnostic_2026 | 1 | 5 | +0.745 |
| H2 | 4h | diagnostic_2026 | 6 | 5 | -0.399 |
| H2 | 4h | diagnostic_2026 | 12 | 5 | +0.390 |
| H2 | 4h | validation | 1 | 6 | -1.052 |
| H2 | 4h | validation | 6 | 6 | +1.297 |
| H2 | 4h | validation | 12 | 6 | +2.219 |
| H3 | 1h | validation | 1 | 9975 | +0.022 |
| H3 | 1h | validation | 3 | 9975 | +0.015 |
| H3 | 1h | validation | 12 | 9964 | -0.075 |
| H3 | 1h | validation | 24 | 9937 | -0.097 |
| H3 | 4h | diagnostic_2026 | 1 | 3014 | +0.044 |
| H3 | 4h | diagnostic_2026 | 6 | 3012 | -0.073 |
| H3 | 4h | diagnostic_2026 | 12 | 3009 | -0.109 |
| H3 | 4h | validation | 1 | 2351 | +0.013 |
| H3 | 4h | validation | 6 | 2347 | -0.080 |
| H3 | 4h | validation | 12 | 2336 | -0.132 |
| H4 | 1h | validation | 1 | 1555 | +0.680 |
| H4 | 1h | validation | 3 | 1555 | +1.118 |
| H4 | 1h | validation | 12 | 1552 | +2.139 |
| H4 | 1h | validation | 24 | 1549 | +2.992 |
| H4 | 4h | diagnostic_2026 | 1 | 783 | +0.990 |
| H4 | 4h | diagnostic_2026 | 6 | 781 | +2.632 |
| H4 | 4h | diagnostic_2026 | 12 | 779 | +3.795 |
| H4 | 4h | validation | 1 | 491 | +1.165 |
| H4 | 4h | validation | 6 | 489 | +2.943 |
| H4 | 4h | validation | 12 | 486 | +4.215 |

Маска события задана на primary-eligible строках; более длинный горизонт дополнительно отсекается у границы периода. Эти таблицы не меняют primary conclusion.

## Избыточность признака

Медиана |корреляции| уровня basis по 16 рядам validation: spot_ret1=0.067, futures_ret1=0.060, spot_volume_ratio24=0.050, futures_volume_ratio24=0.050, spot_volatility12=0.024, futures_volatility12=0.023, funding_latest_diagnostic=0.365. Basis не является простой копией текущего return/volume, но связан с funding. Отличие как рыночного состояния не означает дополнительной прогностической пользы: C не улучшил A.

H2 на 1h имеет лишь 11 validation событий, все на BNB; leave-one-out без BNB не определён. Положительный raw absolute move H4 не является эффектом basis: residual относительно A отрицательный.

## Вывод и ограничения

Primary target — будущий Spot close-to-close return (6h на 1h, 12h на 4h). Event effect — остаток относительно A в заранее зафиксированном направлении; cost hurdles — raw event outcome минус условные 0/0.30/0.60 п.п. за круг. Это не исполнимый trading PnL: путь входа/выхода, spread, impact и funding не моделировались.

Пороги discovery 2024 сохранены в JSON. 2026 4h — заранее определённая диагностика, но история уже изучалась в проекте; pristine external holdout отсутствует. Недельный block bootstrap лишь приближённо учитывает перекрытие forward окон; Holm корректирует 8 primary тестов. Архивный trade close не доказывает нулевую задержку live-публикации. После validation пороги и горизонты не подбирались.

Новый edge: NO. Переход к strategy design: NO; изменения technical-v1 и PAPER: NO. Production/SQLite не менялись. DeepSeek и ордера не вызывались. Commit/push: NO.

Воспроизведение: `.venv/bin/python -B reports/futures_spot_basis_research.py --self-test`, затем `.venv/bin/python -B reports/futures_spot_basis_research.py --evaluate`.
