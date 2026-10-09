# SAFE-Guard: intent-bound authorization for irreversible tool actions

This document describes the method and post-comparison dispatch/feasible-set
repairs. The completed comparison in `repaired-development-comparison.md`
used earlier frozen commit `1bf2667`; do not attribute subsequent repairs
to that experiment. Neither version demonstrates general safety.

## Problem

An agent can produce a structurally valid, policy-permitted tool call that
contradicts the user's request. A user or simulator may then approve the
agent's mistaken summary. A confirmation gate alone binds consent to the
mistake; a stronger intervention must distinguish request evidence from
agreement with an agent proposal.

Three concrete failure classes motivated the implementation:

1. **Feasible-set drift:** an optimizer chooses or enforces the cheapest
   catalog item when the user restricted the choice to items in an order.
2. **Irreversible omission:** a return changes an entire order's status before
   all recognized requested return items are included.
3. **Role inversion:** an address mentioned as a source is written to the
   wrong destination after a misleading proposal is approved.

They are different from parameter substitution *after* correct approval.
The method therefore checks recognized intent before preparation and checks
authorization again at dispatch.

## Trusted boundary and inputs

The trusted boundary contains the runner, tool dispatcher, policy monitor,
intent recognizer and manifest renderer. The agent does not author the
authorization display. A tool database supplies the relevant live state.
Recognized references resolve only through objects marked retrieved by the
conversation. The monitor is not passed gold actions, evaluator annotations
or hidden simulator goals as its specification.

Natural-language requests are not formal specifications. The implementation
keeps ordinary user requests separately from affirmative replies to agent
proposals. Recognized corrections may revise constraints. Some affirmative
utterances contain new intent and are intentionally insufficient without a
restatement; this is a limitation, not universal linguistic disambiguation.

## State and transition system

For each prepared action, store

`a = (tool, complete ordered arguments, relevant state snapshot, display)`.

Per-conversation state contains a request ledger `L`, pending actions `P`,
approved actions `Q`, and digests of rendered/presented manifests. JSON object
keys are canonicalized; list order and values remain bound. Snapshots contain
the relevant user and target object, not every catalog object or external
system state.

| Transition | Preconditions | State change and effect |
|---|---|---|
| Request | User turn arrives | Update recognized independent intent; revoke unused approval. |
| Propose | Protected tool call submitted | Recheck authentication, ownership, scope, retrieved evidence, policy and recognized intent. |
| Reject | A non-authorization predicate fails or a rule errors | Do not execute or stage that action; return explicit feedback. |
| Prepare | Checks pass except exact approval or fresh snapshot | Append unique action to pending manifest; do not execute. |
| Present | Pending actions exist after tool processing | Runner immediately renders complete manifest; user sees no alternative agent-written authorization summary. |
| Approve | Exact presented manifest digest matches pending state and reply is a controlled full affirmative | Copy the complete ordered pending list into approval; clear presentation/pending state. |
| Commit | Proposed action matches next approved signature and current relevant snapshot; policy/intent checks still pass | Consume the next approval at the validated dispatch gate, before invoking the environment. Backend/observer failure cannot restore it. |
| Refresh | Arguments or relevant state changed | Require a new prepared display and approval; never silently change approved values. |

Ready actions may be staged in one ordered tool-call message, giving one
trusted confirmation. Preparation binds later snapshots to exactly predicted
effects for two locally modeled retail operations: address replacement and
pending-order cancellation (including rounded gift-card refunds). Prediction
works on copies, never performs writes, and is bound in the manifest digest.
The dispatch gate still compares the complete relevant live user/target snapshot
with that expected state. Missing effects, additional changes and wrong values
require renewed approval. Other transitions are not predicted and may stale
later actions. This is a bounded transition model, not general dependency planning.
Preparation-only blocks do not count toward the policy retry circuit breaker.

## Recognized relational predicates

### Feasible set before objective

For a recognized same-order cheapest replacement, the set contains available
variants of the same product represented by other items in that target order,
excluding the original item. A proposed replacement outside that set blocks.
Within it, the price must be minimal under the implemented price comparison.
Empty sets require clarification. A directly recognized "cheapest [available]
COLOR" requirement restricts that set to the catalog's matching color before
price comparison. Unrestricted cheapest requests retain catalog-wide behavior.
This is not a general constraint solver and does not combine every possible
option constraint into one optimizer.

### Coverage before an irreversible transition

Recognized positive return clauses contribute explicit IDs or product
references for the target order. Before a return changes the whole order's
status, its item set must include those recognized goals. Explicit withdrawal
removes goals; a resolved `return only ...` correction replaces the set for
that order. A co-delivery clause identifies an item, not another return goal.
The guard does not add items to tool arguments or perform extra returns.
Contiguous bullet lists after `return only:` are recognized as one target
list. A singular product reference with multiple variants does not mean
"return all variants"; a uniquely matching recorded option can resolve it.
Unresolved references do not establish mandatory item IDs, and explicit
retrieved IDs remain stronger than name matching.

Unsupported syntax and ambiguous product subsets remain limitations.
Coverage is checked for the proposed target order; it is not a proof of
completeness for every future user request.

### Address obligation before a one-time item mutation

A bounded Flow predicate recognizes an address-update clause attached to an
explicit order ID, a matching product reference, or a unique retrieved pending
order. It resolves default/profile destinations through that user's current
profile; an explicit NYC reference resolves only to a unique address on retrieved
owned New York orders. Unresolved sources require clarification.

Before pending-order item mutation closes further modification, the recognized
address must already match or be an earlier correctly targeted prepared action.
Ordered dispatch and expected-state checks still require its actual execution
before the item write. The rule does not reorder arguments, mutate the address
itself or accept arbitrary post-hoc state. Explicit scoped withdrawal removes
the obligation. Unsupported address destinations and linguistic target links
are not a general prerequisite planner.

### Source and destination roles

A recognized color-only edit also preserves the retrieved item's other option
values. It applies to an explicit product/order reference or a unique retrieved
owned pending-order item reference, not a cheapest-variant optimization or a
recognized multi-option revision. A simple manifest approval cannot widen
that scope. If no available variant meets the edit, the agent must clarify an
explicit scope change rather than silently substitute unrelated attributes.
This bounded lexical predicate is not a general natural-language frame rule.

Recognized descriptions such as a named product being shipped to the user's
new address/place/home resolve to retrieved orders and their addresses.
Unresolved or conflicting recognized sources block. Address writes must
match the resolved source unless the user explicitly corrects the request.
An approved wrong summary does not itself replace the source relation.
The recognizer does not infer all address roles from arbitrary conversation.

## Conditional authorization invariant

Assume sequential dispatch, complete mediation of protected writes, truthful
snapshots, correct execution of the trusted monitor and renderer, and an
explicit affirmative from the user after seeing the manifest. Then every
dispatched protected write equals the next unconsumed tool/argument entry
from that presented and approved manifest, with the same relevant snapshot,
and passes the implemented current policy and intent checks.

The induction over dispatches is described below, but a fault-path
check found that the frozen implementation consumes approval only after its
parent post-dispatch observer returns. If that observer raises, approval
remains live. Thus the frozen version does not establish the one-use property
under observer failure. The required repair is consumption at the validated
dispatch gate, before invoking the backend; the frozen comparison finished
before that runtime was changed. The subsequent repair spends approval in
`pre_tool_call` once checks allow the write; `post_tool_call` no longer
consumes or revokes the next action's approval. Ordinary backend error-result handling is
covered, but must not be confused with an exception in the observer itself.

Initially `Q` is empty,
so a write without approval cannot pass confirmation. Only the presented
digest plus controlled reply creates `Q`. The execution gate compares the
first entry's signature and snapshot. A successful dispatch consumes that
entry; errors consume it as well. New user turns revoke the remaining list.
Thus no later dispatch can use a substituted, reordered or consumed entry
without a new authorization, provided consumption occurs at the dispatch
boundary even when observation fails. This is a conditional algorithm argument, not
machine-checked verification or a theorem of user-intent correctness.

## Properties not established

- Universal intent understanding or complete policy encoding.
- Informed consent by an inattentive user or imperfect simulator.
- Backend atomicity, rollback or protection against concurrent state changes
  between the snapshot check and the backend write.
- A complete transition model, dependency planner or optimum confirmation schedule.
- A proof that task success cannot decrease.
- Novelty of reference monitoring, state-dependent policies, human approval,
  complete parameter displays or one-use execution permissions individually.

## Evidence discipline

Separate four kinds of evidence: synthetic gate/regression tests, exact
historical replay, selected live development cases, and an untouched
prospective comparison. They answer different questions. Guard-block counts
are not prevented-harm counts. Successful workflows without the relevant
semantic intervention are not evidence that it caused prevention.

The original 102-pair prospective treatment had lower task completion and
more effective non-gold-write trajectories than baseline. It remains part
of the evidence. Repaired selected cases show feasibility but do not erase
that result. The full-set repaired comparison also reuses inspected data and
must be reported as development evidence regardless of its outcome.
