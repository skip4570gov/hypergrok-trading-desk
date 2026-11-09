---
name: desk-risk-limits
description: How the Risk Manager writes the desk's risk limits with the user, sizes every proposed trade from live account state and Hyperliquid's real constraints, checks the book, and issues a PASS or REJECT with exact ticket fields. Use for setting up or changing limits, sizing any trade, and answering "how's the book".
license: MIT
metadata:
  version: "1.1.3"
  author: Galleon Labs
  category: desk
---

# Risk limits and sizing

The user sets any stricter limits in writing. The Risk Manager enforces the paper simulator on every ticket: $100 starting equity, BTC and ETH only, a trailing stop, and at least 2:1 after fees and slippage.

## 0. Desk ceilings

These ceilings reject limits files that exceed the desk's bounds. They are maximum permitted settings, not recommended risk levels; the user chooses stricter limits below.

| Ceiling | Value |
| --- | --- |
| paper wallet | $100, fixed in `scripts/paper_sim.py` |
| symbols | BTC and ETH only |
| max risk per order and total open paper risk | 1% of that equity |
| reward-to-risk | at least 2:1 |
| trailing stop | mandatory on every order |
| live or testnet send | impossible in this checkout |

These numbers are hardcoded in the simulator. A limits file cannot loosen them, and a missing trailing stop is a reject rather than a warning. The Risk Manager submits only through `scripts/paper_sim.py` after the user approves the exact ticket id.

The user's limits file may only be **stricter** than these. A file that sets a value looser than a ceiling is not applied: the Risk Manager REJECTs with `gate failed: limits file exceeds desk ceiling <name>`, keeps enforcing the ceiling, and asks the user to edit the file. The desk never edits the file itself, and no Bot may raise a ceiling.

## 1. Write the limits file (setup, or on change)

Interview the user, one question at a time, then write `$HYPERGROK_STATE/risk-limits.md`. Version it (`v1`, `v2`...) and date every change. Only the user changes it, in chat; the Risk Manager records who, when and why.

```markdown
# Risk limits v1 - 2026-08-16 - set by user

- book: paper simulator journal
- equity basis: replayed from the journal after the explicit reset
- symbols: BTC, ETH
- max risk per trade: 1% of journal equity
- max total open risk: 1% of journal equity
- trailing stop: mandatory, and it must move with the mark inside scripts/paper_sim.py
- take-profit: required, finite, and on the profitable side of the fill
- reward-to-risk: at least 2:1 after fees and slippage
- notes:
```

Record what the user chooses only when it is stricter than the simulator. Do not add another symbol, a missing target, or a live book.

## 2. Size a paper trade

Inputs: symbol (BTC or ETH), side, entry inside the current quote, trailing distance, and a finite target. Equity and open risk come from the paper journal, which starts at $100 after `scripts/paper_sim.py reset`. If the journal is missing, reject and ask for an explicit reset. Do not guess.

### 2.1 Read the journal and the quote

- Equity and open positions: replay the journal in the paper state directory. Do not read `clearinghouseState` or an account balance.
- Quote: `scripts/market_data.py` for that symbol. The entry must sit inside the bid/ask. Record the feed identity.
- A stale quote, a missing trailing stop, or a target that is zero, negative, or on the wrong side of the fill is a reject.

### 2.2 Arithmetic

Planned loss uses the trailing distance plus the simulator's fees and slippage. Size so that planned loss is at most 1% of journal equity, including risk already open. Reward to the target must be at least twice that planned loss. BTC and ETH only. There is no leverage and no $10,200 account.

A stop that later gaps through fills at the gapped mark. The 1% figure is the plan at entry, not a promise that a crash loses only 1%. There is no leverage.

### 2.3 Output

PASS: journal equity, quote, trail, target, planned loss, and `scripts/paper_sim.py submit`. REJECT: one failed gate and the numbers. Write it under `## risk`.

## 3. Book check ("how's the book")

Replay the paper journal. That is the book.

- equity after the explicit reset and later fills, fees, and closes
- open paper positions: symbol (BTC or ETH), side, size, fill, trailing stop, target, and unrealised result versus the latest quote
- open risk versus 1% of journal equity
- a position whose journal event has no trailing stop: reject new risk and treat it as an incident
- day change in journal equity

Timestamp the quote and the journal hash you read. Save a copy under `$HYPERGROK_STATE/briefs/YYYY-MM-DD-book.md` when the user asks for a written check. Do not read an exchange account.

## 4. When the desk hits a limit

- Daily loss stop hit: post it once on the floor, set `status: no-new-risk` in `desk.md`, and REJECT new proposals with that gate until the user resets in writing. Exits and protection are still allowed.
- Paper order missing a trailing stop: reject it. The simulator rejects it too. A real exchange position is outside this checkout; tell the user to handle it themselves.
- Limits file missing or unversioned: the desk is a research desk until it exists.

## Pitfalls

- Sizing from a desired profit instead of from the trailing distance.
- Treating a gap fill as if it happened at the stop. The simulator fills a gapped stop at the mark.
- Reading a missing journal as a fresh $100 wallet. It is not. Ask for an explicit reset.
- Treating a chat message as an open paper position. Only the journal is.
- Adding a symbol other than BTC or ETH.
