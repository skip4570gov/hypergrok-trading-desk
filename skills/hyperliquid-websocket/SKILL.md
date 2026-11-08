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

Read-only, no key. This checkout does not ship a socket client. Price and book reads use `scripts/market_data.py` and the allowlisted info URL.

## Protocol

Subscribe: `{"method": "subscribe", "subscription": {...}}`. Unsubscribe with `"method": "unsubscribe"`. The server acknowledges with `{"channel": "subscriptionResponse", ...}` then streams `{"channel": "<type>", "data": ...}`. Send `{"method": "ping"}` periodically (the SDKs do it for you; the server expects activity within about a minute) and expect `{"channel": "pong"}`.

Subscription types the desk uses:

| Type | Subscription JSON | Data |
| --- | --- | --- |
| Mids for all markets | `{"type":"allMids"}` (optional `"dex"`) | `{"mids": {"BTC": "97123.5", ...}}` |
| Order book | `{"type":"l2Book","coin":"ETH"}` (optional `nSigFigs`, `mantissa`, `fast: true` for 5 levels) | `{"coin","time","levels":[bids,asks]}`, up to 20 levels a side, pushed on each block at least 0.5 s after the last push |
| Trades | `{"type":"trades","coin":"ETH"}` | array of `{coin, side, px, sz, time, hash, tid, users}` |
| Candles | `{"type":"candle","coin":"ETH","interval":"1m"}` | `{t,T,s,i,o,c,h,l,v,n}` updated in place until the bar closes |
| Best bid/offer | `{"type":"bbo","coin":"ETH"}` | `{"coin","time","bbo":[bid, ask]}` |
| Asset context | `{"type":"activeAssetCtx","coin":"ETH"}` | funding, OI, mark, oracle, premium, volume for one market |
| Account fills | `{"type":"userFills","user":"0x..."}` | `{"user","isSnapshot","fills":[...]}` (first message is a snapshot) |
| Order updates | `{"type":"orderUpdates","user":"0x..."}` | array of `{order:{coin,side,limitPx,sz,oid,timestamp,origSz,cloid}, status, statusTimestamp}` |
| Account events | `{"type":"userEvents","user":"0x..."}` | fills, funding, liquidation, non-user cancels; arrives on channel `"user"` |
| Account funding | `{"type":"userFundings","user":"0x..."}` | hourly funding payments |
| Per-market account data | `{"type":"activeAssetData","user":"0x...","coin":"ETH"}` | leverage setting, max trade sizes, available to trade, mark (perps only) |
| Account state stream | `{"type":"clearinghouseState","user":"0x..."}` / `{"type":"openOrders","user":"0x..."}` | `{dex, user, clearinghouseState:{...REST shape...}}` / `{dex, user, orders:[...]}` (order items carry the frontend fields: `isTrigger`, `triggerPx`, `orderType`, `cloid`), pushed |
| TWAP state | `{"type":"twapStates","user":"0x...","dex":""}` / `{"type":"userTwapSliceFills","user":"0x..."}` | running TWAPs and their slice fills |
| Frontend snapshot | `{"type":"webData3","user":"0x..."}` | positions, orders and context in one stream (heavy) |

Limits per IP: up to 10 connections, 30 new connections per minute, 1000 subscriptions, 10 distinct users across user subscriptions, 2000 messages per minute. The server closes a connection silent for 60 seconds. One connection per watch process is plenty.

You can also send `/info` requests over the socket: `{"method":"post","id":1,"request":{"type":"info","payload":{"type":"allMids"}}}` returns `{"channel":"post","data":{"id":1,"response":{...}}}`. Useful inside a watch to avoid mixing REST and WS.

## Poll the public info feed

Do not install a client SDK and do not open a socket from this checkout. A watch records the latest `PriceFeed.quote` for BTC or ETH, including source and time, and alerts from that local record. A missed poll is unavailable data, not a flat book.

## Recover after a gap or restart

Treat account events as prompts to reconcile, not proof of a gap-free history. On a disconnect, stale heartbeat, process restart or uncertain event order, record the last good UTC time, alert `unavailable`, and pause new-risk sends. Retain pending risk reservations and the daily-stop latch; restarting does not clear either.

1. Re-establish the account subscriptions and confirm their acknowledgements. Record a new connection generation so cached messages and old snapshots cannot satisfy recovery.
2. Fetch fresh `/info` account state, `frontendOpenOrders`, and order statuses for every outstanding ticket after reconnect. Recover `userFillsByTime` from an overlap before the last good time through the new reads, with pagination. At desk startup use the last durable reconciliation time; if it is absent or outside the retained history, say that coverage is unavailable.
3. Merge REST history and streamed fills without double counting, using account/network plus `(time, coin, tid)` as the fill identity. Include snapshot fills not already processed. Preserve equal-timestamp boundaries when paging; a saturated page with no forward progress is incomplete evidence, not the end of history.
4. Compare positions, orders, protection and proposal reservations. Separate responses are not atomic: if account activity occurs during the reads or they disagree, refresh the affected state. Keep unknown sends reserved and follow `desk-execution-protocol`; silence never resolves them.
5. Record the recovery window, sources, timestamps and any unresolved gaps. Risk permits new risk only after coverage is complete, the account agrees with the reconciled journal, and a fresh capacity check passes. Report the recovery once. If evidence remains incomplete, keep new risk paused and route protection or exits through the normal approval gates using verified live state.

For a public price/book watch, refresh that market's snapshot and reset its condition baseline before reporting an unchanged result. A recovered price feed alone cannot restore account readiness.

## Watch pattern

A watch is a condition plus an alert (`desk-monitoring`). Poll the allowlisted info feed, log the quote, evaluate the condition, and post the alert once with value, threshold, source, and UTC time. Do not send an order.

## Pitfalls

- Treating the first `userFills` message as new fills; it is a snapshot (`isSnapshot: true`).
- Candle messages repeat for the open bar; act on bar close (`T` reached) unless you want intrabar updates.
- Spot coins are named `@<index>` on the wire (except a few like `PURR/USDC`); resolve via `spotMeta`.
- Silent disconnects. Log a heartbeat and supervise.
- Running many watches on the shared computer; each is a process. Keep it to what the desk needs.
