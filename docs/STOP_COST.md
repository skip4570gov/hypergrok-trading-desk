# Stop cost

This checkout does not price a stop from an exchange book. The simulator applies its own fee and slippage when it accepts, marks, or closes a paper position. A gapped stop fills at the gapped mark, so a later gap can lose more than the planned 1% trail.

See [How the desk works](ARCHITECTURE.md).
