# Hyperliquid trading desk for Cursor

HyperGrok turns Cursor into a paper-only desk: six roles and seventeen skills. It reads public data and submits only to the local simulator. It does not ask for a key.

## Install

Clone the reviewed release:

```bash
git clone --branch paper-only https://github.com/skip4570gov/hypergrok-trading-desk.git
cd hypergrok-trading-desk
python3 scripts/verify_install.py
```

Open the `hypergrok-trading-desk` folder in Cursor and enable the plugin; `.cursor-plugin/plugin.json` points it at the skills, roles and rules. The plugin is also listed on [cursor.directory](https://cursor.directory/plugins/hypergrok).

Load `desk-operating-model` before asking the roles to act.

## What loads

+ **Seventeen skills**: Hyperliquid setup, market data, account state, orders, positions, WebSocket feeds, advanced actions and a compact API reference, plus the desk skills for the trade lifecycle, risk limits and sizing, execution, monitoring, post-trade review, incidents and the strategy lab.
+ **Six roles** from `agents/`: Desk Lead, Market Analyst, Research Analyst, Strategist, Risk Manager and Trade Reviewer. The Risk Manager may run `scripts/paper_sim.py`. No role writes to an exchange. The Cursor manifest loads no order hook because this checkout has no order to confirm.
+ **The desk rule** from `rules/hypergrok-team.mdc`: analysis is not approval, and a send needs your exact approval phrase with the ticket id.

The Claude Code exchange-write hook does not load in Cursor.

## First run, no keys

From the checkout, in Cursor's terminal:

```bash
python3 scripts/opening_bell.py --coin ETH
```

It reads Hyperliquid's public `/info` endpoint only: price, funding, open interest, spread and depth, with no wallet or account. Ask the agent for a market brief next, for example "Brief me on ETH".

## When you want to trade

Do not provision a key. A paper trade goes idea, evidence, Risk Manager sign-off, your approval by ticket id, one `scripts/paper_sim.py` submit, and a journal review.

Perpetual futures can liquidate an account. HyperGrok is documentation and instructions, not financial advice.

## More

+ [README](../README.md) and [how the desk works](ARCHITECTURE.md)
+ Other tools: [Claude Code](hyperliquid-claude-code.md) · [Codex](hyperliquid-codex.md) · [Gemini CLI](hyperliquid-gemini-cli.md) · [Grok Build](hyperliquid-grok-build.md) · Grok Bot: [README Start](../README.md#start)
+ [FAQ](FAQ.md)
