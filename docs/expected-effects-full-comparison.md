# Effect-bound SAFE-Guard: full inspected-set development comparison

## Question

Do the return/color, pre-dispatch consumption, exact prior-effect projection
and payment-provenance repairs recover aggregate task completion without
increasing effective non-gold writes on the entire inspected development set?

The original prospective result and the completed 28/34 versus 23/34 comparison
remain unchanged. Every task below has been inspected or evaluated; none is
independent held-out confirmation.

## Design fixed before execution

- All 34 tasks from `data/heldout2/selected_tasks/retail.jsonl`.
- Two freshly executed arms: baseline and safeguard-transaction.
- Existing gpt-5.4-1 deployment for agent and user, 20-turn budget.
- Seed index 0; two workers; 68 trajectories and 34 complete pairs.
- Same common harness, unchanged baseline prompt, annotations not used as
  runtime treatment specifications.
- No code, prompt, metric or budget changes while the run is active.
- Complete all planned cells regardless of outcomes. Infrastructure-error
  retries retain original execution evidence; no retries to rescue valid failures.
- Freeze source commit and hashes before launching.

## Analysis

Use unchanged full success, effective non-gold-write and commission-error
definitions, task-paired statistics and Holm correction. Report denominators,
missing gold writes, descriptive overhead and all failed/discordant cases.
Preserve zero rewards even when refusal or simulator ambiguity seems responsible.
Lexical attribution remains exploratory. Nonsignificance is not non-inferiority;
no outcome-dependent margin or selective-success headline is permitted.

The intervention includes multiple coupled repairs. This comparison cannot
attribute effects separately to each component or establish universal safety.
Positive development results would justify further independent validation,
not immediate submission with a general effectiveness claim.

## Artifacts

Run: `outputs/runs/transaction-effects-full-development/`.
Analysis: `outputs/runs/transaction-effects-full-development-analysis/`.
Integrity must be checked against frozen source before interpreting outcomes.
