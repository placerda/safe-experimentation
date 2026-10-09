# Post-prospective intent repairs

These changes follow the negative frozen comparison at `53fe8ca`.
They are development changes, not part of that treatment, and do not
establish aggregate safety improvement.

## Mechanisms

1. Candidate-set preservation: recognized cheapest requests restricted to
   peers in the same order are optimized over available same-product peers,
   excluding the original item. Catalog-wide requests retain their original
   behavior. An empty eligible set requires clarification, not substitution.
2. Irreversible return coverage: recognized positive return clauses from
   independent requests contribute item IDs or product references within the
   target order. A return omitting those items is rejected before preparation,
   because the tool changes the order status and blocks subsequent returns.
   Explicit `do not return` clauses withdraw recognized goals. This check
   does not rewrite arguments or silently execute additional returns.
3. Address-source roles: recognized shipping-to-new-place/home/house
   statements resolve against retrieved orders, as do shipping-to-new-address
   statements. A recognized but unresolved source blocks preparation and asks
   for retrieval or an explicit correction. Contradictory or ambiguous sources
   still block. Explicit address corrections also replace earlier recognized
   place/home source clauses while preserving unrelated goals.

The parsers remain bounded: singular/plural product matching and recognized
clauses are not a universal semantic verifier. Product-only return requests
can cover multiple matching items; ambiguous subset intentions require an
explicit item-ID correction. Withdrawal must use recognized language.
Exact one-use authorization and relevant-state checks are unchanged.

## Development validation

The full test suite passes 193 tests after these changes. Cases cover
catalog-versus-order candidate sets, unavailable peers, order-specific return
IDs, separate return goals, withdrawals, purchase-only mentions, address
negation, unresolved retrieval and explicit address-source corrections.

A live calibration will use the inspected failure tasks `retail_049`,
`retail_091`, `retail_104` and `retail_110`, one seed index, the same
`gpt-5.4-1` deployment and 20-turn budget. It is a focused mechanism check,
not an independent replication or a paired causal estimate. Keep all
trajectories, unfavorable outcomes and infrastructure retries. Do not merge
its results with the frozen comparison or present it as untouched held-out
evidence. Additional confirmation friction is not eliminated by these repairs.
