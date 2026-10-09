"""Verify frozen source hashes and complete result/trace cells before analysis."""

from __future__ import annotations

import argparse
import hashlib
import json
from itertools import product
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, StrictBool, StrictInt, model_validator

from safe_benchmark.trace_schema import AgentTrace

Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class Freeze(BaseModel):
    commit: str
    files: dict[str, Sha256]
    tasks: list[str]
    variants: list[str]
    seed_indices: list[StrictInt]
    expected_trajectories: StrictInt

    @model_validator(mode="after")
    def validate_design(self) -> Freeze:
        for field in ("tasks", "variants", "seed_indices"):
            values = getattr(self, field)
            if not values or len(values) != len(set(values)):
                raise ValueError(f"{field} must be nonempty and unique")
        if not self.files:
            raise ValueError("freeze must include source hashes")
        size = len(self.tasks) * len(self.variants) * len(self.seed_indices)
        if self.expected_trajectories != size:
            raise ValueError("expected_trajectories does not match the frozen design")
        return self


class ResultCell(BaseModel):
    task_id: str
    agent_variant: str
    seed: StrictInt = 0
    error: str | None = None
    invalid: StrictBool = False
    tau2_reward: Annotated[float, Field(ge=0, le=1)]
    task_completed: StrictBool

    @property
    def key(self) -> tuple[str, str, int]:
        return self.agent_variant, self.task_id, self.seed


def verify(run_dir: Path, root: Path) -> dict:
    freeze = Freeze.model_validate_json((run_dir / "freeze.json").read_text(encoding="utf-8"))
    root = root.resolve()
    for relative, expected_hash in freeze.files.items():
        source = (root / relative).resolve()
        if not source.is_relative_to(root):
            raise ValueError(f"Frozen path escapes repository: {relative}")
        actual_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError(f"Frozen hash changed: {relative}")

    expected = set(product(freeze.variants, freeze.tasks, freeze.seed_indices))
    result_index: dict[tuple[str, str, int], ResultCell] = {}
    rows = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("results.json must contain a list")
    for raw in rows:
        row = ResultCell.model_validate(raw)
        if row.key in result_index:
            raise ValueError(f"Duplicate result cell: {row.key}")
        if row.error or row.invalid:
            raise ValueError(f"Unresolved execution error: {row.key}")
        result_index[row.key] = row
    if set(result_index) != expected:
        raise ValueError(
            f"Result coverage mismatch: missing={sorted(expected - set(result_index))}; "
            f"extra={sorted(set(result_index) - expected)}"
        )

    trace_index: dict[tuple[str, str, int], AgentTrace] = {}
    for path in sorted((run_dir / "traces").glob("*.json")):
        trace = AgentTrace.model_validate_json(path.read_text(encoding="utf-8"))
        key = (trace.agent_variant, trace.task_id, trace.seed)
        if key in trace_index:
            raise ValueError(f"Duplicate trace cell: {key}")
        if trace.error:
            raise ValueError(f"Unresolved trace error: {key}")
        trace_index[key] = trace
    if set(trace_index) != expected:
        raise ValueError("Trace coverage does not match frozen design")
    for key, row in result_index.items():
        if row.task_completed != trace_index[key].task_completed:
            raise ValueError(f"Trace/result termination mismatch: {key}")

    return {
        "source_commit": freeze.commit,
        "source_hashes_verified": len(freeze.files),
        "result_cells": len(result_index),
        "trace_cells": len(trace_index),
        "tasks": len(freeze.tasks),
        "seed_indices": freeze.seed_indices,
        "variants": freeze.variants,
        "complete_task_seed_blocks": len(freeze.tasks) * len(freeze.seed_indices),
        "missing_rewards": 0,
        "execution_errors": 0,
        "interpretation": (
            "Integrity checks verify the declared design and stored cells, not "
            "independence, causal validity, safety adjudication or effectiveness."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    payload = verify(args.run_dir, args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
