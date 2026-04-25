"""Compare two runs side-by-side for the same task subset."""
from __future__ import annotations
import json
import sys
from pathlib import Path


def main(old_path: Path, new_path: Path, tasks: list[str]) -> None:
    old = {(e["task_id"], e["agent_variant"]): e for e in json.loads(old_path.read_text(encoding="utf-8"))}
    new = {(e["task_id"], e["agent_variant"]): e for e in json.loads(new_path.read_text(encoding="utf-8"))}

    print(f"\nOLD: {old_path}\nNEW: {new_path}\n")
    header = f"{'task':<12} {'variant':<12} {'old':<6} {'new':<6} {'delta':<8} {'old_dims':<28} {'new_dims'}"
    print(header)
    print("-" * 120)
    for t in tasks:
        for v in ["baseline", "safe-aware"]:
            o = old.get((t, v))
            n = new.get((t, v))
            if not o or not n:
                continue
            od = f"S{o['scope']:.1f}/A{o['anchored_decisions']:.1f}/F{o['flow_integrity']:.1f}/E{o['escalation']:.1f}"
            nd = f"S{n['scope']:.1f}/A{n['anchored_decisions']:.1f}/F{n['flow_integrity']:.1f}/E{n['escalation']:.1f}"
            marker = " *" if od != nd else ""
            delta = n["safe_overall"] - o["safe_overall"]
            print(f"{t:<12} {v:<12} {o['safe_overall']:<6.2f} {n['safe_overall']:<6.2f} {delta:<+8.2f} {od:<28} {nd}{marker}")


if __name__ == "__main__":
    old = Path(sys.argv[1])
    new = Path(sys.argv[2])
    tasks = sys.argv[3].split(",")
    main(old, new, tasks)
