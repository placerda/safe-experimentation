# Bounded formal model of SAFE-Guard authority

## Proof boundary

`safe_benchmark.formal_authority` is an executable, finite-state specification
independent of `TransactionGuardEnforcer`. It receives already-normalized user
requests, actions, assent classifications, and relevant-state digests. Natural
language recognition, policy completeness, truthful state observation, and
backend atomicity are explicitly outside the proof boundary.

The model proves a narrower authorization-integrity claim: a protected dispatch
is allowed only for the current ordered head of an exactly presented and fully
assented sequence, with identical complete arguments and relevant state. The
authority is spent before backend execution or post-call observation.

## Variables and transitions

- `request`: normalized actions authorized by the current independent request.
- `proposal`: the candidate ordered action/state sequence. A proposal outside
  `request` is rejected and never changes `request`.
- `presented`: the exact trusted sequence shown for assent.
- `approved`: the unconsumed suffix of a fully assented `presented` sequence.
- `epoch`: incremented by every user turn.
- `dispatches`: immutable records of authorization and actual dispatch values.

Transitions are `user_turn`, `propose`, `present`, `assent`, `dispatch`, and
`observe`. Partial assent authorizes nothing. A user turn revokes unused
approval. Dispatch compares the complete canonical action signature, ordered
position, and state digest, then removes the head before any outcome is known.
`observe`, including failure, cannot restore authority.

## Invariants

1. Proposal and assent cannot change or exceed the normalized request.
2. Approval belongs to the current user-turn epoch.
3. Every dispatch exactly matches its authorized action and state.
4. Approval is one-use and ordered; outcome handling cannot replay it.

`explore_bounded()` exhaustively explores all reachable states through depth
six over two actions, two state values, full/partial assent, exact/substituted/
reordered/stale dispatch, new turns, and successful/failed observations.

## Production conformance

The runtime emits normalized `prepare`, `authorization_user_turn`, and
`dispatch` audit events containing canonical action signatures and hashed
state snapshots. `scripts/check_authority_trace.py TRACE RECOGNITION` translates
those events into the independent model. `RECOGNITION` supplies
`requests_by_turn`, `full_assent_turns`, and `partial_assent_turns`; this makes
the unproved recognition boundary explicit rather than silently treating text
matching as a theorem.

The checker does not import or call production enforcer internals. Mutation
tests alter valid audit streams to cover expanding assent, request overwrite,
partial assent, argument substitution, reordering, stale state, approval
survival across a new turn, and delayed consumption/post-observer restoration.
