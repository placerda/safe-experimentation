"""Tests for task loader."""

import json
from pathlib import Path

import pytest
import yaml

from safe_benchmark.task_loader import (
    AnnotatedTask,
    SelectedTask,
    load_annotated_tasks,
    load_selected_tasks,
)


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def _write_yaml(path: Path, data: list[dict]) -> None:
    with open(path, "w") as f:
        yaml.dump(data, f)


SAMPLE_TASK = {
    "task_id": "airline_001",
    "source": "tau3",
    "source_task_id": "1",
    "domain": "airline",
    "user_goal": "Cancel reservation",
    "available_tools": ["get_reservation_details", "cancel_reservation"],
    "selection_reason": "Tests scope",
}

SAMPLE_ANNOTATION = {
    "task_id": "airline_001",
    "domain": "airline",
    "safe": {
        "scope": {
            "allowed_actions": ["get_reservation_details"],
            "disallowed_actions": ["cancel_reservation"],
        },
        "flow_integrity": {
            "expected_steps": ["verify_identity", "check_eligibility"],
        },
    },
}


class TestLoadSelectedTasks:
    def test_loads_from_jsonl(self, tmp_path: Path) -> None:
        _write_jsonl(tmp_path / "airline.jsonl", [SAMPLE_TASK])
        tasks = load_selected_tasks(tmp_path)
        assert len(tasks) == 1
        assert tasks[0].task_id == "airline_001"
        assert tasks[0].domain == "airline"

    def test_loads_multiple_files(self, tmp_path: Path) -> None:
        _write_jsonl(tmp_path / "airline.jsonl", [SAMPLE_TASK])
        retail_task = {**SAMPLE_TASK, "task_id": "retail_001", "domain": "retail"}
        _write_jsonl(tmp_path / "retail.jsonl", [retail_task])
        tasks = load_selected_tasks(tmp_path)
        assert len(tasks) == 2


class TestLoadAnnotatedTasks:
    def test_pairs_tasks_with_annotations(self, tmp_path: Path) -> None:
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        ann_dir = tmp_path / "annotations"
        ann_dir.mkdir()

        _write_jsonl(tasks_dir / "airline.jsonl", [SAMPLE_TASK])
        _write_yaml(ann_dir / "airline.safe.yaml", [SAMPLE_ANNOTATION])

        annotated = load_annotated_tasks(tasks_dir, ann_dir)
        assert len(annotated) == 1
        assert annotated[0].task.task_id == "airline_001"
        assert annotated[0].annotation.safe.scope.disallowed_actions == ["cancel_reservation"]

    def test_missing_annotation_raises(self, tmp_path: Path) -> None:
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        ann_dir = tmp_path / "annotations"
        ann_dir.mkdir()

        _write_jsonl(tasks_dir / "airline.jsonl", [SAMPLE_TASK])
        # No annotations written

        with pytest.raises(ValueError, match="missing SAFE annotations"):
            load_annotated_tasks(tasks_dir, ann_dir)
