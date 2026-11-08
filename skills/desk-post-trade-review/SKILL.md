---
name: desk-post-trade-review
description: The Trade Reviewer's procedure for journaling desk activity and reviewing trades from the exchange record - process graded separately from outcome, execution costs measured, one repeatable finding per review, plus the weekly desk review. Use after any send, when a trade closes, on the weekly routine, or when the user asks "how did that go".
license: MIT
metadata:
  version: "1.0.2"
  author: Galleon Labs
  category: desk
---

# Journal and post-trade review

The journal is the desk's memory; the review is how the desk learns. Both come from the exchange record first and chat second, and both keep process and outcome apart.

## 1. Journal

`/workspace/trading-desk/journal/YYYY-MM-DD.md`, one file per active day, appended in time order. Entry types:

```
14:02 UTC  HG-20260816-01 opened   ETH-PERP long idea (user); status evidence
14:12 UTC  HG-20260816-01 risk     PASS, trail and target, at most 1% of the $100 journal
14:29 UTC  HG-20260816-01 approval "approve HG-20260816-01" (user)
14:31 UTC  HG-20260816-01 paper    scripts/paper_sim.py submit, journal hash recorded
09:12 UTC  HG-20260816-01 closed   target fill in the journal; fee recorded
10:00 UTC  limits                  stricter paper cap only; symbols stay BTC and ETH
11:40 UTC  incident INC-20260817-01 journal mismatch; no new submit
18:00 UTC  note                    both paper entries this week kept a trailing stop
```

Rules: append only; corrections are new lines with `correction:`; every line has a UTC time and an id where one exists; no opinions in the journal (those go in reviews).

## 2. Trade review

Trigger: a proposal reaches `closed`, or the user asks. Inputs, always listed with timestamps:

- the proposal file
- the paper journal open, trail, stop, target, and close events: price, size, fee, side, and feed
- the quote recorded on those events

Compute entry and exit from the journal fills, fees from the journal, and whether a trailing stop was present the whole time. There is no exchange fill record and no funding payment to sum. Net result is journal PnL after fees.

Grade:

- **Process:** clean / minor break / major break, with the specific stage named. A major break is any send without PASS or approval by id, any missing protection, any resend on unknown result, or any limit breached.
- **Outcome:** result in R and USD, stated without adjectives.

Then **one thing**: a leak, a control that worked, or a break, chosen because it is repeatable. Not a list.

Write the review under `## review` in the proposal file and send the block (format in `agents/trade-reviewer.md`) by DM to the Desk Lead and the user. Set `status: closed`.

## 3. Weekly desk review

From the journal, proposals and the exchange record for the week:

- proposals opened / rejected / voided / executed / closed
- trades closed: count, hit rate, average win and loss in R, expectancy in R (mean of results), largest loss, largest drawdown in equity terms from `portfolio` or start/end equity
- costs: fees and funding in USD and as a share of gross PnL
- process: number of breaks by type; incidents and their status
- limits: any changes and why
- one pattern worth the user's attention, stated as a fact pattern

No recommendations about what to trade. If the user asks, hand strategy questions to the Strategist and sizing questions to the Risk Manager.

## 4. Incident review

For each `INC-YYYYMMDD-NN`: timeline (journal + exchange record), what the desk did, what the controls did, exposure during the incident, root cause where knowable, one corrective action with an owner and a date. Blameless in tone, exact in fact. Written to `/workspace/trading-desk/journal/incidents/<id>.md` and linked from the daily journal.

## Pitfalls

- Reviewing from chat memory rather than fills. Chat says what people meant; fills say what happened.
- Letting the outcome colour the process grade. Grade process first, then look at the outcome.
- Counterfactuals ("if we had held..."). Not evidence.
- Ten findings per review. Nobody acts on ten.
- Editing old journal lines. Append a correction.
