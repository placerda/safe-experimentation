"""Offline re-score preserved traces with the illegitimate-block metrics.

Historical ``results.json`` and trace files are read-only inputs.  Derived
rows are written below ``outputs/derived/illegitimate-block-v1``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from safe_benchmark.evaluators.safety_metrics import evaluate_safety
from safe_benchmark.task_loader import SelectedTask, load_selected_tasks
from safe_benchmark.trace_schema import AgentTrace

SCHEMA_VERSION = "illegitimate-block-v1"
DEFAULT_OUT = Path("outputs/derived") / SCHEMA_VERSION
TASK_DIRS = (
    Path("data/selected_tasks"),
    Path("data/heldout/selected_tasks"),
    Path("data/heldout2/selected_tasks"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_task_index(root: Path) -> dict[str, SelectedTask]:
    index: dict[str, SelectedTask] = {}
    for relative in TASK_DIRS:
        directory = root / relative
        if not directory.exists():
            continue
        for task in load_selected_tasks(directory):
            existing = index.get(task.task_id)
            if existing is not None and existing.model_dump() != task.model_dump():
                raise ValueError(f"Conflicting preserved definitions for {task.task_id}")
            index[task.task_id] = task
    return index


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["agent_variant"]].append(row)
    return {
        variant: {
            "trajectories": len(items),
            "missed_gold_writes": sum(r["metrics"]["missed_gold_writes"] for r in items),
            "missed_gold_writes_blocked": sum(r["metrics"]["missed_gold_writes_blocked"] for r in items),
            "missed_gold_writes_other": sum(r["metrics"]["missed_gold_writes_other"] for r in items),
            "trajectories_with_illegitimate_block": sum(
                bool(r["metrics"]["any_illegitimate_block"]) for r in items
            ),
        }
        for variant, items in sorted(groups.items())
    }


def rescore_run(root: Path, run_dir: Path, out_root: Path, tasks: dict[str, SelectedTask]) -> dict[str, Any]:
    results_path = run_dir / "results.json"
    traces_dir = run_dir / "traces"
    original_rows = json.loads(results_path.read_text(encoding="utf-8"))
    result_keys = {
        (row["agent_variant"], row["task_id"], int(row.get("seed", 0))) for row in original_rows
    }
    derived_rows = []
    for trace_path in sorted(traces_dir.glob("*.json")):
        trace = AgentTrace.model_validate_json(trace_path.read_text(encoding="utf-8"))
        key = (trace.agent_variant, trace.task_id, trace.seed)
        if key not in result_keys:
            raise ValueError(f"{run_dir.name}: trace has no result row: {key}")
        task = tasks.get(trace.task_id)
        if task is None:
            raise ValueError(f"{run_dir.name}: no preserved task definition for {trace.task_id}")
        metrics = evaluate_safety(trace, task)
        derived_rows.append(
            {
                "task_id": trace.task_id,
                "agent_variant": trace.agent_variant,
                "seed": trace.seed,
                "trace": trace_path.relative_to(root).as_posix(),
                "trace_sha256": sha256(trace_path),
                "metrics": {
                    key: metrics[key]
                    for key in (
                        "gold_write_count",
                        "executed_writes",
                        "missed_gold_writes",
                        "missed_gold_writes_blocked",
                        "missed_gold_writes_other",
                        "any_illegitimate_block",
                    )
                },
            }
        )
    if len(derived_rows) != len(original_rows):
        raise ValueError(
            f"{run_dir.name}: result/trace count mismatch ({len(original_rows)} vs {len(derived_rows)})"
        )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "source_run": run_dir.relative_to(root).as_posix(),
        "source_results_sha256": sha256(results_path),
        "evaluator": "src/safe_benchmark/evaluators/safety_metrics.py",
        "evaluator_sha256": sha256(root / "src/safe_benchmark/evaluators/safety_metrics.py"),
        "historical_inputs_modified": False,
        "rows": derived_rows,
        "aggregate": aggregate(derived_rows),
    }
    out_path = out_root / f"{run_dir.name}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "run": run_dir.name,
        "rows": len(derived_rows),
        "output": out_path.relative_to(root).as_posix(),
        "output_sha256": sha256(out_path),
        "aggregate": payload["aggregate"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dirs", nargs="*", type=Path)
    parser.add_argument("--all-transactional", action="store_true")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    if not args.run_dirs and not args.all_transactional:
        parser.error("provide run directories or --all-transactional")

    run_dirs = list(args.run_dirs)
    if args.all_transactional:
        run_dirs.extend(
            d
            for d in sorted((ROOT / "outputs/runs").glob("transaction-*"))
            if (d / "results.json").exists() and (d / "traces").is_dir()
        )
    normalized = sorted(
        {
            path.resolve() if path.is_absolute() else (ROOT / path).resolve()
            for path in run_dirs
        }
    )
    out_root = args.out if args.out.is_absolute() else ROOT / args.out
    tasks = load_task_index(ROOT)
    summaries = [rescore_run(ROOT, run_dir, out_root, tasks) for run_dir in normalized]
    index = {
        "schema_version": SCHEMA_VERSION,
        "runs": summaries,
        "total_runs": len(summaries),
        "total_rows": sum(item["rows"] for item in summaries),
    }
    index_path = out_root / "index.json"
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"rescored {index['total_rows']} preserved trajectories across {index['total_runs']} runs")
    print(index_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
