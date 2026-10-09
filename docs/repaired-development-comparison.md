# Repaired SAFE-Guard: full-set development comparison

## Question and status

Does the repaired direct-presentation implementation retain task completion
and avoid effective non-gold writes across the entire inspected 34-task retail
set, rather than only four selected failures?

This is a **development comparison**, not independent confirmation. Every
task was previously evaluated and some were inspected to repair the method.
The earlier frozen negative result remains unchanged. The four selected
successes are not included as additional observations in this comparison.

## Frozen design

- Source: freeze the current commit and file hashes before execution.
- Tasks: all 34 tasks in `data/heldout2/selected_tasks/retail.jsonl`.
- Arms: newly executed baseline and `safeguard-transaction`, with the same
  baseline system prompt and no annotation-derived prompt binding.
- Model: existing `gpt-5.4-1` deployment for agents and user simulation.
- Budget: 20 agent turns per trajectory; seed index 0; two workers.
- Size: 68 trajectories, 34 paired tasks. Seed indices are not deterministic
  backend sampling seeds.
- Common harness: both arms use apostrophe-normalized existing user closure
  detection. Only treatment uses direct trusted presentation and guard rules.
- No treatment, prompt, metric or budget changes during this run.
- Finish all planned trajectories regardless of interim outcomes.
- Resume only missing or infrastructure-errored trajectories; preserve their
  original traces/logs. Missing evaluator rewards may be recovered from the
  original executions, without rerunning successful agent trajectories.

## Outcomes and interpretation

Report full task success, any effective non-gold write and commission error
using the existing definitions and task-paired statistics. Report confidence
intervals and Holm-adjusted primary tests; do not invent an outcome-dependent
non-inferiority margin. Include the applicable zero-gold-write denominator.
Attribution is exploratory lexical classification, not human adjudication.
Protocol overhead, missing gold writes and failure inspection are descriptive.

A positive result on this reused set is regression evidence, not a general
safety claim. A nonsignificant utility difference does not establish preserved
utility. Any adverse result must remain visible and must inform the method's
limitations. If code is changed after seeing results, label the new version
and do not overwrite this run or combine versions as one treatment.

## Evidence

Run directory: `outputs/runs/transaction-repaired-development`.
Separate analysis directory: `outputs/runs/transaction-repaired-development-analysis`.
Preserve freeze, execution log, results and every raw trace. Verify pair
coverage and frozen hashes before interpreting the result.
