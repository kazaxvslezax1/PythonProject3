"""Typed, verifiable input sent to AI; timestamps are always UTC."""

import math
from typing import Literal

import pandas as pd
from market_data import INTERVALS, utc, validate_candles
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator
from signal_models import TradingSignal
from strategy_engine import generate_signal, indicator_values

INDICATOR_KEYS = {
    "RSI",
    "MACD",
    "MACD_Signal",
    "SMA_20",
    "SMA_50",
    "EMA_12",
    "EMA_26",
    "ATR",
    "ADX",
    "BB_Upper",
    "BB_Middle",
    "BB_Lower",
    "Volume_Ratio",
    "Volatility",
}


class Candle(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    time: AwareDatetime
    close_time: AwareDatetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)


class TimeframeEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    timeframe: str
    close_time: AwareDatetime
    direction: Literal["LONG", "SHORT", "HOLD"]


class MarketSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    symbol: str = Field(pattern=r"^[A-Z0-9]{2,20}USDT$")
    timeframe: str
    as_of: AwareDatetime
    candles: list[Candle] = Field(min_length=60, max_length=300)
    indicators: dict[str, float]
    volume_change_pct: float
    trend: Literal["LONG", "SHORT", "HOLD"]
    support: float = Field(gt=0)
    resistance: float = Field(gt=0)
    timeframes: list[TimeframeEvidence]
    confluence: float | None = Field(default=None, ge=0, le=100)
    technical: TradingSignal
    risk_reward: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_snapshot(self):
        df = pd.DataFrame([c.model_dump() for c in self.candles])
        validate_candles(df, self.timeframe, self.as_of, min_bars=60)
        if self.symbol != self.technical.symbol or self.timeframe != self.technical.timeframe:
            raise ValueError("Signal identity mismatch")
        if self.technical.timestamp != self.candles[-1].close_time:
            raise ValueError("Signal timestamp mismatch")
        if set(self.indicators) != INDICATOR_KEYS or not all(
            math.isfinite(v) for v in self.indicators.values()
        ):
            raise ValueError("Invalid indicators")
        actual = indicator_values(df)
        if any(
            not math.isclose(v, actual[k], rel_tol=1e-8, abs_tol=1e-8) for k, v in self.indicators.items()
        ):
            raise ValueError("Indicators do not match OHLCV")
        expected = generate_signal(df, self.symbol, self.timeframe, self.as_of)
        if expected != self.technical:
            raise ValueError("Technical signal does not match OHLCV")
        if self.trend != expected.direction.value:
            raise ValueError("Trend mismatch")
        if self.support != float(df.low.tail(20).min()) or self.resistance != float(df.high.tail(20).max()):
            raise ValueError("Invalid levels")
        ratio = (
            (float(df.volume.iloc[-1]) / float(df.volume.iloc[-2]) - 1) * 100
            if df.volume.iloc[-2] > 0
            else 0.0
        )
        if not math.isclose(self.volume_change_pct, ratio, abs_tol=1e-8):
            raise ValueError("Volume change mismatch")
        expected_rr = expected.plan.rr if expected.plan else None
        if self.risk_reward != expected_rr:
            raise ValueError("R/R mismatch")
        if len({e.timeframe for e in self.timeframes}) != len(self.timeframes):
            raise ValueError("Duplicate timeframe evidence")
        for item in self.timeframes:
            if item.timeframe not in INTERVALS or item.close_time >= self.as_of:
                raise ValueError("Future or invalid timeframe evidence")
            if (self.as_of - item.close_time).total_seconds() > INTERVALS[item.timeframe] + 30:
                raise ValueError("Stale timeframe evidence")
        agree = sum(e.direction == self.trend for e in self.timeframes)
        expected_confluence = 100 * agree / len(self.timeframes) if self.timeframes else None
        if self.confluence != expected_confluence:
            raise ValueError("Confluence mismatch")
        return self

    def references(self):
        refs = {
            **self.indicators,
            "close": self.candles[-1].close,
            "support": self.support,
            "resistance": self.resistance,
            "volume_change_pct": self.volume_change_pct,
        }
        if self.confluence is not None:
            refs["confluence"] = self.confluence
        if self.technical.plan:
            plan = self.technical.plan
            refs.update(
                entry=plan.entry,
                stop_loss=plan.stop_loss,
                tp1=plan.take_profits[0],
                tp2=plan.take_profits[1],
                tp3=plan.take_profits[2],
                risk_reward=plan.rr,
            )
        return refs


def build_snapshot(df, symbol, timeframe, as_of, timeframes=None):
    df = validate_candles(df, timeframe, as_of, min_bars=60)
    signal = generate_signal(df, symbol, timeframe, as_of)
    evidence = timeframes or []
    volume_prev = float(df.volume.iloc[-2])
    return MarketSnapshot(
        symbol=signal.symbol,
        timeframe=timeframe,
        as_of=utc(as_of).to_pydatetime(),
        candles=[Candle(**r) for r in df.to_dict("records")],
        indicators=indicator_values(df),
        volume_change_pct=(float(df.volume.iloc[-1]) / volume_prev - 1) * 100 if volume_prev > 0 else 0,
        trend=signal.direction.value,
        support=float(df.low.tail(20).min()),
        resistance=float(df.high.tail(20).max()),
        timeframes=evidence,
        confluence=100 * sum(e.direction == signal.direction.value for e in evidence) / len(evidence)
        if evidence
        else None,
        technical=signal,
        risk_reward=signal.plan.rr if signal.plan else None,
    )


def live_snapshot(symbol, timeframe="1h", as_of=None, loader=None):
    from data import get_candles

    loader = loader or get_candles
    cutoff = utc(as_of)
    frames = {
        tf: loader(symbol, tf, limit=120, as_of=cutoff) for tf in dict.fromkeys([timeframe, "1h", "4h"])
    }
    evidence = []
    for tf, df in frames.items():
        sig = generate_signal(df, symbol, tf, cutoff)
        evidence.append(
            TimeframeEvidence(timeframe=tf, close_time=sig.timestamp, direction=sig.direction.value)
        )
    return build_snapshot(frames[timeframe], symbol, timeframe, cutoff, evidence)
