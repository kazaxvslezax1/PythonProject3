"""Shared contracts: quality is a heuristic score, never a probability."""

from enum import Enum
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Direction(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    HOLD = "HOLD"


def direction(value):
    return Direction({"BUY": "LONG", "SELL": "SHORT"}.get(value, value))


class TradePlan(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    direction: Direction
    entry: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    take_profits: list[float] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def valid_levels(self):
        if self.direction == Direction.LONG:
            valid = (
                0
                < self.stop_loss
                < self.entry
                < self.take_profits[0]
                < self.take_profits[1]
                < self.take_profits[2]
            )
        elif self.direction == Direction.SHORT:
            valid = (
                0
                < self.take_profits[2]
                < self.take_profits[1]
                < self.take_profits[0]
                < self.entry
                < self.stop_loss
            )
        else:
            valid = False
        if not valid:
            raise ValueError("Invalid directional trade levels")
        return self

    @property
    def rr(self):
        return abs(self.take_profits[-1] - self.entry) / abs(self.entry - self.stop_loss)


class TradingSignal(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    symbol: str
    timeframe: str
    timestamp: AwareDatetime
    direction: Direction
    quality: float = Field(ge=0, le=10)
    strength: float = Field(ge=-10, le=10)
    status: Literal["OK", "DATA_UNAVAILABLE"] = "OK"
    reasons: list[str]
    plan: TradePlan | None = None
    strategy_version: str = "technical-v1"

    @model_validator(mode="after")
    def coherent(self):
        if self.direction != Direction.HOLD and (not self.plan or self.plan.direction != self.direction):
            raise ValueError("Directional signal requires matching plan")
        if self.direction == Direction.HOLD and self.plan:
            raise ValueError("HOLD cannot contain a trade plan")
        return self
