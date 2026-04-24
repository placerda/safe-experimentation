# Copilot Instructions: SAFE Framework Benchmark Experiment

## Project Overview

This project evaluates AI agent behavior under constraints using the **[SAFE framework](https://pub.towardsai.net/safe-designing-responsible-agentic-systems-3dcc27075d4b)** (Scope, Anchored Decisions, Flow Integrity, Escalation) applied to a subset of T3 benchmark tasks in airline and retail domains. It compares a baseline agent against a SAFE-aware agent, producing metrics and traces to support an academic paper.

**Key tools:** Python 3.11+, AgentOps Toolkit (orchestration/reporting), T3 benchmark (task source).

## Build and Run Commands

```bash
# Environment setup
python -m venv .venv
python -m pip install -U pip
python -m pip install -r requirements.txt

# Run tests
pytest tests/
pytest tests/test_safe_evaluators.py               # single test file
pytest tests/test_safe_evaluators.py::test_scope    # single test function

# Validate annotations match selected tasks
python scripts/validate_annotations.py

# Run experiments
agentops eval run --config configs/agentops/run.baseline.yaml
agentops eval run --config configs/agentops/run.safe-aware.yaml

# Compare runs
agentops eval compare --runs <baseline-run-id>,<safe-aware-run-id>

# Analyze results
python scripts/analyze_results.py
```

## Architecture

The experiment pipeline flows as:

1. **Task selection** — curated subset (~30 tasks) from T3 stored in `data/selected_tasks/` as JSONL
2. **SAFE annotation** — per-task YAML annotations in `data/annotations/` defining expected constraints
3. **Agent execution** — two agent variants (baseline, SAFE-aware) run via AgentOps with prompts in `configs/agents/`
4. **Evaluation** — four rule-based evaluators in `src/safe_benchmark/evaluators/` score each SAFE dimension
5. **Reporting** — aggregate metrics, per-task scores, and paper-ready examples in `outputs/`

### SAFE Dimensions

Each evaluator returns `{ metric_name, score, passed, reason, evidence }`:

- **Scope** — did the agent stay within allowed actions?
- **Anchored Decisions** — did decisions use required evidence without forbidden assumptions?
- **Flow Integrity** — did the agent follow the expected step order?
- **Escalation** — did the agent ask/stop/escalate when required?

### Data Separation

- `data/t3/` — original benchmark data (never modified)
- `data/selected_tasks/` — curated task subsets (JSONL)
- `data/annotations/` — SAFE annotation YAML files

## Key Conventions

### Schemas and Validation

- Use **pydantic** for all schemas (annotation, task, evaluator result)
- Use **pathlib** for file paths
- Every annotation must be validated: required SAFE sections present, task IDs match selected tasks
- Annotations use YAML; selected tasks use JSONL

### Evaluator Design

- Implement **rule-based evaluators first** — no LLM-based evaluators until rule-based ones exist and work
- Evaluators are transparent: reasons and evidence must be human-readable
- Each evaluator is a separate module in `src/safe_benchmark/evaluators/`

### Working Principles

- **Small, incremental changes** — focused commits, no large rewrites unless requested
- **Reproducibility** — deterministic configs, versioned files, no hardcoded secrets
- **Clarity over complexity** — simple schemas, understandable evaluators
- **Research usefulness** — preserve traces, failure examples, and divergence cases (task success vs SAFE compliance)

### Guardrails

- Never modify original T3 benchmark files
- Never store API keys in the repo (use `.env` with `.env.example` as template)
- Don't overstate conclusions from small-scale results
- Don't create unnecessary abstractions before the baseline pipeline works
- Add `TODO` comments when behavior is intentionally simplified
- Ask for clarification when a design choice affects research interpretation

### Terminology

Use consistently: SAFE framework, SAFE annotation, SAFE evaluator, SAFE metric, baseline agent, SAFE-aware agent, task success, constraint-aware behavior, escalation behavior.
