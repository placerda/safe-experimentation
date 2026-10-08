# V6 statistics — SAFE-Guard outcome metrics

Runs: `20261008_180726__v6-heldout`

Unit of inference is the task: (task, seed) pairs are averaged per task before the Wilcoxon signed-rank test. Δ = treatment − control (pair mean) with a 95% task-clustered bootstrap CI. Holm correction within each (family, tier). McNemar on pairs is a sensitivity check that ignores clustering. `unconfirmed_writes` and `unauthenticated_writes` reuse SAFE-Guard heuristics and measure rule adherence, not independent safety.

## Per-variant summary (all domains)

| variant | n | excl. | no reward | success | any_unsafe_write | commission_error | unsafe_extra_writes | missed_gold_writes | transferred | blocked_calls |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 90 | 0 | 0 | 0.722 | 0.156 | 0.000 | 0.156 | 0.289 | 0.056 | 0.000 |
| safeguard | 90 | 0 | 0 | 0.678 | 0.178 | 0.000 | 0.211 | 0.367 | 0.033 | 0.144 |

## Per-variant summary — retail

| variant | n | excl. | no reward | success | any_unsafe_write | commission_error | unsafe_extra_writes | missed_gold_writes | transferred | blocked_calls |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 90 | 0 | 0 | 0.722 | 0.156 | 0.000 | 0.156 | 0.289 | 0.056 | 0.000 |
| safeguard | 90 | 0 | 0 | 0.678 | 0.178 | 0.000 | 0.211 | 0.367 | 0.033 | 0.144 |

## Blocks by rule

- **safeguard**: F:confirm: 3, F:confirm_unbound: 10

## Primary comparisons

| comparison | metric | tier | pairs | tasks | treat | ctrl | Δ [95% CI] | better/worse tasks | p (task Wilcoxon) | p Holm | McNemar b/c, p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| safeguard vs baseline | any_unsafe_write | primary | 90 | 30 | 0.178 | 0.156 | 0.022 [-0.056, 0.111] | 2/3 | 0.812 | 1.000 | 6/4, 0.754 |
| safeguard vs baseline | commission_error | primary | 90 | 30 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | 0/0, 1.000 |
| safeguard vs baseline | success | primary | 90 | 30 | 0.678 | 0.722 | -0.044 [-0.167, 0.067] | 5/6 | 0.523 | 1.000 | 9/13, 0.523 |
| safeguard vs baseline | unsafe_extra_writes | secondary | 90 | 30 | 0.211 | 0.156 | 0.056 [-0.056, 0.200] | 2/3 | 0.688 | 1.000 | — |
| safeguard vs baseline | missed_gold_writes | secondary | 90 | 30 | 0.367 | 0.289 | 0.078 [-0.044, 0.233] | 3/5 | 0.461 | 1.000 | — |
| safeguard vs baseline | executed_writes | secondary | 90 | 30 | 1.678 | 1.700 | -0.022 [-0.122, 0.067] | 3/3 | 0.812 | 1.000 | — |
| safeguard vs baseline | transferred | secondary | 90 | 30 | 0.033 | 0.056 | -0.022 [-0.067, 0.022] | 3/1 | 0.625 | 1.000 | 2/4, 0.688 |
| safeguard vs baseline | unconfirmed_writes | secondary | 90 | 30 | 0.000 | 0.022 | -0.022 [-0.067, 0.000] | 1/0 | 1.000 | 1.000 | — |
| safeguard vs baseline | unauthenticated_writes | secondary | 90 | 30 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs baseline | blocked_calls | secondary | 90 | 30 | 0.144 | 0.000 | 0.144 [0.033, 0.289] | 0/4 | 0.125 | 0.875 | — |

## Primary comparisons — retail only (exploratory)

| comparison | metric | tier | pairs | tasks | treat | ctrl | Δ [95% CI] | better/worse tasks | p (task Wilcoxon) | p Holm | McNemar b/c, p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| safeguard vs baseline | any_unsafe_write | primary | 90 | 30 | 0.178 | 0.156 | 0.022 [-0.056, 0.111] | 2/3 | 0.812 | 1.000 | 6/4, 0.754 |
| safeguard vs baseline | commission_error | primary | 90 | 30 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | 0/0, 1.000 |
| safeguard vs baseline | success | primary | 90 | 30 | 0.678 | 0.722 | -0.044 [-0.167, 0.067] | 5/6 | 0.523 | 1.000 | 9/13, 0.523 |
| safeguard vs baseline | unsafe_extra_writes | secondary | 90 | 30 | 0.211 | 0.156 | 0.056 [-0.056, 0.200] | 2/3 | 0.688 | 1.000 | — |
| safeguard vs baseline | missed_gold_writes | secondary | 90 | 30 | 0.367 | 0.289 | 0.078 [-0.044, 0.233] | 3/5 | 0.461 | 1.000 | — |
| safeguard vs baseline | executed_writes | secondary | 90 | 30 | 1.678 | 1.700 | -0.022 [-0.122, 0.067] | 3/3 | 0.812 | 1.000 | — |
| safeguard vs baseline | transferred | secondary | 90 | 30 | 0.033 | 0.056 | -0.022 [-0.067, 0.022] | 3/1 | 0.625 | 1.000 | 2/4, 0.688 |
| safeguard vs baseline | unconfirmed_writes | secondary | 90 | 30 | 0.000 | 0.022 | -0.022 [-0.067, 0.000] | 1/0 | 1.000 | 1.000 | — |
| safeguard vs baseline | unauthenticated_writes | secondary | 90 | 30 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs baseline | blocked_calls | secondary | 90 | 30 | 0.144 | 0.000 | 0.144 [0.033, 0.289] | 0/4 | 0.125 | 0.875 | — |
