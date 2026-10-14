# Generated SAFE component ablations

This is a deterministic **mechanism test** over structured generated traces. It does not measure agent effectiveness, language understanding, or end-user task success.

- Suite SHA-256: `768bd79554b0730c0e486bf18bc80d40d1c8d5a0ea571f7028caf1b389c6c1fa`
- Agent effectiveness measured: `false`

## Aggregate results

| Profile | Legitimate allow | Illegitimate blocked | Legitimate blocks | Illegitimate allows |
|---|---:|---:|---:|---:|
| `manifest_only` | 24/24 (100.0%) | 22/24 (91.7%) | 0 | 2 |
| `intent_authority_only` | 24/24 (100.0%) | 14/24 (58.3%) | 0 | 10 |
| `full_safe_guard` | 24/24 (100.0%) | 24/24 (100.0%) | 0 | 0 |
| `without_scope` | 24/24 (100.0%) | 18/24 (75.0%) | 0 | 6 |
| `without_anchored_decisions` | 24/24 (100.0%) | 16/24 (66.7%) | 0 | 8 |
| `without_flow_integrity` | 24/24 (100.0%) | 20/24 (83.3%) | 0 | 4 |
| `without_escalation` | 24/24 (100.0%) | 18/24 (75.0%) | 0 | 6 |

## Violation prevention by dimension

| Profile | scope | anchored_decisions | flow_integrity | escalation |
|---|---:|---:|---:|---:|
| `manifest_only` | 6/6 | 7/8 | 3/4 | 6/6 |
| `intent_authority_only` | 6/6 | 6/8 | 0/4 | 2/6 |
| `full_safe_guard` | 6/6 | 8/8 | 4/4 | 6/6 |
| `without_scope` | 0/6 | 8/8 | 4/4 | 6/6 |
| `without_anchored_decisions` | 6/6 | 0/8 | 4/4 | 6/6 |
| `without_flow_integrity` | 6/6 | 8/8 | 0/4 | 6/6 |
| `without_escalation` | 6/6 | 8/8 | 4/4 | 0/6 |

## Violation prevention by family

| Family | manifest_only | intent_authority_only | full_safe_guard | without_scope | without_anchored_decisions | without_flow_integrity | without_escalation |
|---|---:|---:|---:|---:|---:|---:|---:|
| `ambiguity-escalation` | 2/2 | 1/2 | 2/2 | 2/2 | 2/2 | 2/2 | 0/2 |
| `backend-failure` | 2/2 | 0/2 | 2/2 | 2/2 | 2/2 | 2/2 | 0/2 |
| `multi-action-assent` | 2/2 | 1/2 | 2/2 | 2/2 | 2/2 | 2/2 | 0/2 |
| `multi-item-coverage` | 2/2 | 1/2 | 2/2 | 2/2 | 0/2 | 2/2 | 2/2 |
| `observer-failure` | 1/2 | 1/2 | 2/2 | 2/2 | 0/2 | 2/2 | 2/2 |
| `payment-provenance` | 2/2 | 2/2 | 2/2 | 2/2 | 0/2 | 2/2 | 2/2 |
| `reordered-dependencies` | 1/2 | 0/2 | 2/2 | 2/2 | 2/2 | 0/2 | 2/2 |
| `source-destination-inversion` | 2/2 | 2/2 | 2/2 | 0/2 | 2/2 | 2/2 | 2/2 |
| `stale-replayed-approval` | 2/2 | 0/2 | 2/2 | 2/2 | 2/2 | 0/2 | 2/2 |
| `target-substitution` | 2/2 | 2/2 | 2/2 | 0/2 | 2/2 | 2/2 | 2/2 |
| `unauthorized-attribute-change` | 2/2 | 2/2 | 2/2 | 0/2 | 2/2 | 2/2 | 2/2 |
| `wrong-feasible-set` | 2/2 | 2/2 | 2/2 | 2/2 | 0/2 | 2/2 | 2/2 |

## Contract conformance

- `manifest_only`: `all_legitimate_allowed`=true, `partial_surface_has_prevention_signal`=true, `partial_surface_is_not_full_guard`=true
- `intent_authority_only`: `all_legitimate_allowed`=true, `partial_surface_has_prevention_signal`=true, `partial_surface_is_not_full_guard`=true
- `full_safe_guard`: `all_legitimate_allowed`=true, `full_blocks_all_illegitimate`=true
- `without_scope`: `all_legitimate_allowed`=true, `leave_one_out_only_exposes_omitted_dimension`=true
- `without_anchored_decisions`: `all_legitimate_allowed`=true, `leave_one_out_only_exposes_omitted_dimension`=true
- `without_flow_integrity`: `all_legitimate_allowed`=true, `leave_one_out_only_exposes_omitted_dimension`=true
- `without_escalation`: `all_legitimate_allowed`=true, `leave_one_out_only_exposes_omitted_dimension`=true
