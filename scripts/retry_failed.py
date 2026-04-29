"""Retry only the failed evaluations from one or more sweep runs.

Scans the given run directories for results entries with non-empty
``error`` fields, then re-runs each (domain, task, variant, seed)
tuple via run_experiment.py, batching by (domain, variant, seed) to
minimize overhead. Results are written to a new run dir tagged
``v3-retry``.

The retry plan is also written to outputs/sweep_logs/retry_plan.json
for traceability.

Usage:
    python scripts/retry_failed.py outputs/runs/<runA> outputs/runs/<runB> ...

Environment: AZURE_TENANT_ID, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT
must be set (the same vars run_v3_sweep.ps1 sets).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def collect_failures(run_dirs: list[Path]) -> dict[tuple[str, str, str, int], list[str]]:
    """Return {(domain, variant, seed, _) -> [task_ids]} grouped for batching."""
    grouped: dict[tuple[str, str, int], list[str]] = defaultdict(list)
    for d in run_dirs:
        rj = d / "results.json"
        if not rj.exists():
            print(f"!! skipping {d.name}: no results.json")
            continue
        rs = json.loads(rj.read_text(encoding="utf-8"))
        for r in rs:
            if not r.get("error"):
                continue
            key = (r["domain"], r["agent_variant"], int(r.get("seed", 0)))
            grouped[key].append(r["task_id"])
    return grouped


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: retry_failed.py <run_dir> [<run_dir> ...]")
    run_dirs = [Path(a).resolve() for a in sys.argv[1:]]
    grouped = collect_failures(run_dirs)
    total = sum(len(v) for v in grouped.values())
    print(f"Found {total} failed evals across {len(grouped)} (domain,variant,seed) batches")

    if total == 0:
        print("Nothing to retry.")
        return

    plan_path = ROOT / "outputs" / "sweep_logs" / "retry_plan.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps({
        f"{d}|{v}|seed{s}": tasks for (d, v, s), tasks in grouped.items()
    }, indent=2), encoding="utf-8")
    print(f"Wrote plan to {plan_path}")

    for (domain, variant, seed), task_ids in sorted(grouped.items()):
        tasks_csv = ",".join(sorted(set(task_ids)))
        print(f"\n=== {domain}/{variant}/seed={seed}: {len(task_ids)} tasks ===")
        cmd = [
            sys.executable, "scripts/run_experiment.py",
            "--domains", domain,
            "--variants", variant,
            "--seeds", str(seed),
            "--tasks", tasks_csv,
            "--run-tag", "v3-retry",
        ]
        env = os.environ.copy()
        # Defaults required by run_experiment.py — do NOT silently use
        # whatever was last cached. The retry must explicitly target the
        # current resource group's endpoint.
        env.setdefault("AZURE_TENANT_ID", "16b3c013-d300-468d-ac64-7eda0820b6d3")
        env.setdefault("AZURE_OPENAI_ENDPOINT", "https://aif-safe-experimentation.cognitiveservices.azure.com/")
        env.setdefault("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        env.setdefault("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")
        env.setdefault("AZURE_OPENAI_USER_DEPLOYMENT", "gpt-4.1")
        for k in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT", "AZURE_TENANT_ID"):
            print(f"  {k}={env.get(k, '<UNSET>')}")
        result = subprocess.run(cmd, env=env, cwd=str(ROOT))
        if result.returncode != 0:
            print(f"!! batch failed (exit {result.returncode}); continuing with next batch")


if __name__ == "__main__":
    main()
