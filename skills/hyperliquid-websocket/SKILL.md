---
name: hyperliquid-websocket
description: This paper-only checkout does not open a trading socket or install a client SDK. Poll public info through scripts/market_data.py. Read-only. Use when a watch would otherwise have used a streaming client.
license: MIT
metadata:
  version: "1.0.1"
  author: Galleon Labs
  category: hyperliquid
  network-default: public-info
---

# Hyperliquid WebSocket

This checkout does not open a socket and does not ship a socket client. Do not subscribe, ping, or post over a WebSocket. Quotes come from `scripts/market_data.py`.

## Poll the public info feed

Do not install a client SDK and do not open a socket from this checkout. A watch records the latest `PriceFeed.quote` for BTC or ETH, including source and time, and alerts from that local record. A missed poll is unavailable data, not a flat book.

## Recover after a gap or restart

On a stale quote or a restart, pause new paper risk and replay the journal. A missed poll is unavailable data.

1. Read the journal hash chain. If it fails, stop.
2. Fetch a fresh BTC or ETH quote from `scripts/market_data.py`.
3. Run `scripts/paper_sim.py mark` only when the user has an open paper position and the quote is valid.
4. Do not send an order and do not look up exchange fills.

## Watch pattern

A watch is a condition plus an alert (`desk-monitoring`). Poll the allowlisted info feed, log the quote, evaluate the condition, and post the alert once with value, threshold, source, and UTC time. Do not send an order.

## Pitfalls

- Opening a socket because this file used to describe one. It does not.
- Treating a missed poll as a flat book. It is unavailable data.
- Watching a symbol other than BTC or ETH. The paper feed rejects it.
