# tradesync

AI Trading

## FTMO Challenge Trader

This repository includes a minimal FTMO challenge tracker that enforces:

- maximum daily loss (default: 5% of starting balance)
- maximum total loss (default: 10% of starting balance)
- profit target (default: 10% of starting balance)
- minimum trading days (default: 4)

### Quick example

```python
from ftmo_challenge_trader import FTMOChallengeTrader, execute_and_record_trade

trader = FTMOChallengeTrader(starting_balance=100000)

def execute_trade():
    return 1200.0  # Example execution engine PnL output

execute_and_record_trade(trader, execute_trade)
trader.end_day()
print(trader.report())
```

### Persistence

```python
trader.save_state("ftmo_state.json")
restored = FTMOChallengeTrader.load_state("ftmo_state.json")
```

### CLI

```bash
python /home/runner/work/tradesync/tradesync/ftmo_cli.py \
  --state-file /home/runner/work/tradesync/tradesync/ftmo_state.json \
  --starting-balance 100000 \
  --pnl 1200 \
  --end-day \
  --report
```
