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

### A. Journal does not match the last paper submit

1. Do not submit again.
2. Read the paper journal and check its hash chain.
3. If the chain fails, stop and tell the user. Do not reset unless they ask, and a reset must be the explicit command.
4. If the chain is intact, report the last event. There is no exchange order to look up.

### B. Simulator reject

- Quote the reject code. A bad target, a missing trailing stop, or risk over 1% needs a new ticket.
- Do not retry the same order against any other tool.

### C. Paper position does not match the ticket

1. Replay the journal and compare it with the ticket.
2. The Risk Manager stops new risk if open risk is already over the cap.
3. This checkout cannot send an order to an exchange. Journal the mismatch.

### D. Paper order with no trailing stop

1. The Risk Manager rejects it. The simulator rejects it too.
2. Nothing is placed on an exchange.

### E. Orphaned or stuck orders

- Orphaned (position flat, stop still resting): cancel ticket, or the standing approval for orphan clean-up if written in `desk.md`. Confirm from `openOrders`.
- Stuck (order the exchange shows that the desk cannot cancel): read `orderStatus`; check whether it is a trigger child of a grouped order; try `cancelByCloid` if `cancel` by oid fails; if still stuck, report with the exact response and stop.

### F. Exchange unreachable, rate limited, or degraded

- `/info` failing or slow: mark the desk **blind**; no new tickets; watches log the outage; check `https://api.hyperliquid.xyz/info` with a tiny `allMids` call every minute; report when back.
- HTTP 429: back off (respect the response), reduce polling, prefer WebSocket for continuous data. Read `userRateLimit` for the account's remaining budget.
- Blind with open positions: the user is told plainly that stops resting **on the exchange** still work while the desk cannot see; that is why stops are mandatory.
- Connectivity returning is only the start of recovery. Follow `hyperliquid-websocket`'s gap/restart procedure: restore account and detailed order snapshots, recover overlapping fills, reconcile reservations and protection, then let Risk recheck capacity before new risk resumes. A successful public price read or a restarted process cannot lift the account pause. Protection and exits still use verified live state and the normal approval gates.

### G. A secret appeared on the computer

Signs: a journal event the desk did not submit, or a hash chain that fails.

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
