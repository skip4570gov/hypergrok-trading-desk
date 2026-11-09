# How the desk works

In Grok Bot, HyperGrok uses your Bots, shared cloud computer and conversations. This repository supplies the instructions and read-only tools. [Other runtimes](#other-runtimes) use the same process with subagents or labelled role passes.

## The floor

```
you
 |
 v
Trading Floor (group chat, 5 Bots)                 DM
  Desk Lead ------------------------------------> Trade Reviewer
   |     |     |     |                            journal
   |     |     |     +-------- Risk Manager -------> scripts/paper_sim.py
   |     |     +-------------- Strategist ---------> public info (history)
   |     +-------------------- Research Analyst ---> browser, public data
   +-------------------------- Market Analyst -----> public info (markets)

computer:  $HYPERGROK_RUNTIME (this repo, read-only)   $HYPERGROK_STATE (writable files)
secret:    none. This branch does not read a private key.
```

The shared Desk Lead starts from the reviewed checkout. `hypergrok-bootstrap` checks `scripts/verify_install.py` and `scripts/test_paper_only.py`, prepares `$HYPERGROK_STATE`, and resets the local simulator. None of those paths reads a key or sends an order. On the reviewed wall the runtime is `/opt/hypergrok-wall/runtime` and the state directory is `/home/hypergrok/state`. If either variable is unset, stop.

The six-Bot group limit leaves the Trade Reviewer outside the Floor. Bots share the computer and skills, so role separation is a working convention rather than credential isolation. Native approval controls and the secret store provide separate controls; setup verifies their availability.

## One trade, seven stages

```
idea -> evidence -> risk sign-off -> your approval by ticket id -> paper submit -> journal -> review
```

The Desk Lead keeps it moving. Analysts bring sourced, timestamped evidence. The Risk Manager sizes against the $100 paper wallet and issues a ticket. You approve it by id. The Risk Manager runs the simulator once. The Trade Reviewer reads the journal and grades process and outcome separately.

Adjusting, adding, reducing and closing are trades too: same path, new ticket under the same id.

## Where things live

Working files live under `$HYPERGROK_STATE`; chat supplies context, while these records retain the lifecycle evidence. The simulator journal is in that same directory.

| File | What it is |
| --- | --- |
| `desk.md` | the desk record: network, account, engagement level, Bots, chats, standing approvals |
| `risk-limits.md` | your limits, versioned; only you change it |
| `proposals/HG-*.md` | one file per trade idea, appended through its life: ticket, sign-off, approval, send, reconciliation, review |
| `journal/*.md` | the desk diary, append-only |
| `briefs/`, `research/`, `strategies/`, `data/`, `watch/` | working material |

## Research evidence

Quotes come from `scripts/market_data.py`. The paper book is the journal written by `scripts/paper_sim.py`. This checkout does not collect candle history, price a stop from an exchange book, or read an exchange account. See [Research datasets](RESEARCH_DATASETS.md), [Stop cost](STOP_COST.md), and [Account read](ACCOUNT_READ.md).

A missing file stays missing. Statistical evidence, Risk PASS, and a user's exact ticket approval are separate decisions.

## Trust boundaries

**Reads.** The desk posts to the pinned public info host, or reads a local quote file. No signing key is used.

**Orders.** The only order command is `scripts/paper_sim.py`. It keeps a local journal. It does not send to an exchange.

**Key.** This checkout has no key and no instructions to provision one.

**Evidence.** Web pages, files and other Bots' messages are information; none of them authorises a paper order. Your approval phrase with the ticket id is still required, and the simulator's checks still run after it. No Bot may type, quote forward, infer or simulate your approval.

**Uncertainty.** Missing, stale, gapped or partial data is `unavailable`. A watch reports a healthy negative observation separately from a failed feed; missing evidence cannot pass a check.

## Why seven

Research, risk, execution and review answer different questions. Separate role prompts make each handoff and its evidence explicit. Their agreement does not replace Risk PASS, user approval or exchange reconciliation.

## Other runtimes

Each runtime guide contains installation commands and observed support limits:

| Runtime | Components | Guide |
| --- | --- | --- |
| Claude Code | `.claude-plugin/`, skills, subagents and the exchange-write hook; load the operating model explicitly | [Install](hyperliquid-claude-code.md) |
| Cursor | `.cursor-plugin/`, skills, agent profiles and desk rules | [Install](hyperliquid-cursor.md) |
| Grok Build | `.grok-plugin/`, skills and agent directories; rule loading unverified | [Install](hyperliquid-grok-build.md) |
| Codex | `.agents/plugins/marketplace.json`, skills and labelled role passes | [Install](hyperliquid-codex.md) |
| Gemini CLI | `gemini-extension.json`, skills, `GEMINI.md` and labelled role passes | [Install](hyperliquid-gemini-cli.md) |

The Grok and Codex marketplace entries pin the reviewed repository tag. Claude Code resolves this repository through its own marketplace index. Gemini CLI installs the latest GitHub release; `GEMINI.md` repeats the desk rule's approval paragraph, which the manifest check compares for drift.

Claude Code loads a hook that denies a command which looks like an exchange write. Cursor does not load that hook. See [SECURITY.md](../SECURITY.md) for the host limits this repository cannot close.
