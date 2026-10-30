# Frozen higher-timeframe Spot structure protocol

The companion JSON is the machine-readable authority. Both files are frozen before examining any new forward outcome. This is an offline event-distribution study, not a trading strategy or PnL backtest.

Universe: the same eight logical Spot USDT pairs. Source: existing SHA-checked 4h files for 2024–2026 and a limited read-only public Binance Spot 4h extension for 2020–2023. A daily UTC candle aggregates exactly six consecutive closed 4h candles; partial days and prelisting periods are never filled. Discovery is 2020–2022, validation 2023–2025, and 2026 is a previously contaminated diagnostic. Previous research already examined 2024–2026.

Primary outcome for both timeframes is the direction-adjusted next-open to seven-day Spot close return (4h×42 or daily×7); H5 uses half the strongest-minus-weakest spread. Event candle is never part of the future result. Secondary horizons, absolute return and MFE/MAE are descriptive. All outcomes are purged at segment ends.

Five conceptual hypotheses, fixed normalized lookbacks, causal regime definitions, 14-day episode spacing, control strata, cost hurdles, month-block bootstrap, eight-test Holm adjustment and strict PROMISING gate are specified in JSON. H1 continuation and H2 reversal test opposite signs on the **same** large-move events and count as one family. Robust confirmation is impossible on this already studied history. No indicator sweep, AI, futures feature, production edit, order, commit or push.
