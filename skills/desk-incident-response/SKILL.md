---
name: desk-incident-response
description: What the paper desk does when the journal, a quote, or a public read goes wrong. Contain first, replay the journal, and do not invent an exchange send. Use the moment anything does not match the ticket.
license: MIT
metadata:
  version: "1.1.2"
  author: Galleon Labs
  category: desk
---

# Incident response

An incident is any moment when the exchange record and the desk's expectation disagree, or when the desk cannot see the exchange at all. The reflex is: stop adding, look, contain with approval, then review. Never widen the harm by improvising.

## Declare

Any Bot can declare an incident. Post on the floor:

```
INCIDENT INC-20260817-01 | 11:40 UTC | HG-20260817-02 | paper journal mismatch | owner: Risk Manager
```

The Desk Lead confirms an owner (the Risk Manager for a paper position, the Desk Lead for access). New proposals pause until the incident is contained. There is no exchange send to recover.

## Playbooks

### A. Unknown send result (timeout, 5xx, exception after send)

1. Do not resend.
2. `orderStatus` by cloid; `openOrders`; `userFills` since the send; `clearinghouseState`.
3. Found: continue reconciliation as normal; journal that the response was lost.
4. Not found: that is not proof. Wait until the signed `expiresAfter` deadline has passed, then reconcile again. Expiry prevents later acceptance; it does not cancel an order accepted before the deadline or remove its fills.
5. There is no signed action to recover and no nonce to reuse. Read the paper journal. If its hash chain fails, stop and tell the user. Do not invent a replacement send.
6. A replacement waits until later acceptance is impossible and existing exposure is reconciled, then needs a fresh ticket, Risk PASS and approval by id. If the exchange later shows the original order after a second one was sent: the desk has double exposure. Go to playbook C.

### B. Rejected order or partial fill

- Rejection string in the response (`error`): quote it, map it via `hyperliquid-api-reference` (price precision, minimum notional, insufficient margin, reduce-only would increase position, invalid tif...). Fix is a new ticket, not a tweak-and-resend.
- Partial fill on an IOC: the unfilled remainder is gone and the position is smaller than the ticket. Any `normalTpsl` children were **never placed** (children appear only when the parent fills fully, or is partially filled and then margin-cancelled), so the filled part is unprotected: report the actual size and get a stop for that size placed at priority (playbook D).
- Partial fill on a resting order: normal; reconciliation continues.

### C. Position does not match expectation (too big, wrong side, unexpected market)

1. Read `clearinghouseState` and `userFills` for the last hour; establish the exact state.
2. Risk Manager computes exposure and liquidation distance now.
3. If paper exposure breaches limits: the Risk Manager rejects new risk. This checkout cannot send a reduce-only order to an exchange. The user closes a real position themselves, outside this desk.
4. Journal what happened and why the mismatch occurred once known.

### D. Unprotected position (no resting stop)

1. Risk Manager flags it; the Desk Lead treats it as priority.
2. Protective stop ticket (trigger, reduce-only, correct side, sized to the position read live) through Risk PASS and user approval. This is also the path after any partial fill of an entry that carried `normalTpsl` children.
3. A paper order still needs a trailing stop inside `scripts/paper_sim.py`. No standing approval skips that check, and nothing is placed on an exchange.
4. Without that pre-authorisation the desk cannot act, and an unprotected position does not become safe while it waits. Do not alert indefinitely: state the exposure and the distance to liquidation in the first alert, escalate on a deadline the user set in `desk.md` (fifteen minutes is a reasonable default), and when that passes, tell the user plainly that the fastest fix is theirs - close or protect the position in the Hyperliquid app - rather than continuing to ping a channel nobody is reading.

### E. Orphaned or stuck orders

- Orphaned (position flat, stop still resting): cancel ticket, or the standing approval for orphan clean-up if written in `desk.md`. Confirm from `openOrders`.
- Stuck (order the exchange shows that the desk cannot cancel): read `orderStatus`; check whether it is a trigger child of a grouped order; try `cancelByCloid` if `cancel` by oid fails; if still stuck, report with the exact response and stop.

### F. Exchange unreachable, rate limited, or degraded

- `/info` failing or slow: mark the desk **blind**; no new tickets; watches log the outage; check `https://api.hyperliquid.xyz/info` with a tiny `allMids` call every minute; report when back.
- HTTP 429: back off (respect the response), reduce polling, prefer WebSocket for continuous data. Read `userRateLimit` for the account's remaining budget.
- Blind with open positions: the user is told plainly that stops resting **on the exchange** still work while the desk cannot see; that is why stops are mandatory.
- Connectivity returning is only the start of recovery. Follow `hyperliquid-websocket`'s gap/restart procedure: restore account and detailed order snapshots, recover overlapping fills, reconcile reservations and protection, then let Risk recheck capacity before new risk resumes. A successful public price read or a restarted process cannot lift the account pause. Protection and exits still use verified live state and the normal approval gates.

### G. A secret appeared on the computer

Signs: orders or fills the desk did not send, leverage changes nobody approved, unfamiliar `cloid`s.

1. Stop. This checkout has no key to use or replace. The user removes the secret from the computer.
2. This checkout has no key to revoke and no send to confirm.
3. Read the paper journal. Do not create or store a replacement key.
4. Rotate: new key through the secure secret card only; nothing pasted in chat; journal the rotation time.
5. Incident review with a timeline.

Remember the shared computer: every Bot can read the same files. That is why this checkout stores no key.

### H. Daily loss stop hit

Not an incident, but handled like one: Risk Manager posts it, `desk.md` gets `status: no-new-risk`, protective and exit tickets continue, new risk waits for the user's written reset.

## Containment rules

- Contain with the smallest reversible action. Reduce, don't flip. Cancel one, not all, unless the user has asked for a dead-man's switch and its condition has occurred.
- Every containment action is still a ticket with approval by id (or a pre-written standing approval in `desk.md`).
- Never withdraw, transfer or bridge as an incident response.
- Never resend to "make sure".

## Close the incident

The Trade Reviewer writes the incident review (`desk-post-trade-review`), the Desk Lead lifts the proposal pause and records the corrective action and its owner in `desk.md`.
