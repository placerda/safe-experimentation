"""Auto-clean draft annotations: strip parentheticals, remove unknown tools,
and resolve allowed/disallowed overlap by keeping in allowed only."""
from __future__ import annotations

import re
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


def clean_tool(t: str) -> str:
    return re.sub(r"\s*\(.*\)\s*$", "", t.strip())


def clean_one(ann: dict, catalog: set[str]) -> tuple[dict, list[str]]:
    notes: list[str] = []
    sc = ann.get("safe", {}).get("scope", {})
    cleaned_allowed = []
    for t in sc.get("allowed_actions", []) or []:
        ct = clean_tool(t)
        if ct in catalog and ct not in cleaned_allowed:
            cleaned_allowed.append(ct)
        elif ct not in catalog:
            notes.append(f"dropped unknown allowed: {t}")
    cleaned_dis = []
    for t in sc.get("disallowed_actions", []) or []:
        ct = clean_tool(t)
        if ct in catalog and ct not in cleaned_dis and ct not in cleaned_allowed:
            cleaned_dis.append(ct)
        elif ct in cleaned_allowed:
            notes.append(f"removed overlap from disallowed: {ct}")
        elif ct not in catalog:
            notes.append(f"dropped unknown disallowed: {t}")
    sc["allowed_actions"] = cleaned_allowed
    sc["disallowed_actions"] = cleaned_dis
    return ann, notes


def main() -> None:
    paths = sys.argv[1:] or [
        "data/annotations/airline.draft_batch1.yaml",
        "data/annotations/airline.draft_batch2.yaml",
        "data/annotations/retail.draft_batch1.yaml",
        "data/annotations/retail.draft_batch2.yaml",
    ]
    for p in paths:
        path = Path(p)
        if not path.exists():
            continue
        anns = yaml.safe_load(path.read_bytes().decode("utf-8", "replace"))
        catalog = AIRLINE_TOOLS if "airline" in path.name else RETAIL_TOOLS
        total_notes = 0
        for ann in anns:
            _, notes = clean_one(ann, catalog)
            for n in notes:
                print(f"  {ann.get('task_id','?')}: {n}")
            total_notes += len(notes)
        path.write_text(
            yaml.safe_dump(anns, sort_keys=False, allow_unicode=True), encoding="utf-8"
        )
        print(f"== cleaned {path.name}: {total_notes} fixes ==")


if __name__ == "__main__":
    main()
