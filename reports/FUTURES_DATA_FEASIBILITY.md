# FUTURES / MICROSTRUCTURE DATA FEASIBILITY — 2026-10-27 UTC

**Решение:** для следующего *offline* исследования имеет смысл запросить разрешение на ограниченный набор официальных USD‑M Futures данных: 5‑минутные свечи с taker-buy полями, дневные ZIP `metrics` с open interest и историю funding. Полные `aggTrades`, individual trades и L2 сейчас не нужны. Ничего из этого на данном этапе массово не скачано; edge и стратегия не заявляются. Статус предыдущего OOS `breakout_24_btc_range/4h` — `NOT CONFIRMED` (N=222, base −1.709%); искать на тех же OHLCV очередную комбинацию не предлагается.

## Что проверено и как читать доказательства

Прочитаны [аудит 32 PAPER-сделок](PROSPECTIVE_32_TRADE_AUDIT.md), [walk-forward](WALK_FORWARD_AUDIT.md), [technical-v2 research](TECHNICAL_V2_RESEARCH.md), [market-edge discovery](MARKET_EDGE_DISCOVERY.md) с его [JSON](MARKET_EDGE_DISCOVERY.json), [замороженный OOS-протокол](OOS_2026_FROZEN_PROTOCOL.md) и [OOS-результат](OOS_2026_CONFIRMATION.md) с [JSON](OOS_2026_CONFIRMATION.json). Исторические расчёты проекта использовали **Spot** `GET /api/v3/klines`, что видно также в `backend/market_data.py` и `scripts/run_walk_forward.py`; файлов фьючерсных данных в `runtime/` по именам источников не найдено. Spot 1h/4h сохранены за 2024–2025; OOS 2026 сохранён только на 4h. Исследование 2024–2025: 15/16 рядов technical-v1 отрицательны после базовых затрат; 32 закрытые проспективные PAPER-сделки −203.77 USD. Эти итоги не сравнимы напрямую с futures event study.

Источники этого аудита: [официальная USD‑M REST-документация](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data), [официальные market WebSocket streams](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/ws-streams/market), [публичные book streams](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/ws-streams/public) и [репозиторий Binance Public Data](https://github.com/binance/binance-public-data/blob/master/README.md). Дополнительно сделаны только публичные `exchangeInfo`, короткие `fundingRate?limit=1`, HEAD архивных ZIP и чтение **трёх** ZIP `metrics` размером ~11 КБ каждый в памяти. Нет ключей, ордеров, DeepSeek, WebSocket-сессий, сохранённых downloaded datasets или стороннего провайдера. HEAD 200 доказывает существование конкретного файла, **не** полноту непрерывной истории.

## Восемь исходных активов и USD‑M соответствие

Один read-only `GET /fapi/v1/exchangeInfo` 2026‑10‑27 23:xx UTC вернул `TRADING`, `PERPETUAL`, `quoteAsset=USDT`, `marginAsset=USDT` для всех восьми логических активов. Исторический `onboardDate` у всех соответствующих контрактов раньше 2024‑01‑01. Текущий статус не доказывает отсутствия временных остановок, миграций или пропусков в 2024–2026.

| Spot-актив проекта | USD‑M symbol | Текущее состояние | Важная оговорка |
|---|---|---|---|
| BTCUSDT | BTCUSDT | TRADING PERPETUAL USDT | прямое соответствие |
| ETHUSDT | ETHUSDT | TRADING PERPETUAL USDT | прямое соответствие |
| BNBUSDT | BNBUSDT | TRADING PERPETUAL USDT | прямое соответствие |
| SOLUSDT | SOLUSDT | TRADING PERPETUAL USDT | прямое соответствие |
| XRPUSDT | XRPUSDT | TRADING PERPETUAL USDT | прямое соответствие |
| DOGEUSDT | DOGEUSDT | TRADING PERPETUAL USDT | прямое соответствие |
| SHIBUSDT | **1000SHIBUSDT** | TRADING PERPETUAL USDT | разная единица котирования; нормализовать multiplier до basis |
| PEPEUSDT | **1000PEPEUSDT** | TRADING PERPETUAL USDT | разная единица котирования; нормализовать multiplier до basis |

`SHIBUSDT` и `PEPEUSDT` как прямые futures symbols **не присутствовали** в этом `exchangeInfo`. До объединения с Spot проверить контрактный multiplier и непрерывность `onboardDate`/`deliveryDate`/status по историческим файлам; не сравнивать численные цены `1000…` с Spot 1:1.

## Историческая доступность: 2024 / 2025 / 2026

Обозначения: **200** — конкретный HEAD или `limit=1` probe успешно вернул архив/запись; **док.** — тип источника описан официально, но каждый день/символ не проверен; **нет доказанного архива** — в проверенных официальных источниках исторический файл не установлен, это не доказательство абсолютного отсутствия у Binance. 2026 — до последнего опубликованного полного дня, не будущие даты. Не подменять доступность конкретной датой наличием всего года.

| Источник | 2024 | 2025 | 2026 | Официальный архив/API и ограничения |
|---|---|---|---|---|
| USD‑M 5m/1h `klines` с taker-buy и count | BTC 5m 2024‑01‑02 HEAD 200 | BTC 5m HEAD 200 | BTC и все 8 5m на 2026‑09‑01 HEAD 200 | Public Data `futures/um/{daily,monthly}/klines`; месячный BTC 2025‑01 HEAD 200; REST `/fapi/v1/klines` |
| `aggTrades` / raw trades | BTC daily HEAD 200 | BTC daily HEAD 200 | BTC и 8 контрактов daily 2026‑09‑01 HEAD 200 | Public Data `aggTrades`/`trades`; REST aggTrades ограничен последними 48 ч, individual historicalTrades — API key и ~1 месяц |
| `metrics` 5m: OI/OI value + другие поля | **все 8** соответствующих futures symbols daily 2024‑01‑02 HEAD 200 | BTC, 1000SHIB, 1000PEPE daily HEAD 200 | BTC, 1000SHIB, 1000PEPE daily HEAD 200 | Public Data `futures/um/daily/metrics`; месячный BTC 2025‑01 HEAD 404; REST `/futures/data/openInterestHist` только последний 1 месяц |
| Funding history | BTC, 1000SHIB, 1000PEPE `limit=1` вернули запись 2024 | BTC `limit=1` вернул запись 2025 | те же три вернули запись 2026 | Публичный `/fapi/v1/fundingRate`, явного краткого лимита истории в документации нет; для остальных 5 пар/всех интервалов нужен manifest |
| Mark / index / premium-index klines | BTC daily HEAD 200 для каждого вида | BTC 5m daily HEAD 200 | BTC 5m daily HEAD 200 | Public Data архив + REST `/fapi/v1/{markPriceKlines,indexPriceKlines,premiumIndexKlines}`; все пары/дни не проверены |
| Liquidation `forceOrder` | нет доказанного официального исторического архива | то же | только документированный live snapshot stream; исторический архив не установлен | `@forceOrder` выдаёт **лишь последнее** событие на символ за 1000 ms, не полный поток ликвидаций |
| Best bid/ask и L2 | нет доказанного воспроизводимого архива | то же | live REST/WS, прошлые snapshots не запрашиваются | `/ticker/bookTicker`, `/depth`, partial/diff depth WS; L2 требует snapshot + непрерывные update IDs |

Примеры реально проверенных объектов: [BTC `metrics` 2024‑01‑02](https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-2024-01-02.zip), [BTC `metrics` 2025‑01‑02](https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-2025-01-02.zip), [BTC `metrics` 2026‑09‑01](https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-2026-09-01.zip), [1000PEPE `metrics` 2024‑01‑02](https://data.binance.vision/data/futures/um/daily/metrics/1000PEPEUSDT/1000PEPEUSDT-metrics-2024-01-02.zip), [BTC 5m 2026‑09‑01](https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/5m/BTCUSDT-5m-2026-09-01.zip). Их HEAD `Content-Length` применён только для оценки масштаба. Три чтения `metrics` показали по 288 строк/сутки и столбцы `create_time,symbol,sum_open_interest,sum_open_interest_value,count_toptrader_long_short_ratio,sum_toptrader_long_short_ratio,count_long_short_ratio,sum_taker_long_short_vol_ratio`.

## Information против execution

**Information:** aggressor side и signed flow отражают, *кто инициировал исполненные сделки*; OI — число/стоимость открытых фьючерсных позиций; funding — стоимость удержания и возможную скученность; futures-vs-spot basis и premium — разницу рынков; liquidation snapshots — эпизоды принудительного исполнения; order-book imbalance — видимую текущую ликвидность. Этого нет в **сохранённых семипольных Spot OHLCV** проекта. При этом полный Spot kline API тоже может содержать taker-buy поля: сама сторона агрессора не эксклюзивна Futures, но futures flow описывает **другой рынок**. Futures volume **сам по себе** лишь объём другого рынка; price/OI и funding могут быть прокси уже известного тренда. Новизна измерения не равна предсказательной ценности.

**Execution:** spread, depth, slippage, impact и latency прежде всего уточняют возможность получить заявленные entry/exit. Spread/L2 могут также быть признаками состояния рынка, но для горизонтов 1h/4h их кратковременная динамика вероятно менее релевантна, чем для секунд/минут; это гипотеза, не результат теста. Отдельные 1‑минутные summaries могли бы измерять режим ликвидности, если собрать их проспективно.

## Flow: точные кандидаты без тестирования

В официальных USD‑M свечах есть `volume` (позиция 5), `quoteVolume` (7), `numberOfTrades` (8), `takerBuyBaseVolume` (9), `takerBuyQuoteVolume` (10); `takerSellBaseVolume = volume − takerBuyBaseVolume`. Архивные 5m свечи позволяют малый dataset; сырые `aggTrades` дают цены, количества, `T`, флаг `m` и IDs, но до 100 ms одинаковой цены/стороны объединяются. **`m=true` означает покупатель — maker, поэтому инициатор/taker — SELL; `m=false` означает BUY taker.** Нельзя трактовать maker-флаг как направление агрессора. Новое поле `nq` в текущем REST/WS отделяет объём без RPI, тогда как старые архивные схемы его могут не иметь; версионировать схему и не смешивать без проверки. Индивидуальные trade count/large-trade share нельзя восстановить из количества `aggTrades` без оговорок. [REST](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data), [архивная схема](https://github.com/binance/binance-public-data/blob/master/README.md), [WS `m` и `T/E`](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/ws-streams/market).

| Кандидат | Точное определение и raw | Интервал / момент доступности | Риск и хранение |
|---|---|---|---|
| Taker buy/sell volume | `B=Σ takerBuyBaseVolume`, `S=Σ(volume−takerBuyBaseVolume)` из закрытых futures 5m свечей | 5m→1h/4h; только после закрытия последней 5m | проверить `0≤B≤V`, `S≥0`; хранить 5m raw |
| Normalized imbalance | `(B−S)/(B+S)`, NULL при нулевом объёме | 1h/4h, все составляющие уже закрыты | future 5m нельзя включать по совпавшему openTime |
| Signed flow / CVD proxy | `Σ(B−S)` за заранее фиксированное окно; `CVD_t=CVD_{t−1}+B−S` с отдельным началом каждого ряда | 5m/1h/4h | volume в единицах контрактного символа; normalize при межпарном сравнении; CVD не order-book delta |
| Flow acceleration | `imbalance_t−mean(imbalance_{t−k..t−1})`; `k` фиксировать будущим протоколом | 1h/4h после закрытия t | прошлое окно строго `shift(1)`; сам k пока не выбран |
| Trade count / mean size | futures kline `N`, средний размер `V/N`; exact buy/sell count требует individual trades/ID coverage | 5m→1h/4h | count от futures, не Spot; `N=0` → NULL |
| Trade-count imbalance | `(N_buy_taker−N_sell_taker)/(N_buy_taker+N_sell_taker)`; individual trades с `isBuyerMaker`, **не** число агрегированных записей | event-level→5m→1h/4h | для v1 недоступен из kline; raw trades bulk — **DEFER** |
| Large-trade concentration | `Σ qty trades above predeclared causal threshold / Σ qty`; только raw individual trades, не агрегированный trade-size как равный individual | event-level→5m, затем 1h/4h | bulk storage дорогой; **DEFER**, порог не выбирается здесь |

Для 1h/4h первый опыт может использовать даже закрытые futures 1h свечи; 5m целесообразен, чтобы сохранить внутрисвечную форму/ускорение и сформировать оба TF. 1m даёт 4.2 млн строк/год по восьми контрактам и пока не нужен. `aggTrades` доступен в официальном архиве, поэтому prospective flow collector не нужен для истории; REST `aggTrades` — только последние 48 часов, `limit≤1000`, при `startTime+endTime` окно <1h, weight 20. `historicalTrades` требует API key и ограничен последним месяцем; полный архив `trades` значительно тяжелее. Никакие секреты для предложенного архивного этапа не нужны.

## OI, funding, liquidations, book, basis

- **OI:** `/fapi/v1/openInterest` — текущий snapshot с `time`; `/futures/data/openInterestHist` даёт `sumOpenInterest`, `sumOpenInterestValue`, `timestamp` как конец периода, 5m…1d, `limit≤500`, но только около месяца. Официальные ZIP `metrics` содержат исторические 5m OI/OI value как минимум в проверенных датах 2024/25/26. Документация архива не объясняет `create_time` как момент наблюдения или начало интервала: в пробах 2024‑01‑02, 2026‑06‑24/25 было 288 меток `00:00…23:55`, но **по одной сетке нельзя доказать момент известности значения**. Перед расчётом признаков сопоставить архив с REST на перекрывающемся месяце, проверить границы суток и изменения семантики; до этого OI — `timestamp_semantics_unverified`, без допуска к causal dataset. Кандидаты: `ΔOI/OI_{t−1}`, `ΔOI_value` и четыре пары знаков `Δprice×ΔOI`: цена↑/OI↑ — возможное расширение участия, цена↑/OI↓ — возможное закрытие short, цена↓/OI↑ — возможное расширение short, цена↓/OI↓ — возможное сокращение/ликвидация long. Ни одна трактовка не доказывает состав позиций.
- **Funding:** публичный `/fapi/v1/fundingRate` возвращает состоявшийся `fundingTime`, `fundingRate`, `markPrice` и `rateType`, `limit≤1000`, в возрастающем порядке; interval может отличаться по символам и времени, `/fapi/v1/fundingInfo` показывает текущие adjustments. Не использовать ставку следующего расчёта задним числом. Кандидаты: последний **уже состоявшийся** уровень, его изменение, каузальный percentile/extreme, длительность положительного/отрицательного funding и price×funding interaction; сравнить с trailing price trend и premium, иначе возможна дублирующая информация. Пробы по BTC/1000SHIB/1000PEPE подтверждают записи 2024 и 2026, BTC — 2025.
- **Liquidations:** официальный `@forceOrder` — snapshot *последнего* принудительного ордера за 1000 ms на символ, с `E`, `o.T`, `o.S`, `o.q`, `o.p`, `o.ap`, `o.z`. `SELL` — сторона принудительного ордера, не произвольная «ликвидация short»; для направления закрытой позиции нужна проверенная семантика исходного события. Точный total liquidation volume по этому stream **не восстановить**. Полный исторический официальный архив не установлен; third-party возможен только после отдельной оценки лицензии, полноты, timestamp и стоимости. Гипотезы cluster/intensity и continuation/reversal требуют либо честно помеченного censored snapshot, либо полного источника.
- **Best bid/ask и L2:** `/fapi/v1/ticker/bookTicker` и `/fapi/v1/depth` возвращают текущее состояние, не историю. WS partial top 5/10/20 и diff depth 100/250/500ms; реконструкция diff требует snapshot `lastUpdateId` и непрерывных `U/u/pu`, gap → reset/rebootstrap. `spread=(ask−bid)/mid`, top imbalance `(bidQty−askQty)/(bidQty+askQty)`, microprice `(ask·bidQty+bid·askQty)/(bidQty+askQty)`, depth imbalance/slope требуют возрастающей по времени книги. Видимые заявки могут исчезать, RPI исключён из обычного depth; execution slippage нельзя вывести только из top quote. Официальная 2024–2026 L2/quote history в проверенных источниках не подтверждена.
- **Basis / mark / index:** основное `basis_t=(F_trade_close_t−S_spot_close_t)/S_spot_close_t` на синхронно закрытых свечах, после нормализации контрактного множителя `1000…`; не использовать дневной forward fill из будущего. Отдельно `mark−index` и `premiumIndexKlines` описывают расчётную премию, **не** равны futures-vs-Binance-Spot basis: index — другой бенчмарк. Исторические mark/index/premium OHLC доступны в публичном архиве по проверенным BTC-дням 2024/25/26; API даёт `limit≤1500`. Они могут отражать leverage demand/crowding и liquidation-risk state, но incremental value не проверена.

## API и архив: границы для будущего downloader

| Источник | Публичность / лимит / вес | История / pagination | Временные поля |
|---|---|---|---|
| `exchangeInfo` | без ключа, weight 1 | текущее состояние, не historical status | onboard/delivery, serverTime не использовать как свечу |
| `/fapi/v1/klines`, mark/index/premium klines | без ключа, max 1500, вес 1/2/5/10 по limit | архив daily/monthly; REST `startTime/endTime`, курсор строго по openTime | openTime, closeTime; последнюю незакрытую свечу исключить |
| `/fapi/v1/aggTrades` | без ключа, max 1000, weight 20 | REST последние 48 ч, time-window <1h при обеих границах; архив daily/monthly | `T` trade time, `m` buyer maker, ID диапазон |
| `/fapi/v1/historicalTrades` | нужен `X-MBX-APIKEY`, max 500, weight 200 | REST последний месяц; официальный архив `trades` | individual trade time/ID; не использовать ключ здесь |
| `/futures/data/openInterestHist` | без ключа, max 500, weight 0, отдельный IP limit 1000/5min | REST только последний месяц; архив `metrics` daily | REST timestamp = period end; ZIP `create_time` требует семантической проверки |
| `/fapi/v1/fundingRate` | без ключа, max 1000, общий лимит с fundingInfo 500/5min/IP | хронологически по `startTime/endTime`; явного короткого retention в docs нет | `fundingTime` фактического расчёта, не предполагаемые 8h слоты |
| `/ticker/bookTicker`, `/depth` | без ключа; bookTicker weight 2 symbol/5 all; depth weight 2…20 по размеру | только current snapshots | `E/T` при наличии, локальное receive time отдельно |

У ZIP архива нет REST row limit или гарантированного документированного request weight; дневные файлы появляются позже закрытия дня, месячные — после конца месяца. `CHECKSUM` издателя проверять до распаковки. Архив может получить исправленную версию: SHA256 и дату скачивания фиксировать, старый файл не перезаписывать молча. Rate limits и структура API могут меняться; перед будущим download перечитать [официальный REST reference](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data) и [правила public data](https://github.com/binance/binance-public-data/blob/master/README.md).

## Причинное время и качество

Будущая цепочка: **raw source → UTC/ms normalization → validation → агрегация в закрытые 5m → 1h/4h feature snapshot на `closeTime=T` → outcome только после T**. У trade/aggTrade различать `T` исполненной сделки и `E` публикации WS; у OI — `timestamp` конца периода против неразъяснённого `create_time`; у funding — фактический `fundingTime`; у book — `T` transaction, `E` event, локальный receive time и update ID; у клайнов — `openTime/closeTime`. Для исторического replay принимать значение к закрытию T только если доказано, что оно опубликовано не позже T; при неизвестной задержке установить консервативный lag и проверить чувствительность. Никогда не `bfill` будущими значениями. Внутри одной секунды/свечи несовпадающие timestamps не считать строго упорядоченными без отдельных IDs и правил.

Проверки качества: точная сетка 5m/1h UTC; закрытая свеча; уникальный `(market,symbol,openTime)`; `high≥max(open,close,low)`, `low≤min(open,close,high)`, `0≤takerBuy≤volume`, count≥0; ZIP checksum/SHA; полный список ожидаемых daily files с явными 404, а не молчаливый пропуск; дедуп `trade ID`, проверка диапазона `f/l` и event-time order; zero-volume как NULL imbalance; funding gaps/изменение интервала; OI 5m gaps, off-grid timestamps и спорные границы суток; контрактный multiplier и статус; maintenance/halts; book `pu` gaps и resync; WS disconnect/late events — маркировать feature unavailable, не заполнять соседним будущим. Публикационная задержка дневного архива не означает, что live feature была доступна точно в момент закрытия; для строгого prospective validation нужна отдельная регистрация receive time.

## Объём, формат и сложность

Оценки **не квоты и не подтверждённые размеры 2024–2026**. Основа: HEAD ZIP за 2026‑09‑01 для восьми futures symbols: суммарно 5m klines **104,814 B/день**, 1m klines ≈**467 KB/день**, `aggTrades` ≈**49.3 MB/день**; `metrics` на примерах ≈11–12 KB/символ/день. Волатильные дни могут быть гораздо тяжелее. Число строк — расчёт по полной сетке, где это применимо.

| Source | Granularity | Rows/year, 8 symbols | ZIP/year и raw estimate | История / приоритет |
|---|---:|---:|---:|---|
| Futures kline taker fields | 5m | 840,960 | ~38 MB ZIP; ~0.1–0.2 GB CSV | официальный архив; **P0** |
| `metrics` OI | 5m | 840,960 | ~34 MB ZIP; ~0.09–0.15 GB CSV | официальный daily архив, timestamp gate; **P0 условно** |
| Funding | native (типично несколько/сутки) | ориентир ~9k, переменно | <1 MB ZIP/год; ~1–3 MB raw | публичный API; **P1** |
| Futures/Spot basis | 1h/4h, derived | 70,080/17,520 | почти без нового хранения поверх klines | **P1** |
| Mark/index/premium klines | 1h | по 70,080 на вид | порядка 1–5 MB ZIP/вид/год, проверить | официальный архив; **P1/P2** |
| Futures `aggTrades` | event-level | неизвестно, меняется с активностью | **~18 GB ZIP/год** при одном sample day; raw десятки GB | архив есть, **DEFER** |
| Individual trades | event-level | неизвестно | вероятно больше aggTrades; не измерено | архив есть, **DEFER** |
| Best bid/ask summaries | 1m prospective | максимум 840,960 слотов | ~0.1–0.2 GB raw/год при фиксированных полях | нет проверенной истории; **P2** |
| Full L2 diff | 100–500ms live | сильно переменно | возможно десятки+ GB/год, оценка не подтверждена | no-go для 1h/4h сейчас |

**Минимальный dataset v1:** 8 mapped USD‑M perpetual symbols, 2024‑01‑01…последний полный опубликованный день; `5m klines` + дневные `metrics` + `fundingRate`, только после отдельного согласования загрузки. Сохранить текущие Spot 1h/4h OHLCV как контроль: 2024–2025 уже есть, 2026 Spot 1h потребуется отдельно получить, если включать 1h; для basis синхронизировать Spot/contract close и multiplier. Ориентир за ~2.8 года: ~110 MB ZIP klines + ~100 MB ZIP metrics + <5 MB funding; распакованные CSV порядка **0.6–1.0 GB**, рабочее место с checksum/Parquet и временными файлами — **1–2 GB**. Архивные запросы: 5m monthly ≈8×34=272 файлов; `metrics` monthly BTC 2025‑01 дал 404, поэтому ориентир ≈8×1030=8240 daily файлов; funding примерно 25–40 paginated requests при типичных интервалах. Итого ~8.5 тыс. HTTP запросов, преимущественно маленьких ZIP. При учёте throttling/retry/ограничений сеть может занять от десятков минут до часов; точное время без pilot измерения не обещается. Ни один полный набор сейчас не загружен.

Формат: ZIP издателя + `.CHECKSUM` сохранить как immutable raw; normalized event/5m partition по `source/symbol/date` — **Parquet** (typed schema, columnar scan, compression), manifest JSON с `schema_version`, source URL, HTTP status, downloaded_at UTC, publisher checksum, own SHA256, размером, диапазоном UTC, market/contract/multiplier, семантикой времени и числом строк. CSV прозрачен для маленького funding/агрегата, CSV.gz портативен и дешевле CSV, но медленнее выборка колонок и слабая типизация; SQLite подходит для индекса/manifest, не для многогигабайтного raw trade/L2 и не должен использовать существующую PAPER БД. Один research run закрепляет manifest hash и code/protocol hash. Изменённый архив — новая версия, не тихая замена.

## Приоритет и GO / NO-GO

Оценки 1–5: больше `novelty`, `history`, `timestamp`, `1h/4h`, `value` — лучше; больше `complexity` и `storage` — дороже. `value` = **ценность для исследования**, не ожидаемая прибыльность. Подробная машинная матрица — [JSON](FUTURES_DATA_FEASIBILITY.json) и [CSV](FUTURES_DATA_SOURCES.csv).

| Source | Novelty / History / Complexity / Storage / Timestamp / 1h-4h / Value | Решение | Почему |
|---|---|---|---|
| Taker flow из 5m klines | 4/5/2/2/4/5/5 | **GO NOW** | сторона инициатора и форма потока сверх Spot OHLCV; 5m архив мал |
| OI из daily `metrics` | 5/4/3/2/2/5/4 | **GO NOW, только после timestamp gate** | positioning сверх OHLCV; история есть, метка `create_time` не документирована |
| Funding history | 4/4/2/1/4/4/4 | **GO NOW** | дешёвый historical crowding proxy, но тесно связан с premium/trend |
| Liquidation snapshots | 4/1/4/3/3/3/2 | **COLLECT PROSPECTIVELY** | нет доказанной полной истории, stream цензурирует события за 1s; отдельный будущий pilot |
| Best bid/ask spread | 3/1/3/2/4/3/3 | **COLLECT PROSPECTIVELY** | в первую очередь execution realism; без архива исторический OOS невозможен |
| Full L2 imbalance | 5/1/5/5/2/2/2 | **REJECT FOR CURRENT HORIZON** | дорого, сложная реконструкция, важнее для коротких горизонтов |
| Futures-vs-Spot basis | 4/4/3/2/4/4/4 | **GO NOW** | два рынка, исторические цены; проверить mapping и не смешивать с mark/index |

`aggTrades` как способ построить raw flow: **DEFER**, пока дешёвые taker fields не покажут incremental information. `mark/index/premium` — **DEFER** как отдельный большой слой, хотя small basis pilot возможен из уже нужных цен. Сторонние liquidation/L2 datasets не закупать сейчас: нужны доказуемая полнота, лицензия, история по 8 контрактам, доступная цена, timestamp lineage и независимая проверка; публичный поиск по неофициальным источникам не считается валидацией.

## План будущего исследования, без его выполнения

Максимум пять заранее описанных *кандидатных* гипотез, без порогов и параметрического перебора: (1) taker imbalance добавляет информацию к Spot/futures OHLCV для signed 1h/4h return; (2) знак/величина `ΔOI` меняют распределение исхода одинакового price move; (3) extreme historical funding после контроля за прошлым трендом/premium меняет вероятность volatility expansion; (4) нормализованный futures-Spot basis добавляет информацию к price-only baseline; (5) концентрация taker flow в конце уже закрытой свечи меняет следующий forward move. Это вопросы, **не сигналы**. Liquidation cluster можно формулировать только для будущих проспективно сохранённых данных и с пометкой snapshot censoring.

Будущий frozen protocol должен до просмотра outcome задать 1h/4h горизонты, signed return/absolute move/MFE/MAE/volatility expansion и, отдельно, TP-before-SL label с правилом одновременного касания; zero/base/double cost 0/0.3/0.6 п.п. пока нет измеренного spread/slippage. Хронологический train/validation/test, purging перекрывающихся forward окон, одинаковый universe/listing periods и coverage, группы символов и режимов, сравнение **A OHLCV only**, **B новые поля only**, **C OHLCV + новые поля** на *одинаковых* строках; оценка incremental uplift и интервалов по временным кластерам. Для taker flow нужен ещё строгий A2: **Spot + те же Futures OHLCV без taker-полей**, а C должен улучшать именно A2, иначе «улучшение» может прийти только от futures price/volume. Аналогично OI value следует сравнить с OI quantity + price, чтобы не принять изменение цены за positioning. Если новый источник лишь коррелирует с price или работает в одном месяце/мемкоине, этого недостаточно. ML на этом этапе не нужен.

Предлагаемая будущая offline структура — `research/market_data/{download,raw,manifest,normalize,validate,aggregate,features,dataset,replay}`. Зависимости: `download → immutable raw+checksums → normalize → validate → 5m aggregate → closed 1h/4h feature freeze → dataset join with Spot/targets → replay/evaluation`. Отдельный prospective collector **может** понадобиться только для spread/bid-ask и censored liquidation snapshots, не для первой v1. Если он когда-либо будет разрешён: read-only WS, receipt timestamp, bounded reconnect/backoff, gap/sequence detection, resnapshot for book, explicit unavailable intervals, 1m summaries and health metrics; отдельный процесс вне Telegram/API/scanner, без order endpoints и без ретроспективного «залечивания» потерь. Оценка диска для такого pilot требует суточной пробы, которую здесь не запускали.

**Остановиться здесь:** production code, `technical-v1`, PAPER/SQLite, DeepSeek, risk и env не менялись. Стратегия/ML/collector не создавались. Commit/push — **NO**. Следующий шаг требует отдельного выбора и разрешения на ограниченный historical download; не продолжать bulk collection автоматически.

Снимок `git status --short` после отчёта (изменение `backend/simple_bot.py` и остальные старые untracked research-файлы существовали до этого аудита; **новые здесь только три `FUTURES_DATA_*`**):

```text
 M backend/simple_bot.py
?? reports/FUTURES_DATA_FEASIBILITY.json
?? reports/FUTURES_DATA_FEASIBILITY.md
?? reports/FUTURES_DATA_SOURCES.csv
?? reports/MARKET_EDGE_DISCOVERY.json
?? reports/MARKET_EDGE_DISCOVERY.md
?? reports/MARKET_EDGE_EVENTS.csv
?? reports/OOS_2026_CONFIRMATION.json
?? reports/OOS_2026_CONFIRMATION.md
?? reports/OOS_2026_DATA/
?? reports/OOS_2026_EVENTS.csv
?? reports/OOS_2026_FROZEN_PROTOCOL.json
?? reports/OOS_2026_FROZEN_PROTOCOL.md
?? reports/PROSPECTIVE_32_TRADES.csv
?? reports/PROSPECTIVE_32_TRADE_AUDIT.json
?? reports/PROSPECTIVE_32_TRADE_AUDIT.md
?? reports/TECHNICAL_V2_CANDIDATES.csv
?? reports/TECHNICAL_V2_RESEARCH.json
?? reports/TECHNICAL_V2_RESEARCH.md
?? reports/market_edge_discovery.py
?? reports/oos_2026_confirmation.py
?? reports/technical_v2_replay.py
```
