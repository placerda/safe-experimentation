# V6 statistics — SAFE-Guard outcome metrics

Runs: `20261008_123045__v6-pilot`, `20261008_125423__v6-full`, `20261008_141519__v6-ext`

Unit of inference is the task: (task, seed) pairs are averaged per task before the Wilcoxon signed-rank test. Δ = treatment − control (pair mean) with a 95% task-clustered bootstrap CI. Holm correction within each (family, tier). McNemar on pairs is a sensitivity check that ignores clustering. `unconfirmed_writes` and `unauthenticated_writes` reuse SAFE-Guard heuristics and measure rule adherence, not independent safety.

## Per-variant summary (all domains)

| variant | n | excl. | no reward | success | any_unsafe_write | commission_error | unsafe_extra_writes | missed_gold_writes | transferred | blocked_calls |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 325 | 0 | 0 | 0.729 | 0.169 | 0.055 | 0.222 | 0.255 | 0.283 | 0.000 |
| safe-prompt | 300 | 0 | 0 | 0.690 | 0.177 | 0.033 | 0.213 | 0.303 | 0.283 | 0.000 |
| safeguard | 325 | 0 | 0 | 0.766 | 0.095 | 0.022 | 0.108 | 0.215 | 0.326 | 0.194 |
| safeguard-noS | 75 | 0 | 0 | 0.667 | 0.187 | 0.107 | 0.240 | 0.200 | 0.387 | 0.053 |
| safeguard-noA | 75 | 0 | 0 | 0.813 | 0.080 | 0.027 | 0.133 | 0.227 | 0.427 | 0.147 |
| safeguard-noF | 75 | 0 | 0 | 0.760 | 0.107 | 0.053 | 0.173 | 0.400 | 0.453 | 0.147 |
| safeguard-noE | 75 | 0 | 0 | 0.800 | 0.093 | 0.053 | 0.120 | 0.173 | 0.400 | 0.160 |

## Per-variant summary — airline

| variant | n | excl. | no reward | success | any_unsafe_write | commission_error | unsafe_extra_writes | missed_gold_writes | transferred | blocked_calls |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 163 | 0 | 0 | 0.644 | 0.264 | 0.092 | 0.350 | 0.423 | 0.393 | 0.000 |
| safe-prompt | 150 | 0 | 0 | 0.673 | 0.207 | 0.047 | 0.273 | 0.413 | 0.453 | 0.000 |
| safeguard | 163 | 0 | 0 | 0.779 | 0.067 | 0.000 | 0.086 | 0.331 | 0.491 | 0.227 |
| safeguard-noS | 39 | 0 | 0 | 0.667 | 0.179 | 0.103 | 0.205 | 0.333 | 0.410 | 0.000 |
| safeguard-noA | 39 | 0 | 0 | 0.769 | 0.077 | 0.000 | 0.179 | 0.410 | 0.513 | 0.179 |
| safeguard-noF | 39 | 0 | 0 | 0.744 | 0.026 | 0.000 | 0.077 | 0.641 | 0.590 | 0.179 |
| safeguard-noE | 39 | 0 | 0 | 0.821 | 0.026 | 0.000 | 0.051 | 0.308 | 0.513 | 0.179 |

## Per-variant summary — retail

| variant | n | excl. | no reward | success | any_unsafe_write | commission_error | unsafe_extra_writes | missed_gold_writes | transferred | blocked_calls |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 162 | 0 | 0 | 0.815 | 0.074 | 0.019 | 0.093 | 0.086 | 0.173 | 0.000 |
| safe-prompt | 150 | 0 | 0 | 0.707 | 0.147 | 0.020 | 0.153 | 0.193 | 0.113 | 0.000 |
| safeguard | 162 | 0 | 0 | 0.753 | 0.123 | 0.043 | 0.130 | 0.099 | 0.160 | 0.160 |
| safeguard-noS | 36 | 0 | 0 | 0.667 | 0.194 | 0.111 | 0.278 | 0.056 | 0.361 | 0.111 |
| safeguard-noA | 36 | 0 | 0 | 0.861 | 0.083 | 0.056 | 0.083 | 0.028 | 0.333 | 0.111 |
| safeguard-noF | 36 | 0 | 0 | 0.778 | 0.194 | 0.111 | 0.278 | 0.139 | 0.306 | 0.111 |
| safeguard-noE | 36 | 0 | 0 | 0.778 | 0.167 | 0.111 | 0.194 | 0.028 | 0.278 | 0.139 |

## Blocks by rule

- **safeguard**: E:mandated_transfer: 1, F:confirm: 7, F:confirm_unbound: 14, S:basic_economy_locked: 1, S:cancel_flown: 1, S:cancel_ineligible: 19, S:certificate_not_allowed: 2, S:compensation_amount: 1, S:no_seats: 1, S:order_status: 3, S:payment_mix: 4, S:payment_total: 3, S:refund_method: 4, S:route_changed: 4, S:same_item: 2
- **safeguard-noS**: F:confirm_unbound: 4
- **safeguard-noA**: F:confirm_unbound: 5, S:cancel_ineligible: 3, S:compensation_amount: 1, S:payment_mix: 2
- **safeguard-noF**: S:basic_economy_locked: 1, S:cancel_ineligible: 3, S:compensation_amount: 2, S:payment_mix: 1, S:refund_method: 4
- **safeguard-noE**: F:confirm: 1, F:confirm_unbound: 5, S:cancel_ineligible: 3, S:compensation_amount: 1, S:payment_mix: 2

## Primary comparisons

| comparison | metric | tier | pairs | tasks | treat | ctrl | Δ [95% CI] | better/worse tasks | p (task Wilcoxon) | p Holm | McNemar b/c, p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| safeguard vs baseline | any_unsafe_write | primary | 300 | 100 | 0.093 | 0.173 | -0.080 [-0.140, -0.023] | 24/11 | 0.010 | 0.092 | 14/38, 0.001 |
| safeguard vs baseline | commission_error | primary | 300 | 100 | 0.013 | 0.057 | -0.043 [-0.083, -0.007] | 11/2 | 0.037 | 0.223 | 3/16, 0.004 |
| safeguard vs baseline | success | primary | 300 | 100 | 0.763 | 0.720 | 0.043 [-0.020, 0.107] | 24/14 | 0.163 | 0.650 | 38/25, 0.130 |
| safeguard vs baseline | unsafe_extra_writes | secondary | 300 | 100 | 0.103 | 0.223 | -0.120 [-0.207, -0.040] | 24/11 | 0.008 | 0.148 | — |
| safeguard vs baseline | missed_gold_writes | secondary | 300 | 100 | 0.213 | 0.253 | -0.040 [-0.123, 0.033] | 12/14 | 0.500 | 1.000 | — |
| safeguard vs baseline | executed_writes | secondary | 300 | 100 | 1.090 | 1.170 | -0.080 [-0.190, 0.023] | 20/13 | 0.195 | 1.000 | — |
| safeguard vs baseline | transferred | secondary | 300 | 100 | 0.323 | 0.273 | 0.050 [0.003, 0.103] | 8/14 | 0.071 | 0.992 | 28/13, 0.028 |
| safeguard vs baseline | unconfirmed_writes | secondary | 300 | 100 | 0.000 | 0.023 | -0.023 [-0.043, -0.007] | 6/0 | 0.031 | 0.531 | — |
| safeguard vs baseline | unauthenticated_writes | secondary | 300 | 100 | 0.027 | 0.020 | 0.007 [-0.010, 0.030] | 1/1 | 1.000 | 1.000 | — |
| safeguard vs baseline | blocked_calls | secondary | 300 | 100 | 0.193 | 0.000 | 0.193 [0.120, 0.280] | 0/26 | <0.001 | <0.001 | — |
| safe-prompt vs baseline | any_unsafe_write | primary | 300 | 100 | 0.177 | 0.173 | 0.003 [-0.047, 0.053] | 16/15 | 0.942 | 0.942 | 26/25, 1.000 |
| safe-prompt vs baseline | commission_error | primary | 300 | 100 | 0.033 | 0.057 | -0.023 [-0.047, 0.000] | 8/2 | 0.092 | 0.459 | 4/11, 0.118 |
| safe-prompt vs baseline | success | primary | 300 | 100 | 0.690 | 0.720 | -0.030 [-0.087, 0.027] | 21/23 | 0.409 | 0.818 | 31/40, 0.342 |
| safe-prompt vs baseline | unsafe_extra_writes | secondary | 300 | 100 | 0.213 | 0.223 | -0.010 [-0.077, 0.057] | 17/15 | 0.838 | 1.000 | — |
| safe-prompt vs baseline | missed_gold_writes | secondary | 300 | 100 | 0.303 | 0.253 | 0.050 [-0.030, 0.127] | 11/16 | 0.262 | 1.000 | — |
| safe-prompt vs baseline | executed_writes | secondary | 300 | 100 | 1.110 | 1.170 | -0.060 [-0.157, 0.027] | 14/8 | 0.274 | 1.000 | — |
| safe-prompt vs baseline | transferred | secondary | 300 | 100 | 0.283 | 0.273 | 0.010 [-0.037, 0.060] | 13/12 | 0.655 | 1.000 | 23/20, 0.761 |
| safe-prompt vs baseline | unconfirmed_writes | secondary | 300 | 100 | 0.020 | 0.023 | -0.003 [-0.030, 0.020] | 5/4 | 0.973 | 1.000 | — |
| safe-prompt vs baseline | unauthenticated_writes | secondary | 300 | 100 | 0.000 | 0.020 | -0.020 [-0.047, 0.000] | 3/0 | 0.250 | 1.000 | — |
| safe-prompt vs baseline | blocked_calls | secondary | 300 | 100 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safe-prompt | any_unsafe_write | primary | 300 | 100 | 0.093 | 0.177 | -0.083 [-0.143, -0.023] | 22/8 | 0.012 | 0.094 | 14/39, <0.001 |
| safeguard vs safe-prompt | commission_error | primary | 300 | 100 | 0.013 | 0.033 | -0.020 [-0.050, 0.007] | 6/1 | 0.266 | 0.797 | 3/9, 0.146 |
| safeguard vs safe-prompt | success | primary | 300 | 100 | 0.763 | 0.690 | 0.073 [0.010, 0.137] | 28/13 | 0.022 | 0.154 | 47/25, 0.013 |
| safeguard vs safe-prompt | unsafe_extra_writes | secondary | 300 | 100 | 0.103 | 0.213 | -0.110 [-0.190, -0.037] | 22/8 | 0.007 | 0.142 | — |
| safeguard vs safe-prompt | missed_gold_writes | secondary | 300 | 100 | 0.213 | 0.303 | -0.090 [-0.177, -0.010] | 20/11 | 0.052 | 0.833 | — |
| safeguard vs safe-prompt | executed_writes | secondary | 300 | 100 | 1.090 | 1.110 | -0.020 [-0.107, 0.060] | 12/12 | 0.874 | 1.000 | — |
| safeguard vs safe-prompt | transferred | secondary | 300 | 100 | 0.323 | 0.283 | 0.040 [-0.017, 0.100] | 12/17 | 0.267 | 1.000 | 34/22, 0.141 |
| safeguard vs safe-prompt | unconfirmed_writes | secondary | 300 | 100 | 0.000 | 0.020 | -0.020 [-0.040, -0.003] | 5/0 | 0.062 | 0.938 | — |
| safeguard vs safe-prompt | unauthenticated_writes | secondary | 300 | 100 | 0.027 | 0.000 | 0.027 [0.000, 0.060] | 0/3 | 0.250 | 1.000 | — |
| safeguard vs safe-prompt | blocked_calls | secondary | 300 | 100 | 0.193 | 0.000 | 0.193 [0.120, 0.280] | 0/26 | <0.001 | <0.001 | — |

## Ablation comparisons

| comparison | metric | tier | pairs | tasks | treat | ctrl | Δ [95% CI] | better/worse tasks | p (task Wilcoxon) | p Holm | McNemar b/c, p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| safeguard vs safeguard-noS | any_unsafe_write | primary | 75 | 25 | 0.080 | 0.187 | -0.107 [-0.240, 0.013] | 7/4 | 0.128 | 1.000 | 5/13, 0.096 |
| safeguard vs safeguard-noS | commission_error | primary | 75 | 25 | 0.053 | 0.107 | -0.053 [-0.160, 0.040] | 3/2 | 0.500 | 1.000 | 3/7, 0.344 |
| safeguard vs safeguard-noS | success | primary | 75 | 25 | 0.813 | 0.667 | 0.147 [0.013, 0.293] | 9/4 | 0.051 | 0.609 | 16/5, 0.027 |
| safeguard vs safeguard-noS | unsafe_extra_writes | secondary | 75 | 25 | 0.107 | 0.240 | -0.133 [-0.307, 0.040] | 7/3 | 0.178 | 1.000 | — |
| safeguard vs safeguard-noS | missed_gold_writes | secondary | 75 | 25 | 0.160 | 0.200 | -0.040 [-0.187, 0.080] | 3/3 | 0.812 | 1.000 | — |
| safeguard vs safeguard-noS | executed_writes | secondary | 75 | 25 | 1.147 | 1.240 | -0.093 [-0.293, 0.093] | 6/4 | 0.453 | 1.000 | — |
| safeguard vs safeguard-noS | transferred | secondary | 75 | 25 | 0.427 | 0.387 | 0.040 [-0.067, 0.160] | 5/5 | 0.684 | 1.000 | 9/6, 0.607 |
| safeguard vs safeguard-noS | unconfirmed_writes | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noS | unauthenticated_writes | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noS | blocked_calls | secondary | 75 | 25 | 0.227 | 0.053 | 0.173 [0.013, 0.373] | 0/4 | 0.125 | 1.000 | — |
| safeguard vs safeguard-noA | any_unsafe_write | primary | 75 | 25 | 0.080 | 0.080 | 0.000 [-0.067, 0.080] | 3/2 | 1.000 | 1.000 | 4/4, 1.000 |
| safeguard vs safeguard-noA | commission_error | primary | 75 | 25 | 0.053 | 0.027 | 0.027 [0.000, 0.080] | 0/1 | 1.000 | 1.000 | 2/0, 0.500 |
| safeguard vs safeguard-noA | success | primary | 75 | 25 | 0.813 | 0.813 | 0.000 [-0.080, 0.080] | 4/3 | 1.000 | 1.000 | 6/6, 1.000 |
| safeguard vs safeguard-noA | unsafe_extra_writes | secondary | 75 | 25 | 0.107 | 0.133 | -0.027 [-0.133, 0.067] | 3/2 | 0.812 | 1.000 | — |
| safeguard vs safeguard-noA | missed_gold_writes | secondary | 75 | 25 | 0.160 | 0.227 | -0.067 [-0.173, 0.027] | 5/2 | 0.359 | 1.000 | — |
| safeguard vs safeguard-noA | executed_writes | secondary | 75 | 25 | 1.147 | 1.107 | 0.040 [-0.027, 0.107] | 1/3 | 0.500 | 1.000 | — |
| safeguard vs safeguard-noA | transferred | secondary | 75 | 25 | 0.427 | 0.427 | 0.000 [-0.053, 0.053] | 2/2 | 1.000 | 1.000 | 2/2, 1.000 |
| safeguard vs safeguard-noA | unconfirmed_writes | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noA | unauthenticated_writes | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noA | blocked_calls | secondary | 75 | 25 | 0.227 | 0.147 | 0.080 [-0.040, 0.267] | 2/3 | 0.750 | 1.000 | — |
| safeguard vs safeguard-noF | any_unsafe_write | primary | 75 | 25 | 0.080 | 0.107 | -0.027 [-0.080, 0.027] | 3/1 | 0.625 | 1.000 | 3/5, 0.727 |
| safeguard vs safeguard-noF | commission_error | primary | 75 | 25 | 0.053 | 0.053 | 0.000 [-0.040, 0.040] | 1/1 | 1.000 | 1.000 | 1/1, 1.000 |
| safeguard vs safeguard-noF | success | primary | 75 | 25 | 0.813 | 0.760 | 0.053 [-0.013, 0.133] | 4/1 | 0.312 | 1.000 | 8/4, 0.388 |
| safeguard vs safeguard-noF | unsafe_extra_writes | secondary | 75 | 25 | 0.107 | 0.173 | -0.067 [-0.173, 0.013] | 3/1 | 0.375 | 1.000 | — |
| safeguard vs safeguard-noF | missed_gold_writes | secondary | 75 | 25 | 0.160 | 0.400 | -0.240 [-0.453, -0.067] | 6/0 | 0.031 | 0.875 | — |
| safeguard vs safeguard-noF | executed_writes | secondary | 75 | 25 | 1.147 | 0.973 | 0.173 [0.000, 0.400] | 1/5 | 0.156 | 1.000 | — |
| safeguard vs safeguard-noF | transferred | secondary | 75 | 25 | 0.427 | 0.453 | -0.027 [-0.120, 0.067] | 4/2 | 0.781 | 1.000 | 4/6, 0.754 |
| safeguard vs safeguard-noF | unconfirmed_writes | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noF | unauthenticated_writes | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noF | blocked_calls | secondary | 75 | 25 | 0.227 | 0.147 | 0.080 [-0.027, 0.200] | 2/4 | 0.219 | 1.000 | — |
| safeguard vs safeguard-noE | any_unsafe_write | primary | 75 | 25 | 0.080 | 0.093 | -0.013 [-0.093, 0.053] | 3/3 | 1.000 | 1.000 | 4/5, 1.000 |
| safeguard vs safeguard-noE | commission_error | primary | 75 | 25 | 0.053 | 0.053 | 0.000 [-0.040, 0.040] | 1/1 | 1.000 | 1.000 | 2/2, 1.000 |
| safeguard vs safeguard-noE | success | primary | 75 | 25 | 0.813 | 0.800 | 0.013 [-0.080, 0.107] | 5/5 | 1.000 | 1.000 | 8/7, 1.000 |
| safeguard vs safeguard-noE | unsafe_extra_writes | secondary | 75 | 25 | 0.107 | 0.120 | -0.013 [-0.133, 0.107] | 3/3 | 0.719 | 1.000 | — |
| safeguard vs safeguard-noE | missed_gold_writes | secondary | 75 | 25 | 0.160 | 0.173 | -0.013 [-0.093, 0.053] | 2/2 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noE | executed_writes | secondary | 75 | 25 | 1.147 | 1.147 | 0.000 [-0.133, 0.147] | 4/4 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noE | transferred | secondary | 75 | 25 | 0.427 | 0.400 | 0.027 [-0.040, 0.107] | 2/3 | 0.750 | 1.000 | 5/3, 0.727 |
| safeguard vs safeguard-noE | unconfirmed_writes | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noE | unauthenticated_writes | secondary | 75 | 25 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safeguard-noE | blocked_calls | secondary | 75 | 25 | 0.227 | 0.160 | 0.067 [-0.053, 0.253] | 2/2 | 1.000 | 1.000 | — |

## Primary comparisons — airline only (exploratory)

| comparison | metric | tier | pairs | tasks | treat | ctrl | Δ [95% CI] | better/worse tasks | p (task Wilcoxon) | p Holm | McNemar b/c, p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| safeguard vs baseline | any_unsafe_write | primary | 150 | 50 | 0.073 | 0.267 | -0.193 [-0.287, -0.107] | 19/2 | <0.001 | 0.002 | 2/31, <0.001 |
| safeguard vs baseline | commission_error | primary | 150 | 50 | 0.000 | 0.093 | -0.093 [-0.160, -0.040] | 10/0 | 0.002 | 0.016 | 0/14, <0.001 |
| safeguard vs baseline | success | primary | 150 | 50 | 0.773 | 0.640 | 0.133 [0.040, 0.227] | 17/3 | 0.005 | 0.034 | 25/5, <0.001 |
| safeguard vs baseline | unsafe_extra_writes | secondary | 150 | 50 | 0.093 | 0.347 | -0.253 [-0.393, -0.133] | 19/2 | <0.001 | 0.013 | — |
| safeguard vs baseline | missed_gold_writes | secondary | 150 | 50 | 0.320 | 0.413 | -0.093 [-0.247, 0.040] | 8/7 | 0.276 | 1.000 | — |
| safeguard vs baseline | executed_writes | secondary | 150 | 50 | 0.753 | 0.913 | -0.160 [-0.360, 0.040] | 17/8 | 0.130 | 1.000 | — |
| safeguard vs baseline | transferred | secondary | 150 | 50 | 0.487 | 0.387 | 0.100 [0.007, 0.200] | 6/12 | 0.057 | 0.966 | 24/9, 0.014 |
| safeguard vs baseline | unconfirmed_writes | secondary | 150 | 50 | 0.000 | 0.027 | -0.027 [-0.053, -0.007] | 4/0 | 0.125 | 1.000 | — |
| safeguard vs baseline | unauthenticated_writes | secondary | 150 | 50 | 0.053 | 0.040 | 0.013 [-0.020, 0.060] | 1/1 | 1.000 | 1.000 | — |
| safeguard vs baseline | blocked_calls | secondary | 150 | 50 | 0.220 | 0.000 | 0.220 [0.107, 0.347] | 0/14 | <0.001 | 0.017 | — |
| safe-prompt vs baseline | any_unsafe_write | primary | 150 | 50 | 0.207 | 0.267 | -0.060 [-0.127, 0.000] | 11/5 | 0.068 | 0.250 | 9/18, 0.122 |
| safe-prompt vs baseline | commission_error | primary | 150 | 50 | 0.047 | 0.093 | -0.047 [-0.087, -0.007] | 7/1 | 0.062 | 0.250 | 2/9, 0.065 |
| safe-prompt vs baseline | success | primary | 150 | 50 | 0.673 | 0.640 | 0.033 [-0.027, 0.093] | 11/6 | 0.302 | 0.302 | 17/12, 0.458 |
| safe-prompt vs baseline | unsafe_extra_writes | secondary | 150 | 50 | 0.273 | 0.347 | -0.073 [-0.180, 0.027] | 12/5 | 0.167 | 1.000 | — |
| safe-prompt vs baseline | missed_gold_writes | secondary | 150 | 50 | 0.413 | 0.413 | 0.000 [-0.113, 0.113] | 5/5 | 1.000 | 1.000 | — |
| safe-prompt vs baseline | executed_writes | secondary | 150 | 50 | 0.840 | 0.913 | -0.073 [-0.247, 0.080] | 10/5 | 0.563 | 1.000 | — |
| safe-prompt vs baseline | transferred | secondary | 150 | 50 | 0.453 | 0.387 | 0.067 [-0.020, 0.153] | 7/12 | 0.147 | 1.000 | 22/12, 0.121 |
| safe-prompt vs baseline | unconfirmed_writes | secondary | 150 | 50 | 0.007 | 0.027 | -0.020 [-0.047, 0.007] | 4/1 | 0.375 | 1.000 | — |
| safe-prompt vs baseline | unauthenticated_writes | secondary | 150 | 50 | 0.000 | 0.040 | -0.040 [-0.093, 0.000] | 3/0 | 0.250 | 1.000 | — |
| safe-prompt vs baseline | blocked_calls | secondary | 150 | 50 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safe-prompt | any_unsafe_write | primary | 150 | 50 | 0.073 | 0.207 | -0.133 [-0.220, -0.053] | 15/2 | 0.005 | 0.034 | 3/23, <0.001 |
| safeguard vs safe-prompt | commission_error | primary | 150 | 50 | 0.000 | 0.047 | -0.047 [-0.100, -0.007] | 5/0 | 0.062 | 0.250 | 0/7, 0.016 |
| safeguard vs safe-prompt | success | primary | 150 | 50 | 0.773 | 0.673 | 0.100 [0.013, 0.187] | 15/4 | 0.021 | 0.106 | 22/7, 0.008 |
| safeguard vs safe-prompt | unsafe_extra_writes | secondary | 150 | 50 | 0.093 | 0.273 | -0.180 [-0.307, -0.067] | 15/2 | 0.005 | 0.087 | — |
| safeguard vs safe-prompt | missed_gold_writes | secondary | 150 | 50 | 0.320 | 0.413 | -0.093 [-0.213, 0.020] | 12/5 | 0.143 | 1.000 | — |
| safeguard vs safe-prompt | executed_writes | secondary | 150 | 50 | 0.753 | 0.840 | -0.087 [-0.240, 0.047] | 10/8 | 0.413 | 1.000 | — |
| safeguard vs safe-prompt | transferred | secondary | 150 | 50 | 0.487 | 0.453 | 0.033 [-0.073, 0.153] | 12/11 | 0.707 | 1.000 | 24/19, 0.542 |
| safeguard vs safe-prompt | unconfirmed_writes | secondary | 150 | 50 | 0.000 | 0.007 | -0.007 [-0.020, 0.000] | 1/0 | 1.000 | 1.000 | — |
| safeguard vs safe-prompt | unauthenticated_writes | secondary | 150 | 50 | 0.053 | 0.000 | 0.053 [0.000, 0.120] | 0/3 | 0.250 | 1.000 | — |
| safeguard vs safe-prompt | blocked_calls | secondary | 150 | 50 | 0.220 | 0.000 | 0.220 [0.107, 0.347] | 0/14 | <0.001 | 0.017 | — |

## Primary comparisons — retail only (exploratory)

| comparison | metric | tier | pairs | tasks | treat | ctrl | Δ [95% CI] | better/worse tasks | p (task Wilcoxon) | p Holm | McNemar b/c, p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| safeguard vs baseline | any_unsafe_write | primary | 150 | 50 | 0.113 | 0.080 | 0.033 [-0.027, 0.093] | 5/9 | 0.302 | 1.000 | 12/7, 0.359 |
| safeguard vs baseline | commission_error | primary | 150 | 50 | 0.027 | 0.020 | 0.007 [-0.033, 0.047] | 1/2 | 1.000 | 1.000 | 3/2, 1.000 |
| safeguard vs baseline | success | primary | 150 | 50 | 0.753 | 0.800 | -0.047 [-0.127, 0.027] | 7/11 | 0.258 | 1.000 | 13/20, 0.296 |
| safeguard vs baseline | unsafe_extra_writes | secondary | 150 | 50 | 0.113 | 0.100 | 0.013 [-0.073, 0.087] | 5/9 | 0.512 | 1.000 | — |
| safeguard vs baseline | missed_gold_writes | secondary | 150 | 50 | 0.107 | 0.093 | 0.013 [-0.047, 0.067] | 4/7 | 0.827 | 1.000 | — |
| safeguard vs baseline | executed_writes | secondary | 150 | 50 | 1.427 | 1.427 | 0.000 [-0.073, 0.060] | 3/5 | 0.797 | 1.000 | — |
| safeguard vs baseline | transferred | secondary | 150 | 50 | 0.160 | 0.160 | 0.000 [-0.027, 0.027] | 2/2 | 1.000 | 1.000 | 4/4, 1.000 |
| safeguard vs baseline | unconfirmed_writes | secondary | 150 | 50 | 0.000 | 0.020 | -0.020 [-0.053, 0.000] | 2/0 | 0.500 | 1.000 | — |
| safeguard vs baseline | unauthenticated_writes | secondary | 150 | 50 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs baseline | blocked_calls | secondary | 150 | 50 | 0.167 | 0.000 | 0.167 [0.073, 0.280] | 0/12 | <0.001 | 0.010 | — |
| safe-prompt vs baseline | any_unsafe_write | primary | 150 | 50 | 0.147 | 0.080 | 0.067 [0.000, 0.147] | 5/10 | 0.097 | 0.774 | 17/7, 0.064 |
| safe-prompt vs baseline | commission_error | primary | 150 | 50 | 0.020 | 0.020 | 0.000 [-0.020, 0.020] | 1/1 | 1.000 | 1.000 | 2/2, 1.000 |
| safe-prompt vs baseline | success | primary | 150 | 50 | 0.707 | 0.800 | -0.093 [-0.187, -0.007] | 10/17 | 0.073 | 0.655 | 14/28, 0.044 |
| safe-prompt vs baseline | unsafe_extra_writes | secondary | 150 | 50 | 0.153 | 0.100 | 0.053 [-0.027, 0.133] | 5/10 | 0.251 | 1.000 | — |
| safe-prompt vs baseline | missed_gold_writes | secondary | 150 | 50 | 0.193 | 0.093 | 0.100 [0.000, 0.220] | 6/11 | 0.126 | 1.000 | — |
| safe-prompt vs baseline | executed_writes | secondary | 150 | 50 | 1.380 | 1.427 | -0.047 [-0.127, 0.020] | 4/3 | 0.344 | 1.000 | — |
| safe-prompt vs baseline | transferred | secondary | 150 | 50 | 0.113 | 0.160 | -0.047 [-0.087, -0.013] | 6/0 | 0.031 | 0.594 | 1/8, 0.039 |
| safe-prompt vs baseline | unconfirmed_writes | secondary | 150 | 50 | 0.033 | 0.020 | 0.013 [-0.027, 0.053] | 1/3 | 0.750 | 1.000 | — |
| safe-prompt vs baseline | unauthenticated_writes | secondary | 150 | 50 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safe-prompt vs baseline | blocked_calls | secondary | 150 | 50 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safe-prompt | any_unsafe_write | primary | 150 | 50 | 0.113 | 0.147 | -0.033 [-0.120, 0.047] | 7/6 | 0.555 | 1.000 | 11/16, 0.442 |
| safeguard vs safe-prompt | commission_error | primary | 150 | 50 | 0.027 | 0.020 | 0.007 [-0.020, 0.040] | 1/1 | 1.000 | 1.000 | 3/2, 1.000 |
| safeguard vs safe-prompt | success | primary | 150 | 50 | 0.753 | 0.707 | 0.047 [-0.040, 0.133] | 13/9 | 0.323 | 1.000 | 25/18, 0.360 |
| safeguard vs safe-prompt | unsafe_extra_writes | secondary | 150 | 50 | 0.113 | 0.153 | -0.040 [-0.133, 0.047] | 7/6 | 0.468 | 1.000 | — |
| safeguard vs safe-prompt | missed_gold_writes | secondary | 150 | 50 | 0.107 | 0.193 | -0.087 [-0.220, 0.020] | 8/6 | 0.257 | 1.000 | — |
| safeguard vs safe-prompt | executed_writes | secondary | 150 | 50 | 1.427 | 1.380 | 0.047 [-0.020, 0.127] | 2/4 | 0.344 | 1.000 | — |
| safeguard vs safe-prompt | transferred | secondary | 150 | 50 | 0.160 | 0.113 | 0.047 [0.013, 0.087] | 0/6 | 0.031 | 0.594 | 10/3, 0.092 |
| safeguard vs safe-prompt | unconfirmed_writes | secondary | 150 | 50 | 0.000 | 0.033 | -0.033 [-0.067, -0.007] | 4/0 | 0.125 | 1.000 | — |
| safeguard vs safe-prompt | unauthenticated_writes | secondary | 150 | 50 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0/0 | 1.000 | 1.000 | — |
| safeguard vs safe-prompt | blocked_calls | secondary | 150 | 50 | 0.167 | 0.000 | 0.167 [0.073, 0.280] | 0/12 | <0.001 | 0.010 | — |
