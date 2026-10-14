# Generated SAFE challenge benchmark

This benchmark is a deterministic, model-free complement to the selected
τ³ tasks. A declarative specification generates paired adversarial cases and
legitimate near-neighbors for all four SAFE dimensions. Structured traces are
scored by transparent automatic oracles; no model or API call is used.

## Coverage

`data/generated_safe/specification.yaml` defines paired cases for:

- target/order substitution and source/destination inversion;
- incomplete multi-item coverage and the wrong feasible set;
- unauthorized attribute changes and reordered dependencies;
- stale or replayed approval and ambiguous multi-action assent;
- payment provenance;
- backend and observer failure; and
- ambiguity that requires escalation.

Every family has an `adversarial` variant and a `near_neighbor` variant so a
system cannot score well by always refusing. The committed public fixture has
24 challenges (12 pairs) and covers Scope, Anchored Decisions, Flow Integrity,
and Escalation.

## Generate and validate

```powershell
python scripts\generated_safe_benchmark.py generate `
  --seed 1701 `
  --output data\generated_safe\fixtures\public-seed-1701.json

python scripts\generated_safe_benchmark.py validate `
  --suite data\generated_safe\fixtures\public-seed-1701.json
```

Generation selects template variables with a local deterministic PRNG. IDs are
derived from a seed commitment rather than embedding the seed. The suite stores
the specification hash and seed commitment, and validation checks unique IDs,
complete adversarial/near-neighbor pairs, and that every reference trace passes
while every negative trace fails.

Candidate traces use the `CandidateTrace` schema in
`safe_benchmark.generated.schema`. Call
`evaluate_candidate(challenge, candidate)` to obtain a binary score, explicit
violations, and human-readable evidence.

## Component ablations

Run the deterministic component harness without a model or API:

```powershell
python scripts\run_component_ablations.py
```

It compares exact action-manifest consent, intent-authority checks without
whole-manifest binding, full SAFE-Guard, and leave-one-SAFE-dimension-out
profiles. Results are written as JSON and Markdown under
`outputs/derived/component-ablation-v1/`, including per-family and
per-dimension violation prevention, legitimate allow rate, illegitimate
blocks, and contract conformance. These are mechanism tests over structured
traces, not estimates of agent effectiveness or task success.

## Hidden and frozen seeds

Freeze hidden high-entropy seeds before an evaluation:

```powershell
python scripts\generated_safe_benchmark.py freeze `
  --count 4 `
  --seed-file data\generated_safe\private\frozen-seeds.json `
  --manifest data\generated_safe\frozen-seed-manifest.json

python scripts\generated_safe_benchmark.py verify-freeze `
  --seed-file data\generated_safe\private\frozen-seeds.json `
  --manifest data\generated_safe\frozen-seed-manifest.json

python scripts\generated_safe_benchmark.py generate `
  --seed-file data\generated_safe\private\frozen-seeds.json `
  --output data\generated_safe\hidden\suite.json
```

The private seed file and hidden suites are gitignored. The committed manifest
contains only SHA-256 commitments and the specification hash. Keep the private
seed file in controlled evaluation storage: a commitment proves consistency
but cannot recover a lost seed. Use high-entropy generated seeds, because small
human-chosen seeds are vulnerable to enumeration.

## Reproducibility boundary

The oracle consumes structured events, not natural-language transcripts. An
adapter from an agent trace must be fixed before evaluation and reported with
results. The benchmark tests constraint-aware behavior; it does not by itself
measure end-user task quality or prove informed consent.
