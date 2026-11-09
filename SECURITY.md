# Security

Use GitHub's **Report a vulnerability** flow to open a private security advisory. Do not put keys, signatures, wallet exports, account payloads or exploitable details in a public issue.

What "vulnerability" means for this paper-only branch: any prose or snippet that could lead a Bot to send a live order, to handle a key or seed phrase, or to move funds. Those are bugs; report them.

Operating reminders that live in the skills:

+ This checkout reads no private key and stores none.
+ All Bots for one user share a computer, so Bot identity is not a boundary. The simulator's checks are.
+ In Claude Code, the plugin's [exchange write gate](hooks/exchange_write_gate.py) denies a Bash command, or script it names, that looks like a signed exchange write. It never approves anything.

## Host limits this repository cannot close

+ Installing this repository does not provide host isolation. The deployment wall must be verified separately. Nothing in this checkout can prove that the machine, the agent runtime, or the network will refuse a program that is not part of this tree.
+ A stop that gaps through its level fills at the gapped mark, not at the stop. The 1% check is the planned trail when the order is accepted. A later gap can lose more than that, and the cap is not a real-world guarantee.
+ A reviewed host may isolate one subprocess with `sudo /opt/hypergrok-wall/hg-run`. This repository does not install that wall. The wall is subprocess isolation only, not whole-bot isolation. Privileged Shell, sudo, and trading connectors stay outside it. Inside that subprocess the read-only runtime is `/opt/hypergrok-wall/runtime` and the writable state is `/home/hypergrok/state`. `/workspace` is hidden. Set `HYPERGROK_RUNTIME` and `HYPERGROK_STATE` to those paths. If either is unset, stop.
+ The host TLS relay allows `api.hyperliquid.xyz:443`. It does not filter `/info` from `/exchange`. `/exchange` is reachable by the host. This checkout still posts only to `https://api.hyperliquid.xyz/info` and has no signer. Do not claim the host blocks `/exchange`.
+ A person at a shell can still run their own HTTP client. This checkout does not contain a signer, a key path, or an order client, and it cannot stop a program that was never part of the repo.
+ Cursor loads no hook. The deny hook is a Claude Code file. It does not see Cursor tool calls.
+ This process disables urllib environment proxies and refuses redirects off `api.hyperliquid.xyz`. A host that intercepts traffic outside the process is outside this fix.
+ Deleting the state directory removes history the process cannot restore. Submit then refuses until an explicit `reset`, which writes a reset record. The operating system can still delete files.

Supported versions:

| Version | Supported |
| --- | --- |
| 1.x | Yes |
