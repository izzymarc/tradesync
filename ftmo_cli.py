import argparse
from pathlib import Path

from ftmo_challenge_trader import FTMOChallengeTrader, format_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FTMO challenge tracker CLI")
    parser.add_argument("--state-file", required=True, help="Path to JSON state file")
    parser.add_argument("--starting-balance", type=float, help="Required when state file does not exist")
    parser.add_argument("--pnl", action="append", type=float, default=[], help="Trade PnL to record")
    parser.add_argument("--end-day", action="store_true", help="Close trading day")
    parser.add_argument("--report", action="store_true", help="Print challenge report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    state_file = Path(args.state_file)

    if state_file.exists():
        trader = FTMOChallengeTrader.load_state(state_file)
    else:
        if args.starting_balance is None:
            raise SystemExit("--starting-balance is required when initializing a new state file")
        trader = FTMOChallengeTrader(starting_balance=args.starting_balance)

    for pnl in args.pnl:
        trader.record_trade(pnl)

    if args.end_day:
        trader.end_day()

    trader.save_state(state_file)

    if args.report:
        print(format_report(trader.report()))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
