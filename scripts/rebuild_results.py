"""Rebuild results.json from trace files in a run dir.

Useful after a resumed run, where the in-memory results list missed skipped
cells. Reads each trace, re-evaluates with all SAFE evaluators + tau2_reward,
and writes results.json + report.md.

Usage:
    python scripts/rebuild_results.py outputs/runs/<run_dir> [--seed N]

If --seed is omitted, infers seed from the run dir name suffix (e.g.
"__v4-seed2" -> 2) or defaults to 0.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from safe_benchmark.reporting import generate_report, save_results_json
from safe_benchmark.task_loader import load_annotated_tasks
from safe_benchmark.trace_schema import AgentTrace

# Reuse the evaluator wiring from run_experiment.py
from run_experiment import evaluate_trace  # type: ignore


ROOT = Path(__file__).resolve().parent.parent


def infer_seed(run_dir: Path) -> int:
    m = re.search(r"seed(\d+)$", run_dir.name)
    return int(m.group(1)) if m else 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    run_dir: Path = args.run_dir.resolve()
    traces_dir = run_dir / "traces"
    if not traces_dir.exists():
        raise SystemExit(f"No traces/ in {run_dir}")

    seed = args.seed if args.seed is not None else infer_seed(run_dir)
    print(f"Run dir: {run_dir}")
    print(f"Seed:    {seed}")

    tasks_dir = ROOT / "data" / "selected_tasks"
    annotations_dir = ROOT / "data" / "annotations"
    tasks = load_annotated_tasks(tasks_dir, annotations_dir)
    task_by_id = {t.task.task_id: t for t in tasks}

    results = []
    missing = 0
    for trace_path in sorted(traces_dir.glob("*.json")):
        try:
            trace = AgentTrace.model_validate_json(trace_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  WARN: could not parse {trace_path.name}: {e}")
            continue
        task = task_by_id.get(trace.task_id)
        if task is None:
            print(f"  WARN: task {trace.task_id} not found in annotations; skipping")
            missing += 1
            continue
        try:
            row = evaluate_trace(trace, task)
            row["seed"] = seed
            results.append(row)
        except Exception as e:
            print(f"  WARN: eval failed for {trace_path.name}: {e}")

    print(f"Evaluated {len(results)} traces ({missing} missing tasks)")
    save_results_json(results, run_dir / "results.json")
    generate_report(results, run_dir / "report.md")
    print(f"Wrote {run_dir / 'results.json'}")
    print(f"Wrote {run_dir / 'report.md'}")


if __name__ == "__main__":
    main()
