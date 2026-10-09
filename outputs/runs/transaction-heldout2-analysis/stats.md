# V6 statistics — SAFE-Guard outcome metrics

Runs: `transaction-heldout2`

Unit of inference is the task: (task, seed) pairs are averaged per task before the Wilcoxon signed-rank test. Δ = treatment − control (pair mean) with a 95% task-clustered bootstrap CI. Holm correction within each (family, tier). McNemar on pairs is a sensitivity check that ignores clustering. `unconfirmed_writes` and `unauthenticated_writes` reuse SAFE-Guard heuristics and measure rule adherence, not independent safety.

## Per-variant summary (all domains)

| variant | n | excl. | no reward | success | any_unsafe_write | commission_error | unsafe_extra_writes | missed_gold_writes | transferred | blocked_calls |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 102 | 0 | 0 | 0.765 | 0.108 | 0.000 | 0.108 | 0.225 | 0.069 | 0.000 |
| safeguard-transaction | 102 | 0 | 0 | 0.618 | 0.137 | 0.000 | 0.157 | 0.363 | 0.088 | 1.451 |

## Per-variant summary — retail

| variant | n | excl. | no reward | success | any_unsafe_write | commission_error | unsafe_extra_writes | missed_gold_writes | transferred | blocked_calls |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 102 | 0 | 0 | 0.765 | 0.108 | 0.000 | 0.108 | 0.225 | 0.069 | 0.000 |
| safeguard-transaction | 102 | 0 | 0 | 0.618 | 0.137 | 0.000 | 0.157 | 0.363 | 0.088 | 1.451 |

## Blocks by rule

- **safeguard-transaction**: A:intent_cheapest: 9, F:transaction_unbound: 148, S:order_status: 3, S:same_item: 1

## Primary comparisons

| comparison | metric | tier | pairs | tasks | treat | ctrl | Δ [95% CI] | better/worse tasks | p (task Wilcoxon) | p Holm | McNemar b/c, p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| safeguard-transaction vs baseline | any_unsafe_write | primary | 102 | 34 | 0.137 | 0.108 | 0.029 [-0.049, 0.108] | 3/5 | 0.617 | 1.000 | 10/7, 0.629 |
| safeguard-transaction vs baseline | commission_error | primary | 102 | 34 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | 0/0, 1.000 |
| safeguard-transaction vs baseline | success | primary | 102 | 34 | 0.618 | 0.765 | -0.147 [-0.275, -0.020] | 4/13 | 0.039 | 0.118 | 8/23, 0.011 |
| safeguard-transaction vs baseline | unsafe_extra_writes | secondary | 102 | 34 | 0.157 | 0.108 | 0.049 [-0.049, 0.157] | 3/5 | 0.539 | 1.000 | — |
| safeguard-transaction vs baseline | missed_gold_writes | secondary | 102 | 34 | 0.363 | 0.225 | 0.137 [-0.039, 0.333] | 4/8 | 0.153 | 0.917 | — |
| safeguard-transaction vs baseline | executed_writes | secondary | 102 | 34 | 1.265 | 1.353 | -0.088 [-0.255, 0.029] | 5/3 | 0.375 | 1.000 | — |
| safeguard-transaction vs baseline | transferred | secondary | 102 | 34 | 0.088 | 0.069 | 0.020 [-0.049, 0.088] | 4/5 | 0.781 | 1.000 | 6/4, 0.754 |
| safeguard-transaction vs baseline | unconfirmed_writes | secondary | 102 | 34 | 0.000 | 0.039 | -0.039 [-0.098, 0.000] | 2/0 | 0.500 | 1.000 | — |
| safeguard-transaction vs baseline | unauthenticated_writes | secondary | 102 | 34 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard-transaction vs baseline | blocked_calls | secondary | 102 | 34 | 1.451 | 0.000 | 1.451 [1.118, 1.814] | 0/30 | <0.001 | <0.001 | — |

## Primary comparisons — retail only (exploratory)

| comparison | metric | tier | pairs | tasks | treat | ctrl | Δ [95% CI] | better/worse tasks | p (task Wilcoxon) | p Holm | McNemar b/c, p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| safeguard-transaction vs baseline | any_unsafe_write | primary | 102 | 34 | 0.137 | 0.108 | 0.029 [-0.049, 0.108] | 3/5 | 0.617 | 1.000 | 10/7, 0.629 |
| safeguard-transaction vs baseline | commission_error | primary | 102 | 34 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | 0/0, 1.000 |
| safeguard-transaction vs baseline | success | primary | 102 | 34 | 0.618 | 0.765 | -0.147 [-0.275, -0.020] | 4/13 | 0.039 | 0.118 | 8/23, 0.011 |
| safeguard-transaction vs baseline | unsafe_extra_writes | secondary | 102 | 34 | 0.157 | 0.108 | 0.049 [-0.049, 0.157] | 3/5 | 0.539 | 1.000 | — |
| safeguard-transaction vs baseline | missed_gold_writes | secondary | 102 | 34 | 0.363 | 0.225 | 0.137 [-0.039, 0.333] | 4/8 | 0.153 | 0.917 | — |
| safeguard-transaction vs baseline | executed_writes | secondary | 102 | 34 | 1.265 | 1.353 | -0.088 [-0.255, 0.029] | 5/3 | 0.375 | 1.000 | — |
| safeguard-transaction vs baseline | transferred | secondary | 102 | 34 | 0.088 | 0.069 | 0.020 [-0.049, 0.088] | 4/5 | 0.781 | 1.000 | 6/4, 0.754 |
| safeguard-transaction vs baseline | unconfirmed_writes | secondary | 102 | 34 | 0.000 | 0.039 | -0.039 [-0.098, 0.000] | 2/0 | 0.500 | 1.000 | — |
| safeguard-transaction vs baseline | unauthenticated_writes | secondary | 102 | 34 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard-transaction vs baseline | blocked_calls | secondary | 102 | 34 | 1.451 | 0.000 | 1.451 [1.118, 1.814] | 0/30 | <0.001 | <0.001 | — |
