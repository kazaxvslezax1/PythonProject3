# Research index and freeze

Статус на 2026-10-29. Это реестр результатов, а не источник торговых сигналов. Исследовательские эффекты не внедрены в production. История 2024–2026 неоднократно использовалась в исследованиях и не является новым независимым holdout.

| Research | Question | Data | Verdict | Status | Key report |
|---|---|---|---|---|---|
| technical-v1 | Есть ли подтверждённая прибыльность действующей технической логики? | Исторический Spot и проспективные PAPER-наблюдения | **BASELINE ONLY** | Сохранён без оптимизации; edge не подтверждён | [Walk-forward](WALK_FORWARD_AUDIT.md), [PAPER audit](PROSPECTIVE_32_TRADE_AUDIT.md) |
| WALK_FORWARD | Устойчива ли исходная стратегия по времени, парам и издержкам? | 8 пар × 1h/4h, Binance Spot 2024–2025; локальные CSV и signal cache | **NO ROBUST PROFITABILITY** | Исторический результат преимущественно отрицателен после costs; costs не единственная причина | [Audit](WALK_FORWARD_AUDIT.md), [Results](WALK_FORWARD_RESULTS.md), [Protocol](WALK_FORWARD_PROTOCOL.json) |
| PROSPECTIVE PAPER | Подтверждают ли реально записанные PAPER-сделки edge? | 32 закрытые PAPER-позиции, снимок журнала | **NEGATIVE PROSPECTIVE EVIDENCE** | Win rate около 28%, expectancy < 0, profit factor < 1; большинство убытков через initial SL | [Audit](PROSPECTIVE_32_TRADE_AUDIT.md), [Trades](PROSPECTIVE_32_TRADES.csv) |
| TECHNICAL_V2 | Проходит ли хотя бы один заранее заданный кандидат? | Локальные Spot CSV и сжатый cache сигналов walk-forward | **NO CANDIDATE PASSES** | technical-v2 не создан | [Research](TECHNICAL_V2_RESEARCH.md), [Results](TECHNICAL_V2_RESEARCH.json) |
| MARKET_EDGE_DISCOVERY | Есть ли устойчивые OHLCV event effects среди 44 определений? | Локальные исторические Spot OHLCV; 44 заранее заданных условия | **NO ROBUST EDGE FOUND** | Прекращён дальнейший OHLCV feature search | [Research](MARKET_EDGE_DISCOVERY.md), [Events](MARKET_EDGE_EVENTS.csv) |
| OOS_2026 | Подтверждён ли замороженный `breakout_24_btc_range / 4h`? | Binance Spot 4h за 2026, локальный датасет | **FROZEN HYPOTHESIS NOT CONFIRMED** | Гипотеза отвергнута; 2026 не чистый holdout для последующих поисков | [Confirmation](OOS_2026_CONFIRMATION.md), [Protocol](OOS_2026_FROZEN_PROTOCOL.md) |
| FUTURES_DATA_FEASIBILITY | Достаточны ли доступность и качество Futures-источников? | Проверка источников и метаданных | **FEASIBILITY AUDIT ONLY** | Не самостоятельное подтверждение edge | [Feasibility](FUTURES_DATA_FEASIBILITY.md), [Sources](FUTURES_DATA_SOURCES.csv) |
| FUTURES FLOW | Даёт ли taker flow добавочную информацию? | Локальные Futures 5m и связанные публичные ряды | **INCONCLUSIVE** | Пороговый поиск остановлен | [Flow/OI research](FUTURES_FLOW_OI_RESEARCH.md), [Protocol](FUTURES_FLOW_OI_FROZEN_PROTOCOL.md) |
| FUNDING | Даёт ли funding проверяемый edge? | Локальные funding observations | **NO IN TESTED FORMS** | Только проверенные в отчёте формы | [Flow/OI research](FUTURES_FLOW_OI_RESEARCH.md) |
| OPEN INTEREST | Можно ли причинно корректно проверить OI? | Доступные OI-данные и метаданные времени публикации | **NOT TESTED — CAUSALITY UNCONFIRMED** | `OI_CAUSALITY_UNCONFIRMED`; защиту не обходить | [Flow/OI research](FUTURES_FLOW_OI_RESEARCH.md) |
| FUTURES/SPOT BASIS | Есть ли добавочная информация в basis? | Локальные Spot/Futures 1h features | **NO INCREMENTAL INFORMATION** | Оптимизация basis остановлена | [Basis research](FUTURES_SPOT_BASIS_RESEARCH.md), [Protocol](FUTURES_SPOT_BASIS_FROZEN_PROTOCOL.md) |
| HIGHER TIMEFRAME | Оправдана ли отдельная low-turnover стратегия на 4h/1d? | 8 Spot-пар, 2020–2026; локальные 4h и агрегированные 1d | **WEAK EFFECTS ONLY** | H1 continuation и H4 4h pullback оставлены только как гипотезы; стратегии нет | [Research](HIGHER_TIMEFRAME_EDGE_RESEARCH.md), [Protocol](HIGHER_TIMEFRAME_EDGE_PROTOCOL.md) |

## Research Freeze

Остановлены OHLCV/RSI/ADX/EMA/SMA/MACD/Bollinger parameter mining, оптимизация basis, taker-flow и funding, higher-timeframe parameter search, post-hoc оптимизация H1/H4, перебор комбинаций `H4 + flow + basis + RSI` и создание technical-v2/v3. Новое исследование требует действительно новой гипотезы, источника информации или заранее зафиксированного проспективного протокола. Повторный поиск порогов по уже просмотренной истории не является независимым подтверждением.

Операционная политика: `technical-v1 = BASELINE ONLY`; PAPER — `KEEP RUNNING`; AI — `ADVISORY ONLY`; текущий бюджет DeepSeek сохраняется; реальные ордера — `DISABLED`. Это политика, а не подтверждение того, какие процессы сейчас запущены. Результаты исследований не являются production-сигналами; торговые и риск-параметры этим документом не меняются.

## Reproduction and local data

Команды запускать из корня проекта в существующем окружении. Здесь перечислены офлайн-действия; **не запускать** `--fetch` и команды без `--offline` при обычной проверке freeze.

| Research | Offline command or artifact | Repository reproducibility |
|---|---|---|
| WALK_FORWARD | `.venv/bin/python scripts/run_walk_forward.py --symbols BTCUSDT ETHUSDT BNBUSDT SOLUSDT XRPUSDT DOGEUSDT SHIBUSDT PEPEUSDT --timeframes 1h 4h --start 2024-01-01 --end 2026-01-01 --workers 4 --offline` | **PARTIAL**: нужны игнорируемые `runtime/walk_forward/data` CSV и cache; хеши опубликованы в results |
| PROSPECTIVE PAPER | Проверка сохранённых [CSV](PROSPECTIVE_32_TRADES.csv) и [JSON](PROSPECTIVE_32_TRADE_AUDIT.json) | **PARTIAL**: нет отдельного snapshot-replay CLI для исходного состояния SQLite-журнала |
| TECHNICAL_V2 | `.venv/bin/python -B reports/technical_v2_replay.py` (результаты в `/tmp`) | **PARTIAL**: использует локальные игнорируемые walk-forward CSV/cache |
| MARKET_EDGE_DISCOVERY | `.venv/bin/python -B reports/market_edge_discovery.py --evaluate` | **PARTIAL**: 23 МиБ JSON с замороженными определениями и подробными результатами оставлен локально, защищён от случайного Git-коммита; требует отдельного решения для переносимого replay |
| OOS_2026 | `.venv/bin/python -B reports/oos_2026_confirmation.py --self-test`; `--evaluate` требует локальные данные | **PARTIAL**: `OOS_2026_DATA` игнорируется; хеши в отчёте |
| FUTURES_DATA_FEASIBILITY | [Отчёт](FUTURES_DATA_FEASIBILITY.md) и [таблица источников](FUTURES_DATA_SOURCES.csv) | **PARTIAL**: отдельного offline replay-скрипта нет |
| FUTURES FLOW / FUNDING / OI | `.venv/bin/python -B reports/futures_flow_oi_research.py --self-test`; `--evaluate` требует локальные данные | **PARTIAL**: raw/normalized data игнорируются; [manifest](FUTURES_FLOW_OI_DATA/manifest.json) содержит SHA |
| FUTURES/SPOT BASIS | `.venv/bin/python -B reports/futures_spot_basis_research.py --self-test`; `--evaluate` требует локальные данные | **PARTIAL**: derived data игнорируются; [manifest](FUTURES_SPOT_BASIS_DATA/manifest.json) содержит SHA |
| HIGHER TIMEFRAME | `.venv/bin/python -B reports/higher_timeframe_edge_research.py --self-test`; `--evaluate` требует локальные данные | **PARTIAL**: новые Spot-данные игнорируются; [manifest](HIGHER_TIMEFRAME_EDGE_DATA/manifest.json) содержит SHA |

`PARTIAL` означает, что репозиторий без локальных датасетов или исторического состояния журнала сам по себе не восстанавливает весь результат. В текущем рабочем каталоге соответствующие файлы присутствуют; скрипты, отчёты, протоколы и manifest-файлы проверены на существование. Сырые данные не удалены.

## Git data policy

| Class | Paths | Reason |
|---|---|---|
| **A — SHOULD COMMIT** | Верхнеуровневые `reports/*.md`, `reports/*.csv`, `reports/*.py`, `reports/*.json` кроме `MARKET_EDGE_DISCOVERY.json`; `reports/FUTURES_FLOW_OI_DATA/manifest.json`, `reports/FUTURES_SPOT_BASIS_DATA/manifest.json`, `reports/HIGHER_TIMEFRAME_EDGE_DATA/manifest.json`; исследовательские `tests/test_*research.py` | Протоколы, отчёты, небольшие результаты, код и SHA-метаданные. Точные новые пути перечисляются в плане коммитов; ранее отслеживаемые файлы не добавляются повторно. |
| **B — SHOULD IGNORE** | `runtime/`; `reports/OOS_2026_DATA/`; всё содержимое трёх `*_DATA/` выше, кроме manifest; cache, временные файлы и локальные загрузки | Сырые/производные рыночные данные, DB и runtime-состояние; отдельные ZIP и compressed CSV достигают 10–13 МиБ. |
| **C — REVIEW** | `reports/MARKET_EDGE_DISCOVERY.json` | 23 МиБ подробного сгенерированного JSON; нужен для переносимого frozen-protocol replay, но не должен случайно попасть в Git. Сейчас локально сохранён и адресно игнорируется. |

Ни один файл класса A не превышает 10 МиБ; три manifest-файла не содержат секретов и сохраняют SHA/источник. Локальные файлы класса B/C не удалены. Для `MARKET_EDGE_DISCOVERY.json` требуется отдельное решение до возможного включения в Git или создания компактного переносимого протокола. Не применять `git add .` или `git add -A`; staging — только по точным путям после проверки размера и секретов. Пользовательский `backend/simple_bot.py` исключён.
