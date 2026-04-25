"""Diagnose retail regressions in the latest run."""
from __future__ import annotations
import json
from pathlib import Path
import sys


DIMS = ["scope", "anchored_decisions", "flow_integrity", "escalation"]


def main(run_dir: Path) -> None:
    evals = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    by_key = {(e["task_id"], e["agent_variant"]): e for e in evals if e["domain"] == "retail"}
    tasks = sorted({tid for tid, _ in by_key})

    print(f"\n{'task':<10} {'base':<6} {'safe':<6} {'delta':<7} dim_regressions")
    print("-" * 100)
    regression_tasks = []
    for t in tasks:
        b = by_key.get((t, "baseline"))
        s = by_key.get((t, "safe-aware"))
        if not b or not s:
            continue
        delta = s["safe_overall"] - b["safe_overall"]
        regs = []
        for d in DIMS:
            if s[d] < b[d] - 0.01:
                regs.append(f"{d}({b[d]:.2f}->{s[d]:.2f})")
        marker = "  <--" if delta < -0.01 else ""
        print(f"{t:<10} {b['safe_overall']:<6.2f} {s['safe_overall']:<6.2f} {delta:<+7.2f} {', '.join(regs)}{marker}")
        if delta < -0.01:
            regression_tasks.append((t, b, s))

    print(f"\n=== {len(regression_tasks)} retail tasks with overall regressions ===\n")
    for t, b, s in regression_tasks:
        print(f"\n--- {t} (delta={s['safe_overall']-b['safe_overall']:+.2f}, completed: base={b['task_completed']}, safe={s['task_completed']}) ---")
        for d in DIMS:
            if s[d] < b[d] - 0.01:
                print(f"  [{d}] {b[d]:.2f} -> {s[d]:.2f}")
                print(f"    baseline:   {b.get(d+'_reason','')[:300]}")
                print(f"    safe-aware: {s.get(d+'_reason','')[:300]}")


if __name__ == "__main__":
    run_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("outputs/runs/20260424_221902")
    main(run_dir)
