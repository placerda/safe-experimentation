# τ³-bench Official Reward Analysis

Run: `outputs\runs\20260426_172556__gpt-4.1`

τ³-bench reward = action-matching × DB-state-match × communicate-info × NL-assertions
(only the components in each task's `reward_basis` are multiplied; final reward in [0,1])

## Per-variant reward (subset where evaluator succeeded)

| variant | domain | n | mean | 95% bootstrap CI |
|---|---|---:|---:|---|
| baseline | all | 89 | 0.247 | [0.157, 0.337] |
| baseline | airline | 47 | 0.383 | [0.255, 0.532] |
| baseline | retail | 42 | 0.095 | [0.024, 0.190] |
| safe-aware | all | 90 | 0.244 | [0.156, 0.333] |
| safe-aware | airline | 50 | 0.380 | [0.240, 0.520] |
| safe-aware | retail | 40 | 0.075 | [0.000, 0.175] |

## Paired comparison (both variants successfully evaluated)

Paired tasks: **83**

- Mean Δ (safe-aware − baseline): **-0.024**
- safe-aware better on 2 tasks; baseline better on 4; tie on 77
- Sign test (excluding ties): p = 0.6875
- Wilcoxon signed-rank: p = 0.4142

## Evaluator coverage

- baseline: 89/100 traces had a valid τ³-bench reward
- safe-aware: 90/100 traces had a valid τ³-bench reward

Notes on missing rewards (`t3:n/a`):
- Tasks whose `reward_basis` includes `NL_ASSERTION` require an LLM judge call;
  this run did not configure that judge so those evaluations fail safely.
- Some retail traces with rejected actions raise replay errors when tau2 re-executes
  mutating tools — these are flagged in the `tau2_note` field of `results.json`.
