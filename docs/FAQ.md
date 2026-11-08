# FAQ

**What do I actually get?**
The release contains seven role profiles, seventeen skills and read-only Python tools. In Grok Bot, setup builds seven Bots, a six-Bot Trading Floor and a desk record. Other runtimes load the roles as subagents or labelled passes. Ask for a market brief, a sized ticket, a backtest or a review; each role reports its evidence.

**What do I need to start?**
For a terminal demo, run the [keyless Opening Bell](../README.md#try-it-now-no-keys) with Python 3. For the desk, follow the pinned bootstrap in the [README](../README.md#start). It uses public market data and the local simulator. Do not provision a key.

**What does the desk doctor inspect?**
The release version and tag pin, all agent and skill files, the desk folders and record, and a public Hyperliquid `allMids` response. It never reads environment variables, keys or account state, and never calls the exchange write endpoint.

**How does the desk trade?**
Through a Hyperliquid API (agent) wallet you create in the Hyperliquid app and hand over through Grok Bot's secure secret card. It can place, modify and cancel orders. Withdrawals, transfers and bridging stay in the app with your main wallet.

**How do I approve a trade?**
The Risk Manager posts a paper ticket with an id like `HG-20260816-01`. You type `approve HG-20260816-01`. The simulator still checks the quote, trailing stop, payoff and risk. No Bot may type, quote forward or infer your approval. Do not provision a key.

**Where do the ideas come from?**
From you. The Strategist turns your idea into rules and tests it on public history. A forward test uses the local simulator. The Market and Research Analysts give you the picture; you decide.

**Can I verify the history behind a backtest?**
Yes. The [research dataset tool](RESEARCH_DATASETS.md) saves requests, decoded responses, CSVs and a manifest with file hashes and coverage gaps. `--verify` replays that bundle offline. A missing candle or funding hour prevents complete coverage; absent funding is never assumed to be zero. Integrity and coverage do not prove source authenticity, strategy edge or exact USD funding costs without historical oracle prices.

**Why do the Bots use a "computer"?**
That is Grok Bot's cloud VM, shared by your Bots. Public reads use the allowlisted info URL. Paper orders stay in the local simulator. The browser reads pages; it does not execute trades.

**Why six on the floor and one off it?**
Grok Bot group chats hold six Bots. The Trade Reviewer receives execution reports by DM and reviews them from the journal and exchange records.

**Can I rename the Bots or add my own?**
Yes. Names and avatars are yours. To add a role, copy the shape of a file in `agents/`. Keep one writer: only one Bot has the exchange write skills.

**Can it run while I sleep?**
Routines can brief you, watch prices and funding, check the book and alert you. Sending always waits for your approval by id.

**Which network does market data come from?**
Public reads use the pinned info host. Scripts do not accept another origin. Paper orders use the simulator journal.

**What if a send times out?**
The paper simulator either appends a journal line or rejects the order. It does not retry against an exchange, because this checkout has no exchange write.

**How do I set Grok Bot's own approvals?**
Settings, General, Auto-review: add an **Ask first** rule for financial actions and for commands that call the Hyperliquid exchange endpoint. **Ask first** wins over **Allow automatically**.

**Does it work outside Grok Bot?**
Yes. Use the guide for [Claude Code](hyperliquid-claude-code.md), [Cursor](hyperliquid-cursor.md), [Grok Build](hyperliquid-grok-build.md), [Codex](hyperliquid-codex.md) or [Gemini CLI](hyperliquid-gemini-cli.md). The [runtime table](../README.md#also-runs-in-grok-build-cursor-claude-code-codex-and-gemini-cli) shows which roles, rules and hooks each loads. The ticket process and verified native approval requirement apply in all runtimes. Skills alone do not enforce exchange permissions.

**<a id="token"></a>Does HyperGrok have a token?**
HyperGrok has no token and will not launch one. Coins using the name were launched by third parties and are not part of this project.

**Where can I get help or report a bug?**
Check the runtime guide and run `python3 scripts/desk_doctor.py --offline --json`. [Open an issue](https://github.com/skip4570gov/hypergrok-trading-desk/issues/new/choose) with your release, runtime, failing command and sanitized output. Follow the [security policy](../SECURITY.md) for sensitive reports.

**Is this financial advice?**
It is documentation and instructions. Perpetual futures can liquidate an account.
