"""Schemas for generated SAFE challenges and deterministic oracle results."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Dimension(StrEnum):
    SCOPE = "scope"
    ANCHORED_DECISIONS = "anchored_decisions"
    FLOW_INTEGRITY = "flow_integrity"
    ESCALATION = "escalation"


class Variant(StrEnum):
    ADVERSARIAL = "adversarial"
    NEAR_NEIGHBOR = "near_neighbor"


class EventKind(StrEnum):
    OBSERVATION = "observation"
    APPROVAL = "approval"
    ACTION = "action"
    ESCALATION = "escalation"
    STOP = "stop"


class TraceEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: EventKind
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    success: bool | None = None
    approval_token: str | None = None


class EventPattern(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: EventKind | None = None
    name: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    success: bool | None = None
    approval_token: str | None = None


class OrderConstraint(BaseModel):
    before: EventPattern
    after: EventPattern


class CoverageConstraint(BaseModel):
    event: EventPattern
    argument: str
    values: list[Any]


class AllowedValuesConstraint(BaseModel):
    event: EventPattern
    argument: str
    values: list[Any]


class ExactArgumentsConstraint(BaseModel):
    event: EventPattern
    allowed: list[str]


class ApprovalConstraint(BaseModel):
    action: EventPattern
    token: str
    max_uses: int = Field(default=1, ge=1)
    require_prior_approval: bool = True


class OracleSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    required_events: list[EventPattern] = Field(default_factory=list)
    forbidden_events: list[EventPattern] = Field(default_factory=list)
    order: list[OrderConstraint] = Field(default_factory=list)
    exact_action_count: int | None = Field(default=None, ge=0)
    coverage: list[CoverageConstraint] = Field(default_factory=list)
    allowed_values: list[AllowedValuesConstraint] = Field(default_factory=list)
    exact_arguments: list[ExactArgumentsConstraint] = Field(default_factory=list)
    approvals: list[ApprovalConstraint] = Field(default_factory=list)


class CandidateTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    challenge_id: str
    events: list[TraceEvent]


class GeneratedChallenge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    challenge_id: str
    family: str
    dimension: Dimension
    variant: Variant
    issue: str
    prompt: str
    context: dict[str, Any]
    oracle: OracleSpec
    reference_trace: CandidateTrace
    negative_trace: CandidateTrace

    @model_validator(mode="after")
    def trace_ids_match(self) -> GeneratedChallenge:
        if self.reference_trace.challenge_id != self.challenge_id:
            raise ValueError("reference_trace challenge_id does not match challenge")
        if self.negative_trace.challenge_id != self.challenge_id:
            raise ValueError("negative_trace challenge_id does not match challenge")
        return self


class ChallengeSuite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1"
    specification_sha256: str
    seed_visibility: str
    seed_commitment: str
    challenges: list[GeneratedChallenge]


class OracleResult(BaseModel):
    challenge_id: str
    passed: bool
    score: float
    violations: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class VariantTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str
    context: dict[str, Any] = Field(default_factory=dict)
    oracle: OracleSpec
    reference_events: list[TraceEvent]
    negative_events: list[TraceEvent]


class FamilyTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    family: str
    dimension: Dimension
    issue: str
    variables: dict[str, list[Any]]
    variants: dict[Variant, VariantTemplate]

    @model_validator(mode="after")
    def has_paired_variants(self) -> FamilyTemplate:
        required = {Variant.ADVERSARIAL, Variant.NEAR_NEIGHBOR}
        if set(self.variants) != required:
            raise ValueError(f"{self.family}: variants must be adversarial and near_neighbor")
        return self


class BenchmarkSpecification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    specification_version: str
    families: list[FamilyTemplate]
