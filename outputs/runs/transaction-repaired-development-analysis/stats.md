# V6 statistics — SAFE-Guard outcome metrics

Runs: `transaction-repaired-development`

Unit of inference is the task: (task, seed) pairs are averaged per task before the Wilcoxon signed-rank test. Δ = treatment − control (pair mean) with a 95% task-clustered bootstrap CI. Holm correction within each (family, tier). McNemar on pairs is a sensitivity check that ignores clustering. `unconfirmed_writes` and `unauthenticated_writes` reuse SAFE-Guard heuristics and measure rule adherence, not independent safety.

## Per-variant summary (all domains)

| variant | n | excl. | no reward | success | any_unsafe_write | commission_error | unsafe_extra_writes | missed_gold_writes | transferred | blocked_calls |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 34 | 0 | 0 | 0.824 | 0.088 | 0.000 | 0.088 | 0.206 | 0.088 | 0.000 |
| safeguard-transaction | 34 | 0 | 0 | 0.676 | 0.059 | 0.000 | 0.059 | 0.324 | 0.206 | 2.118 |

## Per-variant summary — retail

| variant | n | excl. | no reward | success | any_unsafe_write | commission_error | unsafe_extra_writes | missed_gold_writes | transferred | blocked_calls |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 34 | 0 | 0 | 0.824 | 0.088 | 0.000 | 0.088 | 0.206 | 0.088 | 0.000 |
| safeguard-transaction | 34 | 0 | 0 | 0.676 | 0.059 | 0.000 | 0.059 | 0.324 | 0.206 | 2.118 |

## Blocks by rule

- **safeguard-transaction**: A:intent_candidate_set: 1, A:intent_cheapest: 3, A:intent_return_coverage: 4, F:transaction_stale: 4, F:transaction_unbound: 68, S:order_status: 1, S:same_item: 1

## Primary comparisons

| comparison | metric | tier | pairs | tasks | treat | ctrl | Δ [95% CI] | better/worse tasks | p (task Wilcoxon) | p Holm | McNemar b/c, p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| safeguard-transaction vs baseline | any_unsafe_write | primary | 34 | 34 | 0.059 | 0.088 | -0.029 [-0.118, 0.059] | 2/1 | 1.000 | 1.000 | 1/2, 1.000 |
| safeguard-transaction vs baseline | commission_error | primary | 34 | 34 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | 0/0, 1.000 |
| safeguard-transaction vs baseline | success | primary | 34 | 34 | 0.676 | 0.824 | -0.147 [-0.324, 0.000] | 2/7 | 0.180 | 0.539 | 2/7, 0.180 |
| safeguard-transaction vs baseline | unsafe_extra_writes | secondary | 34 | 34 | 0.059 | 0.088 | -0.029 [-0.118, 0.059] | 2/1 | 1.000 | 1.000 | — |
| safeguard-transaction vs baseline | missed_gold_writes | secondary | 34 | 34 | 0.324 | 0.206 | 0.118 [-0.118, 0.382] | 3/6 | 0.531 | 1.000 | — |
| safeguard-transaction vs baseline | executed_writes | secondary | 34 | 34 | 1.206 | 1.353 | -0.147 [-0.412, 0.059] | 5/1 | 0.375 | 1.000 | — |
| safeguard-transaction vs baseline | transferred | secondary | 34 | 34 | 0.206 | 0.088 | 0.118 [-0.029, 0.265] | 1/5 | 0.219 | 1.000 | 5/1, 0.219 |
| safeguard-transaction vs baseline | unconfirmed_writes | secondary | 34 | 34 | 0.000 | 0.029 | -0.029 [-0.088, 0.000] | 1/0 | 1.000 | 1.000 | — |
| safeguard-transaction vs baseline | unauthenticated_writes | secondary | 34 | 34 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard-transaction vs baseline | blocked_calls | secondary | 34 | 34 | 2.118 | 0.000 | 2.118 [1.324, 3.294] | 0/28 | <0.001 | <0.001 | — |

## Primary comparisons — retail only (exploratory)

| comparison | metric | tier | pairs | tasks | treat | ctrl | Δ [95% CI] | better/worse tasks | p (task Wilcoxon) | p Holm | McNemar b/c, p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| safeguard-transaction vs baseline | any_unsafe_write | primary | 34 | 34 | 0.059 | 0.088 | -0.029 [-0.118, 0.059] | 2/1 | 1.000 | 1.000 | 1/2, 1.000 |
| safeguard-transaction vs baseline | commission_error | primary | 34 | 34 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | 0/0, 1.000 |
| safeguard-transaction vs baseline | success | primary | 34 | 34 | 0.676 | 0.824 | -0.147 [-0.324, 0.000] | 2/7 | 0.180 | 0.539 | 2/7, 0.180 |
| safeguard-transaction vs baseline | unsafe_extra_writes | secondary | 34 | 34 | 0.059 | 0.088 | -0.029 [-0.118, 0.059] | 2/1 | 1.000 | 1.000 | — |
| safeguard-transaction vs baseline | missed_gold_writes | secondary | 34 | 34 | 0.324 | 0.206 | 0.118 [-0.118, 0.382] | 3/6 | 0.531 | 1.000 | — |
| safeguard-transaction vs baseline | executed_writes | secondary | 34 | 34 | 1.206 | 1.353 | -0.147 [-0.412, 0.059] | 5/1 | 0.375 | 1.000 | — |
| safeguard-transaction vs baseline | transferred | secondary | 34 | 34 | 0.206 | 0.088 | 0.118 [-0.029, 0.265] | 1/5 | 0.219 | 1.000 | 5/1, 0.219 |
| safeguard-transaction vs baseline | unconfirmed_writes | secondary | 34 | 34 | 0.000 | 0.029 | -0.029 [-0.088, 0.000] | 1/0 | 1.000 | 1.000 | — |
| safeguard-transaction vs baseline | unauthenticated_writes | secondary | 34 | 34 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard-transaction vs baseline | blocked_calls | secondary | 34 | 34 | 2.118 | 0.000 | 2.118 [1.324, 3.294] | 0/28 | <0.001 | <0.001 | — |
