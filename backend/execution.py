"""Paper execution only. Partial exits and conservative intrabar ordering."""

from dataclasses import dataclass, field

from signal_models import Direction, TradePlan


@dataclass
class PaperPosition:
    plan: TradePlan
    quantity: float
    fee_rate: float = 0.001
    slippage: float = 0.0005
    remaining: float = 1.0
    realized_pnl: float = 0.0
    fills: list = field(default_factory=list)
    done: set = field(default_factory=set)

    @property
    def sign(self):
        return 1 if self.plan.direction == Direction.LONG else -1

    def enter(self, time):
        fee = self.quantity * self.plan.entry * self.fee_rate
        self.realized_pnl -= fee
        self.fills.append(
            {
                "time": str(time),
                "reason": "ENTRY",
                "price": self.plan.entry,
                "quantity": self.quantity,
                "fee": fee,
                "pnl": -fee,
            }
        )

    def close(self, price, fraction, reason, time):
        fraction = min(self.remaining, fraction)
        fill = price * (1 - self.sign * self.slippage)
        qty = self.quantity * fraction
        fee = qty * fill * self.fee_rate
        pnl = qty * (fill - self.plan.entry) * self.sign - fee
        self.realized_pnl += pnl
        self.remaining = max(0.0, self.remaining - fraction)
        self.fills.append(
            {"time": str(time), "reason": reason, "price": fill, "quantity": qty, "fee": fee, "pnl": pnl}
        )

    def mark(self, price):
        return self.realized_pnl + self.quantity * self.remaining * (price - self.plan.entry) * self.sign

    def on_bar(self, row):
        # SL before all TPs if both touched. Gaps filled at adverse open.
        stop = self.plan.stop_loss
        hit = row.low <= stop if self.sign == 1 else row.high >= stop
        if hit:
            price = min(stop, row.open) if self.sign == 1 else max(stop, row.open)
            self.close(price, self.remaining, "STOP_LOSS", row.close_time)
            return
        for i, (target, fraction) in enumerate(zip(self.plan.take_profits, (0.3, 0.3, 0.4))):
            if i in self.done:
                continue
            hit = row.high >= target if self.sign == 1 else row.low <= target
            if not hit:
                continue
            self.close(target, fraction, f"TP{i + 1}", row.close_time)
            self.done.add(i)
            # New stop applies next bar; never infer intrabar price sequence.
            if i == 0:
                self.plan.stop_loss = self.plan.entry
            elif i == 1:
                self.plan.stop_loss = self.plan.entry + (target - self.plan.entry) * 0.5
