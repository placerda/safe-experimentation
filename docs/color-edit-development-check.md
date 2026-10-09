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

## Retained `aa0f46f` selected outcome

74 hashes and two exact trace/result cells verified; no execution errors.
Both full rewards are zero. retail_104 has zero non-gold writes and zero
missing gold writes; address precedes item change and the 2-piece configuration
is preserved. Its full reward still fails and is not rescued from write counts.
The agent selected the correct variant itself, so the live trace does not
establish a causal effect of the color predicate.

retail_111 has zero executed writes and three missing gold writes. Its explicit
reply authorizing all listed actions with exact values/order was rejected by
the overly narrow controlled affirmative grammar; a later "yes" still resulted
in re-preparation and eventual human transfer. The next source extends only
this controlled exact-manifest assent syntax. It still requires a displayed,
unchanged manifest digest; partial approvals and added corrections fail closed.
