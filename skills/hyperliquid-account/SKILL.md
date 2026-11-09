---
name: hyperliquid-account
description: The paper account is the simulator journal. This checkout does not read an exchange account, address, or balance. It cannot move funds.
license: MIT
metadata:
  version: "1.0.2"
  author: Galleon Labs
  category: hyperliquid
  network-default: public-info
---

# Paper account

The paper wallet is the append-only journal in `$HYPERGROK_STATE`. Replay it. Do not rewrite it.

This checkout does not read an exchange account. There is no address argument, no balance query, and no key. An exchange snapshot is not the paper wallet and cannot prove a paper fill.

If `$HYPERGROK_STATE` is unset, or the journal is missing, stop. Do not create a stand-in balance and do not fall back to `/workspace`.
