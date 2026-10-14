"""Bounded model, conformance, and mutation-adequacy tests."""

from copy import deepcopy

import pytest

from safe_benchmark.formal_authority import (
    AuditKind,
    AuthorityAuditEvent,
    AuthorizedAction,
    ProductionRecognition,
    action_signature,
    check_audit_events,
    check_production_trace,
    explore_bounded,
)
from safe_benchmark.trace_schema import AgentTrace, ToolCall
from tests.test_authorization_sequences import synthetic_guard

A = {"signature": "A", "state": "s0"}
B = {"signature": "B", "state": "s0"}


def valid_events():
    return [
        AuthorityAuditEvent(kind=AuditKind.USER_TURN, turn=0, request=["A", "B"]),
        AuthorityAuditEvent(kind=AuditKind.PROPOSE, turn=0, actions=[A, B]),
        AuthorityAuditEvent(kind=AuditKind.PRESENT, turn=0),
        AuthorityAuditEvent(kind=AuditKind.ASSENT, turn=1),
        AuthorityAuditEvent(kind=AuditKind.DISPATCH, turn=2, signature="A", state="s0"),
        AuthorityAuditEvent(kind=AuditKind.OBSERVE, turn=2, succeeded=False),
        AuthorityAuditEvent(kind=AuditKind.DISPATCH, turn=2, signature="B", state="s0"),
    ]


def test_exhaustive_bounded_exploration_has_no_invariant_violation():
    report = explore_bounded(depth=6)
    assert report.states > 50
    assert report.transitions > 1_000
    assert report.violations == []


def test_valid_exact_ordered_one_use_trace_conforms():
    result = check_audit_events(valid_events())
    assert result.passed, result.violations


@pytest.mark.parametrize(
    ("name", "mutate"),
    [
        (
            "assent expands authority",
            lambda e: setattr(
                e[1],
                "actions",
                [A, {"signature": "C", "state": "s0"}],
            ),
        ),
        ("proposal overwrites request", lambda e: setattr(e[0], "request", ["A"])),
        ("partial assent", lambda e: setattr(e[3], "selection", [A])),
        ("argument substitution", lambda e: setattr(e[4], "signature", "C")),
        ("reordering", lambda e: setattr(e[4], "signature", "B")),
        ("stale state", lambda e: setattr(e[4], "state", "s1")),
        (
            "approval surviving a new user turn",
            lambda e: e.insert(
                4,
                AuthorityAuditEvent(
                    kind=AuditKind.USER_TURN,
                    turn=2,
                ),
            ),
        ),
        (
            "delayed consumption/post-observer failure",
            lambda e: e.insert(
                6,
                AuthorityAuditEvent(
                    kind=AuditKind.DISPATCH,
                    turn=2,
                    signature="A",
                    state="s0",
                ),
            ),
        ),
    ],
)
def test_mutation_adequacy(name, mutate):
    events = deepcopy(valid_events())
    mutate(events)
    result = check_audit_events(events)
    assert not result.passed, name


def test_state_model_rejects_partial_assent_directly():
    from safe_benchmark.formal_authority import AuthorityState

    a = AuthorizedAction("A", "s0")
    b = AuthorizedAction("B", "s0")
    state = AuthorityState().user_turn(["A", "B"]).propose([a, b]).present()
    assert state.assent([a]).approved == ()


def test_production_trace_checker_uses_normalized_events_not_enforcer_state():
    guard, proposed = synthetic_guard()
    events = []
    _, first = guard.pre_tool_call(proposed, None, [], 1)
    events.extend(first)
    guard.observe_assistant(guard.render_assistant(""))
    _, user_events = guard.pre_user_turn("yes", None, 2)
    events.extend(user_events)
    _, dispatch = guard.pre_tool_call(proposed, None, [], 3)
    events.extend(dispatch)
    trace = AgentTrace(
        task_id="synthetic",
        domain="retail",
        agent_variant="safeguard-transaction",
        system_prompt="",
        tool_calls_log=[ToolCall(name=proposed.name, arguments=proposed.arguments, raw_result="success")],
        metadata={
            "guardrail_events": [
                {
                    "turn": event.turn,
                    "enforcer": event.enforcer,
                    "hook": event.hook,
                    "action": event.action,
                    "tool_name": event.tool_name,
                    "reason": event.reason,
                    "extra": event.extra,
                }
                for event in events
            ]
        },
    )
    signature = guard._signature(proposed.name, proposed.arguments)
    result = check_production_trace(
        trace,
        ProductionRecognition(
            requests_by_turn={2: [signature]},
            full_assent_turns={2},
        ),
    )
    assert result.passed, result.violations


def test_production_checker_rejects_executed_write_without_dispatch_audit():
    trace = AgentTrace(
        task_id="synthetic",
        domain="retail",
        agent_variant="safeguard-transaction",
        system_prompt="",
        tool_calls_log=[ToolCall(name="write", arguments={"value": 1})],
    )
    signature = action_signature("write", {"value": 1})
    result = check_production_trace(
        trace,
        ProductionRecognition(requests_by_turn={0: [signature]}),
    )
    assert not result.passed
