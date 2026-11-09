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
: "${HYPERGROK_RUNTIME:?}"
: "${HYPERGROK_STATE:?}"
python3 "$HYPERGROK_RUNTIME/scripts/paper_sim.py" reset --state "$HYPERGROK_STATE"
python3 "$HYPERGROK_RUNTIME/scripts/paper_sim.py" submit \
  --config "$HYPERGROK_RUNTIME/config/paper.json" \
  --state "$HYPERGROK_STATE" \
  --symbol BTC --side buy --entry <inside the quote bid/ask> --size <size> \
  --take-profit <target> --trail-distance <distance>
```

The entry has to sit inside the quote bid and ask from the configured feed. The shipped config uses the public info feed. The file-quote procedure in the README is the offline path and the one the paper tests run. On the reviewed wall, runtime is `/opt/hypergrok-wall/runtime` and state is `/home/hypergrok/state`.

`reset` is required when the journal is missing. It writes a reset record. Deleting the journal does not restore a wallet by itself. `mark` moves the trailing stop and can fill the stop or target. `close` exits at the quote. Fees and slippage are applied, and equity is replayed from the journal.

The simulator rejects any other symbol, any order without `trailing_stop.distance`, any reward-to-risk under 2:1, and any order whose risk, including already accepted paper risk, is over 1% of the fixed $100 equity. It ignores a caller-supplied equity or force flag because those arguments do not exist. Accepted and rejected attempts that pass the journal check are not rewritten: the journal is append-only and hash-chained.

Prices come from `scripts/market_data.py`. Config chooses `hyperliquid` or `file`. The file source is a local JSON quote an outside process writes. There is no broker client in this repository.

## Ticket fields

`symbol` BTC or ETH, `side` buy or sell, `entry`, `size`, `take_profit`, and `trailing_stop.distance`. A buy take-profit is above the entry. A sell take-profit is below it. Risk is `size * distance` in quote currency. Reward is `size * |take_profit - entry|`.

Record the simulator's JSON in the proposal. A non-zero exit is a reject. Do not retry it against any other endpoint.
