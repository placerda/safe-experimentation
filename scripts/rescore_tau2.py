"""Re-score tau2 rewards for rows whose evaluator failed (e.g. expired auth token).

Re-evaluates only rows whose ``tau2_note`` starts with "evaluator error" using the
saved traces; the agent is NOT re-run. Writes ``results.rescored.json`` next to
``results.json`` (the original file is left untouched).

Usage:
    python scripts/rescore_tau2.py outputs/runs/<run_dir>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

from safe_benchmark.evaluators import tau2_reward as tau2_mod  # noqa: E402
from safe_benchmark.task_loader import load_annotated_tasks  # noqa: E402
from safe_benchmark.trace_schema import AgentTrace  # noqa: E402

FIELDS = ("tau2_reward", "tau2_reward_basis", "tau2_components", "tau2_db_match", "tau2_note")


def _needs_rescore(row: dict) -> bool:
    return str(row.get("tau2_note") or "").startswith("evaluator error")


def _evaluate(trace: AgentTrace, task) -> dict:
    # Force a fresh token per call so a long re-score cannot expire mid-run.
    if isinstance(getattr(tau2_mod, "_AZURE_AD_TOKEN", None), dict):
        tau2_mod._AZURE_AD_TOKEN["token"] = None
    return tau2_mod.evaluate_tau2_reward(trace, task)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()

    os.chdir(ROOT)  # tau2 task files are resolved relative to the repo root
    load_dotenv(ROOT / ".env")

    run_dir = args.run_dir if args.run_dir.is_absolute() else ROOT / args.run_dir
    rows = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    tasks = load_annotated_tasks(ROOT / "data" / "selected_tasks", ROOT / "data" / "annotations")
    task_by_id = {t.task.task_id: t for t in tasks}

    targets = [r for r in rows if _needs_rescore(r)]
    print(f"rows={len(rows)} needing_rescore={len(targets)}", flush=True)

    fixed = still_failing = 0
    for i, row in enumerate(targets, 1):
        trace_path = run_dir / "traces" / f"{row['agent_variant']}_{row['task_id']}_seed{row['seed']}.json"
        trace = AgentTrace.model_validate_json(trace_path.read_text(encoding="utf-8"))
        task = task_by_id[row["task_id"]]
        res = _evaluate(trace, task)
        if str(res.get("tau2_note") or "").startswith("evaluator error"):
            res = _evaluate(trace, task)  # one retry
        for key in FIELDS:
            row[key] = res.get(key)
        row["tau2_rescored"] = True
        if res.get("tau2_reward") is None:
            still_failing += 1
            print(f"[{i}/{len(targets)}] FAIL {trace_path.name}: {res.get('tau2_note')}", flush=True)
        else:
            fixed += 1
            print(f"[{i}/{len(targets)}] ok {trace_path.name} reward={res['tau2_reward']}", flush=True)

    out = run_dir / "results.rescored.json"
    out.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    print(f"fixed={fixed} still_failing={still_failing} -> {out}", flush=True)
    return 0 if still_failing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
