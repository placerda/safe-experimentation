"""Scenario loader and pydantic models for the SAFE demo."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Literal

import yaml
from pydantic import BaseModel, Field, model_validator

Principle = Literal["scope", "anchored", "flow", "escalation"]


class BaselineReply(BaseModel):
    reply: str


class SafeReply(BaseModel):
    reply: str
    principles: List[Principle] = Field(default_factory=list)
    explanations: Dict[Principle, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_explanations(self) -> "SafeReply":
        missing = [p for p in self.principles if p not in self.explanations]
        if missing:
            raise ValueError(f"Missing explanations for principles: {missing}")
        return self


class Turn(BaseModel):
    customer: str
    baseline: BaselineReply
    safe: SafeReply


class Closing(BaseModel):
    baseline: str
    safe: str


class Scenario(BaseModel):
    title: str
    subtitle: str
    customer_name: str = "Customer"
    baseline_label: str = "Baseline Agent"
    safe_label: str = "SAFE-aware Agent"
    turns: List[Turn]
    closing: Closing


def load_scenario(path: str | Path) -> Scenario:
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Scenario.model_validate(data)
