"""Read-only spot symbol constraints for paper fills; never places orders."""

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal

import requests
from market_data import normalize_symbol
from signal_models import TradePlan


@dataclass(frozen=True)
class ExchangeRules:
    tick: Decimal
    step: Decimal
    min_qty: Decimal
    max_qty: Decimal
    min_notional: Decimal

    def __post_init__(self):
        if not all(
            x.is_finite() for x in (self.tick, self.step, self.min_qty, self.max_qty, self.min_notional)
        ):
            raise ValueError("Non-finite exchange constraints")
        if (
            self.tick <= 0
            or self.step <= 0
            or self.min_qty < 0
            or self.max_qty <= self.min_qty
            or self.min_notional < 0
        ):
            raise ValueError("Invalid exchange constraints")

    def price(self, value, up=False):
        return float(
            (Decimal(str(value)) / self.tick).to_integral_value(rounding=ROUND_CEILING if up else ROUND_FLOOR)
            * self.tick
        )

    def plan(self, plan):
        long = plan.direction.value == "LONG"
        return TradePlan(
            direction=plan.direction,
            entry=self.price(plan.entry, up=long),
            stop_loss=self.price(plan.stop_loss, up=not long),
            take_profits=[self.price(p, up=long) for p in plan.take_profits],
        )

    def quantity(self, notional, price):
        quantity = (Decimal(str(notional)) / Decimal(str(price)) / self.step).to_integral_value(
            rounding=ROUND_FLOOR
        ) * self.step
        if not self.min_qty <= quantity <= self.max_qty or quantity * Decimal(str(price)) < self.min_notional:
            raise ValueError("Quantity or notional rejected")
        return float(quantity)


def get_exchange_rules(symbol):
    response = requests.get(
        "https://api.binance.com/api/v3/exchangeInfo",
        params={"symbol": normalize_symbol(symbol)},
        timeout=(5, 20),
    )
    response.raise_for_status()
    item = response.json()["symbols"][0]
    if item["symbol"] != normalize_symbol(symbol) or item["status"] != "TRADING":
        raise ValueError("Instrument unavailable")
    filters = {f["filterType"]: f for f in item["filters"]}
    price, lot = filters["PRICE_FILTER"], filters["LOT_SIZE"]
    notional = filters.get("NOTIONAL", filters.get("MIN_NOTIONAL"))
    if notional is None:
        raise ValueError("Missing notional constraints")
    return ExchangeRules(
        Decimal(price["tickSize"]),
        Decimal(lot["stepSize"]),
        Decimal(lot["minQty"]),
        Decimal(lot["maxQty"]),
        Decimal(notional["minNotional"]),
    )
