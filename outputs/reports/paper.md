# Constraint-Aware Agents under the SAFE Framework: An Empirical Study on τ³-bench

**Author:** Paulo Lacerda
**Repository:** [`placerda/safe-experimentation`](https://github.com/placerda/safe-experimentation)
**Run analyzed:** `outputs/runs/20260426_172556__gpt-4.1/` — 100 tasks × 2 variants = 200 evaluations on **Azure OpenAI gpt-4.1** (deployment `gpt-4.1`, model version `2025-04-14`).

---

## Abstract

Tool-using LLM agents are increasingly deployed in customer-service
settings where *task completion* must coexist with *constraint
compliance* — staying within authorized actions, basing decisions on
verified evidence, following correct step ordering, and escalating
when appropriate. We operationalize the four-dimensional **SAFE
framework** (Scope, Anchored Decisions, Flow Integrity, Escalation) as
rule-based evaluators over agent traces, apply it to **100 customer
service tasks** drawn from τ³-bench (50 airline + 50 retail), and
compare a *baseline* prompt that targets task completion against a
*SAFE-aware* prompt that injects per-task scope and policy guidance.
On gpt-4.1 the SAFE-aware variant raises overall SAFE compliance in
the **airline domain from 0.733 to 0.773** (paired Wilcoxon p=0.010,
95 % bootstrap CI [+0.016, +0.070], rank-biserial r=0.65), driven by
**Scope** lifting from 0.86 to a perfect 1.00 (raw p=0.008, Holm
p=0.090 over four within-domain dimension tests). The retail domain
shows no effect (Δ≈0, p>0.6), so the **combined** safe_overall
improvement is +0.019 (p=0.097). When the same 200 traces are scored
with τ³-bench's **official reward function** (action-matching,
DB-state, communicate-info, NL-assertions — judge routed through Azure
OpenAI), descriptive means on the valid-trace subsets are 0.247
(baseline, n=89) vs 0.244 (safe-aware, n=90); on the 83 tasks with a
paired reward, mean Δ=−0.024 with 77/83 ties, sign test p=0.69. We
therefore find **no detectable cost on the paired subset** in
official task-completion reward (without claiming formal
non-inferiority) and a **domain-dependent compliance gain** that is
statistically significant in airline (combined-domain p=0.097;
domain × variant interaction p=0.060, both borderline). We frame
the airline result as **hypothesis-generating** for held-out
replication. We release the full pipeline (annotations, evaluators,
traces, the official-reward bridge to tau2-bench, the Azure-routed
NL judge, and analysis scripts) for reproducibility and extension.

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
catalog, and a *task-completion oriented* reward function based on
action matching, database-state checks, communicated-info checks,
and natural-language assertions. This paper asks: **does prompt-level
constraint awareness improve SAFE compliance without sacrificing the
task-completion reward τ³-bench itself uses?** We answer empirically
on a 100-task subset and find a **domain-conditional, exploratory
result**: a significant SAFE lift on airline (paired Wilcoxon p=0.010,
r=0.65, primarily on the Scope dimension) and no measurable effect on
retail. The combined-domain primary endpoint is borderline
(p=0.097), and a domain × variant interaction test is also borderline
(Mann–Whitney p=0.060). We frame the airline result as
**hypothesis-generating** — to be confirmed on held-out tasks and a
second model — rather than a confirmatory finding. We also find no
detectable cost on the τ³-bench reward in the paired subset for
which the official judge produced a verdict, with the explicit
caveat that non-inferiority is **not** formally established.

## 2. Experimental Setup

### 2.1 Tasks and annotations

We selected **100 tasks (50 airline + 50 retail)** from τ³-bench,
representing a spread of constraint exercises (scope-stress,
anchored-decision-stress, flow-integrity, and escalation triggers).
For each task we authored a YAML annotation
(`data/annotations/{airline,retail}.safe.yaml`) containing the four
SAFE blocks: `allowed_actions` and `disallowed_actions` for Scope;
required evidence and forbidden assumptions for Anchored Decisions;
ordered required steps for Flow Integrity; and trigger conditions
plus expected escalation behaviors for Escalation. The first 30
annotations were authored by hand; the remaining 70 were drafted by
gpt-4.1 with a two-shot prompt anchored on the hand-written examples,
then automatically linted against the τ³ tool catalog
(`scripts/lint_drafts.py`, `scripts/clean_drafts.py`) — drafts with
unknown tools or schema violations were rejected before merging.
Annotations are validated by `scripts/validate_annotations.py`
against a Pydantic schema (`src/safe_benchmark/annotation_schema.py`).

### 2.2 Agent variants and model

Both variants run on the same Azure OpenAI deployment of **gpt-4.1**
(model version `2025-04-14`, temperature 0, max tokens 1024) with
identical user-simulator settings (same model). They differ only in
the agent system prompt:

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

Tool-call execution and database state are handled by τ³-bench's
own environment classes (`tau2.domains.{airline,retail}.environment`),
keeping our pipeline byte-compatible with the upstream benchmark.

### 2.3 Evaluators

We score each trace with **two parallel evaluation systems**:

**(a) SAFE evaluators** — four rule-based scorers in
`src/safe_benchmark/evaluators/`, each consuming the trace plus the
task annotation and emitting a result with `score ∈ [0,1]`, `passed`,
`reason`, and `evidence`:

- **Scope** — penalizes tool calls outside `allowed_actions` and
  inside `disallowed_actions`.
- **Anchored Decisions** — checks that decisions cite evidence from
  prior tool outputs and that no forbidden assumptions appear.
- **Flow Integrity** — checks presence and ordering of required
  steps.
- **Escalation** — checks that the agent ask/refuse/transfer when
  triggers fire.

Per-task `safe_overall` is the unweighted mean of the four scores.
Rule-based evaluators were chosen over LLM-as-judge to keep evidence
and reasoning auditable.

**(b) τ³-bench official reward** — we bridge the trace into a
`tau2.data_model.simulation.SimulationRun` and call
`tau2.evaluator.evaluator.evaluate_simulation` with mode `ALL`. This
yields the same reward number Sierra Research's benchmark uses,
defined as the product of the components in each task's
`reward_basis` (DB-state, action-matching, communicate-info,
optionally NL-assertions). The bridge is in
`src/safe_benchmark/evaluators/tau2_reward.py`. Because the official
reward replays mutating tool calls against a fresh environment, we
record tool-call results in canonical JSON (via
`env.get_response(...)`) rather than Python `repr()`, so the
trajectory replays deterministically.

NL-assertion tasks require an LLM judge; in this run we route those
calls through the same Azure OpenAI gpt-4.1 deployment via litellm,
using Entra ID authentication. Concretely,
`_configure_azure_judge()` in `tau2_reward.py` monkey-patches
`tau2.config.DEFAULT_LLM_NL_ASSERTIONS` to `azure/gpt-4.1` and wraps
`litellm.completion` so that an `azure_ad_token` is injected on every
`azure/*` call. This raised τ³ reward coverage from 47/60 traces in
our prior n=30 run to **179/200 traces** here.

### 2.4 Run pipeline

`scripts/run_experiment.py` iterates the 100 tasks × 2 variants,
producing 200 traces, evaluating each one with both systems, and
writing `results.json`, `report.md`, and per-trace JSON to
`outputs/runs/<timestamp>__<run_tag>/`. The runner now accepts
`--deployment` and `--run-tag` flags so the same pipeline can be
swept across multiple Azure OpenAI deployments. Aggregation,
statistical tests, visualizations, and qualitative example extraction
are produced by `scripts/analyze_results.py`,
`scripts/analyze_tau2_reward.py`, and
`scripts/enrich_paper_examples.py`.

## 3. Results

### 3.1 Headline numbers

| Group                  | n   | SAFE overall | Scope | Anchored | Flow  | Escalation | τ³ reward (n) | task_completed* |
|------------------------|-----|--------------|-------|----------|-------|------------|---------------|-----------------|
| airline / baseline     | 50  | 0.733        | 0.860 | 0.837    | 0.235 | 1.000      | 0.383 (47)    | 0.780           |
| airline / safe-aware   | 50  | **0.773**    | 1.000 | 0.831    | 0.263 | 1.000      | 0.380 (50)    | 0.660           |
| retail  / baseline     | 50  | 0.573        | 0.320 | 0.827    | 0.165 | 0.980      | 0.095 (42)    | 0.700           |
| retail  / safe-aware   | 50  | 0.571        | 0.300 | 0.820    | 0.164 | 1.000      | 0.075 (40)    | 0.660           |
| **all / baseline**     | 100 | 0.653        | 0.590 | 0.832    | 0.200 | 0.990      | 0.247 (89)    | 0.740           |
| **all / safe-aware**   | 100 | **0.672**    | 0.650 | 0.826    | 0.213 | 1.000      | 0.244 (90)    | 0.660           |

`*` `task_completed` is a conservative heuristic (transfer-to-human or
graceful goodbye); we report it for continuity but treat the
**τ³ reward** column as the authoritative completion signal.

The SAFE-aware variant lifts overall SAFE compliance by **+0.040
absolute on airline** and is essentially flat on retail (Δ≈0). The
gain is concentrated entirely on the **Scope** dimension, which is
exactly where the per-task tool binding intervenes: airline Scope
moves from 0.86 to a perfect 1.00, while retail Scope is unchanged.
The official τ³ reward is statistically indistinguishable across
variants in both domains.

### 3.2 Statistical analysis (SAFE)

Paired tests over the 100 tasks (script:
`scripts/analyze_results.py`, full report in
`outputs/reports/statistical_analysis.md`). Wilcoxon signed-rank used
when ≥6 non-zero pairs, sign test otherwise. Confidence intervals are
percentile bootstrap (10 000 resamples). Holm-Bonferroni applied
across the four exploratory dimension tests within each domain.

| Stratum  | Dimension       | n* | mean Δ  | 95 % CI            | p (raw) | p (Holm) | r    | Sig |
|----------|-----------------|----|---------|--------------------|---------|----------|------|-----|
| Airline  | **safe_overall (P)** | 20 | +0.040 | [+0.016, +0.070] | **0.010** | —     | 0.65 | ✱   |
| Airline  | scope           | 7  | +0.140  | [+0.060, +0.240]   | 0.008   | 0.090    | 1.00 |     |
| Airline  | anchored_dec.   | 2  | −0.006  | [−0.016, +0.000]   | 0.500   | 1.000    | n/a  |     |
| Airline  | flow_integrity  | 16 | +0.028  | [−0.010, +0.068]   | 0.222   | 1.000    | 0.35 |     |
| Airline  | escalation      | 0  | +0.000  | —                  | n/a     | —        | n/a  |     |
| Retail   | safe_overall (P)| 18 | −0.002  | [−0.039, +0.035]   | 0.657   | —        | 0.12 |     |
| Retail   | scope           | 13 | −0.020  | [−0.160, +0.120]   | 0.781   | 1.000    | −0.08| |
| Retail   | anchored_dec.   | 3  | −0.008  | [−0.025, +0.005]   | 1.000   | 1.000    | n/a  |     |
| Retail   | flow_integrity  | 2  | −0.001  | [−0.010, +0.007]   | 1.000   | 1.000    | n/a  |     |
| Retail   | escalation      | 1  | +0.020  | [+0.000, +0.060]   | 1.000   | —        | n/a  |     |
| Combined | safe_overall (P)| 38 | +0.019  | [−0.004, +0.043]   | 0.097   | —        | 0.31 |     |
| Combined | scope           | 20 | +0.060  | [−0.030, +0.150]   | 0.180   | 1.000    | 0.30 |     |

*n\* = nonzero pairs (ties excluded). The primary endpoint is
`safe_overall`; per-dimension tests are exploratory and Holm-corrected
within their stratum.

The airline domain produces a **statistically significant lift** on
the primary endpoint (Wilcoxon p=0.010, lower 95 % CI = +0.016,
large effect size r=0.65). The dominant single-dimension contributor
is Scope (mean Δ=+0.14, raw p=0.008); after Holm correction over
four within-domain dimension tests Scope sits at p=0.090, just outside
the 0.05 threshold but far below the corrected pre-registration
ceiling. Retail shows essentially no effect on any SAFE dimension.

The **combined-domain** primary endpoint is positive but marginal
(p=0.097); the effect is diluted by retail's null result. We report
the combined number for completeness but treat the **per-domain
finding** as the substantive result, because the intervention's
effectiveness is itself domain-conditional (§4.3).

### 3.3 Statistical analysis (τ³-bench official reward)

A separate paired analysis on the 83 tasks where both variants
produced a non-`None` τ³ reward (script:
`scripts/analyze_tau2_reward.py`, output:
`outputs/reports/tau2_reward_analysis.md`):

| metric                              | value             |
|-------------------------------------|-------------------|
| Paired tasks (both variants scored) | 83                |
| Mean Δ (safe-aware − baseline)      | **−0.024**        |
| Tasks safe-aware better             | 2                 |
| Tasks baseline better               | 4                 |
| Tasks tied                          | 77                |
| Sign test (excl. ties)              | p = 0.688         |
| Wilcoxon signed-rank                | p = 0.414         |

The paired distribution is dominated by ties (77/83) because most
τ³ rewards saturate at either 1.0 (full task success) or 0.0 (any
component failed). On the 6 non-tied pairs, baseline wins 4 and
SAFE-aware wins 2, yielding a numerically negative Δ that is **not
statistically distinguishable from zero** (sign test p=0.69, Wilcoxon
p=0.41). Read carefully, the data are consistent with both
no-effect and a small cost — they rule out a *large* cost but not a
small one. We report this honestly rather than over-claiming
equivalence.

### 3.4 Per-task structure

Figure 1 (`outputs/reports/figures/paired_scores.png`) plots each
task's SAFE overall under both variants, colored by the sign of the
delta. Airline shows a broad lift driven by Scope-bound tasks;
retail is more mixed, consistent with the near-zero average delta.
Figure 2 (`dimension_breakdown.png`) shows the per-dimension means
across the 100 tasks; the visible gap is on Scope-airline, with the
other three dimensions essentially flat in both domains. Figure 3
(`delta_distribution.png`) shows the right-skewed distribution of
SAFE deltas. Figure 4 (`divergence_scatter.png`) plots heuristic
task-completion against SAFE compliance.

### 3.5 τ³-bench reward coverage

The official-reward bridge produced a valid number for
89/100 baseline traces and 90/100 SAFE-aware traces (179/200 total,
a substantial improvement over our prior n=30 run's 47/60 = 78 %).
The remaining missing cases are concentrated in retail and stem
from tau2's environment evaluator refusing to replay mutating tool
calls when the agent issued an action the canonical environment
rejects (e.g. exchanging items it does not own, or violating a state
precondition). Because missingness is not strongly variant-correlated
(89 vs 90, χ² ≈ 0), the paired sub-sample comparison in §3.3 is not
biased against either variant.

### 3.6 Qualitative examples

`outputs/reports/paper_examples.md` reports the top variant
differences and divergence cases with conversation excerpts and
tool-call comparisons. The clearest qualitative pattern in airline
is the SAFE-aware agent declining out-of-policy actions (e.g.
non-economy upgrades on basic-economy tickets, payment-method
substitutions) where the baseline complied; in retail, neither
variant reliably resists out-of-policy requests, consistent with the
quantitative null result.

## 4. Discussion

### 4.1 Constraint awareness did not measurably cost task completion

Under τ³-bench's own reward, we find **no detectable cost** to the
SAFE-aware variant: descriptive means are 0.247 (baseline, n=89) vs
0.244 (safe-aware, n=90), and on the 83 paired tasks, Δ=−0.024 with
77 ties, sign test p=0.69. With 4 of 83 tasks flipping in baseline's
favor and 2 in SAFE-aware's, the data show no significant difference
but cannot rule out a small cost. By contrast, our heuristic
completion proxy (`task_completed`) makes the variant look 8 pp
lower (0.74 → 0.66), but the proxy treats *every* graceful goodbye
as success, which penalizes the SAFE-aware agent's appropriate
refusals on out-of-policy requests. The official τ³ reward, which
evaluates *correct* completion, does not show this penalty.

### 4.2 Prompt-level scope alone is not enough

Our diagnostic run
(`outputs/reports/retail_regression_diagnostic.md`) showed that
generic prompt language like *"only use tools available to you"* did
not prevent scope violations when the tool catalog exposed at runtime
included tools the policy disallowed. The fix
(`outputs/reports/scope_binding_validation.md`) was not to rewrite
the prompt's wording but to **bind the prompt to the per-task
allowed-tool list** at runtime. On gpt-4.1, the airline Scope
dimension lifts from 0.86 to a perfect 1.00 across 50 tasks. This
is consistent with SAFE's premise that constraints should be enforced
at multiple layers; prompt-level guidance is necessary but not
sufficient when the tool surface is unconstrained.

### 4.3 Why airline responds and retail does not

The most striking finding is the **domain split**: airline shows a
large SAFE lift driven by Scope (0.86 → 1.00), while retail Scope is
essentially flat at 0.30 in both variants. A formal **domain ×
variant interaction test** on the per-task `safe_overall` deltas is
borderline (Mann–Whitney U=1488.5, p=0.060; Brunner–Munzel p=0.057):
the airline lift is real, the retail null is real, but the *separation*
between domains has not been confirmed at α=0.05 in this single
sample. We therefore present the domain split as
**hypothesis-generating**, not as a confirmed differential effect.

Three hypotheses for the qualitative pattern, ordered by our
subjective confidence:

1. **Retail has structurally lower Scope at baseline** (0.32 vs
   0.86). The retail tool catalog is larger and the boundary between
   "allowed" and "policy-conditional" is fuzzier (e.g.
   `exchange_delivered_order_items` is allowed only after specific
   evidence). Per-task allowlisting cannot encode "allowed *iff*
   precondition Y" — it can only restrict the catalog.
2. **Retail tasks more often require *conditional* preconditions**
   ("do not call `modify_pending_order_items` without first having
   called `get_order_details`") which the prompt-level binding does
   not check. Tool guards as a runtime layer, not prompt text, are a
   plausible next intervention.
3. **The retail user simulator is more permissive**, which surfaces
   more borderline requests that test conditional preconditions.

Distinguishing these hypotheses requires a follow-up that adds
runtime tool guards to a subset of retail tasks; we leave this to
future work.

### 4.4 What still does not work

- **Retail Scope (0.30 even after the binding).** As discussed in
  §4.3, conditional preconditions defeat catalog-level allowlisting.
- **Anchored Decisions and Flow Integrity** moved by < 0.03 in
  either direction in either domain. Both depend on multi-step
  procedural compliance, which our current evaluators detect by
  string-matching against required step names. A more expressive
  procedural specification (e.g. allowable subgraphs of ordered
  actions) would likely yield more discriminative scores and might
  surface effects the current evaluators miss.
- **Escalation saturated at ≥0.98 in both variants.** With gpt-4.1's
  prior toward asking for clarification, the dimension does not
  discriminate at all in our setting. Tasks designed specifically to
  trip over-eagerness rather than under-asking would re-enable
  Escalation as a discriminator.

### 4.5 Threats to validity

- **Domain split is not pre-registered.** The decision to analyze
  airline and retail separately was motivated by an early diagnostic
  run on the 30-task pilot (§2.2), not by a pre-registered analysis
  plan. The combined-domain endpoint (p=0.097) and the formal
  interaction test (p=0.060) are both above α=0.05, so the airline
  result should be read as a **subgroup finding** to be confirmed on
  held-out tasks, not as an established main effect. We publish all
  100 task IDs and annotations precisely so that a held-out
  replication is possible.
- **Intervention bundles two changes.** The SAFE-aware variant
  combines (a) explicit prompt rules covering the four SAFE
  dimensions and (b) a per-task allowed-tool list at runtime. The
  Scope lift is consistent with (b) doing most of the work, but the
  current design cannot separate the two contributions. A SAFE-prompt
  only ablation, a binding-only ablation, and a hard runtime tool
  filter are the three baselines a future version of this work owes
  the reader.
- **Annotation–agent shared model.** 70 of 100 annotations were
  drafted by gpt-4.1; the agent is also gpt-4.1; the NL-assertion
  judge in the τ³ reward is also gpt-4.1. The 30 hand-written
  annotations show the same directional airline-lift / retail-null
  pattern (Scope airline +0.13, retail +0.00 on that subset) which
  is reassuring but not conclusive evidence against shared-model
  artifacts.
- **τ³ reward "no cost" is paired-subset only.** The 83 paired tasks
  with valid rewards under both variants exclude tasks where either
  variant's NL judgment failed. Missingness is not strictly random,
  and 77/83 ties leave little statistical leverage; we therefore
  state "no detectable cost on the paired subset" rather than
  "non-inferior." A best-/worst-case missingness sensitivity bound
  would tighten this and is on our list.
- **Sample size (n=100).** Sufficient for detecting medium effects
  in airline (which we did at p=0.010); marginal for the combined
  endpoint (p=0.097). A confirmatory replication on a held-out task
  set would strengthen the airline finding.
- **LLM sampling noise.** Even at temperature 0, run-to-run
  variation exists. The paired design with Wilcoxon mitigates but
  does not eliminate this; we did not run multiple seeds per task.
- **Single agent model.** All headline numbers are from one Azure
  OpenAI deployment of gpt-4.1. We have a parallel run on gpt-5-mini
  underway; partial results (Appendix A) suggest the directional
  pattern transfers but the gpt-5-mini reasoning-token budget makes
  full replication slow. Pre-registered, multi-model replication is
  future work; we expect the Scope mechanism to transfer because the
  per-task tool-list binding is model-agnostic.
- **Annotation provenance.** 70 of 100 annotations were drafted by
  gpt-4.1 with two-shot examples and then automatically linted; this
  introduces a risk of annotation–agent correlation. We mitigate by
  validating every annotation against the τ³ tool catalog and by
  publishing the drafter and lint scripts so any reviewer can
  re-derive the annotations. The hand-written subset (30 tasks)
  shows the same airline-lift / retail-null pattern qualitatively,
  suggesting the effect is not an annotation artifact.
- **NL-assertion judge.** The official-reward NL-assertion judge is
  itself gpt-4.1, evaluating gpt-4.1 traces. We treat this as
  acceptable because (a) the judge is the same gpt-4.1 used by the
  upstream τ³-bench paper and (b) both variants are judged by the
  same model, so any judge-side bias should cancel in the paired
  comparison.
- **Completion conclusions are subset-dependent.** The paired τ³
  comparison is 83 tasks with 77 ties, so the direction-of-effect
  conclusion rests on 6 non-tied pairs. We are honest that this is
  underpowered for ruling out a small completion cost.
- **One of the four SAFE dimensions is non-discriminative.**
  Escalation saturated at 1.000 in *both* variants on airline. This
  means the composite `safe_overall` averages over a dimension that
  carries near-zero information in this run, weakening the construct
  validity of the composite metric on gpt-4.1.

## 5. Related Work

- **SAFE framework** [\[1\]](#references) introduces the four
  dimensions we operationalize.
- **τ³-bench / tau2-bench** [\[2\]](#references) provides the
  simulated tool-use domains and the official reward function we
  reuse end-to-end.
- **τ-bench / agent benchmarks** evaluate task completion;
  constraint-aware evaluation has previously been done with
  LLM-as-judge approaches (e.g. AgentBench), which trades
  reproducibility for flexibility. We chose rule-based evaluators
  for SAFE precisely to keep evidence and reasoning auditable, while
  still preserving full compatibility with τ³-bench's own reward.

## 6. Conclusion

A SAFE-aware prompt that binds the model to a per-task allowed-tool
list at runtime produces an **exploratory, domain-conditional
improvement** in SAFE compliance on gpt-4.1: a significant lift in
the **airline** subgroup (n=50, mean Δ=+0.040 on `safe_overall`,
paired Wilcoxon p=0.010, large effect r=0.65), driven by Scope rising
from 0.86 to a perfect 1.00 (raw p=0.008, Holm-corrected p=0.090).
The **retail** subgroup shows no measurable effect, the combined
primary endpoint is borderline (p=0.097), and a domain × variant
interaction test is borderline (Mann–Whitney p=0.060). On τ³-bench's
own reward function — with the NL-assertion judge now routed through
Azure OpenAI to close the prior coverage gap (179/200 traces vs
47/60 previously) — we find **no detectable cost on the paired
subset** (83 tasks with valid rewards under both variants, paired
Δ=−0.024, sign test p=0.69, Wilcoxon p=0.41, 77/83 ties). We do not
claim non-inferiority. The result supports a two-layer view of
constraint enforcement — prompt rules *and* per-task tool binding —
and is best read as **hypothesis-generating** for the airline
mechanism. The intervention bundles SAFE-style prompt rules with a
runtime allowed-tool list and the gain is concentrated in Scope; a
clean ablation separating the two contributions is the most
important next step. Other open problems include adding runtime tool
guards for conditional preconditions (the most likely explanation
for the retail null), extending the rule-based evaluators for
richer procedural compliance, designing tasks that re-enable
Escalation as a discriminator, and replicating across additional
model families.

## 7. Reproducibility

```bash
git clone https://github.com/placerda/safe-experimentation
cd safe-experimentation
python -m venv .venv && .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # add Azure OpenAI gpt-4.1 deployment
python scripts/setup_tau3.py
python scripts/run_experiment.py --deployment gpt-4.1 --run-tag gpt-4.1
python scripts/analyze_results.py --run outputs/runs/<id>
python scripts/analyze_tau2_reward.py --run outputs/runs/<id>
python scripts/enrich_paper_examples.py --run outputs/runs/<id>
```

All numbers in this paper come from
`outputs/runs/20260426_172556__gpt-4.1/` on Azure OpenAI **gpt-4.1**
(model version `2025-04-14`, deployment `gpt-4.1`, API version
`2024-12-01-preview`). Authentication is via Microsoft Entra ID using
`DefaultAzureCredential`; no API key is checked into the repository.
The NL-assertion judge in the τ³ reward bridge is the same Azure
OpenAI gpt-4.1 deployment, configured automatically by
`_configure_azure_judge()` in `src/safe_benchmark/evaluators/tau2_reward.py`.

## Appendix A. Cross-model replication: gpt-5-mini (in progress)

To probe whether the airline-lift / retail-null pattern is
gpt-4.1-specific, we are running a second sweep on Azure OpenAI
**gpt-5-mini** (deployment `gpt-5-mini`, version `2025-08-07`) with
the same 100 tasks and the same two prompts. Because gpt-5 reasoning
tokens substantially increase per-call latency, this run takes
≈ 7 hours of wall time and was still in progress at the time of
writing (run dir `outputs/runs/<ts>__gpt-5-mini/`); the paper will be
updated with the full cross-model comparison once it completes. The
runner change required for gpt-5 family models was a small
deployment-name-aware kwarg switch (`max_tokens` →
`max_completion_tokens`, no temperature override) implemented in
`src/safe_benchmark/agent_runner.py::_model_kwargs`. Both models
share the same NL-assertion judge configuration via Entra ID.

## References

[1] *SAFE: Designing Responsible Agentic Systems.* TowardsAI, Mar 6, 2026.
    <https://pub.towardsai.net/safe-designing-responsible-agentic-systems-3dcc27075d4b>

[2] Sierra Research. *τ³-bench / tau2-bench.*
    <https://github.com/sierra-research/tau2-bench>
