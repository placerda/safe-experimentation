"""SAFE annotation schema — Pydantic models for task-level SAFE constraints.

Each selected task gets a SAFE annotation defining expected behavior
across four dimensions: Scope, Anchored Decisions, Flow Integrity, Escalation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ScopeAnnotation(BaseModel):
    """Defines what actions the agent is allowed/disallowed to perform."""

    allowed_actions: list[str] = Field(default_factory=list, description="Tool calls the agent may use")
    disallowed_actions: list[str] = Field(default_factory=list, description="Tool calls the agent must NOT use")
    scope_notes: str = Field(default="", description="Free-text explanation of scope boundaries")


class AnchoredDecisionsAnnotation(BaseModel):
    """Defines what evidence the agent must gather before deciding."""

    required_facts: list[str] = Field(default_factory=list, description="Facts agent must verify before acting")
    forbidden_assumptions: list[str] = Field(
        default_factory=list, description="Assumptions the agent must NOT make"
    )
    evidence_notes: str = Field(default="", description="Explanation of evidence requirements")


class FlowIntegrityAnnotation(BaseModel):
    """Defines expected step ordering for the task."""

    expected_steps: list[str] = Field(default_factory=list, description="Steps in expected order")
    critical_order_constraints: list[str] = Field(
        default_factory=list, description="Ordering rules that must not be violated"
    )


class EscalationAnnotation(BaseModel):
    """Defines when the agent must escalate, ask, or stop."""

    must_escalate_when: list[str] = Field(
        default_factory=list, description="Conditions requiring escalation/clarification"
    )
    acceptable_escalation_behaviors: list[str] = Field(
        default_factory=list, description="Valid ways to escalate (ask, refuse, transfer)"
    )


class SafeAnnotation(BaseModel):
    """All four SAFE dimensions for a single task."""

    scope: ScopeAnnotation = Field(default_factory=ScopeAnnotation)
    anchored_decisions: AnchoredDecisionsAnnotation = Field(default_factory=AnchoredDecisionsAnnotation)
    flow_integrity: FlowIntegrityAnnotation = Field(default_factory=FlowIntegrityAnnotation)
    escalation: EscalationAnnotation = Field(default_factory=EscalationAnnotation)


class TaskAnnotation(BaseModel):
    """Complete SAFE annotation for a selected task."""

    task_id: str = Field(description="Must match task_id in selected_tasks JSONL")
    domain: str = Field(description="airline or retail")
    safe: SafeAnnotation = Field(default_factory=SafeAnnotation)


def load_annotations(path: Path) -> list[TaskAnnotation]:
    """Load and validate SAFE annotations from a YAML file.

    The YAML file should contain a list of task annotations.
    """
    with open(path) as f:
        raw: Any = yaml.safe_load(f)

    if not isinstance(raw, list):
        raise ValueError(f"Expected a YAML list of annotations, got {type(raw).__name__}")

    return [TaskAnnotation.model_validate(item) for item in raw]


def load_all_annotations(annotations_dir: Path) -> dict[str, TaskAnnotation]:
    """Load all annotation files from a directory, keyed by task_id."""
    annotations: dict[str, TaskAnnotation] = {}
    for path in sorted(annotations_dir.glob("*.safe.yaml")):
        for ann in load_annotations(path):
            if ann.task_id in annotations:
                raise ValueError(f"Duplicate annotation for task_id: {ann.task_id}")
            annotations[ann.task_id] = ann
    return annotations
