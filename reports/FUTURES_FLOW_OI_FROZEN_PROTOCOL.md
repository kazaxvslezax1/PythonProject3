# Замороженный протокол: Futures flow / OI / funding, фаза 1

Зафиксирован **до просмотра forward outcomes нового исследования**. Машиночитаемое определение — [JSON](FUTURES_FLOW_OI_FROZEN_PROTOCOL.json); при расхождении приоритет имеет JSON. Цель — узнать, добавляют ли новые наблюдаемые поля информацию сверх Spot и Futures OHLCV. Это event study, не стратегия и не торговый PnL. Технический бот и PAPER не меняются.

## Gate OI

Решение: **`OI_CAUSALITY_UNCONFIRMED`**. [USD‑M REST reference](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data) определяет `openInterestHist.timestamp` как конец периода. [Официальный Public Data README](https://github.com/binance/binance-public-data/blob/master/README.md) не определяет `metrics.create_time`, период измерения и момент публикации архивной строки. Соответствие `create_time` и REST `timestamp` документально не доказано; возможен сдвиг/задняя метка. Ни один безопасный lag не обосновывает семантику без источника. OI не загружается и не участвует в H3/H5. Статус этих гипотез — `NOT TESTED`.

## Данные и время

Восемь Spot логических пар BTC, ETH, BNB, SOL, XRP, DOGE, SHIB, PEPE / USDT; Futures symbols совпадают, кроме SHIB→`1000SHIBUSDT` и PEPE→`1000PEPEUSDT`. Для basis коэффициент контракта 1000; basis не primary и без отдельной загрузки. Источник flow — официальные месячные USD‑M Futures 5m ZIP `data.binance.vision`; funding — публичный `/fapi/v1/fundingRate`; Spot — локальные проверенные файлы walk-forward 2024–25 и 4h OOS 2026. Данные берутся от 2024‑01‑01 00:00 UTC до 2026‑10‑01 00:00 UTC, exclusive, по последнему полностью опубликованному месяцу. 1h анализируется в 2024–25, 4h также в январе–сентябре 2026. Последний период уже затронут прошлым OHLCV исследованием, полностью нетронутым holdout не является.

На границе T используются только 12 или 48 закрытых 5m свечей, `closeTime <= T−1ms`; funding только с `fundingTime < T`. 5m с нулевым объёмом дают NULL imbalance. Нет `bfill`, переноса funding старше 24h, интерполяции пропусков или пересечения целевых окон с границами train/validation. Будущие OHLC используются лишь для outcome. Архив не доказывает нулевую live задержку публикации свечи; результатов PAPER исполнения здесь нет.

## Features, controls, outcomes

Flow: текущий нормированный imbalance `Σ(2×takerBuyBase−volume)/Σvolume`, средний imbalance трёх прошлых интервалов (взвешенный объёмом), persistence знака, acceleration, taker-buy share и контекст числа сделок относительно прошлых 24 интервалов. Funding: последний известный rate, знак, средний последних трёх и ранг абсолютной величины в прошлых 90 днях при 30+ записях. Цена: доходности за 1/3/6 завершённых баров, range, средний |return| 12 баров, текущий объём к прошлой 24‑барной медиане и close к прошлой 24‑барной средней. Контроль A — Spot OHLCV; A2 — Spot + те же Futures OHLCV **без taker**; B — flow/funding; C — A2 + B. Главный контроль — A2, поскольку без него улучшение можно ошибочно приписать flow вместо фьючерсной цены. Для формального comparison — одна Ridge `alpha=10` на каждую пару/TF, стандартизация только на 2024, одинаковые complete rows. Основная метрика uplift — `(MSE_A2−MSE_C)/MSE_A2` на 2025. Это модель измерения информации, не сигнала.

Outcome: Spot forward close-to-close signed и absolute return, а также MFE/MAE по **будущим** Spot high/low. 1h горизонты 1/3/6/12/24, primary 6; 4h 1/3/6/12, primary 3. Остальные exploratory. Направленный event-effect сравнивается с A2-предсказанием, обученным в discovery. Издержки 0/0.30/0.60 процентного пункта round trip показываются только как hurdle, не как реализуемый PnL.

## Шесть primary ячеек и решение

H1: сильный flow `|imbalance|≥q75`, совпадающий по знаку с текущим futures price move; гипотеза положительного будущего направленного residual относительно A2. H2: экстремальный flow `|imbalance|≥q90` после большого `|futures return|≥q75`, знаки совпадают; гипотеза отрицательного residual (истощение). H4: экстремальный **уже известный** `|funding|≥q90`; гипотеза положительного residual будущего абсолютного move. H3 и H5 не тестируются. Все пороги — квантили **только 2024 discovery** по паре/TF. Primary: H1/H2/H4 × 1h/4h; Holm correction для шести one-sided tests. Недельный UTC cluster bootstrap: 500 повторов, seed 20261028, все пары одной недели в одном блоке. Перекрытие горизонтов и общерыночная корреляция не позволяют считать свечи независимыми.

Классы `REJECT/WEAK/PROMISING/ROBUST` и точные условия приведены в JSON. Для `ROBUST` требуются эффект и Holm p<0.05 на 2025, >=6/8 согласованных пар, устойчивый leave-one-out, совпадающий знак на 2026 4h diagnostic, uplift C над A2 >=0.001, эффект >=0.30 п.п. и положительный после 0.60 п.п. hurdle, без утечки. Минимум 100 событий/12 недель. 2026 не внешний pristine test. Любой красивый отдельный secondary horizon не меняет primary verdict. Никаких SL/TP/entry правил из результата не строится.

## Бюджет до загрузки

33 полных месяца × 8 контрактов = **264 ZIP** и до **264 publisher `.CHECKSUM`**; funding ориентировочно **40 страниц** (точное число определяется ответами), итого примерно **568 GET**. По прошлой HEAD‑пробе ожидается около **110 MB** ZIP; жёсткий потолок **215 MiB** ZIP и **2 GiB** дополнительного рабочего места. До загрузки свободно около **41 GiB**. При выходе за пределы скрипт останавливается. Raw ZIP/JSON неизменяемы, SHA‑256 и UTC download time фиксируются в manifest. Normalized — CSV.gz: `pyarrow` в текущей среде отсутствует, установка новой зависимости не нужна. Схемы, дубликаты, сетка 5m, OHLC, объём, taker≤total, count, funding gaps проверяются отдельно по symbol/source. Повторный запуск не загружает валидные файлы снова.
