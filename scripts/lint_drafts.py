"""Validate draft annotations: schema + tool-name catalog match.

Reports violations but does NOT block — used for lint/inspection during the
batch-drafting workflow.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

AIRLINE_TOOLS = {
    "book_reservation", "calculate", "cancel_reservation", "get_flight_status",
    "get_reservation_details", "get_user_details", "list_all_airports",
    "search_direct_flight", "search_onestop_flight", "send_certificate",
    "transfer_to_human_agents", "update_reservation_baggages",
    "update_reservation_flights", "update_reservation_passengers", "think",
}
RETAIL_TOOLS = {
    "calculate", "cancel_pending_order", "exchange_delivered_order_items",
    "find_user_id_by_email", "find_user_id_by_name_zip", "get_item_details",
    "get_order_details", "get_product_details", "get_user_details",
    "list_all_product_types", "modify_pending_order_address",
    "modify_pending_order_items", "modify_pending_order_payment",
    "modify_user_address", "return_delivered_order_items",
    "transfer_to_human_agents", "think",
}
ESCALATION_VALID = {
    "refuse_unsafe_action", "transfer_to_human", "ask_for_clarification",
    "ask_user", "stop", "escalate",
}


def validate_one(ann: dict, catalog: set[str]) -> list[str]:
    errors: list[str] = []
    safe = ann.get("safe", {})
    for sect in ("scope", "anchored_decisions", "flow_integrity", "escalation"):
        if sect not in safe:
            errors.append(f"missing section: {sect}")
    sc = safe.get("scope", {})
    for tool in sc.get("allowed_actions", []) or []:
        if tool not in catalog:
            errors.append(f"unknown allowed_action: {tool}")
    for tool in sc.get("disallowed_actions", []) or []:
        if tool not in catalog:
            errors.append(f"unknown disallowed_action: {tool}")
    overlap = set(sc.get("allowed_actions", []) or []) & set(
        sc.get("disallowed_actions", []) or []
    )
    if overlap:
        errors.append(f"action both allowed and disallowed: {sorted(overlap)}")
    esc = safe.get("escalation", {})
    for beh in esc.get("acceptable_escalation_behaviors", []) or []:
        if beh not in ESCALATION_VALID:
            errors.append(f"unusual escalation behavior: {beh}")
    fi = safe.get("flow_integrity", {})
    if not fi.get("expected_steps"):
        errors.append("flow_integrity has no expected_steps")
    return errors


def main() -> None:
    paths = sys.argv[1:] or [
        "data/annotations/airline.draft_batch1.yaml",
        "data/annotations/airline.draft_batch2.yaml",
        "data/annotations/retail.draft_batch1.yaml",
        "data/annotations/retail.draft_batch2.yaml",
    ]
    total_errors = 0
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"  [skip] {p} not found")
            continue
        ann_list = yaml.safe_load(path.read_bytes().decode("utf-8", "replace"))
        catalog = AIRLINE_TOOLS if "airline" in path.name else RETAIL_TOOLS
        print(f"\n== {path.name} ({len(ann_list)} annotations) ==")
        for ann in ann_list:
            errs = validate_one(ann, catalog)
            if errs:
                total_errors += len(errs)
                print(f"  {ann.get('task_id','?')}: {len(errs)} issue(s)")
                for e in errs:
                    print(f"    - {e}")
            else:
                print(f"  {ann.get('task_id','?')}: OK")
    print(f"\nTOTAL ISSUES: {total_errors}")
    sys.exit(0)


if __name__ == "__main__":
    main()
