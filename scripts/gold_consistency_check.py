
"""Compare SAFE annotations with selected-task gold actions.

This is an offline consistency audit. It uses the selected task JSONL files as the
source of tau2/tau3 gold actions because they preserve each task's
``evaluation_criteria.actions`` from the benchmark source. Original ``data/t3``
files are never modified.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from safe_benchmark.annotation_schema import TaskAnnotation, load_all_annotations  # noqa: E402

SELECTED_DIR = ROOT / "data" / "selected_tasks"
ANNOTATIONS_DIR = ROOT / "data" / "annotations"
OUT_DIR = ROOT / "outputs" / "offline"

STEP_KEYWORDS = {
    "verify_user_identity": ["get_user_details", "find_user_id_by_name_zip", "find_user_id_by_email"],
    "authenticate_user_identity": ["get_user_details", "find_user_id_by_name_zip", "find_user_id_by_email"],
    "look_up_reservation": ["get_reservation_details"],
    "look_up_both_reservations": ["get_reservation_details"],
    "look_up_reservation_and_flight_details": ["get_reservation_details", "get_flight_status"],
    "look_up_order": ["get_order_details"],
    "look_up_order_details": ["get_order_details"],
    "look_up_product_details_for_each_item": ["get_product_details", "get_item_details"],
    "look_up_product_details_for_exchange": ["get_product_details", "get_item_details"],
    "look_up_product_catalog_for_tshirts": ["list_all_product_types", "get_product_details"],
    "execute_exchange": ["exchange_delivered_order_items"],
    "execute_exchange_after_confirmation": ["exchange_delivered_order_items"],
    "execute_return": ["return_delivered_order_items"],
    "cancel_reservation": ["cancel_reservation"],
    "update_default_address": ["modify_user_address"],
    "update_pending_order_addresses_if_needed": ["modify_pending_order_address"],
    "transfer_to_human": ["transfer_to_human_agents"],
}

TEXT_ONLY_PREFIXES = (
    "explain_", "request_", "confirm_", "collect_", "provide_", "deny_", "suggest_", "handle_",
    "list_", "communicate_", "calculate_", "check_", "identify_",
)


def load_selected_tasks() -> dict[str, dict[str, Any]]:
    tasks: dict[str, dict[str, Any]] = {}
    for path in sorted(SELECTED_DIR.glob("*.jsonl")):
        with path.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    task = json.loads(line)
                    tasks[task["task_id"]] = task
    return tasks


def gold_actions(task: dict[str, Any]) -> list[str]:
    return [a.get("name", "") for a in task.get("evaluation_criteria", {}).get("actions", []) if a.get("name")]


def step_supported_by_gold(step: str, actions: set[str], assertions: list[str]) -> bool:
    if step in STEP_KEYWORDS:
        return any(tool in actions for tool in STEP_KEYWORDS[step])
    if step.startswith(TEXT_ONLY_PREFIXES):
        tokens = [t for t in step.replace("_", " ").split() if len(t) > 3]
        assertion_text = " ".join(assertions).lower()
        return bool(assertion_text) and any(t in assertion_text for t in tokens)
    return False


def task_mismatches(task: dict[str, Any], ann: TaskAnnotation) -> list[dict[str, str]]:
    actions = set(gold_actions(task))
    assertions = task.get("evaluation_criteria", {}).get("nl_assertions", []) or []
    mismatches: list[dict[str, str]] = []

    for action in sorted(actions & set(ann.safe.scope.disallowed_actions)):
        mismatches.append({
            "mismatch_type": "gold_action_disallowed_by_annotation",
            "item": action,
            "detail": f"Gold requires action '{action}' but annotation disallows it.",
        })

    if ann.safe.scope.allowed_actions:
        missing_allowed = actions - set(ann.safe.scope.allowed_actions) - {"think"}
        for action in sorted(missing_allowed):
            mismatches.append({
                "mismatch_type": "gold_action_not_in_allowed_actions",
                "item": action,
                "detail": f"Gold requires action '{action}' but annotation allowed_actions omits it.",
            })

    for step in ann.safe.flow_integrity.expected_steps:
        if not step_supported_by_gold(step, actions, assertions):
            mismatches.append({
                "mismatch_type": "required_step_absent_from_gold",
                "item": step,
                "detail": f"Annotation expects step '{step}', but no mapped gold action/assertion was found.",
            })
    return mismatches


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tasks = load_selected_tasks()
    annotations = load_all_annotations(ANNOTATIONS_DIR)
    rows: list[dict[str, str]] = []
    checked = 0
    for task_id, ann in sorted(annotations.items()):
        task = tasks.get(task_id)
        if task is None:
            rows.append({
                "task_id": task_id, "domain": ann.domain, "mismatch_type": "annotation_without_selected_task",
                "item": task_id, "detail": "Annotation has no matching selected task.",
            })
            continue
        checked += 1
        for mismatch in task_mismatches(task, ann):
            rows.append({"task_id": task_id, "domain": ann.domain, **mismatch})

    csv_path = OUT_DIR / "gold_consistency.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "domain", "mismatch_type", "item", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["mismatch_type"]] = counts.get(row["mismatch_type"], 0) + 1
    md = ["# Gold consistency check", "", f"- Tasks checked: {checked}", f"- Mismatches: {len(rows)}", ""]
    md.append("## Mismatch counts")
    if counts:
        for k, v in sorted(counts.items()):
            md.append(f"- {k}: {v}")
    else:
        md.append("- None")
    md.append("")
    md.append(f"CSV: `{csv_path.as_posix()}`")
    md_path = OUT_DIR / "gold_consistency_summary.md"
    md_path.write_text("\n".join(md), encoding="utf-8")
    print(f"Checked {checked} tasks; found {len(rows)} mismatches. Wrote {csv_path} and {md_path}.")


if __name__ == "__main__":
    main()
