"""Tests for the trace -> tau2 message converter used by the tau2 reward.

Blocked tool calls never reached the environment, so they must be excluded
from the replay; otherwise tau2's set_state() re-executes them and the
replayed DB diverges from what the agent actually did.
"""

from __future__ import annotations

import pytest

pytest.importorskip("tau2")

from safe_benchmark.evaluators.tau2_reward import _trace_to_tau2_messages  # noqa: E402
from safe_benchmark.trace_schema import AgentTrace, Message, ToolCall  # noqa: E402


def _trace(messages: list[Message]) -> AgentTrace:
    return AgentTrace(
        task_id="t",
        domain="retail",
        agent_variant="test",
        system_prompt="",
        messages=messages,
    )


def test_blocked_calls_are_excluded_and_raw_result_is_replayed():
    from tau2.data_model.message import AssistantMessage, ToolMessage

    blocked = ToolCall(
        name="cancel_pending_order",
        arguments={"order_id": "#W1"},
        result="BLOCKED: confirm first",
        blocked=True,
        blocked_by="safeguard",
    )
    allowed = ToolCall(
        name="get_user_details",
        arguments={"user_id": "u1"},
        result="RAW\n\nnote",
        raw_result="RAW",
    )
    only_blocked = ToolCall(
        name="cancel_pending_order",
        arguments={"order_id": "#W2"},
        result="BLOCKED again",
        blocked=True,
        blocked_by="safeguard",
    )
    trace = _trace(
        [
            Message(role="user", content="hi"),
            Message(role="assistant", content=None, tool_calls=[blocked, allowed]),
            Message(role="tool", content="BLOCKED: confirm first"),
            Message(role="tool", content="RAW\n\nnote"),
            Message(role="assistant", content=None, tool_calls=[only_blocked]),
            Message(role="tool", content="BLOCKED again"),
            Message(role="assistant", content="Done."),
        ]
    )

    out = _trace_to_tau2_messages(trace)

    calls = [
        tc
        for m in out
        if isinstance(m, AssistantMessage) and m.tool_calls
        for tc in m.tool_calls
    ]
    tool_msgs = [m for m in out if isinstance(m, ToolMessage)]

    assert [c.name for c in calls] == ["get_user_details"]
    assert calls[0].id == "call_0001"
    assert len(tool_msgs) == 1
    assert tool_msgs[0].id == "call_0001"
    assert tool_msgs[0].content == "RAW"

    # The all-blocked, text-less assistant turn is dropped entirely.
    assistants = [m for m in out if isinstance(m, AssistantMessage)]
    assert len(assistants) == 2
    assert assistants[-1].content == "Done."


def test_legacy_trace_without_raw_result_uses_message_content():
    from tau2.data_model.message import ToolMessage

    call = ToolCall(name="get_user_details", arguments={"user_id": "u1"}, result="R")
    trace = _trace(
        [
            Message(role="user", content="hi"),
            Message(role="assistant", content=None, tool_calls=[call]),
            Message(role="tool", content="R"),
            Message(role="assistant", content="ok"),
        ]
    )

    out = _trace_to_tau2_messages(trace)
    tool_msgs = [m for m in out if isinstance(m, ToolMessage)]

    assert len(tool_msgs) == 1
    assert tool_msgs[0].content == "R"
    assert tool_msgs[0].id == "call_0001"


def test_ids_are_sequential_across_turns():
    from tau2.data_model.message import ToolMessage

    a = ToolCall(name="x", arguments={}, result="1", raw_result="1")
    b = ToolCall(name="y", arguments={}, result="2", raw_result="2")
    trace = _trace(
        [
            Message(role="user", content="hi"),
            Message(role="assistant", content=None, tool_calls=[a]),
            Message(role="tool", content="1"),
            Message(role="assistant", content=None, tool_calls=[b]),
            Message(role="tool", content="2"),
        ]
    )

    out = _trace_to_tau2_messages(trace)
    ids = [m.id for m in out if isinstance(m, ToolMessage)]

    assert ids == ["call_0001", "call_0002"]
