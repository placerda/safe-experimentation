"""Regenerate data/selected_tasks/{domain}.jsonl from current annotations.

For every annotation in data/annotations/{domain}.safe.yaml, this writes the
corresponding selected-task record by reading the τ³ task source.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TAU2 = ROOT / "data" / "t3" / "data" / "tau2" / "domains"
ANN_DIR = ROOT / "data" / "annotations"
OUT_DIR = ROOT / "data" / "selected_tasks"


def build_record(domain: str, task: dict) -> dict:
    eid = int(task["id"])
    tid = f"{domain}_{eid:03d}"
    us = task.get("user_scenario") or {}
    instr = us.get("instructions") or {}
    desc = task.get("description") or {}
    eval_crit = task.get("evaluation_criteria") or {}
    return {
        "task_id": tid,
        "source": "tau3",
        "source_task_id": str(eid),
        "domain": domain,
        "user_goal": instr.get("reason_for_call"),
        "task_instructions": instr.get("task_instructions"),
        "known_info": instr.get("known_info"),
        "unknown_info": instr.get("unknown_info"),
        "initial_context": None,
        "available_tools": [],
        "evaluation_criteria": eval_crit,
        "purpose": desc.get("purpose"),
        "relevant_policies": desc.get("relevant_policies"),
        "selection_reason": "auto-generated to match annotation pool",
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for domain in ("airline", "retail"):
        anns = yaml.safe_load(
            (ANN_DIR / f"{domain}.safe.yaml").read_bytes().decode("utf-8", "replace")
        )
        wanted = {int(a["task_id"].split("_")[1]) for a in anns}
        tasks = json.loads(
            (TAU2 / domain / "tasks.json").read_bytes().decode("utf-8", "replace")
        )
        out = OUT_DIR / f"{domain}.jsonl"
        with out.open("w", encoding="utf-8") as f:
            n = 0
            for t in tasks:
                if int(t["id"]) in wanted:
                    rec = build_record(domain, t)
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    n += 1
            print(f"{domain}: wrote {n} tasks to {out}")


if __name__ == "__main__":
    main()
