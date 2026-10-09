# Transactional SAFE-Guard: exact authorization at the execution boundary

## Motivation and retained negative result

The original v6 retail held-out experiment had five agent-attributable unsafe
trajectories versus zero for baseline (90 paired trajectories; pair-level exact
McNemar p = 0.0625). That is an observed regression, not evidence of equivalence.
Task success was also lower, 0.678 versus 0.722. These results must remain in
any paper describing the method's development.

The old confirmation check accepted overlap with any mentioned identifier.
This does not bind an action to its target and values. An agent-generated
summary can swap addresses or items before the user says yes. Seeing both
addresses in the history does not establish which address belongs to which order.

An attempted rule rejecting use of the original profile address was discarded:
changing a profile address does not prohibit intentionally shipping another
order to the old address. Likewise an idempotent address write is not
inherently unsafe. The transactional variant allows explicitly approved
idempotent address writes.

## Algorithm

1. **Propose and validate.** A proposed write is checked against the encoded
   domain policy, authentication, ownership, retrieval and prefix evidence.
   Policy failures and rule crashes block execution.
2. **Bind recognized intent relations.** Independent user requests, not
   affirmations of agent proposals, supply a separate constraint ledger.
   Supported relations include a new address sourced from a named product's
   retrieved order, named products belonging to the same order, collective
   item exchange coverage, cheapest variants,
   resolution/waterproof/budget constraints and explicit preservation or
   numeric changes to selected options. Contradictions block preparation,
   even if a simulated user previously said yes to the wrong summary.
   Explicit address corrections replace address relations without discarding
   unrelated request clauses.
3. **Prepare.** If these checks pass but no exact authorization exists, the
   write is staged, not executed. Staged actions contain the complete tool
   name and arguments, a snapshot of the relevant user and target state,
   and resolved address/item details from the live database.
4. **Present.** On the next text turn, the trusted runner replaces the agent
   summary with a deterministic manifest. This manifest includes every
   argument, current address for address changes, and item/product variants
   where resolvable. Only the exact rendered text observed by the guard
   can establish a presented manifest.
5. **Confirm.** A controlled affirmative reply authorizes the complete manifest.
   Replies with extra qualifications, partial approval or revisions do not
   authorize anything. Every new user turn revokes unused authorizations.
   Multiple staged actions are authorized together, in their presented order.
6. **Commit.** Immediately before each write, tool name, complete arguments
   (including ordered lists), relevant state snapshot and next-action order
   must match. Policy is rechecked against current state. The authorization
   is consumed after dispatch, even if the tool reports an error.
7. **Recover.** Changed arguments or stale state require a newly presented
   manifest and confirmation. Ordinary policy failures retain corrective
   feedback and the circuit breaker. Preparation is not a retry failure;
   repeated preparations do not trip the circuit breaker. Transfer clears
   pending and approved actions.

The implementation is `TransactionGuardEnforcer`; it does not access task
annotations, expected/gold actions or simulator instructions. Offline
evaluation remains separate and may use gold actions.

## Conditional guarantee, not an aggregate performance promise

Assume all writes pass through this runner, dispatch is sequential within a
conversation, the tool database snapshot is truthful, and the user sees and
deliberately confirms the trusted manifest. Then an executed protected write
must match the next unconsumed confirmed tool-and-arguments entry and its
relevant state snapshot. Parameter substitution, target swapping after
confirmation, authorization reuse, unqualified partial approval and detected
stale-state commits are rejected.

This is an **authorization integrity** guarantee, not a theorem that the
agent understands every user intention or that task success cannot decrease.
An inattentive or imperfect simulated user can approve the wrong proposal.
Natural-language user intent is not a trusted formal specification. The
policy-as-code encoding may omit rules. Database reads and dispatch are not
an atomic backend transaction: concurrent external mutations require backend
compare-and-swap/version preconditions, which this benchmark lacks.

The intent ledger is conservative rule-based parsing, not full natural-language
understanding. Unsupported phrasings, unnamed/ambiguous references and
unrecognized option relations have no intent-correctness guarantee. A short
product noun resolves only when unique among retrieved product names.
"Same price already paid" in the camera budget rule is operationalized as
no more than the original price, allowing cheaper options; it does not assert
exact price equality. Numeric option comparisons require parseable numbers.
Tied optimal variants remain allowable when the user specified no tie-breaker;
a gold list containing only one tied variant can penalize an otherwise
permitted alternative. Such discrepancies must be reported, not silently
reclassified to improve the headline metric.
New user intentions expressed as ordinary affirmations can require explicit
restatement. No inferred relation should be presented as a general safety law.

The first live manifest-only calibration still produced wrong writes after
the simulator approved an inconsistent agent proposal. This unsuccessful
intermediate result motivated the independent-request ledger; it is retained
in `outputs/runs/transaction-calibration`, not discarded.
The subsequent intent-ledger calibration corrected the observed address
inversion with full task success for `retail_109`, but did not solve every
calibration failure. It remains development evidence, not a general result.

The extra confirmation has measurable interaction costs. The conservative
confirmation language and snapshot checks can force renewed approval. Staged
actions are not an all-or-nothing transaction: a later failure does not roll
back an earlier successful write. "Transactional" describes authorization
preparation and consumption, not distributed ACID atomicity.

This design builds on reference monitors, least-authority execution,
transaction preparation and trusted confirmation displays. Do not claim
these primitives are new. A potential research contribution is their
oracle-free SAFE mapping, action/state-bound implementation, failure taxonomy
and evaluation of safety versus task completion. Novelty requires comparison
with prior agent authorization and human-in-the-loop systems.

Relevant prior work includes [AgentSpec: Customizable Runtime Enforcement for
Safe and Reliable LLM Agents](https://arxiv.org/abs/2503.18666) and
[AgentGuard: An Attribute-Based Access Control Framework for Tool-Use
LLM-Based Agent](https://arxiv.org/abs/2605.28071). The titles and identifiers
were checked against arXiv; detailed feature comparison and any novelty claim
still require reading the complete papers. Exact approval alone is not a
novelty claim for SAFE.

## Diagnostic replay

`scripts/shadow_replay.py` reproduces the original trajectory, including all
original unblocked calls. Hypothetical blocks do not affect later database
state or circuit-breaker counters. Original blocks do affect counters and are
not executed. Message/flat-call consistency, invalid source traces, rule
errors and exact raw tool-output mismatches fail explicitly.

Gold matches in replay are evaluation-only labels. Non-gold writes are not
automatically unsafe; gold-matching writes can still lack required
confirmation. A replay detection count is not a counterfactual success rate.
The first address-heuristic replay covered 180 traces and reproduced their
outputs, but its discarded direction rule must not be presented as evidence
for the final transactional method.

## Prospective protocol

- **Development/calibration:** all previously inspected tasks, including the
  original held-out set. Live calibration uses `retail_109`, `retail_103`,
  `retail_099` and `retail_064`. These are not confirmatory observations.
- **Untouched task set:** the previously frozen `data/heldout2` set of all
  34 remaining retail tasks. Do not inspect its goals or gold actions to tune
  rules. Run only after code, configuration and this protocol are frozen.
- **Comparison:** baseline versus `safeguard-transaction`, three seed indices
  (0, 1, 2), 204 trajectories, same deployment (`gpt-5.4-1`), baseline system
  prompt and 20-turn budget. Runtime protocol reminders and manifests are part
  of the treatment. No task-specific prompt bindings.
- **Primary outcomes:** any gold-derived unsafe write, commission error and
  binary full task success. All three matter; omission-driven safety gains
  with lower success do not establish a superior method.
- **Secondary outcomes:** unsafe-write counts, omitted gold writes, transfers,
  blocked calls, preparation/confirmation overhead and the existing
  exploratory attribution/strict-attribution metrics. Attribution remains
  heuristic, not human adjudication.
- **Inference:** pair by task and seed; primary tests on per-task mean
  differences, task-clustered bootstrap confidence intervals, Holm correction
  across primary outcomes. Pair-level McNemar is sensitivity-only because
  seeds share tasks.
- **Validity:** record API errors and exclusions, require pair coverage,
  preserve raw traces and exact tool outputs, and report incomplete pairs.
  Do not rerun successful trajectories selectively. Infrastructure-error
  retries must be disclosed and cannot change the frozen treatment.
- **Stopping and claims:** no early outcome-based stopping. Freeze code/config
  hashes before execution. If implementation changes after viewing fresh
  results, those tasks become development data. Report unfavorable outcomes.
  A nonsignificant difference is not proof of no degradation; no
  non-inferiority margin is invented after observing results.

The original result and a new prospective result answer different questions.
Neither should be hidden or merged into one favorable headline.
