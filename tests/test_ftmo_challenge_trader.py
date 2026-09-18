import unittest

from ftmo_challenge_trader import FTMOChallengeTrader, FTMORuleBreachError


class TestFTMOChallengeTrader(unittest.TestCase):
    def test_passes_only_after_profit_target_and_min_days(self) -> None:
        trader = FTMOChallengeTrader(starting_balance=100000)

        for _ in range(3):
            trader.record_trade(3000)
            trader.end_day()

        self.assertFalse(trader.passed)

        trader.record_trade(1000)
        trader.end_day()

        self.assertTrue(trader.profit_target_reached)
        self.assertTrue(trader.passed)

    def test_daily_loss_limit_breach_raises(self) -> None:
        trader = FTMOChallengeTrader(starting_balance=100000)

        with self.assertRaises(FTMORuleBreachError):
            trader.record_trade(-5001)

    def test_total_loss_limit_breach_raises(self) -> None:
        trader = FTMOChallengeTrader(starting_balance=100000)

        trader.record_trade(-5000)
        trader.end_day()

        with self.assertRaises(FTMORuleBreachError):
            trader.record_trade(-5001)


if __name__ == "__main__":
    unittest.main()
