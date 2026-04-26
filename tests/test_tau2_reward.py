"""Tests for the τ³-bench reward evaluator integration."""
from __future__ import annotations

from pathlib import Path

import pytest

from safe_benchmark.evaluators.tau2_reward import evaluate_tau2_reward
from safe_benchmark.task_loader import load_annotated_tasks
from safe_benchmark.trace_schema import AgentTrace, Message, ToolCall


@pytest.fixture(scope="module")
def annotated_tasks() -> dict:
    tasks = load_annotated_tasks(
        Path("data/selected_tasks"), Path("data/annotations")
    )
    return {t.task.task_id: t for t in tasks}


def _make_trace(task_id: str, domain: str, **kwargs) -> AgentTrace:
    return AgentTrace(
        task_id=task_id,
        domain=domain,
        agent_variant="test",
        system_prompt="",
        **kwargs,
    )


def test_handles_trace_with_error(annotated_tasks):
    trace = _make_trace(
        "airline_000", "airline", error="azure timeout"
    )
    res = evaluate_tau2_reward(trace, annotated_tasks["airline_000"])
    assert res["tau2_reward"] is None
    assert "error" in (res["tau2_note"] or "")


def test_returns_reward_for_real_trace(annotated_tasks):
    """Sanity: a recorded airline trace should produce a deterministic reward."""
    trace_path = Path(
        "outputs/runs/20260426_140931/traces/baseline_airline_000.json"
    )
    if not trace_path.exists():
        pytest.skip("reference trace not present")
    trace = AgentTrace.model_validate_json(
        trace_path.read_bytes().decode("utf-8", "replace")
    )
    res = evaluate_tau2_reward(trace, annotated_tasks["airline_000"])
    assert isinstance(res["tau2_reward"], float)
    assert 0.0 <= res["tau2_reward"] <= 1.0
    assert "DB" in res["tau2_reward_basis"] or "COMMUNICATE" in res["tau2_reward_basis"]


def test_empty_trace_does_not_crash(annotated_tasks):
    trace = _make_trace("airline_000", "airline")
    res = evaluate_tau2_reward(trace, annotated_tasks["airline_000"])
    # Either returns 0/None gracefully — must not raise.
    assert "tau2_reward" in res
    assert "tau2_reward_basis" in res
