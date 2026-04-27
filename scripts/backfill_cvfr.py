"""Backfill the CVFR metric on existing run results.json files.

The CVFR evaluator was added in v3 (see protocol.md §3.3 and
src/safe_benchmark/evaluators/cvfr.py). Existing runs from v2 do not
have the ``cvfr`` / ``cvfr_passed`` columns, so this script reloads the
trace files, re-runs only the CVFR evaluator, and rewrites results.json
in place (with a `.bak` backup the first time).

Usage:
    python scripts/backfill_cvfr.py outputs/runs/<run_dir>
    python scripts/backfill_cvfr.py outputs/runs/<run_dir1> outputs/runs/<run_dir2> ...
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from safe_benchmark.evaluators.cvfr import evaluate_cvfr
from safe_benchmark.task_loader import load_annotated_tasks
from safe_benchmark.trace_schema import AgentTrace

ROOT = Path(__file__).resolve().parent.parent


def backfill(run_dir: Path) -> tuple[int, int]:
    results_path = run_dir / "results.json"
    traces_dir = run_dir / "traces"
    if not results_path.exists():
        print(f"  ! no results.json in {run_dir}; skipping")
        return (0, 0)
    if not traces_dir.exists():
        print(f"  ! no traces/ in {run_dir}; skipping")
        return (0, 0)

    annotated = {t.task.task_id: t for t in load_annotated_tasks(
        ROOT / "data" / "selected_tasks", ROOT / "data" / "annotations"
    )}
    results = json.loads(results_path.read_text(encoding="utf-8"))

    bak = results_path.with_suffix(".json.bak")
    if not bak.exists():
        bak.write_text(json.dumps(results, indent=2), encoding="utf-8")

    n_filled = 0
    n_skipped = 0
    for r in results:
        if "cvfr" in r and r["cvfr"] is not None and "cvfr_passed" in r:
            n_skipped += 1
            continue
        task_id = r["task_id"]
        variant = r["agent_variant"]
        seed = r.get("seed", 0)
        candidates = [
            traces_dir / f"{variant}_{task_id}_seed{seed}.json",
            traces_dir / f"{variant}_{task_id}.json",
        ]
        trace_path = next((p for p in candidates if p.exists()), None)
        if trace_path is None:
            r["cvfr"] = None
            r["cvfr_passed"] = None
            r["cvfr_reason"] = "trace file not found"
            continue
        trace = AgentTrace.model_validate_json(trace_path.read_text(encoding="utf-8"))
        ann = annotated.get(task_id)
        if ann is None:
            r["cvfr"] = None
            r["cvfr_passed"] = None
            r["cvfr_reason"] = "annotation not found"
            continue
        cvfr = evaluate_cvfr(trace, ann.annotation)
        r["cvfr"] = cvfr.score
        r["cvfr_passed"] = cvfr.passed
        r["cvfr_reason"] = cvfr.reason
        n_filled += 1

    results_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return (n_filled, n_skipped)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: backfill_cvfr.py <run_dir> [<run_dir> ...]")
    for arg in sys.argv[1:]:
        run_dir = Path(arg).resolve()
        print(f"Backfilling {run_dir.name}...")
        filled, skipped = backfill(run_dir)
        print(f"  filled={filled} already_had={skipped}")


if __name__ == "__main__":
    main()
