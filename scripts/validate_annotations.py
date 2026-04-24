"""Validate that SAFE annotations match selected tasks.

Checks:
- Every selected task has a corresponding annotation
- Every annotation references a valid selected task
- All SAFE sections are present and valid (via pydantic)
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from safe_benchmark.annotation_schema import load_all_annotations

SELECTED_TASKS_DIR = Path(__file__).resolve().parent.parent / "data" / "selected_tasks"
ANNOTATIONS_DIR = Path(__file__).resolve().parent.parent / "data" / "annotations"


def load_selected_task_ids() -> set[str]:
    """Load all task IDs from selected task JSONL files."""
    task_ids: set[str] = set()
    for path in sorted(SELECTED_TASKS_DIR.glob("*.jsonl")):
        with open(path) as f:
            for line in f:
                task = json.loads(line)
                task_ids.add(task["task_id"])
    return task_ids


def main() -> None:
    errors: list[str] = []

    # Load selected tasks
    if not SELECTED_TASKS_DIR.exists():
        print(f"ERROR: Selected tasks directory not found: {SELECTED_TASKS_DIR}")
        sys.exit(1)

    task_ids = load_selected_task_ids()
    print(f"Found {len(task_ids)} selected tasks: {sorted(task_ids)}")

    # Load and validate annotations
    if not ANNOTATIONS_DIR.exists():
        print(f"ERROR: Annotations directory not found: {ANNOTATIONS_DIR}")
        sys.exit(1)

    try:
        annotations = load_all_annotations(ANNOTATIONS_DIR)
    except Exception as e:
        print(f"ERROR: Failed to load annotations: {e}")
        sys.exit(1)

    annotation_ids = set(annotations.keys())
    print(f"Found {len(annotation_ids)} annotations: {sorted(annotation_ids)}")

    # Check for missing annotations
    missing = task_ids - annotation_ids
    if missing:
        errors.append(f"Tasks without annotations: {sorted(missing)}")

    # Check for orphan annotations
    orphans = annotation_ids - task_ids
    if orphans:
        errors.append(f"Annotations without matching tasks: {sorted(orphans)}")

    # Validate each annotation has non-trivial content
    for task_id, ann in annotations.items():
        safe = ann.safe
        if not safe.scope.allowed_actions and not safe.scope.disallowed_actions:
            errors.append(f"{task_id}: scope has no allowed or disallowed actions")
        if not safe.flow_integrity.expected_steps:
            errors.append(f"{task_id}: flow_integrity has no expected_steps")

    # Report results
    if errors:
        print(f"\nValidation FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\nValidation PASSED: all annotations are valid and match selected tasks.")


if __name__ == "__main__":
    main()
