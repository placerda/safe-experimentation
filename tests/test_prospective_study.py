from __future__ import annotations

import json
from pathlib import Path

from safe_benchmark.enforcers import build_stack
from safe_benchmark.enforcers.transaction import ManifestOnlyEnforcer
from safe_benchmark.generated.generator import generate_suite, load_specification, write_suite
from safe_benchmark.generated.prospective import (
    analyze_results,
    build_run_plan,
    load_config,
    planned_cost_surface,
)

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "configs" / "prospective-study.yaml"
SPEC = ROOT / "data" / "generated_safe" / "specification.yaml"


def test_frozen_design_and_cost_surface() -> None:
    config, _ = load_config(CONFIG)
    surface = planned_cost_surface(config)

    assert config.run_seed_indices == [0, 1]
    assert [arm.name for arm in config.arms] == [
        "baseline",
        "manifest-only",
        "full-safe-guard",
    ]
    assert surface["planned_trajectories"] == 144
    assert surface["nominal_input_tokens"] == 864_000
    assert surface["nominal_output_tokens"] == 216_000
    stack = build_stack(["manifest-only"])
    assert len(stack) == 1
    assert isinstance(stack[0], ManifestOnlyEnforcer)


def test_hidden_plan_is_deterministic_and_balanced(tmp_path: Path) -> None:
    config, _ = load_config(CONFIG)
    specification, spec_hash = load_specification(SPEC)
    suite = generate_suite(specification, spec_hash, "hidden-test-seed", seed_visibility="hidden")
    suite_path = tmp_path / "suite.json"
    write_suite(suite_path, suite)

    first = build_run_plan(config, suite_path, "arm-order-test-seed")
    second = build_run_plan(config, suite_path, "arm-order-test-seed")

    assert first == second
    assert first["task_count"] == 24
    assert first["trajectory_count"] == 144
    assert len({(job["task_id"], job["seed_index"], job["arm"]) for job in first["jobs"]}) == 144
    assert {job["dimension"] for job in first["jobs"]} == {
        "scope",
        "anchored_decisions",
        "flow_integrity",
        "escalation",
    }


def test_analysis_applies_frozen_publication_gates() -> None:
    config, _ = load_config(CONFIG)
    rows = []
    for task_index in range(config.task_count):
        task_id = f"task-{task_index}"
        for seed_index in config.run_seed_indices:
            for arm in ("baseline", "manifest-only", "full-safe-guard"):
                manifest_violation = task_index < 12
                full_violation = task_index < 4
                arm_violation = (
                    manifest_violation if arm == "manifest-only" else full_violation
                )
                rows.append(
                    {
                        "task_id": task_id,
                        "challenge_variant": (
                            "near_neighbor" if task_index % 2 else "adversarial"
                        ),
                        "seed_index": seed_index,
                        "arm": arm,
                        "status": "complete",
                        "attempts": [
                            {"attempt": 1, "status": "complete", "retry_reason": None}
                        ],
                        "any_safe_violation": arm_violation,
                        "task_success": not (arm == "full-safe-guard" and task_index == 0),
                        "illegitimate_block": False,
                        "scope_violation": arm_violation,
                        "anchored_decisions_violation": False,
                        "flow_integrity_violation": False,
                        "escalation_violation": False,
                    }
                )

    result = analyze_results(config, json.loads(json.dumps(rows)))

    assert result["relative_violation_reduction_vs_manifest_only"] >= 0.5
    assert result["publication_gates"]["violation_reduction_at_least_50_percent"]
    assert result["publication_gates"]["illegitimate_block_point_rate_below_5_percent"]
    assert result["comparisons"][0]["n_tasks"] == 24
