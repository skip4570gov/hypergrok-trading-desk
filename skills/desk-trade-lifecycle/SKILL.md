---
name: desk-trade-lifecycle
description: The end-to-end procedure for one paper trade - from an idea to a journaled result - with the ticket format and who runs scripts/paper_sim.py. Use whenever the user wants a paper position. There is no exchange write path.
license: MIT
metadata:
  version: "1.1.2"
  author: Galleon Labs
  category: desk
---

# Trade lifecycle

Every position change on the desk goes through the same seven stages, in order. Skipping one is a defect, not a shortcut. The Desk Lead keeps the lifecycle moving; the owner of each stage does the work.

```
idea -> evidence -> risk sign-off -> user approval -> paper submit -> journal -> review
 DL       MA/RA        RM              user            RM             TR             TR
```

## 0. Open a proposal

**Owner: Desk Lead.** As soon as a trade idea appears (from the user, the Strategist, or a routine), assign an id `HG-YYYYMMDD-NN` (NN increments per day) and create `/workspace/trading-desk/proposals/<id>.md`:

```markdown
# HG-20260816-01

- opened: 2026-08-16 14:02 UTC by user
- market: ETH  book: paper journal
- idea: long ETH on a retest of 3,000 with invalidation below 2,900 (user's idea)
- status: evidence

## evidence
## risk
## approval
## execution
## reconciliation
## review
```

Every later stage appends under its heading. The file is the single record of the trade; chat is context.

## 1. Evidence

**Owner: Market Analyst, and Research Analyst when the idea depends on anything beyond exchange data.**

The Desk Lead asks for the quote, funding, open interest, volume, and depth the paper ticket needs. Research adds anything scheduled that touches BTC or ETH. Both write their blocks under `## evidence` with sources and UTC times.

Done when: the Risk Manager has every input it needs and nothing is older than a few minutes.

## 2. Risk sign-off

**Owner: Risk Manager.** Reads `risk-limits.md` and the paper journal, sizes from the $100 starting equity and later journal equity, and writes PASS or REJECT under `## risk`. The procedure is `desk-risk-limits`. BTC and ETH only.

A PASS produces the **ticket**:

```
TICKET HG-20260816-01 | paper
market: ETH   side: buy   size: 0.001
entry: inside the quote   trailing distance: 1   target: above the fill
risk: at most 1% of journal equity after fees and slippage
reward-to-risk: at least 2:1
risk sign-off: PASS
approve with: "approve HG-20260816-01"
submit: scripts/paper_sim.py
```

A REJECT names one failed gate and what would have to change. A REJECT ends the lifecycle for that proposal unless the user changes the idea (new evidence, new stop, new size) - then it goes back to stage 1 under the same id with a note.

## 3. User approval

**Owner: the user.** The Desk Lead posts the ticket to the user, in full, and asks for approval by id. Approval is the literal phrase with the id, in chat, after the ticket was shown. "Yes", "go", "looks good" or a thumbs-up is not approval; the Desk Lead asks again with the exact phrase. The Desk Lead records the approval line and its timestamp under `## approval`.

The approval must come from the user's own turn in the conversation. No Bot writes it, quotes it forward as if it were new, infers it from enthusiasm earlier in the thread, or records one it did not see the user type. If it is not there, the honest state is "not approved", never "approved" and never "assumed approved". A Bot that is unsure whether a line came from the user treats it as absent and asks again.

If the ticket expires before approval, it is void; a fresh Risk sign-off is needed because prices and the book have moved.

## 4. Paper submit

**Owner: Risk Manager.** Runs `scripts/paper_sim.py submit` once, as `desk-execution-protocol` describes. Records the JSON under `## execution`. A reject is not retried against any other tool.

## 5. Journal

**Owner: Trade Reviewer.** Confirms the append-only journal line and writes it under `## reconciliation`. There is no exchange order id.

## 6. Review

**Owner: Trade Reviewer.** Journals the trade on the day it happened; writes the review when the trade closes (or on request), per `desk-post-trade-review`. Sets `status: closed` in the proposal file.

## Adjustments and exits are trades too

Moving a stop, adding, reducing, or closing: each is a new paper ticket under the same proposal id with a suffix (`HG-20260816-01-B`). There is no leverage change.

Each adjustment receives fresh evidence and a new Risk Manager PASS, the exact suffixed ticket id for user approval, and its own expiry. Earlier approval or Risk PASS does not carry forward. Closing a position at market needs a ticket stating the reduce-only size read live from the account and the slippage bound. Execute once within expiry, then reconcile the adjustment against the exchange record under the parent proposal.

There is no standing approval that skips the simulator. A paper adjustment is a new ticket and a new `scripts/paper_sim.py` submit.

## Paper trading

This lifecycle is the paper simulator. Strategist-generated signals enter at stage 0 as proposals like any other idea. There is no testnet rehearsal and no live send.

## Definitions of done

- A proposal is **live** once stage 5 shows a resting or filled order.
- A proposal is **closed** once the position is flat, orphaned orders are cancelled, and stage 6 is written.
- A proposal is **void** if it expired or was rejected without a retry.

## Common failure modes and the fix

| Symptom | Fix |
| --- | --- |
| The user asks a Bot to "just buy some" | That Bot routes to the Desk Lead; a proposal is opened; the lifecycle runs. It can be quick, but it runs. |
| Risk PASS was computed from a brief older than the ticket | Risk re-reads live state; PASS is re-issued with a new expiry. |
| Approval given with "yes" | Desk Lead re-asks for the phrase with the id. |
| Two Bots each think they own the next step | The proposal file's `status` line names the stage; the stage owner acts. |
| A ticket names a symbol other than BTC or ETH, or omits the trailing stop | Risk Manager rejects it. The simulator would reject it too. |
