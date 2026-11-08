# Set up the HyperGrok trading desk

You are a Grok Bot building the user's Hyperliquid trading desk from this repository. Follow this file top to bottom. When you finish, the user has seven specialist Bots (six on a **Trading Floor** group chat, one reviewer by DM), seventeen shared skills, a prepared desk computer and a written desk record. Setup is read-only: no keys, no orders.

In Grok Bot, if your runtime loaded this repository as a plugin, invoke `hypergrok-bootstrap`: it performs this runbook, rings a live zero-key Opening Bell first, and returns the same receipt. This file remains the complete manual path and source of truth.

## 1. Get the repository onto the desk computer

If `/workspace/hypergrok` already contains a Git checkout, preserve it. `git rev-parse --abbrev-ref HEAD` must be `paper-only`. If it is `main` or a tag, report the existing commit and stop dependent setup without overwriting, resetting or switching the checkout. For a matching existing checkout, run only the final `cd`, commit and test line below; otherwise clone:

```bash
mkdir -p /workspace && cd /workspace
git clone https://github.com/skip4570gov/hypergrok-trading-desk.git hypergrok
git -C hypergrok checkout __PAPER_COMMIT__
cd /workspace/hypergrok && git rev-parse HEAD && bash scripts/check.sh
```

That pin is a release tag, not a moving branch: the desk you build is the desk that was reviewed. Check the repository's releases for a newer tag before setting up, and do not swap the tag for `main` to pick up unreleased work.

`git clone` prints `warning: refs/tags/... is not a commit!` when it shallow-clones an annotated tag. That warning is expected and harmless: the clone still resolves to the tagged commit, which is why the command prints it. Judge the step by `scripts/check.sh`, not by that line.

`scripts/check.sh` is the desk's own structural check: it runs offline, touches no keys and no network, and confirms the skills, agents and manifests are intact and internally consistent. If it fails, stop and tell the user; do not build a desk from a tree that does not check out.

Before using any agent profile or System prompt, run `git diff --exit-code HEAD -- agents/` in the checkout. A matching branch name does not prove the working files are unchanged. If the command reports differences or fails, name the affected paths, stop dependent setup and preserve the user's files.

Record the commit `git rev-parse HEAD` printed. It goes into `desk.md` in section 8 as `instructions commit`, so the desk can always say which version of these rules it is running and the user can diff it later.

If the clone fails, report the error and keep setup pending. Do not switch to plain HTTP or unpack an archive with unverified provenance. Structural checks establish internal consistency, not that an archive came from this release; a user-supplied archive still needs trusted release provenance before setup continues.

## 2. Read the desk

Read these before creating anything:

1. `docs/ARCHITECTURE.md` - how the team fits together.
2. `skills/hypergrok-bootstrap/SKILL.md` and `skills/desk-operating-model/SKILL.md` - setup and the rules every Bot follows.
3. All seven files in `agents/` - each has a **Bot profile** (Name, Job, Description) and a full **System prompt**.
4. `skills/README.md` - the index of skills and which Bot uses which.

## 3. Prepare the desk computer (read-only)

Follow `skills/hyperliquid-setup/SKILL.md` sections 1-3 only: install the Python SDK, confirm both Hyperliquid networks answer a public read, and create the working folders:

```bash
mkdir -p /workspace/trading-desk/{proposals,briefs,research,strategies,data,journal/incidents,watch}
cd /workspace/hypergrok
python3 scripts/opening_bell.py --coin ETH
python3 scripts/desk_doctor.py --desk-root /workspace/trading-desk
```

Show the Opening Bell output to the user. It is a timestamped public market snapshot and must say that it is not a trading signal. A `desk.md` warning from the doctor is expected until section 8; a repository or public API failure is not. Research, briefs and the strategy lab need no key. This checkout never adds one.

For a requested historical experiment, the Market Analyst and Strategist follow [Research datasets](docs/RESEARCH_DATASETS.md): explicit UTC bounds, a new saved bundle, coverage checks and offline replay before analysis. Do not fetch a large historical dataset as an automatic setup step. Dataset completeness does not establish an edge or change any approval gate.

## 4. Create the Bots

For each file in `agents/`, select one verified Bot or create a separate one. Use the profile card exactly:

| File | Name | Job |
| --- | --- | --- |
| `agents/desk-lead.md` | Desk Lead | Head of the Hyperliquid trading desk |
| `agents/market-analyst.md` | Market Analyst | Hyperliquid market data and microstructure |
| `agents/research-analyst.md` | Research Analyst | Fundamentals, news and catalyst research |
| `agents/strategist.md` | Strategist | Strategy design and testing partner |
| `agents/risk-manager.md` | Risk Manager | Paper sizing and the only simulator submit |
| `agents/trade-reviewer.md` | Trade Reviewer | Desk journal and post-trade review |

For each Bot:

- **Name** and **Job** from the profile card.
- **Description** (the Bot's enduring rules) from the profile card, verbatim.
- **Avatar:** the desk mascot at `/workspace/hypergrok/assets/mascot.jpg` (attach it from the computer, or let the user pick their own).
- Then send the new Bot its full **System prompt** section as its first message, prefixed with: "These are your standing instructions. Confirm you have read them and state your job in one sentence." Ask it to keep the instructions in memory and to re-read its file at `/workspace/hypergrok/agents/<name>.md` whenever it is unsure.

Read back the native Name, Job and Description and compare them exactly with the profile. Before reuse or after creation, verify the complete standing System prompt through supported native readback. If a full persistent instruction field is not exposed, acceptable separate evidence is readback of the exact full System prompt delivered as a standing-instructions message, the Bot's acknowledgement that it follows the pinned agent file, and that local file's hash matching the expected bytes from `git show 'HEAD:agents/<name>.md'`. Hashing an arbitrary local file is insufficient. Record this as `delivery-and-pointer`, with the limitation that delivery and the checked target do not establish byte-identical persistent memory. A matching Description, summarized memory or file pointer alone is insufficient.

If an existing seat differs, is missing or lacks both proof methods, create a separate Bot and verify it. Preserve the existing Bots and unrelated desks' profiles, prompts and memories. Record the selected native Bot IDs; names alone do not identify the intended seats. Grok Bot lets existing Bots create focused Bots. If a needed creation step or both supported verification methods are unavailable, give the user the exact profile card and full standing prompt for each affected role as labelled copy-and-paste blocks, and keep readiness pending until verified. The Grok Bot desk uses six separate Bots. None of them writes to an exchange.

## 5. Install the skills

Skills in Grok Bot are shared across all of the user's Bots. Inspect the shared skills first: a Desk Lead added from the public HyperGrok template carries this release's bootstrap skill. Setup installs the remaining reviewed skills from the pinned checkout without creating duplicates.

For each directory under `skills/`, compare the source with actual supported native readback of the shared skill's exact name, exact description and complete Markdown body. Grok stores the name and description separately and rebuilds the YAML wrapper without source license or metadata. Remove frontmatter, leading empty lines and the final newline only when comparing bodies; preserve all internal text, spaces and line breaks, including trailing spaces within lines. The seventeen full-file hashes in `template/grok-bot.json` still verify the pinned checkout. Neither those hashes nor a staged save argument proves the native stored content.

Record exactly one status for each skill:

1. `template`: an already-present shared skill independently read back and matched, then enabled for the selected Desk Lead. This does not claim all seventeen skills were exported by the public share.
2. `installed`: a missing skill saved with exact source name, description and normalized body, then independently read back and matched.
3. `pointer`: if the app cannot save the body, save the source name and description with "When this skill is used, read `/workspace/hypergrok/skills/<name>/SKILL.md` and follow it." Verify the complete stored pointer text and target's full-file hash.
4. `mismatch`: native content differs or cannot be read back completely. Name the reason and fail native readiness. Do not overwrite shared content used by unrelated desks without user authority.

The receipt must list exactly seventeen unique names, one status and native readback evidence or an unavailable reason for each. A name, local file or staged argument alone is insufficient.

When copying a skill into another workspace or distributing the desk, retain its `LICENSE` and `ATTRIBUTION.md` beside the instructions. If the destination only accepts a single instruction field, keep the complete license notice in its accompanying project documentation or third-party notices. See [reuse and attribution](ATTRIBUTION.md); stars and public credit links are optional.


Skills to install (17):

- Bootstrap: `hypergrok-bootstrap`
- Hyperliquid: `hyperliquid-setup`, `hyperliquid-market-data`, `hyperliquid-account`, `hyperliquid-orders`, `hyperliquid-positions`, `hyperliquid-websocket`, `hyperliquid-advanced`, `hyperliquid-api-reference`
- Desk: `desk-operating-model`, `desk-trade-lifecycle`, `desk-risk-limits`, `desk-execution-protocol`, `desk-monitoring`, `desk-post-trade-review`, `desk-incident-response`, `desk-strategy-lab`

Tell each Bot which skills are its own (listed in its agent file's frontmatter). Any Bot may read any skill. Only the Risk Manager runs `scripts/paper_sim.py`. `hyperliquid-orders`, `hyperliquid-positions` and `hyperliquid-advanced` do not send an exchange request.

## 6. Create the Trading Floor

Create one private group chat named **Trading Floor** with the selected native Bot IDs for exactly these five roles: Desk Lead, Market Analyst, Research Analyst, Strategist, Risk Manager. (The Trade Reviewer works from its own conversation and by direct message.) Reuse a group only when its ID is already selected for this desk and native readback confirms exactly those five member IDs. Preserve prior groups; a matching name alone is insufficient. Record the group ID and membership IDs. If creation or membership readback is unavailable, return the exact manual step and keep group readiness pending. Send the welcome message and later role checks to the recorded Floor ID.

Post this as the first message in the group:

> Welcome to the Trading Floor. Desk Lead routes; Market Analyst and Research Analyst bring evidence; Strategist helps the user test their own ideas; Risk Manager sizes and can refuse, and is the only Bot that may run the paper simulator after you approve a ticket by id. Rules: `/workspace/hypergrok/skills/desk-operating-model/SKILL.md`. Trade Reviewer is a DM away. Today is setup: nothing is submitted.

## 7. Approvals

Do not provision a key and do not submit a live order to test the desk. A paper order still needs the user's exact ticket id. Record that this checkout has no exchange writer in `desk.md`.

There is no standing approval that skips the trailing stop, the 2:1 payoff, or the 1% risk cap. Those checks live in `scripts/paper_sim.py`.

## 8. Write the desk record

Ask the user two questions, then write `/workspace/trading-desk/desk.md`:

Record only verified Bot, group and member IDs as observed; mark uncreated, manual or unverified roles and any unverified Floor as pending rather than copying the desired six-Bot/five-member inventory as an observed result.

1. Engagement level is **paper**. Do not ask for testnet or mainnet.
2. Optional: a public address for read-only `scripts/account_read.py`. It is not the paper wallet.

```markdown
# Desk record

- created: 2026-08-16 15:00 UTC
- instructions commit: 0000000        # git rev-parse HEAD from step 1
- engagement level: paper
- network: public-info
- account: none
- bots: Desk Lead, Market Analyst, Research Analyst, Strategist, Risk Manager, Trade Reviewer
- bot ids: <role to verified native Bot ID>
- group chats: Trading Floor (5)
- trading floor id and member ids: <verified native group and five Bot IDs>
- risk limits: simulator defaults in skills/desk-risk-limits
- standing approvals: none
- exchange writer: none
- status: paper-only; no key requested
```

Then hand the Risk Manager the `desk-risk-limits` interview to write `risk-limits.md` with the user. It is short, and it is where the user decides how the desk trades for them.

## 9. Verify the desk (read-only)

Run the desk-wide checks first:

```bash
cd /workspace/hypergrok
python3 scripts/desk_doctor.py --desk-root /workspace/trading-desk
python3 scripts/opening_bell.py --coin BTC
```

Then run these and record the results:

1. In the Trading Floor, ask: "@Market Analyst brief us on BTC." Expect a timestamped brief with sources.
2. Ask: "@Risk Manager size a hypothetical long BTC on the $100 paper wallet." Expect a PASS or REJECT that names the trailing stop, 2:1 payoff, and 1% cap.
3. Ask: "@Risk Manager what command submits that ticket?" Expect `scripts/paper_sim.py` and a refusal to use any other path.
4. DM the Trade Reviewer: "Open today's journal and record that the desk was set up." Expect a journal entry.
5. Ask the Research Analyst for one sourced fact about Hyperliquid itself.

## 10. Return the receipt

Finish by giving the user:

- the six Bot IDs, created/reused/manual-card status, profile comparison and standing-instruction proof method, including any `delivery-and-pointer` limitation
- each skill's status, native readback method or unavailable reason, normalized stored body length/hash and comparison result; distinguish pointer evidence
- the Trading Floor ID and verified member IDs
- the desk record and its paper engagement level
- confirmation that no exchange writer exists
- the desk doctor and Opening Bell results
- the results of the five verification checks
- confirmation that setup requested no key and placed no live order

Only after the required checks pass, say: "The desk is ready. Ask the Desk Lead for a market brief, or ask the Risk Manager to paper-submit a BTC or ETH ticket." Otherwise name the failed or pending check and next safe action.

## If you are not Grok Bot

Use the guide for your runtime:

- [Claude Code](docs/hyperliquid-claude-code.md): plugin skills, subagents and the exchange-write confirmation hook. Invoke `/hypergrok:desk-operating-model` explicitly; `rules/` is not a Claude Code plugin component.
- [Cursor](docs/hyperliquid-cursor.md): skills, role profiles and the declared desk rules.
- [Grok Build](docs/hyperliquid-grok-build.md): skills and agent directories; rule loading remains unverified.
- [Codex](docs/hyperliquid-codex.md): skills, with role prompts run as labelled passes.
- [Gemini CLI](docs/hyperliquid-gemini-cli.md): skills and `GEMINI.md`, with role prompts run as labelled passes.

Grok Bot's cloud paths, native Bot creation and Trading Floor steps do not describe these runtimes. Use their supported workspace and role mechanisms, and report what actually loaded. Preserve the paper simulator's checks. Do not provision a key.
