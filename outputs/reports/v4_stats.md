# v4 statistical analysis

- Source runs: ['20261005_151758__full-gpt-5.4']
- Total rows: 720, unique cells: 720
- Variants: ['all-guardrails', 'baseline', 'binding', 'escalation', 'evidence', 'flow']
- Domains: ['airline', 'retail', 'telecom']

## Per-(variant, domain) means

| variant | domain | n | S | A | F | E | CVFR | reward |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| all-guardrails | airline | 50 | 1.000 | 0.821 | 0.289 | 0.960 | 1.000 | 0.440 |
| all-guardrails | retail | 50 | 1.000 | 0.827 | 0.158 | 0.940 | 1.000 | 0.091 |
| all-guardrails | telecom | 20 | 1.000 | 0.772 | 0.013 | 1.000 | 1.000 | 0.100 |
| baseline | airline | 50 | 0.940 | 0.826 | 0.257 | 0.980 | 1.000 | 0.460 |
| baseline | retail | 50 | 0.640 | 0.830 | 0.162 | 0.960 | 1.000 | 0.121 |
| baseline | telecom | 20 | 1.000 | 0.686 | 0.013 | 1.000 | 1.000 | 0.050 |
| binding | airline | 50 | 1.000 | 0.819 | 0.271 | 0.960 | 1.000 | 0.460 |
| binding | retail | 50 | 1.000 | 0.833 | 0.145 | 0.960 | 1.000 | 0.129 |
| binding | telecom | 20 | 1.000 | 0.659 | 0.013 | 1.000 | 1.000 | 0.000 |
| escalation | airline | 50 | 0.980 | 0.837 | 0.262 | 0.940 | 1.000 | 0.480 |
| escalation | retail | 50 | 0.640 | 0.830 | 0.159 | 0.980 | 1.000 | 0.125 |
| escalation | telecom | 20 | 1.000 | 0.721 | 0.013 | 1.000 | 1.000 | 0.100 |
| evidence | airline | 50 | 0.960 | 0.825 | 0.255 | 1.000 | 1.000 | 0.480 |
| evidence | retail | 50 | 0.580 | 0.823 | 0.156 | 0.980 | 1.000 | 0.088 |
| evidence | telecom | 20 | 0.800 | 0.768 | 0.013 | 1.000 | 1.000 | 0.100 |
| flow | airline | 50 | 0.960 | 0.834 | 0.241 | 0.980 | 1.000 | 0.480 |
| flow | retail | 50 | 0.640 | 0.826 | 0.145 | 0.940 | 1.000 | 0.125 |
| flow | telecom | 20 | 1.000 | 0.678 | 0.013 | 1.000 | 1.000 | 0.050 |

## H1' — per-dimension lift (paired bootstrap, Holm within 4)

| dimension | domain | target | n | Δ mean | 95% CI | p | p_holm | reject H0 |
|---|---|---|---:|---:|---|---:|---:|---|
| S | airline | binding | 50 | +0.060 | [+0.000, +0.140] | 0.082 | 0.738 | no |
| S | retail | binding | 50 | +0.360 | [+0.220, +0.500] | 0.000 | 0.000 | **yes** |
| S | telecom | binding | 20 | +0.000 | [+0.000, +0.000] | 1.000 | 1.000 | no |
| A | airline | evidence | 50 | -0.001 | [-0.023, +0.019] | 0.899 | 1.000 | no |
| A | retail | evidence | 50 | -0.007 | [-0.018, +0.000] | 0.217 | 1.000 | no |
| A | telecom | evidence | 20 | +0.082 | [+0.005, +0.147] | 0.011 | 0.125 | no |
| F | airline | flow | 50 | -0.017 | [-0.042, +0.009] | 0.205 | 1.000 | no |
| F | retail | flow | 50 | -0.017 | [-0.037, -0.003] | 0.028 | 0.284 | no |
| F | telecom | flow | 20 | +0.000 | [+0.000, +0.000] | 1.000 | 1.000 | no |
| E | airline | escalation | 50 | -0.040 | [-0.100, +0.000] | 0.248 | 1.000 | no |
| E | retail | escalation | 50 | +0.020 | [+0.000, +0.060] | 0.533 | 1.000 | no |
| E | telecom | escalation | 20 | +0.000 | [+0.000, +0.000] | 1.000 | 1.000 | no |

## SAFE-aware vs baseline (task-clustered bootstrap, Holm across metrics)

| metric | domain | pairs | tasks | Δ mean | 95% CI | p | p_holm | reject H0 |
|---|---|---:|---:|---:|---|---:|---:|---|

## H3' — composability (all-guardrails vs single-enforcer target)

| dimension | domain | n | Δ vs target | 95% CI | interpretation |
|---|---|---:|---:|---|---|
| S | airline | 50 | +0.000 | [+0.000, +0.000] | all-guardrails matches or beats target |
| S | retail | 50 | +0.000 | [+0.000, +0.000] | all-guardrails matches or beats target |
| S | telecom | 20 | +0.000 | [+0.000, +0.000] | all-guardrails matches or beats target |
| A | airline | 50 | -0.004 | [-0.020, +0.009] | all-guardrails matches or beats target |
| A | retail | 50 | +0.004 | [-0.008, +0.018] | all-guardrails matches or beats target |
| A | telecom | 20 | +0.005 | [-0.056, +0.064] | all-guardrails worse than target |
| F | airline | 50 | +0.048 | [+0.014, +0.087] | all-guardrails matches or beats target |
| F | retail | 50 | +0.013 | [+0.000, +0.033] | all-guardrails matches or beats target |
| F | telecom | 20 | +0.000 | [+0.000, +0.000] | all-guardrails matches or beats target |
| E | airline | 50 | +0.020 | [+0.000, +0.060] | all-guardrails matches or beats target |
| E | retail | 50 | -0.040 | [-0.100, +0.000] | all-guardrails worse than target |
| E | telecom | 20 | +0.000 | [+0.000, +0.000] | all-guardrails matches or beats target |

## Guardrail event firing summary

- **all-guardrails**: {'binding/filter': 120, 'evidence/block': 31, 'flow/remind': 4, 'escalation/remind': 6}
- **binding**: {'binding/filter': 120}
- **escalation**: {'escalation/remind': 5}
- **evidence**: {'evidence/block': 50}
- **flow**: {'flow/remind': 5}
