# Hyperliquid trading desk for Codex

HyperGrok gives Codex a paper-only desk: seventeen skills and six labelled passes. It reads public data and submits only to the local simulator. It does not ask for a key.

## Install

```bash
git clone --branch paper-only https://github.com/skip4570gov/hypergrok-trading-desk.git
cd hypergrok-trading-desk
python3 scripts/verify_install.py
```

Do not use `codex plugin marketplace add` without this check. The branch only fetches the line. `python3 scripts/verify_install.py` checks `install-manifest.json` and the reviewed ancestor.

Load `desk-operating-model` before asking the roles to act.

## What loads

+ **Seventeen skills**: Hyperliquid setup, market data, account state, orders, positions, WebSocket feeds, advanced actions and a compact API reference, plus the desk skills for the trade lifecycle, risk limits and sizing, execution, monitoring, post-trade review, incidents and the strategy lab.
+ **Roles as labelled passes.** This plugin's Codex entry installs skills without registering `agents/` as native subagents. Run the six roles as labelled passes using each role's system prompt. No pass writes to an exchange.

The Claude Code exchange-write hook does not load in Codex. The desk's approval by ticket id still applies.

## First run, no keys

Ask for a market brief, for example "Brief me on ETH". The reads use Hyperliquid's public `/info` endpoint, with no wallet or account. The same read works from a terminal:

```bash
git clone --branch paper-only https://github.com/skip4570gov/hypergrok-trading-desk.git
cd hypergrok-trading-desk
export HYPERGROK_RUNTIME="$PWD"
export HYPERGROK_STATE="$(mktemp -d)"
python3 "$HYPERGROK_RUNTIME/scripts/verify_install.py" --root "$HYPERGROK_RUNTIME"
python3 "$HYPERGROK_RUNTIME/scripts/paper_sim.py" reset --state "$HYPERGROK_STATE"
```

## When you want to trade

Do not provision a key. A paper trade goes idea, evidence, Risk Manager sign-off, your approval by ticket id, one `scripts/paper_sim.py` submit, and a journal review.

Perpetual futures can liquidate an account. HyperGrok is documentation and instructions, not financial advice.

## More

+ [README](../README.md) and [how the desk works](ARCHITECTURE.md)
+ Other tools: [Claude Code](hyperliquid-claude-code.md) · [Cursor](hyperliquid-cursor.md) · [Gemini CLI](hyperliquid-gemini-cli.md) · [Grok Build](hyperliquid-grok-build.md) · Grok Bot: [README Start](../README.md#start)
+ [FAQ](FAQ.md)
