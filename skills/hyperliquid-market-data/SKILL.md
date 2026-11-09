---
name: hyperliquid-market-data
description: Read public market data through scripts/market_data.py. The Hyperliquid feed posts only to the allowlisted info URL. A local file feed can supply BTC and ETH quotes. No key and no base URL override. Use for any market brief, depth read, funding question or data pull.
license: MIT
metadata:
  version: "1.2.2"
  author: Galleon Labs
  category: hyperliquid
  network-default: mainnet-for-reads
---

# Hyperliquid market data

Quotes for this desk come from `scripts/market_data.py`. The paper symbols are BTC and ETH.

The Hyperliquid feed posts only to `https://api.hyperliquid.xyz/info`. It refuses any other host, follows no redirect, and does not use environment proxies. There is no `--base-url` and no testnet switch. A host relay may allow all of `api.hyperliquid.xyz:443`, including `/exchange`. This module does not post there and has no signer. Do not describe the host as path-filtered.

`config/paper.json` selects the source:

- `price_source: hyperliquid` reads the public info feed. That is the shipped default.
- `price_source: file` reads a local JSON file an outside process writes. The README schema is `symbol`, `bid`, `ask`, `mark`, `source` of `robinhood`, and `fetched_at`. Only BTC and ETH are accepted. Stale, non-finite, or out-of-spread marks are rejected. The default max age is 300 seconds.
- `fallback` is `none` in the shipped config. A file feed uses Hyperliquid only when `fallback` is exactly `hyperliquid`.

Every quote records `feed` as `file` or `hyperliquid`. Say that identity and the UTC time. Do not call another client for the same number.

A quote has `symbol`, `bid`, `ask`, `mark`, `source`, `feed`, and `fetched_at`. A paper entry must sit between bid and ask. This skill does not place that order. Submit stays in `scripts/paper_sim.py`.

This checkout does not collect candle history, funding history, or a second-origin book. If a brief needs a field this feed does not return, say it is unavailable. Do not invent depth, funding, or another URL.

Runtime files are under `$HYPERGROK_RUNTIME`. If that variable is unset, stop. Do not look in `/workspace`.
