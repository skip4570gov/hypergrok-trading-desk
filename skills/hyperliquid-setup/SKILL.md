---
name: hyperliquid-setup
description: Confirm this checkout is the paper-only desk. Public info reads use one allowlisted URL. No private key, API wallet, SDK, or exchange write is installed or read.
license: MIT
metadata:
  version: "2.0.0"
  author: Galleon Labs
  category: hyperliquid
---

# Paper-only setup

This checkout does not provision a wallet or install a signing client.

1. Use the `paper-only` branch. Do not check out `main` to trade, and do not point setup at a release tag.
2. Market data goes through `scripts/market_data.py`. The Hyperliquid implementation posts only to `https://api.hyperliquid.xyz/info`.
3. `config/paper.json` selects `price_source`. `hyperliquid` is the shipped default. `file` reads the local quotes file documented in the README. `fallback` is `none` unless the config sets it to `hyperliquid`.
4. Paper orders go through `scripts/paper_sim.py` into an append-only journal under `$HYPERGROK_STATE`.

Do not create a secret, read a key file, or set a network variable that selects an exchange. There is no testnet mode and no `--base-url`. If `HYPERGROK_RUNTIME` or `HYPERGROK_STATE` is unset, stop. On the reviewed wall those paths are `/opt/hypergrok-wall/runtime` and `/home/hypergrok/state`.

Readiness is `python3 "$HYPERGROK_RUNTIME/scripts/verify_install.py" --root "$HYPERGROK_RUNTIME"` plus `python3 "$HYPERGROK_RUNTIME/scripts/test_paper_only.py"`. A passing check is not permission to send an order.
