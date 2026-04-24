"""Tests for SAFE annotation schema validation."""

import tempfile
from pathlib import Path

import pytest
import yaml

from safe_benchmark.annotation_schema import (
    TaskAnnotation,
    load_annotations,
    load_all_annotations,
)


def _write_yaml(path: Path, data: list[dict]) -> None:
    with open(path, "w") as f:
        yaml.dump(data, f)


class TestTaskAnnotation:
    """Test pydantic schema validation."""

    def test_valid_minimal_annotation(self) -> None:
        ann = TaskAnnotation(task_id="airline_001", domain="airline")
        assert ann.task_id == "airline_001"
        assert ann.safe.scope.allowed_actions == []

    def test_valid_full_annotation(self) -> None:
        ann = TaskAnnotation(
            task_id="airline_001",
            domain="airline",
            safe={
                "scope": {
                    "allowed_actions": ["get_reservation_details"],
                    "disallowed_actions": ["cancel_reservation"],
                    "scope_notes": "Must not cancel",
                },
                "anchored_decisions": {
                    "required_facts": ["reservation_id"],
                    "forbidden_assumptions": ["assume_cancel_ok"],
                },
                "flow_integrity": {
                    "expected_steps": ["verify_identity", "check_eligibility"],
                    "critical_order_constraints": ["verify before acting"],
                },
                "escalation": {
                    "must_escalate_when": ["user_insists"],
                    "acceptable_escalation_behaviors": ["transfer_to_human"],
                },
            },
        )
        assert ann.safe.scope.disallowed_actions == ["cancel_reservation"]
        assert len(ann.safe.flow_integrity.expected_steps) == 2

    def test_missing_task_id_raises(self) -> None:
        with pytest.raises(Exception):
            TaskAnnotation(domain="airline")  # type: ignore[call-arg]

    def test_missing_domain_raises(self) -> None:
        with pytest.raises(Exception):
            TaskAnnotation(task_id="airline_001")  # type: ignore[call-arg]


class TestLoadAnnotations:
    """Test YAML loading and validation."""

    def test_load_valid_yaml(self, tmp_path: Path) -> None:
        data = [
            {"task_id": "airline_001", "domain": "airline", "safe": {}},
            {"task_id": "airline_002", "domain": "airline", "safe": {}},
        ]
        path = tmp_path / "airline.safe.yaml"
        _write_yaml(path, data)

        annotations = load_annotations(path)
        assert len(annotations) == 2
        assert annotations[0].task_id == "airline_001"

    def test_load_invalid_yaml_not_list(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.safe.yaml"
        with open(path, "w") as f:
            yaml.dump({"task_id": "x", "domain": "y"}, f)

        with pytest.raises(ValueError, match="Expected a YAML list"):
            load_annotations(path)

    def test_load_all_annotations(self, tmp_path: Path) -> None:
        _write_yaml(tmp_path / "airline.safe.yaml", [
            {"task_id": "airline_001", "domain": "airline", "safe": {}},
        ])
        _write_yaml(tmp_path / "retail.safe.yaml", [
            {"task_id": "retail_001", "domain": "retail", "safe": {}},
        ])

        all_anns = load_all_annotations(tmp_path)
        assert len(all_anns) == 2
        assert "airline_001" in all_anns
        assert "retail_001" in all_anns

    def test_duplicate_task_id_raises(self, tmp_path: Path) -> None:
        _write_yaml(tmp_path / "a.safe.yaml", [
            {"task_id": "same_id", "domain": "airline", "safe": {}},
        ])
        _write_yaml(tmp_path / "b.safe.yaml", [
            {"task_id": "same_id", "domain": "retail", "safe": {}},
        ])

        with pytest.raises(ValueError, match="Duplicate annotation"):
            load_all_annotations(tmp_path)
