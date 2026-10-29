# Futures flow / funding: frozen incremental-information research

**OI: `OI_CAUSALITY_UNCONFIRMED`; H3/H5 `NOT TESTED`.** Исходы — Spot event study, не торговый PnL.

Протокол JSON SHA-256 `7079ba6e597928450cfd9d0e12a7054bfbe517d81e1efc51a25f34a7c728ec91`; MD `ca38f613205b7e39210dc4383cf390277e5ce35497047edf0e5cdd54e8400d8c`. Код `40b5093241ebdadc03182df8b0d7f6a5070288d508375b91847fdcfb25a7b42d`; manifest `2b21b433ab80fdbe106f1048570eb1b22d27629b3598290b7d2af42687c8f241`.
Raw: 560 файлов, 104,781,353 B. Рабочие research данные: 278,302,226 B. Период UTC: 2024-01-01–2026-10-01 exclusive; 1h только 2024–25, 4h также 2026 diagnostic.

## Решение и происхождение данных

**Нового устойчивого information edge не найдено; к design торговой стратегии переходить рано.** Flow: `INCONCLUSIVE` (условная связь H1 есть, но первичный C<A2 и gross эффект ниже 0.30 п.п.); funding: `NO` в проверенных формах; OI: `NOT TESTED`. Ни один результат не переносится в PAPER.

Источник flow: официальный Binance Public Data USD-M monthly 5m ZIP с taker-buy полями и издательскими SHA-256; funding: публичный `/fapi/v1/fundingRate`; Spot: уже сохранённые и сверенные с прежними SHA-256 файлы проекта. 264 ZIP + 264 CHECKSUM + 32 REST JSON = 560 raw файлов. Funding и свечи доступны на одинаковом полном периоде у всех восьми контрактов. OHLCV Spot 1h заканчивается 2025-12-31, поэтому 2026 — только 4h diagnostic.

| Spot | USD-M perpetual | Множитель цены для сравнения со Spot |
|---|---|---:|
| BTCUSDT | BTCUSDT | 1 |
| ETHUSDT | ETHUSDT | 1 |
| BNBUSDT | BNBUSDT | 1 |
| SOLUSDT | SOLUSDT | 1 |
| XRPUSDT | XRPUSDT | 1 |
| DOGEUSDT | DOGEUSDT | 1 |
| SHIBUSDT | 1000SHIBUSDT | 1000 |
| PEPEUSDT | 1000PEPEUSDT | 1000 |

OI: официальная REST-документация описывает `openInterestHist.timestamp` как конец периода, но не доказывает семантику/доступность архивного `metrics.create_time`. Поэтому OI raw не загружался; H3/H5 не тестировались. Basis тоже не тестировался в этой фазе.

## Primary validation 2025

| Гипотеза | TF | N / недель | residual effect п.п. | 95% weekly CI | Holm p | C vs A2 MSE uplift | Класс |
|---|---|---:|---:|---:|---:|---:|---|
| H1 | 1h | 19178 / 53 | +0.0961 | [+0.0426, +0.1517] | 0.0120 | -0.5327% | WEAK |
| H1 | 4h | 4654 / 53 | +0.3183 | [+0.1313, +0.5411] | 0.0200 | -0.5100% | WEAK |
| H2 | 1h | 2808 / 53 | -0.2476 | [-0.3886, -0.1060] | 1.0000 | -0.5327% | REJECT |
| H2 | 4h | 749 / 53 | -0.8707 | [-1.3312, -0.4322] | 1.0000 | -0.5100% | REJECT |
| H4 | 1h | 384 / 24 | -0.1871 | [-0.4335, +0.1182] | 1.0000 | -0.5327% | REJECT |
| H4 | 4h | 96 / 24 | -0.1393 | [-0.4359, +0.2393] | 1.0000 | -0.5100% | REJECT |

## Временная и парная устойчивость

- H1 1h: validation 8/8 пар с ожидаемым знаком; leave-one-out min=+0.090, max=+0.105 п.п.; 2026 N=0, effect=None; gross zero/base/double hurdle={'zero': 0.03703236794696045, 'base': -0.2629676320530395, 'double': -0.5629676320530396}. Кварталы: 2025Q1:+0.171(4324), 2025Q2:+0.060(4694), 2025Q3:+0.024(5274), 2025Q4:+0.143(4886).
- H1 4h: validation 8/8 пар с ожидаемым знаком; leave-one-out min=+0.273, max=+0.355 п.п.; 2026 N=4316, effect=0.16599005882883253; gross zero/base/double hurdle={'zero': 0.1523619585248935, 'base': -0.14763804147510648, 'double': -0.44763804147510644}. Кварталы: 2025Q1:+0.485(942), 2025Q2:+0.399(1083), 2025Q3:+0.103(1412), 2025Q4:+0.368(1217), 2026Q1:+0.439(1333), 2026Q2:-0.007(1509), 2026Q3:+0.096(1474).
- H2 1h: validation 0/8 пар с ожидаемым знаком; leave-one-out min=-0.266, max=-0.221 п.п.; 2026 N=0, effect=None; gross zero/base/double hurdle={'zero': -0.09337898788462087, 'base': -0.3933789878846209, 'double': -0.6933789878846208}. Кварталы: 2025Q1:-0.408(766), 2025Q2:-0.181(636), 2025Q3:-0.085(738), 2025Q4:-0.307(668).
- H2 4h: validation 0/8 пар с ожидаемым знаком; leave-one-out min=-0.955, max=-0.784 п.п.; 2026 N=575, effect=-0.5044166109798444; gross zero/base/double hurdle={'zero': -0.4057888601442863, 'base': -0.7057888601442863, 'double': -1.0057888601442864}. Кварталы: 2025Q1:-1.165(181), 2025Q2:-0.436(162), 2025Q3:-0.847(198), 2025Q4:-0.976(208), 2026Q1:-0.914(214), 2026Q2:-0.051(200), 2026Q3:-0.523(161).
- H4 1h: validation 2/8 пар с ожидаемым знаком; leave-one-out min=-0.378, max=-0.112 п.п.; 2026 N=0, effect=None; gross zero/base/double hurdle={'zero': 1.5845972508908395, 'base': 1.2845972508908394, 'double': 0.9845972508908395}. Кварталы: 2025Q1:+0.169(120), 2025Q2:-0.321(96), 2025Q3:-0.262(32), 2025Q4:-0.389(136).
- H4 4h: validation 2/8 пар с ожидаемым знаком; leave-one-out min=-0.283, max=+0.078 п.п.; 2026 N=76, effect=-0.1471683569588579; gross zero/base/double hurdle={'zero': 2.1478146092015353, 'base': 1.8478146092015353, 'double': 1.5478146092015352}. Кварталы: 2025Q1:-0.579(30), 2025Q2:-0.111(24), 2025Q3:+0.825(8), 2025Q4:+0.002(34), 2026Q1:-0.171(56), 2026Q2:+0.217(16), 2026Q3:-1.265(4).

## Компоненты и другие горизонты

- 1h A2_flow vs A2: validation MSE uplift -0.1305% (диагностическая ablation, не primary).
- 1h A2_funding vs A2: validation MSE uplift -0.4014% (диагностическая ablation, не primary).
- 4h A2_flow vs A2: validation MSE uplift -0.4808% (диагностическая ablation, не primary).
- 4h A2_funding vs A2: validation MSE uplift -0.1454% (диагностическая ablation, не primary).
- Корреляция flow к текущему futures return, validation по 16 рядам: min=+0.380, median=+0.477, max=+0.569.
- Корреляция flow к объёму futures, validation по 16 рядам: min=-0.105, median=-0.040, max=+0.008.
- Корреляция funding к прошлому Spot return, validation по 16 рядам: min=-0.033, median=+0.054, max=+0.316.
- `taker_buy_share=(flow_imbalance+1)/2` при ненулевом объёме: детерминированная избыточность двух признаков, не отдельный источник информации.

| Гипотеза | TF | Период | Горизонт, бары | N | Средний raw forward, % |
|---|---|---|---:|---:|---:|
| H1 | 1h | validation | 1 | 19187 | +0.0017 |
| H1 | 1h | validation | 3 | 19186 | -0.0098 |
| H1 | 1h | validation | 12 | 19158 | +0.0521 |
| H1 | 1h | validation | 24 | 19131 | +0.0411 |
| H1 | 4h | diagnostic_2026 | 1 | 4320 | +0.0396 |
| H1 | 4h | diagnostic_2026 | 6 | 4310 | +0.2138 |
| H1 | 4h | diagnostic_2026 | 12 | 4298 | +0.2473 |
| H1 | 4h | validation | 1 | 4659 | +0.0512 |
| H1 | 4h | validation | 6 | 4650 | +0.1700 |
| H1 | 4h | validation | 12 | 4643 | +0.3845 |
| H2 | 1h | validation | 1 | 2808 | +0.0272 |
| H2 | 1h | validation | 3 | 2808 | +0.0313 |
| H2 | 1h | validation | 12 | 2806 | +0.1472 |
| H2 | 1h | validation | 24 | 2806 | +0.1189 |
| H2 | 4h | diagnostic_2026 | 1 | 576 | +0.1255 |
| H2 | 4h | diagnostic_2026 | 6 | 574 | +0.2346 |
| H2 | 4h | diagnostic_2026 | 12 | 573 | +0.3568 |
| H2 | 4h | validation | 1 | 750 | +0.0982 |
| H2 | 4h | validation | 6 | 749 | +0.1277 |
| H2 | 4h | validation | 12 | 749 | +0.1510 |
| H4 | 1h | validation | 1 | 384 | +0.7723 |
| H4 | 1h | validation | 3 | 384 | +1.1723 |
| H4 | 1h | validation | 12 | 384 | +2.2145 |
| H4 | 1h | validation | 24 | 376 | +2.9941 |
| H4 | 4h | diagnostic_2026 | 1 | 76 | +1.3028 |
| H4 | 4h | diagnostic_2026 | 6 | 76 | +3.3791 |
| H4 | 4h | diagnostic_2026 | 12 | 76 | +4.4856 |
| H4 | 4h | validation | 1 | 96 | +1.2616 |
| H4 | 4h | validation | 6 | 94 | +2.7994 |
| H4 | 4h | validation | 12 | 92 | +3.6847 |
Secondary horizons только exploratory: без контроля A2 для этих горизонтов и без отбора лучшей ячейки.

## Integrity и ограничения

- BTCUSDT futures_5m: PASS; rows=289152; missing 5m=0; funding gaps >24h=n/a.
- BTCUSDT funding: PASS; rows=3012; missing 5m=n/a; funding gaps >24h=0.
- ETHUSDT futures_5m: PASS; rows=289152; missing 5m=0; funding gaps >24h=n/a.
- ETHUSDT funding: PASS; rows=3012; missing 5m=n/a; funding gaps >24h=0.
- BNBUSDT futures_5m: PASS; rows=289152; missing 5m=0; funding gaps >24h=n/a.
- BNBUSDT funding: PASS; rows=3012; missing 5m=n/a; funding gaps >24h=0.
- SOLUSDT futures_5m: PASS; rows=289152; missing 5m=0; funding gaps >24h=n/a.
- SOLUSDT funding: PASS; rows=3012; missing 5m=n/a; funding gaps >24h=0.
- XRPUSDT futures_5m: PASS; rows=289152; missing 5m=0; funding gaps >24h=n/a.
- XRPUSDT funding: PASS; rows=3012; missing 5m=n/a; funding gaps >24h=0.
- DOGEUSDT futures_5m: PASS; rows=289152; missing 5m=0; funding gaps >24h=n/a.
- DOGEUSDT funding: PASS; rows=3012; missing 5m=n/a; funding gaps >24h=0.
- 1000SHIBUSDT futures_5m: PASS; rows=289152; missing 5m=0; funding gaps >24h=n/a.
- 1000SHIBUSDT funding: PASS; rows=3012; missing 5m=n/a; funding gaps >24h=0.
- 1000PEPEUSDT futures_5m: PASS; rows=289152; missing 5m=0; funding gaps >24h=n/a.
- 1000PEPEUSDT funding: PASS; rows=3012; missing 5m=n/a; funding gaps >24h=0.
Все 8 × 33 месячных ряда 5m прошли checks: 289 152 строк на контракт, 0 отсутствующих 5m интервалов, дубликатов, некорректных OHLC/объёма/taker/count; funding — 3 012 событий на контракт, 0 дубликатов и разрывов >24h. Из joined 1h 17 543 строк на пару complete 17 302; из 4h 6 023 complete 5 963: ранние окна исключены из-за причинного прогрева признаков. Funding stale и zero-volume flow: 0. Пропуски не заполнялись.

## Следующий источник информации

Сначала запросить у Binance документированную семантику `metrics.create_time` и point-in-time публикацию OI. Пока её нет, следующий дешёвый отдельный frozen test — futures/Spot basis на уже имеющихся ценах с нормализацией множителя 1000; это новая гипотеза, не часть текущих шести primary ячеек. Проспективный spread нужен для реалистичности исполнения, но здесь collector не создавался.

Детальные per-symbol, model, thresholds и source hashes — в [JSON](FUTURES_FLOW_OI_RESEARCH.json); события — в [CSV](FUTURES_FLOW_OI_RESULTS.csv).

Ограничения: Исторические 2024–2025 OHLCV уже исследовались в предыдущей работе проекта; 2026 4h ранее использовался для OHLCV OOS, это не чистый внешний holdout; Метка fundingTime и закрытие архивной свечи не доказывают нулевую live-задержку публикации; Исходы событий не являются исполнимым торговым PnL; OI исключён из причинного воспроизведения

Воспроизведение без сети: `.venv/bin/python -B reports/futures_flow_oi_research.py --self-test` затем `.venv/bin/python -B reports/futures_flow_oi_research.py --evaluate`.

Production, technical-v1, PAPER/SQLite и DeepSeek не изменялись. Ордеров, commit и push нет.
