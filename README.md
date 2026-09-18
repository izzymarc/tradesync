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
from ftmo_challenge_trader import FTMOChallengeTrader

trader = FTMOChallengeTrader(starting_balance=100000)
trader.record_trade(1200)
trader.end_day()
```
