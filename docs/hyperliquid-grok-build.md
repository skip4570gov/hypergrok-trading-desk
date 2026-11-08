# Hyperliquid trading desk for Grok Build

HyperGrok turns Grok Build into a paper-only desk: six roles and seventeen skills. It reads public data and submits only to the local simulator. It does not ask for a key. For the shared Trading Floor, use [Grok Bot](../README.md#start).

## Install

Install the reviewed release:

```bash
grok plugin install skip4570gov/hypergrok-trading-desk@6ebafa835d1466df646dd1c7d5c5a8aaaaf0ee2c --trust
```

Or register this repository's Grok marketplace, which pins the same release, and install by name:

```bash
grok plugin marketplace add skip4570gov/hypergrok-trading-desk
grok plugin install hypergrok --trust
```

The installation format was tested with Grok Build 1.0.30 for an earlier release; 1.6.1 has no native installation proof yet.

Load `desk-operating-model` before asking the roles to act.

## What loads

+ **Seventeen skills**: Hyperliquid setup, market data, account state, orders, positions, WebSocket feeds, advanced actions and a compact API reference, plus the desk skills for the trade lifecycle, risk limits and sizing, execution, monitoring, post-trade review, incidents and the strategy lab.
+ **Six roles** from `agents/`: Desk Lead, Market Analyst, Research Analyst, Strategist, Risk Manager and Trade Reviewer. No role writes to an exchange.

Grok Build reports the skills and agents directories; loading `rules/` is not verified, and the Claude Code exchange-write hook does not load. The desk's approval by ticket id still applies.

## First run, no keys

Ask for a market brief, for example "Brief me on ETH". The reads use Hyperliquid's public `/info` endpoint, with no wallet or account. The same read works from a terminal:

```bash
git clone https://github.com/skip4570gov/hypergrok-trading-desk.git
git checkout 6ebafa835d1466df646dd1c7d5c5a8aaaaf0ee2c
cd hypergrok-trading-desk
python3 scripts/opening_bell.py --coin ETH
```

## When you want to trade

Do not provision a key. A paper trade goes idea, evidence, Risk Manager sign-off, your approval by ticket id, one `scripts/paper_sim.py` submit, and a journal review.

Perpetual futures can liquidate an account. HyperGrok is documentation and instructions, not financial advice.

## More

+ [README](../README.md) and [how the desk works](ARCHITECTURE.md)
+ Other tools: [Claude Code](hyperliquid-claude-code.md) · [Cursor](hyperliquid-cursor.md) · [Codex](hyperliquid-codex.md) · [Gemini CLI](hyperliquid-gemini-cli.md) · Grok Bot: [README Start](../README.md#start)
+ [FAQ](FAQ.md)
