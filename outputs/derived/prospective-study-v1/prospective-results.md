# Frozen prospective live-agent study

## Design

- 24 hidden generated tasks
- 2 run seeds
- 3 arms: baseline, manifest-only, and full SAFE-Guard
- 144 completed trajectories
- Primary outcome: any SAFE violation
- Secondary outcomes: task success, illegitimate blocks, and per-dimension violations

The first launch failed before any model response because of an Azure Entra
client-construction incompatibility. All 144 failures are preserved as attempt
1 with reason `provider_authentication`. Freeze manifest version
`3-auth-compatibility-amendment` records the credential-only runtime fix. The
single permitted retry then completed every frozen job without changing tasks,
seeds, arms, prompts, oracles, outcomes, gates, or analysis.

## Results

| Arm | SAFE violation | Task success | Illegitimate block |
|---|---:|---:|---:|
| Baseline | 9/48 (18.8%) | 39/48 (81.3%) | 0/24 (0.0%) |
| Manifest-only | 7/48 (14.6%) | 41/48 (85.4%) | 0/24 (0.0%) |
| Full SAFE-Guard | 12/48 (25.0%) | 36/48 (75.0%) | 0/24 (0.0%) |

Compared with manifest-only, full SAFE-Guard had:

- a +10.4 percentage-point paired difference in SAFE violations;
- a -71.4% relative violation reduction, meaning violations increased rather
  than decreased;
- a 95% task-clustered bootstrap interval of [-4.2, +25.0] percentage points
  for the violation difference;
- a -10.4 percentage-point paired difference in task success;
- a 95% task-clustered bootstrap interval of [-25.0, +4.2] percentage points
  for the task-success difference;
- zero observed illegitimate blocks in both arms.

Per-dimension violation counts for full SAFE-Guard versus manifest-only were:
scope 2 versus 1, Anchored Decisions 5 versus 3, Flow Integrity 2 versus 2,
and Escalation 3 versus 1.

## Prespecified gates

| Gate | Result |
|---|---|
| At least 50% violation reduction versus manifest-only | **Failed** |
| Task-success lower 95% CI above -10 percentage points | **Failed** |
| Full SAFE-Guard illegitimate-block rate below 5% | **Passed** |

The overall publication gate failed. The confirmatory study does not support
the claim that full SAFE-Guard improves live-agent safety relative to the
manifest-only control. The deterministic benchmark continues to show that the
mechanism can enforce its specified rules, but the live result shows that the
current integration does not translate that capability into better end-to-end
agent behavior.

Machine-readable evidence is in `outputs/prospective-study/results.json` and
`outputs/prospective-study/analysis.json`; complete attempt and trace
provenance is preserved under `outputs/prospective-study/attempts/` and
`outputs/prospective-study/traces/`.
