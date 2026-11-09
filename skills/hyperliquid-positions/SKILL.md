---
name: hyperliquid-positions
description: Paper positions live only in the simulator journal. This checkout cannot change leverage, margin, or an exchange position, and it cannot close or transfer one.
license: MIT
metadata:
  version: "2.0.0"
  author: Galleon Labs
  category: hyperliquid
---

# Paper positions

There is no leverage, margin mode, or reduce-only close in this checkout. The paper book is the accepted events in the simulator journal. Reconstruct it by reading that file. Do not rewrite it.

Open risk is the sum of accepted `risk_usd` values. It starts from a $100 wallet and cannot grow by deposit. A new order is rejected when the added risk would put open risk over $1.

There is no exchange account read. The journal is the only position record.
