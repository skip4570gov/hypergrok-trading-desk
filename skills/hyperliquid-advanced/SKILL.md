---
name: hyperliquid-advanced
description: Actions this paper desk does not implement. No dead-man switch, TWAP, spot order, agent approval, sub-account, transfer, or withdrawal. Use to refuse those requests.
license: MIT
metadata:
  version: "2.0.0"
  author: Galleon Labs
  category: hyperliquid
---

# Refused actions

This checkout has no function for a dead-man's switch, TWAP, spot order, agent approval, sub-account, vault, transfer, bridge, or withdrawal. `scripts/paper_sim.py` rejects an order whose type is transfer, withdraw, deposit, or send.

If a request asks for any of those, say it is unavailable on the paper-only branch and stop. Do not sketch a signed payload, install a client, or point at another network. Switching to `main` or commit `01c2a46` is a repository revert described in `REVERT.md`, not a trading step, and this branch does not perform it.
