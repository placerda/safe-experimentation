# Constraint-Aware Agents under the SAFE Framework: An Empirical Study on τ³-bench

**Author:** Paulo Lacerda
**Repository:** [`placerda/safe-experimentation`](https://github.com/placerda/safe-experimentation)
**Run analyzed:** `outputs/runs/20260426_140931/` — 30 tasks × 2 variants = 60 evaluations on **Azure OpenAI gpt-4.1** (deployment `gpt-4.1`, model version `2025-04-14`).

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
On gpt-4.1, the SAFE-aware variant raises overall SAFE compliance
from 0.658 to 0.697 (+0.039 absolute, paired Wilcoxon p=0.089 on
combined data, 95 % bootstrap CI [+0.000, +0.083]); after
Holm-Bonferroni correction no SAFE test crosses p<0.05, so we treat
these signals as **borderline, exploratory direction-of-effect
evidence** rather than confirmed effects. The numerically dominant
gain is on the **Scope** dimension (0.533 → 0.700, mean Δ=+0.167,
raw p=0.059) and is driven by surfacing each task's
`allowed_actions` list inside the prompt at runtime. When we score
the same traces with τ³-bench's **official reward function**
(action-matching, DB-state, communicated-info), descriptive means
on the valid-trace subsets are 0.409 (n=22 baseline) and 0.440
(n=25 safe-aware); on the 22 tasks where both variants produced a
valid reward, the paired difference is Δ=+0.045 with sign test
p=1.000 and Wilcoxon p=0.564 (19 of 22 ties). We therefore find
**no evidence of a decrease** in official task-completion reward,
but the data are too tied to claim equivalence.We
release the full pipeline (annotations, evaluators, traces, the
official-reward bridge to tau2-bench, analysis scripts) for
reproducibility and extension.

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
action matching, database-state checks, and communicated-info checks.
This paper asks: **does prompt-level constraint awareness improve
SAFE compliance without sacrificing the task-completion reward
τ³-bench itself uses?** We answer empirically on a 30-task subset and
show that the answer is yes for the dominant dimension (Scope),
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

Tasks whose `reward_basis` includes `NL_ASSERTION` need an LLM-judge
call. We did not configure that judge in this run, so those tasks
return `tau2_reward = None`; they are reported separately under
*coverage* (§3.5).

### 2.4 Run pipeline

`scripts/run_experiment.py` iterates the 30 tasks × 2 variants,
producing 60 traces, evaluating each one with both systems, and
writing `results.json`, `report.md`, and per-trace JSON to
`outputs/runs/<timestamp>/`. Aggregation, statistical tests,
visualizations, and qualitative example extraction are produced by
`scripts/analyze_results.py`,
`scripts/analyze_tau2_reward.py`, and
`scripts/enrich_paper_examples.py`.

## 3. Results

### 3.1 Headline numbers

| Group                  | n  | SAFE overall | Scope  | Anchored | Flow   | Escalation | τ³ reward (n)  | task_completed* |
|------------------------|----|--------------|--------|----------|--------|------------|----------------|-----------------|
| airline / baseline     | 15 | 0.739        | 0.800  | 0.787    | 0.370  | 1.000      | 0.538 (13)     | 0.800           |
| airline / safe-aware   | 15 | **0.789**    | 1.000  | 0.787    | 0.370  | 1.000      | **0.600 (15)** | 0.733           |
| retail  / baseline     | 15 | 0.576        | 0.267  | 0.753    | 0.283  | 1.000      | 0.222 (9)      | 0.867           |
| retail  / safe-aware   | 15 | **0.605**    | 0.400  | 0.742    | 0.278  | 1.000      | 0.200 (10)     | 0.800           |
| **all / baseline**     | 30 | 0.658        | 0.533  | 0.770    | 0.327  | 1.000      | 0.409 (22)     | 0.833           |
| **all / safe-aware**   | 30 | **0.697**    | 0.700  | 0.764    | 0.324  | 1.000      | **0.440 (25)** | 0.767           |

`*` `task_completed` is a conservative heuristic (transfer-to-human or
graceful goodbye); we report it for continuity but treat the
**τ³ reward** column as the authoritative completion signal.

The SAFE-aware variant improves overall SAFE compliance by **+0.039**
absolute (+5.9 % relative) and the **τ³-bench official reward by
+0.031** absolute on the union of evaluable tasks (+0.045 on the
n=22 paired subset). The SAFE gain is concentrated entirely on the
**Scope** dimension (+0.167 absolute), which is exactly where the
per-task tool binding intervenes.

### 3.2 Statistical analysis (SAFE)

Paired tests over the 30 tasks (script:
`scripts/analyze_results.py`, full report in
`outputs/reports/statistical_analysis.md`). Wilcoxon signed-rank used
when ≥6 non-zero pairs, sign test otherwise. Confidence intervals are
percentile bootstrap (10 000 resamples). Holm-Bonferroni applied
across the four exploratory dimension tests within each domain.

| Stratum  | Dimension       | n  | mean Δ  | 95 % CI            | p (raw) | effect r |
|----------|-----------------|----|---------|--------------------|---------|----------|
| Combined | safe_overall    | 11 | +0.040  | [+0.000, +0.083]   | 0.089   | 0.58     |
| Combined | scope           |  7 | +0.167  | [+0.000, +0.333]   | 0.059   | 0.71     |
| Combined | anchored_dec.   |  2 | −0.006  | [−0.033, +0.017]   | 1.000   | n/a      |
| Combined | flow_integrity  |  4 | −0.003  | [−0.033, +0.028]   | 1.000   | n/a      |
| Combined | escalation      |  0 | +0.000  | [+0.000, +0.000]   | n/a     | n/a      |
| Airline  | safe_overall    |  4 | +0.050  | [+0.008, +0.100]   | 0.125   | n/a      |
| Retail   | safe_overall    |  7 | +0.029  | [−0.036, +0.100]   | 0.446   | 0.32     |

After Holm-Bonferroni correction over the four within-stratum
dimension tests, no test crosses p<0.05. The two strongest signals
are *Scope combined* (p=0.059, r=0.71) and *safe_overall combined*
(p=0.089, r=0.58). The point estimate for safe_overall is positive
on every stratum; the lower 95 % bootstrap bound on the combined
endpoint is at zero. We frame the study as exploratory; the sample
is intentionally small to keep evaluation costs and annotation
effort tractable, and the reported numbers should be read as
*direction-of-effect evidence* rather than confirmatory inference.

### 3.3 Statistical analysis (τ³-bench official reward)

A separate paired analysis on the 22 tasks where both variants
produced a non-`None` τ³ reward (script:
`scripts/analyze_tau2_reward.py`, output:
`outputs/reports/tau2_reward_analysis.md`):

| metric                              | value             |
|-------------------------------------|-------------------|
| Paired tasks (both variants scored) | 22                |
| Mean Δ (safe-aware − baseline)      | **+0.045**        |
| Tasks safe-aware better             | 2                 |
| Tasks baseline better               | 1                 |
| Tasks tied                          | 19                |
| Sign test (excl. ties)              | p = 1.000         |
| Wilcoxon signed-rank                | p = 0.564         |

The paired distribution is extremely tied (19/22) because most
tasks evaluate to a saturated reward of either 1.0 or 0.0 under
both variants. The non-tied flips favor SAFE-aware 2:1 and lift
the mean reward in absolute terms, but with only 3 non-tied pairs
neither test approaches significance. The honest reading of the
combined evidence is: SAFE compliance is **numerically higher** on
its dominant dimension (Scope, raw p=0.059, non-significant after
correction), and the official τ³ reward shows **no evidence of a
decrease** (paired Δ=+0.045, p=1.000). We therefore conclude that
constraint-aware prompting **did not measurably reduce
task-completion reward** on this benchmark, while explicitly noting
that the paired sample is underpowered and that a true equivalence
claim would require a pre-specified non-inferiority margin.

### 3.4 Per-task structure

Figure 1 (`outputs/reports/figures/paired_scores.png`) plots each
task's SAFE overall under both variants, colored by the sign of the
delta. Airline shows broad lift on Scope-bound tasks. Retail is
more mixed, consistent with the smaller absolute delta. Figure 2
(`dimension_breakdown.png`) shows the per-dimension means; the
visible gap is on Scope, with the other three dimensions essentially
flat. Figure 3 (`delta_distribution.png`) shows the right-skewed
distribution of deltas. Figure 4 (`divergence_scatter.png`) plots
heuristic task-completion against SAFE compliance.

### 3.5 τ³-bench reward coverage and missing cases

The official-reward bridge produced a valid number for
22/30 baseline traces and 25/30 SAFE-aware traces. The 8 + 5 missing
cases break down as:

- **NL_ASSERTION tasks (most of the missingness).** Tasks whose
  `reward_basis` includes `NL_ASSERTION` require tau2's LLM-judge
  backend, which we did not configure; these surface as
  `tau2_note="evaluator error: ... AuthenticationError"` in
  `results.json`.
- **Replay-error cases (a smaller subset, including two airline
  baseline traces — `airline_005`, `airline_049`).** tau2's
  environment evaluator re-executes mutating tool calls during
  replay; if the agent issued a call the canonical environment
  refuses (e.g. exchanging items it does not own, or a call that
  violates a state precondition), the replay raises before a reward
  can be computed. These also surface in the `tau2_note` field.

Because missingness is mostly correlated with task type (NL-assertion
tasks) rather than with variant, and because the SAFE-aware variant
has *fewer* missing cases (5 vs 8), the sub-sample comparison is not
biased against SAFE-aware.

### 3.6 Qualitative examples

`outputs/reports/paper_examples.md` reports the top variant
differences and divergence cases with conversation excerpts and
tool-call comparisons.

## 4. Discussion

### 4.1 Constraint awareness did not measurably cost task completion

The headline question of this paper is whether the SAFE-aware prompt
*pays* for its compliance gains in lost task completion. Under
τ³-bench's own reward, we find **no evidence of a cost**: descriptive
means are 0.409 (baseline, n=22) and 0.440 (safe-aware, n=25), and
on the 22 tasks where both variants produced a valid reward, the
paired difference is Δ=+0.045 with 2 of 22 tasks flipping in favor
of SAFE-aware and only 1 flipping against (sign test p=1.000,
Wilcoxon p=0.564). With 19 of 22 pairs tied this is an
underpowered comparison and we do not claim equivalence — only that
the data show no detectable decrease. By contrast, our heuristic
completion proxy (`task_completed`) makes the variant look 6.6 pp
lower (0.833 → 0.767), but the proxy treats *every* graceful
goodbye as success, which penalizes the SAFE-aware agent's
appropriate refusals on out-of-policy requests. The official τ³
reward, which evaluates *correct* completion, does not show this
penalty.

### 4.2 Prompt-level scope alone is not enough

Our diagnostic run
(`outputs/reports/retail_regression_diagnostic.md`) showed that
generic prompt language like *"only use tools available to you"* did
not prevent scope violations when the tool catalog exposed at runtime
included tools the policy disallowed. The fix
(`outputs/reports/scope_binding_validation.md`) was not to rewrite
the prompt's wording but to **bind the prompt to the per-task
allowed-tool list** at runtime. On gpt-4.1, the Scope dimension lifts
from 0.533 to 0.700 across 30 tasks (combined), with airline reaching
a perfect 1.000. This is consistent with SAFE's premise that
constraints should be enforced at multiple layers; prompt-level
guidance is necessary but not sufficient when the tool surface is
unconstrained.

### 4.3 What still does not work

- **Retail Scope (0.400 even after the binding).** Several retail
  tasks still see scope violations because the agent issues mutating
  tool calls (e.g. exchange/return) on insufficient evidence. The
  per-task binding restricts the *catalog* but cannot enforce
  *conditional preconditions* like "do not call X without first
  having called Y". A natural next step is to expose tool guards as
  a runtime layer rather than as prompt text.
- **Anchored Decisions and Flow Integrity** moved by < 0.01 in
  either direction. Both depend on multi-step procedural compliance,
  which our current evaluators detect by string-matching against
  required step names. A more expressive procedural specification
  (e.g. allowable subgraphs of ordered actions) would likely yield
  more discriminative scores and might surface effects the current
  evaluators miss.
- **Escalation saturated at 1.000** in both variants. With gpt-4.1's
  prior toward asking for clarification, the dimension does not
  discriminate at all in our setting. Tasks designed specifically to
  trip over-eagerness rather than under-asking would re-enable
  Escalation as a discriminator.

### 4.4 Threats to validity

- **Sample size (n=30).** Sufficient for direction-of-effect
  exploration; insufficient for confirmatory inference. Larger runs
  are constrained by τ³-bench evaluation cost and annotation effort.
- **LLM sampling noise.** Even at temperature 0, run-to-run
  variation exists. The paired design with Wilcoxon mitigates but
  does not eliminate this.
- **Single agent model.** All numbers are from one Azure OpenAI
  deployment of gpt-4.1. Generalization to other model families is
  future work; we expect Scope gains to transfer (the binding
  mechanism is model-agnostic) and Anchored/Flow gains to depend on
  base-model instruction following.
- **NL-assertion tasks excluded from τ³ reward.** 13/60 traces have
  `tau2_reward = None` because they require an LLM judge or hit a
  replay error. These are reported separately and are not used in
  the paired τ³ test.
- **Completion conclusions are metric-dependent and subset-dependent.**
  The heuristic `task_completed` and the official τ³ reward
  *disagree in direction* on this run: the heuristic shows the
  SAFE-aware variant 6.6 pp lower while the official reward shows it
  numerically higher. We treat the official reward as authoritative
  for the headline claim, but readers should note that (a) the
  official reward is only available on 47/60 traces and (b) the
  paired sample is 22 tasks with 19 ties, so the direction-of-effect
  conclusion rests on a small, underpowered subset.
- **One of the four SAFE dimensions is non-discriminative.**
  Escalation saturated at 1.000 in *both* variants. This means the
  composite `safe_overall` averages over a dimension that carries
  zero information in this run, weakening the construct validity of
  the composite metric on gpt-4.1.
- **Human authorship of annotations.** The annotation YAMLs encode
  one author's interpretation of the task policies. We mitigate this
  with the validation script and by keeping annotations versioned
  alongside the code.

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

A SAFE-aware prompt that binds the model to per-task scope at runtime
**numerically improves** SAFE compliance over a task-completion
baseline on gpt-4.1 (+0.039 overall, +0.167 on Scope alone), with
**no detectable decrease** in the official τ³-bench reward
(descriptive +0.031 absolute; paired Δ=+0.045 on the 22 tasks with
valid rewards under both variants, sign test p=1.000). After
multiple-comparison correction no SAFE test crosses p<0.05, so we
present these results as **exploratory direction-of-effect evidence**
rather than confirmed effects. Improvements are concentrated in
Scope; Anchored Decisions and Flow Integrity moved by < 0.01 in
either direction, and Escalation saturated at 1.000 in both variants
and did not discriminate. The largest single fix recovered scope
violations that prompt language alone could not prevent. The result
supports a two-layer view of constraint enforcement — prompt rules
*and* per-task tool binding — and is *consistent with* responsible
agent design being compatible with practical task performance on
customer-service workloads, while leaving confirmatory inference to
larger replications. Open problems include extending the rule-based
evaluators for richer procedural compliance, configuring an
NL-assertion judge to close the τ³ reward coverage gap, designing
tasks that re-enable Escalation as a discriminator, and replicating
across additional model families.

## 7. Reproducibility

```bash
git clone https://github.com/placerda/safe-experimentation
cd safe-experimentation
python -m venv .venv && .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # add Azure OpenAI gpt-4.1 deployment
python scripts/setup_tau3.py
python scripts/run_experiment.py
python scripts/analyze_results.py --latest
python scripts/analyze_tau2_reward.py --run-dir outputs/runs/<id>
python scripts/enrich_paper_examples.py --latest
```

All numbers in this paper come from `outputs/runs/20260426_140931/`
on Azure OpenAI **gpt-4.1** (model version `2025-04-14`, deployment
`gpt-4.1`, API version `2024-10-21`). Authentication is via Microsoft
Entra ID using `DefaultAzureCredential`; no API key is checked into
the repository.

## References

[1] *SAFE: Designing Responsible Agentic Systems.* TowardsAI, Mar 6, 2026.
    <https://pub.towardsai.net/safe-designing-responsible-agentic-systems-3dcc27075d4b>

[2] Sierra Research. *τ³-bench / tau2-bench.*
    <https://github.com/sierra-research/tau2-bench>
