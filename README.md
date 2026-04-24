# SAFE Framework Benchmark Experiment

Evaluates AI agent behavior under constraints using the [SAFE framework](https://pub.towardsai.net/safe-designing-responsible-agentic-systems-3dcc27075d4b) applied to [τ³-bench](https://github.com/sierra-research/tau2-bench) tasks.

Compares a **baseline agent** (task-completion only) against a **SAFE-aware agent** (constrained behavior) across airline and retail customer service scenarios.

## SAFE Dimensions

- **Scope** — did the agent stay within allowed actions?
- **Anchored Decisions** — were decisions based on evidence, not assumptions?
- **Flow Integrity** — did the agent follow the expected step order?
- **Escalation** — did the agent ask/stop/escalate when required?

## Setup

```bash
# Clone and enter
git clone <this-repo> && cd safe-experimentation

# Python environment
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

pip install -U pip
pip install -e ".[dev]"

# Environment variables
cp .env.example .env
# Edit .env with your Azure OpenAI credentials

# Install τ³-bench locally
python scripts/setup_tau3.py
```

## Quick Start

```bash
# Explore available τ³-bench tasks
python scripts/explore_tasks.py

# Validate SAFE annotations
python scripts/validate_annotations.py

# Run experiments (both agent variants)
python scripts/run_experiment.py

# Analyze results
python scripts/analyze_results.py
```

## Project Structure

```
configs/agents/          # Baseline and SAFE-aware system prompts
configs/experiment.yaml  # Experiment configuration
data/selected_tasks/     # Curated task subsets (JSONL)
data/annotations/        # SAFE annotation YAML per task
src/safe_benchmark/      # Core library (schemas, runner, evaluators)
scripts/                 # CLI scripts for each pipeline step
outputs/                 # Generated results, traces, reports (gitignored)
tests/                   # Unit tests with fixtures
```

## Running Tests

```bash
pytest                                          # all tests
pytest tests/test_safe_evaluators.py            # single file
pytest tests/test_safe_evaluators.py::test_scope  # single test
```
