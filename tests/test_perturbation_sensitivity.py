
from safe_benchmark.trace_schema import AgentTrace, Message, ToolCall
from scripts.perturbation_sensitivity import (
    perturb_drop_tool_call,
    perturb_remove_escalation_message,
    perturb_swap_adjacent_steps,
)


def make_trace() -> AgentTrace:
    return AgentTrace(
        task_id="t1",
        domain="airline",
        agent_variant="baseline",
        system_prompt="test",
        tool_calls_log=[
            ToolCall(name="get_user_details", arguments={"user_id": "u"}),
            ToolCall(name="get_reservation_details", arguments={"reservation_id": "r"}),
        ],
        messages=[
            Message(role="assistant", content=None, tool_calls=[ToolCall(name="get_user_details", arguments={})]),
            Message(role="assistant", content="I cannot do that because policy does not allow it."),
        ],
    )


def test_drop_tool_call_removes_first_flat_and_message_call():
    perturbed = perturb_drop_tool_call(make_trace())
    assert perturbed is not None
    assert [tc.name for tc in perturbed.tool_calls_log] == ["get_reservation_details"]
    assert perturbed.messages[0].tool_calls == []


def test_swap_adjacent_steps_swaps_first_two_flat_calls_only():
    perturbed = perturb_swap_adjacent_steps(make_trace())
    assert perturbed is not None
    assert [tc.name for tc in perturbed.tool_calls_log] == ["get_reservation_details", "get_user_details"]


def test_remove_escalation_message_blanks_refusal_text():
    perturbed = perturb_remove_escalation_message(make_trace())
    assert perturbed is not None
    assert perturbed.messages[1].content == ""
