# Bounded color-edit development check

## Mechanism and hypothesis

The retained `f93994c` retail_104 failure changed a 2-piece luggage set to a
4-piece set while the independent request asked only for red. Exact manifest
approval did not establish that the unrequested piece-count change was intended.
The next bounded predicate recognizes color-only edits and preserves other
retrieved option values. It resolves explicit product/order targets or a unique
retrieved owned pending-order item. It does not use hidden goals or gold actions.
Recognized explicit multi-option revisions and cheapest selection are excluded
from this predicate, and plain agreement cannot widen its edit scope.

Nine synthetic regressions cover correct and incorrect edits, generic target
ambiguity, other-order references, optimization, explicit later scope revision
and plain approval. Full suite: 8,049 tests passed before execution.

## Fixed selected design

Run `transaction-color-edit-regression`: retail_104 and retail_111, treatment
only, seed index 0, two workers, existing gpt-5.4-1 deployment and unchanged
20-turn budget. Freeze commit/hashes first; keep source unchanged through
execution and integrity verification. Preserve original rewards and mismatches,
including valid failures. This is another versioned development check, not
replacement of earlier valid trajectories or independent confirmation.
