from decimal import Decimal

import pytest
from exchange_rules import ExchangeRules
from signal_models import TradePlan


def test_small_price_precision_and_min_notional():
    rules = ExchangeRules(*map(Decimal, ["0.00000001", "1", "1", "100000000000", "5"]))
    plan = rules.plan(
        TradePlan(
            direction="LONG",
            entry=0.000012345,
            stop_loss=0.000011101,
            take_profits=[0.000013333, 0.000014444, 0.000015555],
        )
    )
    assert plan.entry == 0.00001235
    assert plan.stop_loss == 0.00001110
    with pytest.raises(ValueError, match="notional"):
        rules.quantity(0.1, plan.entry)
    assert rules.quantity(100, plan.entry) > 0


def test_short_rounding_preserves_direction():
    rules = ExchangeRules(*map(Decimal, [".01", ".001", ".001", "100000", "5"]))
    plan = rules.plan(
        TradePlan(direction="SHORT", entry=100.123, stop_loss=101.123, take_profits=[99.123, 98.123, 97.123])
    )
    assert plan.entry == 100.12 and plan.stop_loss == 101.13
    assert plan.take_profits == [99.12, 98.12, 97.12]
