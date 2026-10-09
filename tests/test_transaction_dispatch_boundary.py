"""Approval must be spent before calling an irreversible backend."""

import pytest

from safe_benchmark.enforcers.safeguard import SafeGuardEnforcer
from safe_benchmark.trace_schema import ToolCall
from tests.test_authorization_sequences import synthetic_guard


def approved_guard():
    guard, proposed = synthetic_guard()
    guard.pre_tool_call(proposed, None, [], 1)
    guard.observe_assistant(guard.render_assistant(""))
    guard.pre_user_turn("yes", None, 2)
    return guard, proposed


def test_dispatch_gate_spends_approval_without_post_callback():
    guard, proposed = approved_guard()
    decision, _ = guard.pre_tool_call(proposed, None, [], 3)
    assert decision.action == "allow"
    assert not guard.authorization.approved
    assert guard._check_confirmation(proposed.name, proposed.arguments)


def test_post_observation_exception_does_not_restore_spent_approval(monkeypatch):
    guard, proposed = approved_guard()
    decision, _ = guard.pre_tool_call(proposed, None, [], 3)
    assert decision.action == "allow"

    def fail_observation(*args, **kwargs):
        raise ValueError("Injected post-dispatch observation failure")

    monkeypatch.setattr(SafeGuardEnforcer, "post_tool_call", fail_observation)
    with pytest.raises(ValueError, match="post-dispatch observation failure"):
        guard.post_tool_call(proposed, "success", None, 3)
    assert guard._check_confirmation(proposed.name, proposed.arguments)


def test_delayed_observer_does_not_revoke_next_independent_approval():
    guard, first = synthetic_guard()
    guard.state.db.orders["#W2"] = {
        **guard.state.db.orders["#W1"],
        "order_id": "#W2",
        "address": guard.state.db.orders["#W1"]["address"].copy(),
    }
    guard.post_tool_call(
        ToolCall(name="get_order_details", arguments={"order_id": "#W2"}),
        "#W2", None, 0,
    )
    second = first.model_copy(deep=True)
    second.arguments["order_id"] = "#W2"
    guard.pre_tool_call(first, None, [], 1)
    guard.pre_tool_call(second, None, [], 1)
    guard.observe_assistant(guard.render_assistant(""))
    guard.pre_user_turn("yes", None, 2)

    assert guard.pre_tool_call(first, None, [], 3)[0].action == "allow"
    assert not guard._check_confirmation(second.name, second.arguments)
    guard.post_tool_call(first, "success", None, 3)
    guard.post_tool_call(first, "duplicate delayed observation", None, 3)
    assert not guard._check_confirmation(second.name, second.arguments)
    assert guard.pre_tool_call(second, None, [], 4)[0].action == "allow"
    assert not guard.authorization.approved
