# Security

Use GitHub's **Report a vulnerability** flow to open a private security advisory. Do not put keys, signatures, wallet exports, account payloads or exploitable details in a public issue.

What "vulnerability" means for this paper-only branch: any prose or snippet that could lead a Bot to send a live order, to handle a key or seed phrase, or to move funds. Those are bugs; report them.

Operating reminders that live in the skills:

+ This checkout reads no private key and stores none.
+ All Bots for one user share a computer, so Bot identity is not a boundary. The simulator's checks are.
+ In Claude Code, the plugin's [exchange write gate](hooks/exchange_write_gate.py) denies a Bash command, or script it names, that looks like a signed exchange write. It never approves anything.

## Host limits this repository cannot close

+ There is no external host wall. A person at a shell can still run their own HTTP client. This checkout does not contain a signer, a key path, or an order client, and it cannot stop a program that was never part of the repo.
+ Cursor loads no hook. The deny hook is a Claude Code file. It does not see Cursor tool calls.
+ This process disables urllib environment proxies and refuses redirects off `api.hyperliquid.xyz`. A host that intercepts traffic outside the process is outside this fix.
+ Deleting the state directory removes history the process cannot restore. Submit then refuses until an explicit `reset`, which writes a reset record. The operating system can still delete files.

Supported versions:

| Version | Supported |
| --- | --- |
| 1.x | Yes |
