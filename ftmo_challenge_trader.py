from dataclasses import dataclass
from pathlib import Path
import json
from typing import Callable


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

    def report(self) -> dict[str, float | int | bool]:
        max_daily_loss_used = max(0.0, -self._day_pnl)
        max_total_loss_used = max(0.0, -self._total_pnl)
        return {
            "balance": self.balance,
            "total_pnl": self._total_pnl,
            "daily_drawdown_used": max_daily_loss_used,
            "daily_drawdown_limit": self.rules.max_daily_loss,
            "total_drawdown_used": max_total_loss_used,
            "total_drawdown_limit": self.rules.max_total_loss,
            "trading_days": self._trading_days,
            "min_trading_days": self.rules.min_trading_days,
            "profit_target": self.rules.profit_target,
            "profit_target_reached": self.profit_target_reached,
            "passed": self.passed,
        }

    def save_state(self, path: str | Path) -> None:
        payload = {
            "starting_balance": self.starting_balance,
            "rules": {
                "max_daily_loss": self.rules.max_daily_loss,
                "max_total_loss": self.rules.max_total_loss,
                "profit_target": self.rules.profit_target,
                "min_trading_days": self.rules.min_trading_days,
            },
            "state": {
                "total_pnl": self._total_pnl,
                "day_pnl": self._day_pnl,
                "traded_today": self._traded_today,
                "trading_days": self._trading_days,
            },
        }
        target = Path(path)
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load_state(cls, path: str | Path) -> "FTMOChallengeTrader":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        rules = FTMORules(**payload["rules"])
        trader = cls(starting_balance=payload["starting_balance"], rules=rules)
        state = payload["state"]
        trader._total_pnl = float(state["total_pnl"])
        trader._day_pnl = float(state["day_pnl"])
        trader._traded_today = bool(state["traded_today"])
        trader._trading_days = int(state["trading_days"])
        return trader


def execute_and_record_trade(
    trader: FTMOChallengeTrader, execute_trade: Callable[..., float], *args, **kwargs
) -> float:
    pnl = float(execute_trade(*args, **kwargs))
    trader.record_trade(pnl)
    return pnl


def format_report(report: dict[str, float | int | bool]) -> str:
    return "\n".join(
        [
            f"Balance: {report['balance']:.2f}",
            f"Total PnL: {report['total_pnl']:.2f}",
            f"Daily Drawdown Used: {report['daily_drawdown_used']:.2f}/{report['daily_drawdown_limit']:.2f}",
            f"Total Drawdown Used: {report['total_drawdown_used']:.2f}/{report['total_drawdown_limit']:.2f}",
            f"Trading Days: {report['trading_days']}/{report['min_trading_days']}",
            f"Profit Target Reached: {report['profit_target_reached']}",
            f"Passed: {report['passed']}",
        ]
    )
