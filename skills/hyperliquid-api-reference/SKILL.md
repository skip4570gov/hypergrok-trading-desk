---
name: hyperliquid-api-reference
description: Read-only reference for the paper desk. Public market data uses one allowlisted info URL. This checkout documents no signing scheme and no exchange-write action.
license: MIT
metadata:
  version: "2.0.0"
  author: Galleon Labs
  category: hyperliquid
---

# Read-only reference

The only market-data request this checkout implements is a POST to `https://api.hyperliquid.xyz/info`. `scripts/market_data.py` refuses every other URL. Scripts do not accept `--base-url` or `--testnet`.

`PriceFeed.quote(symbol)` returns bid, ask, mark, source, and time for BTC or ETH. `HyperliquidInfoFeed` implements it from the public book. `FileQuoteFeed` implements it from a local JSON file. `build_feed` selects one from config and falls back to the public info feed only when the file cannot supply a fresh BTC or ETH quote.

Info request types still used by the read scripts include `allMids`, `l2Book`, `meta`, `metaAndAssetCtxs`, and `candleSnapshot`. They are reads. This file does not list a signing scheme or a write action.

Quote file fields are `symbol`, `bid`, `ask`, `mark`, `source` (`robinhood`), and `fetched_at` (timezone-aware ISO8601). See the README for the schema and the stale-quote rule.
