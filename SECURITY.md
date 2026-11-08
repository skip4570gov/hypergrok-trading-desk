# Security

Use GitHub's **Report a vulnerability** flow to open a private security advisory. Do not put keys, signatures, wallet exports, account payloads or exploitable details in a public issue.

What "vulnerability" means for this paper-only branch: any prose or snippet that could lead a Bot to send a live order, to handle a key or seed phrase, or to move funds. Those are bugs; report them.

Operating reminders that live in the skills:

+ This checkout reads no private key and stores none.
+ All Bots for one user share a computer, so Bot identity is not a boundary. The simulator's checks are.
+ In Claude Code, the plugin's [exchange write gate](hooks/exchange_write_gate.py) denies a Bash command, or script it names, that looks like a signed exchange write. It never approves anything. Cursor does not load that hook; this branch removes the write instead of asking Cursor to confirm one.
+ Resting entries and unknown sends retain risk and margin reservations until terminal reconciliation. A restart, old ticket expiry or cancel acknowledgement cannot free dispatched capacity; a feed reconnect requires account recovery before new risk resumes.
+ If a send times out or errors after leaving the machine, do not retry. Reconcile the client order id first, and treat a replacement as unsafe until the original send's expiry has passed and a further check is clean - not finding an order is not proof it will never arrive.
+ Suspected key misuse: the user revokes the API wallet in the Hyperliquid app first, then the desk investigates.

Supported versions:

| Version | Supported |
| --- | --- |
| 1.x | Yes |
