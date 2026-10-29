# OOS 2026: проверка замороженной гипотезы

**Вердикт: `NOT CONFIRMED`.** Это outcome 24-барного event study, не торговая стратегия и не исторический PAPER PnL.

Период UTC: 2026-01-01T00:00:00Z — 2026-10-26T04:00:00Z (конец не включён). 4h, 8 пар, 1789 закрытых свечей на пару. 120 исторических свечей 2025 — только прогрев.

Замороженная гипотеза: альткоин закрывается за предыдущим 24-bar high/low; одновременно закрытый BTC efficiency≤0.15. Следующий open → close 24-й свечи (96 часов). Zero/base/double cost: 0/0.30/0.60 п.п. Основная метрика — mean signed return после base.

N=222; недели=38; base mean=-1.7088%; 95% week-bootstrap lower=-4.1209%.

## Проверка критериев

| Критерий | Выполнен |
|---|---|
|minimum_n|да|
|minimum_event_weeks|да|
|base_mean_gt_zero|нет|
|bootstrap_lower_gt_zero|нет|
|base_median_gte_zero|нет|
|double_mean_gt_zero|нет|
|temporal_stability|нет|
|symbol_stability|нет|
|leave_one_symbol_out|нет|
|remove_best_event|нет|
|top5pct_contribution|нет|
|incremental_control_A|нет|
|excess_control_B|нет|
|excess_control_C|нет|

## Издержки и распределение

|Сценарий|N|Mean %|Median %|Win >0|p05 %|p90 %|
|---|---:|---:|---:|---:|---:|---:|
|zero|222|-1.4088|-1.6708|0.360|-14.6883|+5.9290|
|base|222|-1.7088|-1.9708|0.351|-14.9883|+5.6290|
|double|222|-2.0088|-2.2708|0.338|-15.2883|+5.3290|

MFE mean=+5.1900%, MAE mean=-6.4215%, median MFE/|MAE|=0.5712313250094053. Квантили p10/p25/p75 и полные распределения — JSON.

## Контроли

A все breakout N=860, mean base=-0.5169%; A вне BTC-range N=638, mean base=-0.1022%; incremental=-1.6066 п.п.
B средний excess=-1.5725 п.п.; C matched symbol/month/vol/momentum excess=-1.6571 п.п. Это описательные контроли, не доказательство причинности.

## Временная и парная устойчивость

|Месяц|N|Mean base %|
|---|---:|---:|
|2026-01|16|+0.9241|
|2026-02|52|-6.2193|
|2026-03|14|-2.4228|
|2026-04|19|-2.5105|
|2026-05|21|-1.7086|
|2026-06|18|+0.7455|
|2026-07|32|-0.3688|
|2026-08|12|+0.2135|
|2026-09|16|+1.2146|
|2026-10|22|+1.0524|

|Пара|N|Mean base %|Без пары mean base %|
|---|---:|---:|---:|
|ETHUSDT|29|-1.9600|-1.6710|
|BNBUSDT|37|-2.5973|-1.5311|
|SOLUSDT|29|-2.5643|-1.5802|
|XRPUSDT|27|-2.5415|-1.5935|
|DOGEUSDT|33|-3.3049|-1.4301|
|SHIBUSDT|32|-2.4918|-1.5769|
|PEPEUSDT|35|+3.0108|-2.5921|

## Выбросы и данные

Без лучшего события mean base=-1.9264%; доля всех положительных gross returns от top 1%=0.258, top 5%=0.536.

|Пара|2026 свечей|SHA256 CSV|Зрелые breakout|Незрелые conditioned|
|---|---:|---|---:|---:|
|BTCUSDT|1789|`f63e733e52e931a959b7dc7a1089f633e069d89a1a93a2f585e2a3abaf10daf6`|—|—|
|ETHUSDT|1789|`d33e173b274ddd746767c2bd141053bd5752f7a5908be9a6bd0d7abf5b613313`|114|0|
|BNBUSDT|1789|`f634bd8bc99346273400a2d52245b22fe1e1413cf0855d36476887021a0a292f`|138|0|
|SOLUSDT|1789|`0249d66bd9db518608abc0fc1f28fc75427e4b5a0c160756768e91965302cde8`|136|2|
|XRPUSDT|1789|`1b162304cb7d08fb7a0700443c95bc6607c6642d67ec1c9eccf94a2aca8a1002`|141|0|
|DOGEUSDT|1789|`0899bd355b1a69ad5a7be3a52790d5563bbf1fc968c726fbece6c7091d8e786e`|107|0|
|SHIBUSDT|1789|`54ee2ba591e946e6da0b77ca0591a088e6039a1e850e297de6089bb8b5d74188`|119|0|
|PEPEUSDT|1789|`83c76dfcff2db0b090ebfce45b801ed99565bf5f772ceaec160ffa109f0d76dc`|105|1|

Во всех рядах: missing=0, duplicates=0, invalid OHLC=0, UTC 4h grid и закрытие свечи проверены. Незрелые правые события не оценивались; месяцы/пары с плохим результатом не исключались.

## Воспроизводимость и ограничения

Frozen MD SHA256 `f0a91f1bd7cb80a1fd379ddbb03996c65efa6728c7bd9baf5ff00e2c572c50e6`; JSON SHA256 `10d4457f4f8afbd246340f572d12580843e47d0c42095f124c797b95101ffe7d`; analysis code SHA256 `f7a0362cf1c986defaebc0c1b077877867c72f38da7107c1bd1883b768e8a599`; исходный research-code SHA256 `0fe0e8205234f02068acb50fb5677ef01c0339cd3b550f8de6a86a21601d71db`.

`python3 -B reports/oos_2026_confirmation.py --self-test` затем `python3 -B reports/oos_2026_confirmation.py --evaluate` с неизменёнными файлами данных. `--fetch` нужен только для первичной публичной загрузки и не перезаписывает файлы.

Гипотеза выбрана после просмотра 2024–2025. События перекрываются, 24-bar выход не учитывает путь исполнения SL/TP, funding, spread/impact и реализованный портфель. Даже `CONFIRMED` не разрешает менять действующий PAPER bot. Следующий исследовательский этап требует новой будущей полосы; потенциально независимые от OHLCV признаки — bid/ask spread, order-book imbalance, aggressor flow, фактическое проскальзывание, funding, open interest и liquidations — могут добавлять новые сведения, но edge не гарантируют.
