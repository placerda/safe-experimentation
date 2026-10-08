# V6 statistics — SAFE-Guard outcome metrics

Runs: `20261008_125423__v6-full`

Unit of inference is the task: (task, seed) pairs are averaged per task before the Wilcoxon signed-rank test. Δ = treatment − control (pair mean) with a 95% task-clustered bootstrap CI. Holm correction within each (family, tier). McNemar on pairs is a sensitivity check that ignores clustering. `unconfirmed_writes` and `unauthenticated_writes` reuse SAFE-Guard heuristics and measure rule adherence, not independent safety.

## Per-variant summary (all domains)

| variant | n | excl. | success | any_unsafe_write | commission_error | unsafe_extra_writes | missed_gold_writes | transferred | blocked_calls |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 75 | 0 | 0.707 | 0.187 | 0.120 | 0.267 | 0.333 | 0.387 | 0.000 |
| safe-prompt | 75 | 0 | 0.720 | 0.213 | 0.093 | 0.307 | 0.333 | 0.347 | 0.000 |
| safeguard | 75 | 0 | 0.813 | 0.080 | 0.053 | 0.107 | 0.160 | 0.427 | 0.227 |
| safeguard-noS | 75 | 0 | 0.667 | 0.187 | 0.107 | 0.240 | 0.200 | 0.387 | 0.053 |
| safeguard-noA | 75 | 0 | 0.813 | 0.080 | 0.027 | 0.133 | 0.227 | 0.427 | 0.147 |
| safeguard-noF | 75 | 0 | 0.760 | 0.107 | 0.053 | 0.173 | 0.400 | 0.453 | 0.147 |
| safeguard-noE | 75 | 0 | 0.800 | 0.093 | 0.053 | 0.120 | 0.173 | 0.400 | 0.160 |

## Per-variant summary — airline

| variant | n | excl. | success | any_unsafe_write | commission_error | unsafe_extra_writes | missed_gold_writes | transferred | blocked_calls |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 39 | 0 | 0.564 | 0.256 | 0.154 | 0.333 | 0.564 | 0.410 | 0.000 |
| safe-prompt | 39 | 0 | 0.615 | 0.256 | 0.103 | 0.410 | 0.564 | 0.410 | 0.000 |
| safeguard | 39 | 0 | 0.821 | 0.026 | 0.000 | 0.077 | 0.282 | 0.513 | 0.154 |
| safeguard-noS | 39 | 0 | 0.667 | 0.179 | 0.103 | 0.205 | 0.333 | 0.410 | 0.000 |
| safeguard-noA | 39 | 0 | 0.769 | 0.077 | 0.000 | 0.179 | 0.410 | 0.513 | 0.179 |
| safeguard-noF | 39 | 0 | 0.744 | 0.026 | 0.000 | 0.077 | 0.641 | 0.590 | 0.179 |
| safeguard-noE | 39 | 0 | 0.821 | 0.026 | 0.000 | 0.051 | 0.308 | 0.513 | 0.179 |

## Per-variant summary — retail

| variant | n | excl. | success | any_unsafe_write | commission_error | unsafe_extra_writes | missed_gold_writes | transferred | blocked_calls |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 36 | 0 | 0.861 | 0.111 | 0.083 | 0.194 | 0.083 | 0.361 | 0.000 |
| safe-prompt | 36 | 0 | 0.833 | 0.167 | 0.083 | 0.194 | 0.083 | 0.278 | 0.000 |
| safeguard | 36 | 0 | 0.806 | 0.139 | 0.111 | 0.139 | 0.028 | 0.333 | 0.306 |
| safeguard-noS | 36 | 0 | 0.667 | 0.194 | 0.111 | 0.278 | 0.056 | 0.361 | 0.111 |
| safeguard-noA | 36 | 0 | 0.861 | 0.083 | 0.056 | 0.083 | 0.028 | 0.333 | 0.111 |
| safeguard-noF | 36 | 0 | 0.778 | 0.194 | 0.111 | 0.278 | 0.139 | 0.306 | 0.111 |
| safeguard-noE | 36 | 0 | 0.778 | 0.167 | 0.111 | 0.194 | 0.028 | 0.278 | 0.139 |

## Blocks by rule

- **safeguard**: F:confirm: 2, F:confirm_unbound: 5, S:cancel_ineligible: 3, S:payment_mix: 3, S:refund_method: 4
- **safeguard-noS**: F:confirm_unbound: 4
- **safeguard-noA**: F:confirm_unbound: 5, S:cancel_ineligible: 3, S:compensation_amount: 1, S:payment_mix: 2
- **safeguard-noF**: S:basic_economy_locked: 1, S:cancel_ineligible: 3, S:compensation_amount: 2, S:payment_mix: 1, S:refund_method: 4
- **safeguard-noE**: F:confirm: 1, F:confirm_unbound: 5, S:cancel_ineligible: 3, S:compensation_amount: 1, S:payment_mix: 2

## Primary comparisons

| comparison | metric | tier | pairs | tasks | treat | ctrl | Δ [95% CI] | better/worse tasks | p (task Wilcoxon) | p Holm | McNemar b/c, p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| safeguard vs baseline | any_unsafe_write | primary | 75 | 25 | 0.080 | 0.187 | -0.107 [-0.227, 0.027] | 8/3 | 0.189 | 1.000 | 4/12, 0.077 |
| safeguard vs baseline | commission_error | primary | 75 | 25 | 0.053 | 0.120 | -0.067 [-0.187, 0.040] | 5/2 | 0.406 | 1.000 | 3/8, 0.227 |
| safeguard vs baseline | success | primary | 75 | 25 | 0.813 | 0.707 | 0.107 [-0.027, 0.240] | 9/4 | 0.201 | 1.000 | 13/5, 0.096 |
| safeguard vs baseline | unsafe_extra_writes | secondary | 75 | 25 | 0.107 | 0.267 | -0.160 [-0.320, 0.000] | 8/3 | 0.100 | 1.000 | — |
| safeguard vs baseline | missed_gold_writes | secondary | 75 | 25 | 0.160 | 0.333 | -0.173 [-0.387, -0.013] | 5/1 | 0.125 | 1.000 | — |
| safeguard vs baseline | executed_writes | secondary | 75 | 25 | 1.147 | 1.133 | 0.013 [-0.200, 0.253] | 6/6 | 0.999 | 1.000 | — |
| safeguard vs baseline | transferred | secondary | 75 | 25 | 0.427 | 0.387 | 0.040 [-0.067, 0.160] | 3/4 | 0.672 | 1.000 | 7/4, 0.549 |
| safeguard vs baseline | unconfirmed_writes | secondary | 75 | 25 | 0.000 | 0.027 | -0.027 [-0.067, 0.000] | 2/0 | 0.500 | 1.000 | — |
| safeguard vs baseline | unauthenticated_writes | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs baseline | blocked_calls | secondary | 75 | 25 | 0.227 | 0.000 | 0.227 [0.040, 0.427] | 0/5 | 0.062 | 1.000 | — |
| safe-prompt vs baseline | any_unsafe_write | primary | 75 | 25 | 0.213 | 0.187 | 0.027 [-0.067, 0.133] | 4/4 | 1.000 | 1.000 | 8/6, 0.791 |
| safe-prompt vs baseline | commission_error | primary | 75 | 25 | 0.093 | 0.120 | -0.027 [-0.080, 0.027] | 3/1 | 0.625 | 1.000 | 2/4, 0.688 |
| safe-prompt vs baseline | success | primary | 75 | 25 | 0.720 | 0.707 | 0.013 [-0.107, 0.107] | 6/3 | 0.781 | 1.000 | 8/7, 1.000 |
| safe-prompt vs baseline | unsafe_extra_writes | secondary | 75 | 25 | 0.307 | 0.267 | 0.040 [-0.093, 0.187] | 4/4 | 0.586 | 1.000 | — |
| safe-prompt vs baseline | missed_gold_writes | secondary | 75 | 25 | 0.333 | 0.333 | 0.000 [-0.160, 0.160] | 3/3 | 1.000 | 1.000 | — |
| safe-prompt vs baseline | executed_writes | secondary | 75 | 25 | 1.173 | 1.133 | 0.040 [-0.093, 0.200] | 4/4 | 0.805 | 1.000 | — |
| safe-prompt vs baseline | transferred | secondary | 75 | 25 | 0.347 | 0.387 | -0.040 [-0.160, 0.067] | 4/3 | 0.562 | 1.000 | 7/10, 0.629 |
| safe-prompt vs baseline | unconfirmed_writes | secondary | 75 | 25 | 0.027 | 0.027 | 0.000 [-0.053, 0.067] | 2/1 | 1.000 | 1.000 | — |
| safe-prompt vs baseline | unauthenticated_writes | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safe-prompt vs baseline | blocked_calls | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safe-prompt | any_unsafe_write | primary | 75 | 25 | 0.080 | 0.213 | -0.133 [-0.280, 0.000] | 7/2 | 0.125 | 1.000 | 4/14, 0.031 |
| safeguard vs safe-prompt | commission_error | primary | 75 | 25 | 0.053 | 0.093 | -0.040 [-0.147, 0.053] | 3/1 | 0.625 | 1.000 | 3/6, 0.508 |
| safeguard vs safe-prompt | success | primary | 75 | 25 | 0.813 | 0.720 | 0.093 [-0.040, 0.227] | 7/3 | 0.254 | 1.000 | 12/5, 0.143 |
| safeguard vs safe-prompt | unsafe_extra_writes | secondary | 75 | 25 | 0.107 | 0.307 | -0.200 [-0.373, -0.027] | 7/2 | 0.051 | 1.000 | — |
| safeguard vs safe-prompt | missed_gold_writes | secondary | 75 | 25 | 0.160 | 0.333 | -0.173 [-0.347, -0.027] | 5/1 | 0.094 | 1.000 | — |
| safeguard vs safe-prompt | executed_writes | secondary | 75 | 25 | 1.147 | 1.173 | -0.027 [-0.213, 0.147] | 4/4 | 0.867 | 1.000 | — |
| safeguard vs safe-prompt | transferred | secondary | 75 | 25 | 0.427 | 0.347 | 0.080 [-0.053, 0.227] | 3/5 | 0.375 | 1.000 | 11/5, 0.210 |
| safeguard vs safe-prompt | unconfirmed_writes | secondary | 75 | 25 | 0.000 | 0.027 | -0.027 [-0.080, 0.000] | 1/0 | 1.000 | 1.000 | — |
| safeguard vs safe-prompt | unauthenticated_writes | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safe-prompt | blocked_calls | secondary | 75 | 25 | 0.227 | 0.000 | 0.227 [0.040, 0.427] | 0/5 | 0.062 | 1.000 | — |

## Ablation comparisons

| comparison | metric | tier | pairs | tasks | treat | ctrl | Δ [95% CI] | better/worse tasks | p (task Wilcoxon) | p Holm | McNemar b/c, p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| safeguard vs safeguard-noS | any_unsafe_write | primary | 75 | 25 | 0.080 | 0.187 | -0.107 [-0.240, 0.013] | 7/4 | 0.128 | 1.000 | 5/13, 0.096 |
| safeguard vs safeguard-noS | commission_error | primary | 75 | 25 | 0.053 | 0.107 | -0.053 [-0.160, 0.040] | 3/2 | 0.500 | 1.000 | 3/7, 0.344 |
| safeguard vs safeguard-noS | success | primary | 75 | 25 | 0.813 | 0.667 | 0.147 [0.013, 0.280] | 9/4 | 0.051 | 0.609 | 16/5, 0.027 |
| safeguard vs safeguard-noS | unsafe_extra_writes | secondary | 75 | 25 | 0.107 | 0.240 | -0.133 [-0.320, 0.040] | 7/3 | 0.178 | 1.000 | — |
| safeguard vs safeguard-noS | missed_gold_writes | secondary | 75 | 25 | 0.160 | 0.200 | -0.040 [-0.187, 0.080] | 3/3 | 0.812 | 1.000 | — |
| safeguard vs safeguard-noS | executed_writes | secondary | 75 | 25 | 1.147 | 1.240 | -0.093 [-0.293, 0.093] | 6/4 | 0.453 | 1.000 | — |
| safeguard vs safeguard-noS | transferred | secondary | 75 | 25 | 0.427 | 0.387 | 0.040 [-0.067, 0.160] | 5/5 | 0.684 | 1.000 | 9/6, 0.607 |
| safeguard vs safeguard-noS | unconfirmed_writes | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noS | unauthenticated_writes | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noS | blocked_calls | secondary | 75 | 25 | 0.227 | 0.053 | 0.173 [0.013, 0.360] | 0/4 | 0.125 | 1.000 | — |
| safeguard vs safeguard-noA | any_unsafe_write | primary | 75 | 25 | 0.080 | 0.080 | 0.000 [-0.067, 0.067] | 3/2 | 1.000 | 1.000 | 4/4, 1.000 |
| safeguard vs safeguard-noA | commission_error | primary | 75 | 25 | 0.053 | 0.027 | 0.027 [0.000, 0.080] | 0/1 | 1.000 | 1.000 | 2/0, 0.500 |
| safeguard vs safeguard-noA | success | primary | 75 | 25 | 0.813 | 0.813 | 0.000 [-0.080, 0.080] | 4/3 | 1.000 | 1.000 | 6/6, 1.000 |
| safeguard vs safeguard-noA | unsafe_extra_writes | secondary | 75 | 25 | 0.107 | 0.133 | -0.027 [-0.133, 0.067] | 3/2 | 0.812 | 1.000 | — |
| safeguard vs safeguard-noA | missed_gold_writes | secondary | 75 | 25 | 0.160 | 0.227 | -0.067 [-0.173, 0.027] | 5/2 | 0.359 | 1.000 | — |
| safeguard vs safeguard-noA | executed_writes | secondary | 75 | 25 | 1.147 | 1.107 | 0.040 [-0.027, 0.107] | 1/3 | 0.500 | 1.000 | — |
| safeguard vs safeguard-noA | transferred | secondary | 75 | 25 | 0.427 | 0.427 | 0.000 [-0.053, 0.053] | 2/2 | 1.000 | 1.000 | 2/2, 1.000 |
| safeguard vs safeguard-noA | unconfirmed_writes | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noA | unauthenticated_writes | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noA | blocked_calls | secondary | 75 | 25 | 0.227 | 0.147 | 0.080 [-0.040, 0.267] | 2/3 | 0.750 | 1.000 | — |
| safeguard vs safeguard-noF | any_unsafe_write | primary | 75 | 25 | 0.080 | 0.107 | -0.027 [-0.080, 0.013] | 3/1 | 0.625 | 1.000 | 3/5, 0.727 |
| safeguard vs safeguard-noF | commission_error | primary | 75 | 25 | 0.053 | 0.053 | 0.000 [-0.040, 0.040] | 1/1 | 1.000 | 1.000 | 1/1, 1.000 |
| safeguard vs safeguard-noF | success | primary | 75 | 25 | 0.813 | 0.760 | 0.053 [-0.013, 0.120] | 4/1 | 0.312 | 1.000 | 8/4, 0.388 |
| safeguard vs safeguard-noF | unsafe_extra_writes | secondary | 75 | 25 | 0.107 | 0.173 | -0.067 [-0.173, 0.013] | 3/1 | 0.375 | 1.000 | — |
| safeguard vs safeguard-noF | missed_gold_writes | secondary | 75 | 25 | 0.160 | 0.400 | -0.240 [-0.453, -0.067] | 6/0 | 0.031 | 0.875 | — |
| safeguard vs safeguard-noF | executed_writes | secondary | 75 | 25 | 1.147 | 0.973 | 0.173 [0.000, 0.387] | 1/5 | 0.156 | 1.000 | — |
| safeguard vs safeguard-noF | transferred | secondary | 75 | 25 | 0.427 | 0.453 | -0.027 [-0.120, 0.067] | 4/2 | 0.781 | 1.000 | 4/6, 0.754 |
| safeguard vs safeguard-noF | unconfirmed_writes | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noF | unauthenticated_writes | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noF | blocked_calls | secondary | 75 | 25 | 0.227 | 0.147 | 0.080 [-0.013, 0.200] | 2/4 | 0.219 | 1.000 | — |
| safeguard vs safeguard-noE | any_unsafe_write | primary | 75 | 25 | 0.080 | 0.093 | -0.013 [-0.093, 0.053] | 3/3 | 1.000 | 1.000 | 4/5, 1.000 |
| safeguard vs safeguard-noE | commission_error | primary | 75 | 25 | 0.053 | 0.053 | 0.000 [-0.040, 0.040] | 1/1 | 1.000 | 1.000 | 2/2, 1.000 |
| safeguard vs safeguard-noE | success | primary | 75 | 25 | 0.813 | 0.800 | 0.013 [-0.080, 0.107] | 5/5 | 1.000 | 1.000 | 8/7, 1.000 |
| safeguard vs safeguard-noE | unsafe_extra_writes | secondary | 75 | 25 | 0.107 | 0.120 | -0.013 [-0.133, 0.107] | 3/3 | 0.719 | 1.000 | — |
| safeguard vs safeguard-noE | missed_gold_writes | secondary | 75 | 25 | 0.160 | 0.173 | -0.013 [-0.080, 0.053] | 2/2 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noE | executed_writes | secondary | 75 | 25 | 1.147 | 1.147 | 0.000 [-0.133, 0.133] | 4/4 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noE | transferred | secondary | 75 | 25 | 0.427 | 0.400 | 0.027 [-0.040, 0.093] | 2/3 | 0.750 | 1.000 | 5/3, 0.727 |
| safeguard vs safeguard-noE | unconfirmed_writes | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noE | unauthenticated_writes | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noE | blocked_calls | secondary | 75 | 25 | 0.227 | 0.160 | 0.067 [-0.053, 0.240] | 2/2 | 1.000 | 1.000 | — |
