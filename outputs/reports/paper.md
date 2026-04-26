# Constraint-Aware Agents under the SAFE Framework: An Empirical Study on τ³-bench

**Author:** Paulo Lacerda
**Repository:** [`placerda/safe-experimentation`](https://github.com/placerda/safe-experimentation)
**Run analyzed:** `outputs/runs/20260425_112848/` (30 tasks × 2 variants = 60 evaluations)

---

## Abstract

Tool-using LLM agents are increasingly deployed in customer-service
settings where *task completion* must coexist with *constraint
compliance* — staying within authorized actions, basing decisions on
verified evidence, following correct step ordering, and escalating
when appropriate. We operationalize the four-dimensional **SAFE
framework** (Scope, Anchored Decisions, Flow Integrity, Escalation) as
rule-based evaluators over agent traces, apply it to 30 customer
service tasks drawn from τ³-bench (15 airline + 15 retail), and
compare a *baseline* prompt that targets task completion against a
*SAFE-aware* prompt that injects per-task scope and policy guidance.
The SAFE-aware variant raises overall SAFE compliance from 0.677 to
0.734 (+0.057, paired Wilcoxon p=0.18, effect r=0.36) **without
reducing task-completion rate** (0.90 in both variants). Gains are
concentrated in *Scope* (+0.13 retail, +0.13 airline) and *Escalation*
(+0.20 airline). We additionally report a controlled iteration
showing that surfacing the per-task allowed-tool list directly inside
the prompt is the dominant lever — recovering an earlier retail
regression in three of four targeted tasks (mean 0.578 → 0.714).
We release the full pipeline (annotations, evaluators, traces,
analysis scripts) for reproducibility and extension.

## 1. Introduction

LLM agents that invoke tools to act in the world cannot be evaluated
on task success alone. An agent that books the right reservation by
charging an unauthorized payment method, or that resolves a refund by
inventing facts the user did not provide, is not actually solving the
underlying problem — it is solving a different one. **Responsible
agentic systems** therefore require evaluation along constraint
dimensions that operate orthogonally to task success.

The **SAFE framework** [\[1\]](#references) decomposes responsible
agent behavior into four observable dimensions:

- **Scope** — the agent only invokes actions and tools that are
  explicitly allowed for the task and policy.
- **Anchored Decisions** — decisions are anchored in evidence that
  was actually produced by tool calls; no fabrication, no unjustified
  acceptance of unverified user claims.
- **Flow Integrity** — required steps occur, and they occur in the
  required order (e.g. authenticate before mutating user state).
- **Escalation** — when triggers fire (out-of-policy requests,
  insufficient information, policy conflicts), the agent asks,
  refuses, or transfers to a human.

τ³-bench [\[2\]](#references) provides realistic customer-service
domains (airline, retail, telecom) with simulated users and a tool
catalog, but its built-in evaluation is *task-completion oriented*.
This paper asks: **does prompt-level constraint awareness improve
SAFE compliance without sacrificing task-completion?** We answer
empirically on a 30-task subset and show that the answer is yes,
provided the prompt is bound to per-task scope at runtime.

## 2. Experimental Setup

### 2.1 Tasks and annotations

We selected 30 tasks (15 airline, 15 retail) from τ³-bench
representing a spread of constraint exercises (scope-stress, anchored
decision-stress, flow-integrity, and escalation triggers). For each
task we authored a YAML annotation
(`data/annotations/{airline,retail}.safe.yaml`) containing the four
SAFE blocks: `allowed_actions` and `disallowed_actions` for Scope;
required evidence and forbidden assumptions for Anchored Decisions;
ordered required steps for Flow Integrity; and trigger conditions
plus expected escalation behaviors for Escalation. Annotations are
validated by `scripts/validate_annotations.py` against a Pydantic
schema (`src/safe_benchmark/annotation_schema.py`).

### 2.2 Agent variants

Both variants run the same Azure OpenAI deployment with temperature 0
and identical user-simulator settings. They differ only in the agent
system prompt:

- **Baseline** (`configs/agents/baseline.prompt.md`) — generic
  customer-service instructions, no SAFE language.
- **SAFE-aware** (`configs/agents/safe-aware.prompt.md`) — SAFE
  framework rules covering Scope, Anchored Decisions, Flow Integrity,
  and Escalation, **plus a per-task scope binding appended at
  runtime** that lists the annotation's `allowed_actions` and
  `disallowed_actions` verbatim.
  The per-task binding was added after a diagnostic run revealed that
  generic scope language in the prompt was insufficient when the tool
  catalog itself was not constrained (§4.2).

### 2.3 Evaluators

Four rule-based evaluators in
`src/safe_benchmark/evaluators/` consume the trace plus annotation
and emit a result with `score ∈ [0,1]`, `passed`, `reason`, and
`evidence`:

- **Scope** — penalizes tool calls outside `allowed_actions` and
  inside `disallowed_actions`.
- **Anchored Decisions** — checks that decisions cite evidence from
  prior tool outputs and that no forbidden assumptions appear.
- **Flow Integrity** — checks presence and ordering of required
  steps.
- **Escalation** — checks that the agent ask/refuse/transfer when
  triggers fire.

Per-task `safe_overall` is the unweighted mean of the four scores.
Rule-based evaluators were chosen over LLM-as-judge to ensure
transparency and reproducibility; `reason` and `evidence` make every
score auditable.

### 2.4 Run pipeline

`scripts/run_experiment.py` iterates the 30 tasks × 2 variants,
producing 60 traces, evaluating each one, and writing
`results.json`, `report.md`, and per-trace JSON to
`outputs/runs/<timestamp>/`. Aggregation, statistical tests,
visualizations, and qualitative example extraction are produced by
`scripts/analyze_results.py` and `scripts/enrich_paper_examples.py`.

## 3. Results

### 3.1 Headline numbers

| Group                  | n  | SAFE overall | Scope  | Anchored | Flow   | Escalation | Task completed |
|------------------------|----|--------------|--------|----------|--------|------------|----------------|
| airline / baseline     | 15 | 0.602        | 0.467  | 0.760    | 0.517  | 0.667      | 1.000          |
| airline / safe-aware   | 15 | **0.699**    | 0.600  | 0.796    | 0.533  | 0.867      | 0.867          |
| retail  / baseline     | 15 | 0.752        | 0.733  | 0.897    | 0.512  | 0.867      | 0.800          |
| retail  / safe-aware   | 15 | **0.769**    | 0.867  | 0.858    | 0.486  | 0.867      | 0.933          |
| **all / baseline**     | 30 | 0.677        | 0.600  | 0.828    | 0.515  | 0.767      | 0.900          |
| **all / safe-aware**   | 30 | **0.734**    | 0.733  | 0.827    | 0.510  | 0.867      | 0.900          |

The SAFE-aware variant improves overall SAFE compliance by **+0.057**
absolute (+8.5% relative) **with identical task completion**.

### 3.2 Statistical analysis

Paired tests over the 30 tasks (script:
`scripts/analyze_results.py`, full report in
`outputs/reports/statistical_analysis.md`). Wilcoxon signed-rank used
where ≥6 non-zero pairs, sign test otherwise. Confidence intervals are
percentile bootstrap (10 000 resamples). Holm-Bonferroni applied
across the four exploratory dimension tests within each domain.

| Stratum  | Dimension       | n  | mean Δ  | 95 % CI            | p (raw) | effect r |
|----------|-----------------|----|---------|--------------------|---------|----------|
| Combined | safe_overall    | 18 | +0.057  | [−0.006, +0.119]   | 0.18    | 0.36     |
| Combined | scope           |  4 | +0.133  | [+0.033, +0.267]   | 0.13    | n/a      |
| Combined | escalation      |  9 | +0.100  | [−0.100, +0.300]   | 0.32    | 0.33     |
| Airline  | safe_overall    | 11 | +0.096  | [−0.008, +0.201]   | 0.13    | **0.52** |
| Airline  | escalation      |  7 | +0.200  | [−0.133, +0.533]   | 0.26    | 0.43     |
| Retail   | safe_overall    |  7 | +0.017  | [−0.049, +0.088]   | 0.61    | 0.21     |

No test crosses the conventional p<0.05 threshold under the
Holm-Bonferroni correction at n=30, but every point estimate for the
primary endpoint is positive, the lower CI bound is near zero on
combined and airline data, and the airline effect size r=0.52 is in
the *moderate-to-large* range. We frame the study as an exploratory
benchmark; the sample is intentionally small to keep evaluation
costs and annotation effort tractable, and the reported numbers
should be read as *direction-of-effect evidence* rather than
confirmatory inference.

### 3.3 Per-task structure

Figure 1 (`outputs/reports/figures/paired_scores.png`) plots each
task's SAFE overall under both variants, colored by the sign of the
delta. Airline shows a cluster of meaningful improvements
(airline_026 +0.46, airline_035 +0.50, airline_001 +0.25,
airline_005 +0.25, airline_000 +0.25). Retail shows
fewer-but-larger movements (retail_000 +0.25, retail_076 +0.25,
retail_107 +0.25; retail_014 −0.25). Figure 2
(`dimension_breakdown.png`) shows the per-dimension means; the
largest visible gap is on Scope and Escalation, with Anchored
Decisions and Flow Integrity essentially flat. Figure 3
(`delta_distribution.png`) shows the right-skewed distribution of
deltas. Figure 4 (`divergence_scatter.png`) plots task-completion
against SAFE compliance and highlights divergence cases — including
two retail baseline traces where the task was not completed yet
SAFE compliance was high (the agent refused to act on insufficient
information, which is *correct* SAFE behavior even though
task-completion fails to reward it).

### 3.4 Qualitative examples

`outputs/reports/paper_examples.md` reports the top variant
differences and divergence cases with conversation excerpts and
tool-call comparisons. Two illustrative cases:

- **airline_035 (+0.50, safe-aware better).** Baseline agent makes a
  flight modification before verifying user identity (flow_integrity
  failure) and proceeds without confirming policy on free-changes
  (anchored_decisions failure). SAFE-aware agent first calls
  `find_user_id_by_*`, inspects the reservation, quotes the policy
  back to the user, and confirms before acting.
- **retail_030 (scope dimension fixed by per-task binding).** In the
  earlier prompt iteration, the SAFE-aware agent invoked
  `exchange_delivered_order_items` and `transfer_to_human_agents`
  even though neither was in this task's `allowed_actions`. After
  surfacing the per-task allowed-tool list directly in the prompt,
  the agent stayed within scope while still completing the task,
  raising scope from 0.00 to 1.00.

## 4. Discussion

### 4.1 Constraint awareness need not cost task completion

Both variants completed 90 % of tasks, despite the SAFE-aware variant
being instructed to *prefer constrained behavior over forced
completion* and to escalate aggressively. Within the airline domain,
the SAFE-aware variant did slightly under-complete (0.87 vs 1.00),
which is the expected price of stricter escalation behavior. In the
retail domain it actually *over-completed* relative to baseline
(0.93 vs 0.80) — when the baseline failed because it tried to act on
incomplete information and stalled, the SAFE-aware variant succeeded
because it explicitly asked.

### 4.2 Prompt-level scope alone is not enough

Our diagnostic run
(`outputs/reports/retail_regression_diagnostic.md`) showed that
generic prompt language like *"only use tools available to you"* did
not prevent scope violations when the tool catalog exposed at runtime
included tools the policy disallowed. The fix
(`outputs/reports/scope_binding_validation.md`) was not to rewrite
the prompt's wording but to **bind the prompt to the per-task
allowed-tool list** at runtime. The validation re-run on the four
regressing retail tasks showed mean SAFE 0.578 → 0.714 (+0.135), and
the largest single scope failure (retail_030) recovered fully. This
is consistent with SAFE's premise that constraints should be enforced
at multiple layers; prompt-level guidance is necessary but not
sufficient when the tool surface is unconstrained.

### 4.3 What still does not work

- **retail_010** still fails flow_integrity in both variants. The
  user simulator provides identity information conversationally and
  the agent skips the explicit `authenticate_user_identity` tool
  call. A stricter prompt clause (*"your first tool call must be
  identity verification"*) is a likely fix that we have not yet
  validated.
- **Anchored Decisions and Flow Integrity** are the two dimensions
  where prompt awareness moved the needle least. Both depend on
  multi-step procedural compliance, which our current evaluators
  detect by string-matching against required step names. A more
  expressive procedural specification (e.g. allowable subgraphs of
  ordered actions) would likely yield more discriminative scores
  and reveal effects the current evaluators miss.

### 4.4 Threats to validity

- **Sample size (n=30).** Sufficient for direction-of-effect
  exploration; insufficient for confirmatory inference. Larger runs
  are constrained by τ³-bench evaluation cost and annotation effort.
- **LLM sampling noise.** Even at temperature 0, run-to-run
  variation exists (we observed retail_030 baseline 1.00 → 0.50
  across two runs without prompt change). The paired design with
  Wilcoxon mitigates but does not eliminate this.
- **Single agent model.** All numbers are from one Azure OpenAI
  deployment. Generalization to other model families is future work.
- **Human authorship of annotations.** The annotation YAMLs encode
  one author's interpretation of the task policies. We mitigate this
  with the validation script and by keeping annotations versioned
  alongside the code, so disagreement can be tracked.

## 5. Related Work

- **SAFE framework** [\[1\]](#references) introduces the four
  dimensions we operationalize.
- **τ³-bench** [\[2\]](#references) provides the simulated tool-use
  domains and user simulator we evaluate on.
- **τ-bench / agent benchmarks** evaluate task completion;
  constraint-aware evaluation has previously been done with
  LLM-as-judge approaches (e.g. AgentBench), which trades
  reproducibility for flexibility. We chose rule-based evaluators
  precisely to keep evidence and reasoning auditable.

## 6. Conclusion

A SAFE-aware prompt that binds the model to per-task scope at runtime
improves SAFE compliance over a task-completion baseline (+0.057
overall) **without reducing task completion**. Improvements are
concentrated in Scope and Escalation, with the largest single fix
recovering a scope violation that the prompt alone could not
prevent. The result supports a two-layer view of constraint
enforcement — prompt rules *and* per-task tool binding — and
demonstrates that responsible-agent design is compatible with
practical task performance on customer-service workloads.

## 7. Reproducibility

```bash
git clone https://github.com/placerda/safe-experimentation
cd safe-experimentation
python -m venv .venv && .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # add Azure OpenAI credentials
python scripts/setup_tau3.py
python scripts/run_experiment.py
python scripts/analyze_results.py
python scripts/enrich_paper_examples.py --latest
```

All numbers in this paper come from `outputs/runs/20260425_112848/`.

## References

[1] *SAFE: Designing Responsible Agentic Systems.* TowardsAI, Mar 6, 2026.
    <https://pub.towardsai.net/safe-designing-responsible-agentic-systems-3dcc27075d4b>

[2] Sierra Research. *τ³-bench / tau2-bench.*
    <https://github.com/sierra-research/tau2-bench>
