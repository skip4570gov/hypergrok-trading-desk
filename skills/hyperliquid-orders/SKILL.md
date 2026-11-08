---
name: hyperliquid-orders
description: Submit a local paper order through scripts/paper_sim.py. BTC and ETH only, trailing stop required, reward-to-risk at least 2:1, risk at most 1% of the $100 wallet. This checkout cannot sign or send an exchange order.
license: MIT
metadata:
  version: "2.0.0"
  author: Galleon Labs
  category: hyperliquid
---

# Paper orders

This skill does not sign, cancel, or send an exchange request. The only order command is the local simulator:

```bash
python3 scripts/paper_sim.py submit \
  --config config/paper.json \
  --journal /workspace/trading-desk/journal/paper.jsonl \
  --symbol BTC --side buy --entry 100000 --size 0.00001 \
  --take-profit 100200 --trail-distance 100
```

The simulator rejects any other symbol, any order without `trailing_stop.distance`, any reward-to-risk under 2:1, and any order whose risk, including already accepted paper risk, is over 1% of the fixed $100 equity. It ignores a caller-supplied equity or force flag because those arguments do not exist. Accepted and rejected attempts that pass the journal check are not rewritten: the journal is append-only and hash-chained.

Prices come from `scripts/market_data.py`. Config chooses `hyperliquid` or `file`. The file source is a local JSON quote an outside process writes. There is no broker client in this repository.

## Ticket fields

`symbol` BTC or ETH, `side` buy or sell, `entry`, `size`, `take_profit`, and `trailing_stop.distance`. A buy take-profit is above the entry. A sell take-profit is below it. Risk is `size * distance` in quote currency. Reward is `size * |take_profit - entry|`.

Record the simulator's JSON in the proposal. A non-zero exit is a reject. Do not retry it against any other endpoint.
