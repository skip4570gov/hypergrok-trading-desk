# Skills

Seventeen skills in the portable `SKILL.md` format (`name` and `description` frontmatter, body under 320 lines). Grok Bot installs them as shared skills from the pinned checkout. The [runtime guides](../README.md#also-runs-in-grok-build-cursor-claude-code-codex-and-gemini-cli) cover plugin and extension installation in Grok Build, Cursor, Claude Code, Codex and Gemini CLI. Start with `desk-operating-model`; install `hypergrok-bootstrap` to build the native Grok Bot desk.

## Bootstrap

| Skill | What it teaches | Primary users |
| --- | --- | --- |
| [hypergrok-bootstrap](hypergrok-bootstrap/SKILL.md) | Pinned install, zero-key Opening Bell, team creation, desk doctor and evidence receipt | Desk Lead |

## Hyperliquid skills (how to work with the exchange)

| Skill | What it teaches | Writes to the exchange? | Primary users |
| --- | --- | --- | --- |
| [hyperliquid-setup](hyperliquid-setup/SKILL.md) | Paper-only checkout, allowlisted public info URL, no key | no | Desk Lead |
| [hyperliquid-market-data](hyperliquid-market-data/SKILL.md) | Prices, book depth, funding, OI, volume, candles, spot and HIP-3 metadata, dataset saving | no | Market Analyst, Strategist, Risk Manager |
| [hyperliquid-account](hyperliquid-account/SKILL.md) | Public account reads through the allowlisted info URL | no | Risk Manager, Trade Reviewer |
| [hyperliquid-orders](hyperliquid-orders/SKILL.md) | Local paper submit only: trailing stop, 2:1, 1% of $100, BTC and ETH | no | Risk Manager |
| [hyperliquid-positions](hyperliquid-positions/SKILL.md) | Paper journal positions; no leverage or close on an exchange | no | Risk Manager |
| [hyperliquid-websocket](hyperliquid-websocket/SKILL.md) | Poll the public info feed; no client SDK and no socket order path | no | Market Analyst, Strategist |
| [hyperliquid-advanced](hyperliquid-advanced/SKILL.md) | Actions this checkout refuses: transfer, withdrawal, agent approval, TWAP | no | Risk Manager |
| [hyperliquid-api-reference](hyperliquid-api-reference/SKILL.md) | Request and action reference, statuses, asset ids, tick/lot, rate limits, WS types, error strings, docs links | no | everyone |

## Desk skills (how the team works)

| Skill | What it covers | Primary users |
| --- | --- | --- |
| [desk-operating-model](desk-operating-model/SKILL.md) | Roles, seats, workspace, engagement levels, evidence standard, approval model, handoff format | everyone |
| [desk-trade-lifecycle](desk-trade-lifecycle/SKILL.md) | The seven stages of a trade, the proposal file, the ticket, approval by id, definitions of done | Desk Lead, everyone |
| [desk-risk-limits](desk-risk-limits/SKILL.md) | The limits file, sizing arithmetic, margin tiers, book check, veto rules | Risk Manager |
| [desk-execution-protocol](desk-execution-protocol/SKILL.md) | One paper submit after approval, then the journal | Risk Manager |
| [desk-monitoring](desk-monitoring/SKILL.md) | Routines, the desk brief, watches and alert conditions | Desk Lead, Risk Manager, Market Analyst |
| [desk-post-trade-review](desk-post-trade-review/SKILL.md) | Journal format, trade review, weekly review, incident review | Trade Reviewer |
| [desk-incident-response](desk-incident-response/SKILL.md) | Playbooks for a bad paper journal, bad quotes, and public-info outages | Risk Manager, Desk Lead |
| [desk-strategy-lab](desk-strategy-lab/SKILL.md) | Rules first, honest backtests, sanity checks, local paper trading | Strategist |

## Conventions

- Frontmatter: `name` (matches the directory), `description` (what and when, under 1024 characters), `license`, `metadata` (`version`, `author`, `category`, and `network-default` for Hyperliquid skills).
- Bodies: purpose, concepts, copy-pasteable commands (`curl` for reads, Python SDK first and TypeScript second for writes), procedure, pitfalls. No strategy content, no return claims, no emoji.
- Every write path says who may use it and under what approval. Every read says which address to use.
- Examples state their required environment and key loading. An example that signs still requires the full ticket protocol and native approval coverage; copying a block does not authorize a send.
