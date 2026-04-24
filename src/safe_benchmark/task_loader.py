"""Task loader — loads selected tasks and matches them with SAFE annotations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from safe_benchmark.annotation_schema import TaskAnnotation, load_all_annotations


class SelectedTask(BaseModel):
    """A curated task from τ³-bench with its metadata."""

    task_id: str
    source: str
    source_task_id: str
    domain: str
    user_goal: str
    task_instructions: str = ""
    known_info: str = ""
    unknown_info: str | None = None
    initial_context: Any = None
    available_tools: list[str] = Field(default_factory=list)
    evaluation_criteria: Any = None
    purpose: str | None = None
    relevant_policies: str | None = None
    selection_reason: str = ""


class AnnotatedTask(BaseModel):
    """A selected task paired with its SAFE annotation."""

    task: SelectedTask
    annotation: TaskAnnotation


def load_selected_tasks(tasks_dir: Path) -> list[SelectedTask]:
    """Load all selected tasks from JSONL files in a directory."""
    tasks: list[SelectedTask] = []
    for path in sorted(tasks_dir.glob("*.jsonl")):
        with open(path) as f:
            for line in f:
                raw = json.loads(line)
                tasks.append(SelectedTask.model_validate(raw))
    return tasks


def load_annotated_tasks(tasks_dir: Path, annotations_dir: Path) -> list[AnnotatedTask]:
    """Load selected tasks and pair them with SAFE annotations.

    Raises ValueError if any task is missing an annotation.
    """
    tasks = load_selected_tasks(tasks_dir)
    annotations = load_all_annotations(annotations_dir)

    annotated: list[AnnotatedTask] = []
    missing: list[str] = []

    for task in tasks:
        if task.task_id not in annotations:
            missing.append(task.task_id)
            continue
        annotated.append(AnnotatedTask(task=task, annotation=annotations[task.task_id]))

    if missing:
        raise ValueError(f"Tasks missing SAFE annotations: {missing}")

    return annotated
