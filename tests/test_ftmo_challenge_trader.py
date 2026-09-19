import unittest
from pathlib import Path
import subprocess
import sys
import tempfile

from ftmo_challenge_trader import (
    FTMOChallengeTrader,
    FTMORuleBreachError,
    execute_and_record_trade,
    format_report,
)


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

    def test_daily_loss_exact_boundary_is_allowed(self) -> None:
        trader = FTMOChallengeTrader(starting_balance=100000)
        trader.record_trade(-5000)
        self.assertEqual(trader.total_pnl, -5000)

    def test_total_loss_exact_boundary_is_allowed(self) -> None:
        trader = FTMOChallengeTrader(starting_balance=100000)
        trader.record_trade(-5000)
        trader.end_day()
        trader.record_trade(-5000)
        self.assertEqual(trader.total_pnl, -10000)

    def test_zero_pnl_day_does_not_count_as_trading_day(self) -> None:
        trader = FTMOChallengeTrader(starting_balance=100000)
        trader.record_trade(0)
        trader.end_day()
        self.assertEqual(trader.trading_days, 0)

    def test_multiple_trades_in_same_day_are_accumulated(self) -> None:
        trader = FTMOChallengeTrader(starting_balance=100000)
        trader.record_trade(-2000)
        trader.record_trade(-2000)
        self.assertEqual(trader.total_pnl, -4000)
        with self.assertRaises(FTMORuleBreachError):
            trader.record_trade(-1001)

    def test_report_contains_core_status_fields(self) -> None:
        trader = FTMOChallengeTrader(starting_balance=100000)
        trader.record_trade(-1200)
        report = trader.report()
        self.assertEqual(report["balance"], 98800.0)
        self.assertEqual(report["daily_drawdown_used"], 1200.0)
        self.assertEqual(report["total_drawdown_used"], 1200.0)
        self.assertFalse(report["passed"])
        rendered = format_report(report)
        self.assertIn("Balance: 98800.00", rendered)
        self.assertIn("Passed: False", rendered)

    def test_persistence_round_trip(self) -> None:
        trader = FTMOChallengeTrader(starting_balance=100000)
        trader.record_trade(1500)
        trader.end_day()

        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "ftmo_state.json"
            trader.save_state(state_file)
            restored = FTMOChallengeTrader.load_state(state_file)

        self.assertEqual(restored.balance, 101500.0)
        self.assertEqual(restored.trading_days, 1)
        self.assertEqual(restored.total_pnl, 1500.0)

    def test_execution_flow_records_trade_automatically(self) -> None:
        trader = FTMOChallengeTrader(starting_balance=100000)

        def mock_execute() -> float:
            return 750.0

        pnl = execute_and_record_trade(trader, mock_execute)
        self.assertEqual(pnl, 750.0)
        self.assertEqual(trader.total_pnl, 750.0)

    def test_cli_initializes_persists_and_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "state.json"
            cli_path = Path(__file__).resolve().parents[1] / "ftmo_cli.py"

            result = subprocess.run(
                [
                    sys.executable,
                    str(cli_path),
                    "--state-file",
                    str(state_file),
                    "--starting-balance",
                    "100000",
                    "--pnl",
                    "1200",
                    "--end-day",
                    "--report",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            self.assertIn("Balance: 101200.00", result.stdout)
            restored = FTMOChallengeTrader.load_state(state_file)
            self.assertEqual(restored.total_pnl, 1200.0)
            self.assertEqual(restored.trading_days, 1)


if __name__ == "__main__":
    unittest.main()
