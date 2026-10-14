from __future__ import annotations

import json
from pathlib import Path

import pytest

from safe_benchmark.generated.generator import load_suite
from safe_benchmark.generated.live_runtime import (
    DeterministicSmokeAgent,
    job_is_runnable,
    run_live_challenge,
    validate_live_inputs,
)
from safe_benchmark.generated.prospective import load_config

ROOT = Path(__file__).resolve().parent.parent
SUITE_PATH = ROOT / "data" / "generated_safe" / "hidden" / "prospective-suite.json"
PLAN_PATH = ROOT / "data" / "generated_safe" / "hidden" / "prospective-run-plan.json"
CONFIG_PATH = ROOT / "configs" / "prospective-study.yaml"


@pytest.mark.parametrize(
    ("family", "variant"),
    [
        ("target-substitution", "adversarial"),
        ("payment-provenance", "adversarial"),
        ("reordered-dependencies", "adversarial"),
        ("backend-failure", "adversarial"),
        ("target-substitution", "near_neighbor"),
    ],
)
def test_live_runtime_covers_each_dimension_and_legitimate_neighbor(
    family: str, variant: str
) -> None:
    suite = load_suite(SUITE_PATH)
    challenge = next(
        item for item in suite.challenges
        if item.family == family and item.variant.value == variant
    )
    trace, result = run_live_challenge(
        challenge,
        arm="full-safe-guard",
        seed_index=0,
        system_prompt="Public baseline prompt.",
        agent=DeterministicSmokeAgent(challenge.prompt, challenge.context),
    )

    assert result["status"] == "complete"
    assert result["task_success"]
    assert not result["any_safe_violation"]
    assert not result["illegitimate_block"]
    serialized = trace.model_dump_json()
    assert challenge.prompt in serialized
    assert '"oracle"' not in trace.system_prompt.lower()
    assert "required_events" not in serialized
    assert "reference_trace" not in serialized


def test_frozen_plan_validation_enforces_full_cross_product() -> None:
    config, _ = load_config(CONFIG_PATH)
    suite, plan = validate_live_inputs(config, SUITE_PATH, PLAN_PATH)

    assert len(suite.challenges) == 24
    assert len(plan["jobs"]) == 144
    assert {job["seed_index"] for job in plan["jobs"]} == {0, 1}
    assert {job["arm"] for job in plan["jobs"]} == {
        "baseline",
        "manifest-only",
        "full-safe-guard",
    }


def test_hidden_oracle_is_not_present_in_agent_messages() -> None:
    challenge = load_suite(SUITE_PATH).challenges[0]

    class InspectingAgent:
        def reply(self, messages, tools, *, seed_index):
            payload = json.dumps({"messages": messages, "tools": tools})
            assert "required_events" not in payload
            assert "reference_trace" not in payload
            assert "negative_trace" not in payload
            return type("Reply", (), {"text": "done", "tool_calls": []})()

    run_live_challenge(
        challenge,
        arm="baseline",
        seed_index=0,
        system_prompt="Public prompt only.",
        agent=InspectingAgent(),
    )


def test_only_one_enumerated_infrastructure_retry_is_runnable() -> None:
    first_failure = {
        "status": "incomplete",
        "attempts": [
            {
                "attempt": 1,
                "status": "infrastructure_failure",
                "failure_reason": "provider_429",
                "retry_reason": None,
            }
        ],
    }
    assert job_is_runnable(None)
    assert job_is_runnable(first_failure)
    assert not job_is_runnable(
        {
            **first_failure,
            "attempts": [
                *first_failure["attempts"],
                {
                    "attempt": 2,
                    "status": "infrastructure_failure",
                    "failure_reason": "provider_429",
                    "retry_reason": "provider_429",
                },
            ],
        }
    )
    assert not job_is_runnable(
        {
            "status": "incomplete",
            "attempts": [{"attempt": 1, "status": "model_refusal"}],
        }
    )
    assert not job_is_runnable({"status": "complete", "attempts": []})


def test_scripted_user_confirms_agent_requested_action() -> None:
    challenge = next(
        item for item in load_suite(SUITE_PATH).challenges
        if item.family == "target-substitution" and item.variant.value == "near_neighbor"
    )

    class ConfirmationAgent:
        turn = 0

        def reply(self, messages, tools, *, seed_index):
            self.turn += 1
            if self.turn == 1:
                return type(
                    "Reply",
                    (),
                    {"text": "Please confirm that I should cancel ORD-382.", "tool_calls": []},
                )()
            if self.turn == 2:
                return type(
                    "Reply",
                    (),
                    {
                        "text": "",
                        "tool_calls": [("cancel_order", {"order_id": "ORD-382"})],
                    },
                )()
            return type("Reply", (), {"text": "Complete.", "tool_calls": []})()

    trace, result = run_live_challenge(
        challenge,
        arm="baseline",
        seed_index=0,
        system_prompt="Public prompt only.",
        agent=ConfirmationAgent(),
    )

    assert result["task_success"]
    assert any(message.role == "user" and message.content == "yes" for message in trace.messages)
