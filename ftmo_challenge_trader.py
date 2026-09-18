from dataclasses import dataclass


class FTMORuleBreachError(ValueError):
    """Raised when a trade would violate FTMO challenge rules."""


@dataclass(frozen=True)
class FTMORules:
    max_daily_loss: float
    max_total_loss: float
    profit_target: float
    min_trading_days: int = 4


class FTMOChallengeTrader:
    def __init__(
        self,
        starting_balance: float,
        rules: FTMORules | None = None,
    ) -> None:
        if starting_balance <= 0:
            raise ValueError("starting_balance must be positive")

        self.starting_balance = float(starting_balance)
        self.rules = rules or FTMORules(
            max_daily_loss=self.starting_balance * 0.05,
            max_total_loss=self.starting_balance * 0.10,
            profit_target=self.starting_balance * 0.10,
            min_trading_days=4,
        )

        self._total_pnl = 0.0
        self._day_pnl = 0.0
        self._traded_today = False
        self._trading_days = 0

    @property
    def balance(self) -> float:
        return self.starting_balance + self._total_pnl

    @property
    def total_pnl(self) -> float:
        return self._total_pnl

    @property
    def trading_days(self) -> int:
        return self._trading_days

    @property
    def profit_target_reached(self) -> bool:
        return self._total_pnl >= self.rules.profit_target

    @property
    def passed(self) -> bool:
        return self.profit_target_reached and self._trading_days >= self.rules.min_trading_days

    def record_trade(self, pnl: float) -> None:
        proposed_day_pnl = self._day_pnl + pnl
        proposed_total_pnl = self._total_pnl + pnl

        if proposed_day_pnl < -self.rules.max_daily_loss:
            raise FTMORuleBreachError("daily loss limit would be exceeded")

        if proposed_total_pnl < -self.rules.max_total_loss:
            raise FTMORuleBreachError("total loss limit would be exceeded")

        self._day_pnl = proposed_day_pnl
        self._total_pnl = proposed_total_pnl
        if pnl != 0:
            self._traded_today = True

    def end_day(self) -> None:
        if self._traded_today:
            self._trading_days += 1
        self._day_pnl = 0.0
        self._traded_today = False
