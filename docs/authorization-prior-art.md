# Authorization prior art and contribution boundary

This is a public-paper comparison, not an implementation comparison or proof
that another system cannot express SAFE-Guard's protocol. Absence from the
sections inspected is not evidence of absence. No relative-performance or
"first" claim follows from this review.

## Evidence labels used below

Each row distinguishes three things and must not blur them:

- **Verified presence** ("Established overlap"): a mechanism this review
  actually read in the cited section, abstract, or figure of the source.
- **Absence not established**: SAFE-Guard's review did not find a mechanism
  in the inspected material. This is not a claim that the source lacks it;
  unread sections (full method sections, appendices, reference
  implementations) may contain it.
- **Unresolved implementation detail**: a specific mechanical question
  (e.g., exact-argument binding, one-use consumption, ordered batch display,
  state-bound reapproval) that the inspected material does not answer either
  way, so no comparison claim can be made on that point yet.

| Source | Established overlap | Distinction requiring evidence |
|---|---|---|
| AgentSpec, Wang, Poskitt and Sun, 2025 | Runtime triggers, predicates and enforcement; user inspection with abstract permit/stop semantics (§3–4). | Binary permit/stop does not establish complete displayed-argument binding, ordered batch approval, state-bound reapproval or one-use semantics. |
| AgentGuard, Luo et al., submitted 27 May 2026 | Attribute-based tool access control and rule-based, LLM-assisted and manual inspection (§2). | Architecture-level descriptions do not settle exact display, approval lifecycle or state binding. Public implementation was not compared. |
| CaMeL, Debenedetti et al., 2025 | Provenance-tagged values, separate planning/query components, parameter-aware Python security policies; policy-triggered explicit user approval (§2–4.3). | Data provenance is adjacent to, but not identical to, distinguishing new requests from assent to a proposing agent. No claim of superior protection is supported. |
| Progent, Shi et al., 2025 | Task-specific privilege policies; a retrieved recipient can tighten the allowed destination; generated policies receive user confirmation (§2–3.1). | Recipient binding is already prior art. The full policy-execution design was not inspected, so detailed transaction semantics remain unresolved. |
| IsolateGPT, Wu et al., 2024 / NDSS 2025 | Non-LLM deterministic operators, mediated inter-app communication, consent before irreversible actions, actual permission dialogs (§IV-A–C, figures 3–4). | Irreversible-action consent does not itself establish requested-item coverage. Appendix A-D, referenced for permission details, was not inspected. |
| SEAgent, Ji et al., 2026 | Mandatory/attribute-based controls, execution-flow/state modeling and block/prompt/allow enforcement (§1–3.2). | Detailed design sections were not inspected; exact approval mechanisms are unresolved. |
| OWASP Transaction Authorization Cheat Sheet | What You See Is What You Sign, transaction-specific/one-time authorization, sequential authorization, protection of transaction data, final execution gate and limited validity. | These are established transaction-security primitives. A snapshot check alone does not solve backend TOCTOU without atomic mediation. |
| Agent Memory Is a Surface for Endogenous Authorization Laundering, 2609.01836 | Treats persistent agent memory as part of the effective authorization policy; shows incremental memory writers fabricate false permissions for up to 50.2% of unauthorized requests and executors then act on that false authority in 98.6% of trials; proposes requiring stored permissions to be backed by valid source events and bounded event sourcing as partial safeguards, with a measured safety/utility tradeoff (abstract; App. C.3, EAL-Bench design). | This targets drift/fabrication in cross-turn *stored* authorization state (memory), not a per-write exact-argument manifest consumed at dispatch. SAFE-Guard's request-relation ledger is checked at commit time against live state, not evaluated for its own internal consistency across turns the way EAL-Bench evaluates memory. Whether SAFE-Guard's ledger is itself susceptible to the same endogenous-laundering pattern over long conversations is an unresolved implementation detail this review does not test. Only the abstract and one appendix subsection were inspected; the core benchmark and safeguard sections were not. |
| Auditing Provenance Sensitivity in LLM Agent Action Selection, 2607.20827 | Formalizes authority as target-specific (tool call and each argument scored separately), labels context evidence Valid/Invalid/Neutral by source authorization rather than truthfulness, and empirically shows models are source-authority sensitive but not fully isolated from unauthorized competing evidence (5.4% of competing cases change the produced action; 2.4% [2.1, 3.0] retain unauthorized influence under valid-evidence degradation) (Introduction, abstract). | This is a diagnostic/auditing methodology measuring whether a model's *internal* action selection responds to evidence provenance; it is not a runtime enforcement or user-confirmation mechanism and specifies no manifest, staged write, or consumption-based approval. It measures model susceptibility to unauthorized evidence; SAFE-Guard provides an external backstop independent of whether the underlying model internally resisted that evidence. The target-specific authority framing is conceptually adjacent to SAFE-Guard's recognized-request-relation ledger but operates at a different layer (score/action diagnostics vs. execution gate). |
| Authenticated Delegation and Authorized AI Agents, 2501.09674 | Proposes extending OAuth 2.0 / OpenID Connect with agent-specific credentials and metadata for authenticated, authorized, and auditable delegation; proposes translating natural-language permissions into auditable access-control configurations; discusses human-in-the-loop oversight and grounds the framework in agency law (apparent authority, Restatement (Third) of Agency) and UETA's security-procedure/error-correction provisions (abstract; §5.5). | This is a pre-execution identity/credential and delegated-scope layer (who the agent is, what scope a principal granted in advance), not a per-transaction, per-write exact-argument display-and-confirm gate checked immediately before dispatch. Whether its "auditable access control configurations" include per-call state-bound reapproval, ordered batch display, or one-use consumption is an unresolved implementation detail — this review inspected the abstract and §5.5 (legal grounding) only; the core protocol sections (§3–4, by typical structure) were not inspected, so absence of transaction-level binding there is not established. |
| OAuth AI-agent on-behalf-of-user drafts (IETF Internet-Drafts, e.g. draft-klrc-aiagent-auth-02 "AI Agent Authentication and Authorization"; draft-liu-ai-agent-authorization-integration-00; the AOA proposal) | Specify workload identity for agents (SPIFFE/WIMSE-style identifiers), short-lived credential issuance, rotation and posture assessment before a credential is issued, and policy-based authorization that is meant to bind delegated user consent to an agent's workload identity (draft-klrc-aiagent-auth-02, §6–7, credential provisioning and posture assessment). | These are pre-execution identity, authentication, and session/scope-authorization mechanisms at the protocol layer; the inspected section does not specify how a conversational agent's tool-call arguments are bound to a displayed manifest, batched in order, or consumed once per user approval — that remains an unresolved implementation detail, not an established absence, since only one section of one draft was inspected. These are Internet-Drafts, not RFCs: they are explicitly works in progress, may expire, be renamed, or be superseded, and must be reverified (draft number/date) before any submission cites them. |

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

### Where the expanded comparison set leaves the novelty boundary

Adding the memory-laundering, provenance-auditing, authenticated-delegation
and OAuth agent-identity sources does not narrow the boundary above; it
confirms it sits at a different layer than each of them inspects:

- The identity/credential/delegation-scope layer (authenticated delegation,
  the OAuth/OIDC agent extension, and the IETF agent-authorization drafts)
  answers *who the agent is* and *what scope a principal granted in
  advance*. SAFE-Guard does not address that layer at all and takes agent
  and user identity as already established.
- The internal-model-behavior layer (provenance-sensitivity auditing)
  answers *whether a model's action selection resists unauthorized evidence
  internally*. SAFE-Guard is an external enforcement backstop that does not
  depend on, and was not evaluated against, that internal property.
- The cross-turn stored-authorization-state layer (endogenous authorization
  laundering) answers *whether persistent memory faithfully preserves
  permission history*. SAFE-Guard's request-relation ledger is consulted and
  checked against live state at commit time; whether that ledger is itself
  robust to the same multi-turn fabrication pattern EAL-Bench measures in
  memory is an open, untested question, not a settled distinction.

No source reviewed here was found, in the sections inspected, to specify an
exact-argument manifest presented before dispatch, ordered batch approval,
state-bound reapproval, or one-use authorization consumption at the
tool-call boundary. That is a statement about what this review did and did
not find in the material it read, not a claim that such mechanisms are
absent from unread sections, reference implementations, or other prior work.

## Primary sources

- AgentSpec: https://arxiv.org/abs/2503.18666
- AgentGuard: https://arxiv.org/abs/2605.28071
- CaMeL: https://arxiv.org/abs/2503.18813
- Progent: https://arxiv.org/abs/2504.11703
- IsolateGPT: https://arxiv.org/abs/2403.04960
- SEAgent: https://arxiv.org/abs/2601.11893
- Agent Memory Is a Surface for Endogenous Authorization Laundering: https://arxiv.org/abs/2609.01836
- Auditing Provenance Sensitivity in LLM Agent Action Selection: https://arxiv.org/abs/2607.20827
- Authenticated Delegation and Authorized AI Agents: https://arxiv.org/abs/2501.09674
- IETF, AI Agent Authentication and Authorization (AIMS): https://www.ietf.org/archive/id/draft-klrc-aiagent-auth-02.html
- IETF, AI Agent Authorization Integration Framework: https://datatracker.ietf.org/doc/html/draft-liu-ai-agent-authorization-integration-00
- OWASP: https://cheatsheetseries.owasp.org/cheatsheets/Transaction_Authorization_Cheat_Sheet.html

Sections are identified from the public manuscripts inspected. Titles,
version dates and section numbering should be checked again against the
versions cited in a final submission. No unsupported bibliography date
should be inferred from a venue year or a secondary citation.
