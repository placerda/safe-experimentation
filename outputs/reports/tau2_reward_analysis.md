# τ³-bench Official Reward Analysis

Run: `outputs\runs\20260426_140931`

τ³-bench reward = action-matching × DB-state-match × communicate-info × NL-assertions
(only the components in each task's `reward_basis` are multiplied; final reward in [0,1])

## Per-variant reward (subset where evaluator succeeded)

| variant | domain | n | mean | 95% bootstrap CI |
|---|---|---:|---:|---|
| baseline | all | 22 | 0.409 | [0.227, 0.636] |
| baseline | airline | 13 | 0.538 | [0.231, 0.769] |
| baseline | retail | 9 | 0.222 | [0.000, 0.556] |
| safe-aware | all | 25 | 0.440 | [0.240, 0.640] |
| safe-aware | airline | 15 | 0.600 | [0.333, 0.867] |
| safe-aware | retail | 10 | 0.200 | [0.000, 0.500] |

## Paired comparison (both variants successfully evaluated)

Paired tasks: **22**

- Mean Δ (safe-aware − baseline): **+0.045**
- safe-aware better on 2 tasks; baseline better on 1; tie on 19
- Sign test (excluding ties): p = 1.0000
- Wilcoxon signed-rank: p = 0.5637

## Evaluator coverage

- baseline: 22/30 traces had a valid τ³-bench reward
- safe-aware: 25/30 traces had a valid τ³-bench reward

Notes on missing rewards (`t3:n/a`):
- Tasks whose `reward_basis` includes `NL_ASSERTION` require an LLM judge call;
  this run did not configure that judge so those evaluations fail safely.
- Some retail traces with rejected actions raise replay errors when tau2 re-executes
  mutating tools — these are flagged in the `tau2_note` field of `results.json`.
