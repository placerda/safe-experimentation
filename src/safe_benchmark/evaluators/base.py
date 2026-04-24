"""Base evaluator types shared across all SAFE evaluators."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EvaluatorResult(BaseModel):
    """Result from a single SAFE evaluator on a single task."""

    metric_name: str
    score: float = Field(ge=0.0, le=1.0, description="0.0 = fail, 1.0 = pass")
    passed: bool
    reason: str
    evidence: list[str] = Field(default_factory=list)
