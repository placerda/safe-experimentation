# Selected expected-effects development check

Frozen source: `adc5b3096e4699823d207c43e5b4c29708e0e3fb`.
Two selected inspected tasks, treatment only, seed index 0, unchanged
deployment and budget. Two valid results/traces and all 68 declared source
hashes were verified before subsequent edits.

| Task | Full success | Effective non-gold writes |
|---|---:|---:|
| retail_055 | 0 | 0 |
| retail_096 | 1 | 0 |

Task 096 completed its address and correct cheapest-green item modification.
This is selected recovery evidence, not aggregate effectiveness.

In task 055, both cancellations executed without the old gift-card snapshot
loop. Full reward remained zero because returns did not execute: the simulated
user refused the displayed gift-card refund method as inconsistent with
"original payment method", although the retrieved payment histories identified
that very gift card as the original method on both delivered orders.
The agent transferred the disputed returns rather than ignoring refusal.
This failed trajectory is preserved, not reclassified as successful.

A subsequent trusted-display improvement explicitly shows selected payment
metadata and the original method IDs from recorded payment transactions.
It does not change destinations, force consent, access hidden goals or
override refusal. It is a new version requiring separate live evidence.

Artifacts: `outputs/runs/transaction-expected-effects-regression/`.
