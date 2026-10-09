# V6 statistics — SAFE-Guard outcome metrics

Runs: `transaction-effects-full-development`

Unit of inference is the task: (task, seed) pairs are averaged per task before the Wilcoxon signed-rank test. Δ = treatment − control (pair mean) with a 95% task-clustered bootstrap CI. Holm correction within each (family, tier). McNemar on pairs is a sensitivity check that ignores clustering. `unconfirmed_writes` and `unauthenticated_writes` reuse SAFE-Guard heuristics and measure rule adherence, not independent safety.

## Per-variant summary (all domains)

| variant | n | excl. | no reward | success | any_unsafe_write | commission_error | unsafe_extra_writes | missed_gold_writes | transferred | blocked_calls |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 34 | 0 | 0 | 0.735 | 0.147 | 0.000 | 0.176 | 0.206 | 0.000 | 0.000 |
| safeguard-transaction | 34 | 0 | 0 | 0.765 | 0.088 | 0.000 | 0.088 | 0.265 | 0.118 | 1.853 |

## Per-variant summary — retail

| variant | n | excl. | no reward | success | any_unsafe_write | commission_error | unsafe_extra_writes | missed_gold_writes | transferred | blocked_calls |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 34 | 0 | 0 | 0.735 | 0.147 | 0.000 | 0.176 | 0.206 | 0.000 | 0.000 |
| safeguard-transaction | 34 | 0 | 0 | 0.765 | 0.088 | 0.000 | 0.088 | 0.265 | 0.118 | 1.853 |

## Blocks by rule

- **safeguard-transaction**: A:intent_candidate_set: 1, A:intent_return_coverage: 1, F:transaction_stale: 1, F:transaction_unbound: 62, S:same_item: 1, S:variant_unavailable: 1

## Primary comparisons

| comparison | metric | tier | pairs | tasks | treat | ctrl | Δ [95% CI] | better/worse tasks | p (task Wilcoxon) | p Holm | McNemar b/c, p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| safeguard-transaction vs baseline | any_unsafe_write | primary | 34 | 34 | 0.088 | 0.147 | -0.059 [-0.206, 0.088] | 4/2 | 0.688 | 1.000 | 2/4, 0.688 |
| safeguard-transaction vs baseline | commission_error | primary | 34 | 34 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | 0/0, 1.000 |
| safeguard-transaction vs baseline | success | primary | 34 | 34 | 0.765 | 0.735 | 0.029 [-0.147, 0.206] | 6/5 | 1.000 | 1.000 | 6/5, 1.000 |
| safeguard-transaction vs baseline | unsafe_extra_writes | secondary | 34 | 34 | 0.088 | 0.176 | -0.088 [-0.265, 0.059] | 4/2 | 0.531 | 1.000 | — |
| safeguard-transaction vs baseline | missed_gold_writes | secondary | 34 | 34 | 0.265 | 0.206 | 0.059 [-0.176, 0.324] | 4/5 | 0.836 | 1.000 | — |
| safeguard-transaction vs baseline | executed_writes | secondary | 34 | 34 | 1.294 | 1.441 | -0.147 [-0.324, 0.000] | 5/1 | 0.188 | 0.938 | — |
| safeguard-transaction vs baseline | transferred | secondary | 34 | 34 | 0.118 | 0.000 | 0.118 [0.029, 0.235] | 0/4 | 0.125 | 0.750 | 4/0, 0.125 |
| safeguard-transaction vs baseline | unconfirmed_writes | secondary | 34 | 34 | 0.000 | 0.029 | -0.029 [-0.088, 0.000] | 1/0 | 1.000 | 1.000 | — |
| safeguard-transaction vs baseline | unauthenticated_writes | secondary | 34 | 34 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard-transaction vs baseline | blocked_calls | secondary | 34 | 34 | 1.853 | 0.000 | 1.853 [1.324, 2.471] | 0/29 | <0.001 | <0.001 | — |

## Primary comparisons — retail only (exploratory)

| comparison | metric | tier | pairs | tasks | treat | ctrl | Δ [95% CI] | better/worse tasks | p (task Wilcoxon) | p Holm | McNemar b/c, p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| safeguard-transaction vs baseline | any_unsafe_write | primary | 34 | 34 | 0.088 | 0.147 | -0.059 [-0.206, 0.088] | 4/2 | 0.688 | 1.000 | 2/4, 0.688 |
| safeguard-transaction vs baseline | commission_error | primary | 34 | 34 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | 0/0, 1.000 |
| safeguard-transaction vs baseline | success | primary | 34 | 34 | 0.765 | 0.735 | 0.029 [-0.147, 0.206] | 6/5 | 1.000 | 1.000 | 6/5, 1.000 |
| safeguard-transaction vs baseline | unsafe_extra_writes | secondary | 34 | 34 | 0.088 | 0.176 | -0.088 [-0.265, 0.059] | 4/2 | 0.531 | 1.000 | — |
| safeguard-transaction vs baseline | missed_gold_writes | secondary | 34 | 34 | 0.265 | 0.206 | 0.059 [-0.176, 0.324] | 4/5 | 0.836 | 1.000 | — |
| safeguard-transaction vs baseline | executed_writes | secondary | 34 | 34 | 1.294 | 1.441 | -0.147 [-0.324, 0.000] | 5/1 | 0.188 | 0.938 | — |
| safeguard-transaction vs baseline | transferred | secondary | 34 | 34 | 0.118 | 0.000 | 0.118 [0.029, 0.235] | 0/4 | 0.125 | 0.750 | 4/0, 0.125 |
| safeguard-transaction vs baseline | unconfirmed_writes | secondary | 34 | 34 | 0.000 | 0.029 | -0.029 [-0.088, 0.000] | 1/0 | 1.000 | 1.000 | — |
| safeguard-transaction vs baseline | unauthenticated_writes | secondary | 34 | 34 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard-transaction vs baseline | blocked_calls | secondary | 34 | 34 | 1.853 | 0.000 | 1.853 [1.324, 2.471] | 0/29 | <0.001 | <0.001 | — |
