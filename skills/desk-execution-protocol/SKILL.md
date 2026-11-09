---
name: desk-execution-protocol
description: Turn an approved paper ticket into one scripts/paper_sim.py submit. No exchange send, no retry against an endpoint, and no key. Use after Risk PASS and the user's exact ticket approval.
license: MIT
metadata:
  version: "2.0.0"
  author: Galleon Labs
  category: desk
---

# Paper execution

The Risk Manager runs this after a PASS and the user's exact `approve <id>` line. One command, one journal append.

1. The ticket symbol is BTC or ETH and includes a trailing-stop distance, take-profit, entry, and size.
2. Reward-to-risk is at least 2:1 and risk is at most 1% of the $100 wallet, counting open paper risk.
3. Run `scripts/paper_sim.py submit` with `config/paper.json` and the desk journal path. Do not add a flag the script does not have.
4. Paste the JSON result under `## execution`. A reject stays a reject.
5. Tell the Trade Reviewer the journal path. Reconciliation is the journal record, not an exchange id.

There is no second send, no cancel on an exchange, and no leverage change. A timeout does not exist for this command because it does not leave the machine.
