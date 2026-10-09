# Authorization prior art and contribution boundary

This is a public-paper comparison, not an implementation comparison or proof
that another system cannot express SAFE-Guard's protocol. Absence from the
sections inspected is not evidence of absence. No relative-performance or
"first" claim follows from this review.

| Source | Established overlap | Distinction requiring evidence |
|---|---|---|
| AgentSpec, Wang, Poskitt and Sun, 2025 | Runtime triggers, predicates and enforcement; user inspection with abstract permit/stop semantics (§3–4). | Binary permit/stop does not establish complete displayed-argument binding, ordered batch approval, state-bound reapproval or one-use semantics. |
| AgentGuard, Luo et al., submitted 27 May 2026 | Attribute-based tool access control and rule-based, LLM-assisted and manual inspection (§2). | Architecture-level descriptions do not settle exact display, approval lifecycle or state binding. Public implementation was not compared. |
| CaMeL, Debenedetti et al., 2025 | Provenance-tagged values, separate planning/query components, parameter-aware Python security policies; policy-triggered explicit user approval (§2–4.3). | Data provenance is adjacent to, but not identical to, distinguishing new requests from assent to a proposing agent. No claim of superior protection is supported. |
| Progent, Shi et al., 2025 | Task-specific privilege policies; a retrieved recipient can tighten the allowed destination; generated policies receive user confirmation (§2–3.1). | Recipient binding is already prior art. The full policy-execution design was not inspected, so detailed transaction semantics remain unresolved. |
| IsolateGPT, Wu et al., 2024 / NDSS 2025 | Non-LLM deterministic operators, mediated inter-app communication, consent before irreversible actions, actual permission dialogs (§IV-A–C, figures 3–4). | Irreversible-action consent does not itself establish requested-item coverage. Appendix A-D, referenced for permission details, was not inspected. |
| SEAgent, Ji et al., 2026 | Mandatory/attribute-based controls, execution-flow/state modeling and block/prompt/allow enforcement (§1–3.2). | Detailed design sections were not inspected; exact approval mechanisms are unresolved. |
| OWASP Transaction Authorization Cheat Sheet | What You See Is What You Sign, transaction-specific/one-time authorization, sequential authorization, protection of transaction data, final execution gate and limited validity. | These are established transaction-security primitives. A snapshot check alone does not solve backend TOCTOU without atomic mediation. |

## Defensible method formulation

SAFE-Guard is an **implemented specialization** of transaction authorization
for conversational tool execution. It keeps recognized independent request
relations separate from assent to an agent proposal; checks feasible-set,
source/destination and irreversible coverage constraints; and combines these
checks with trusted direct presentation of ordered actions and state-bound
approval. Direct presentation and batching address interaction cost as well
as authorization integrity.

This is a contribution hypothesis requiring evidence of useful behavior
and reproducibility, not a claim that any primitive or their composition is
unprecedented. General policy languages may encode the same specialization.
The exact-argument gate protects against substitution and detected state
changes; it does **not** prove that the original proposed action preserved
intent. That question depends on the separate bounded recognizer.

The negative frozen prospective result remains evidence against efficacy
of that version. Selected repaired successes and the reused full-set
comparison are development evidence. Neither supports general safety,
non-inferiority, or superiority over these systems.

## Primary sources

- AgentSpec: https://arxiv.org/abs/2503.18666
- AgentGuard: https://arxiv.org/abs/2605.28071
- CaMeL: https://arxiv.org/abs/2503.18813
- Progent: https://arxiv.org/abs/2504.11703
- IsolateGPT: https://arxiv.org/abs/2403.04960
- SEAgent: https://arxiv.org/abs/2601.11893
- OWASP: https://cheatsheetseries.owasp.org/cheatsheets/Transaction_Authorization_Cheat_Sheet.html

Sections are identified from the public manuscripts inspected. Titles,
version dates and section numbering should be checked again against the
versions cited in a final submission. No unsupported bibliography date
should be inferred from a venue year or a secondary citation.
