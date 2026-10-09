"""Finite adversarial event sequences; no benchmark task or gold inputs."""

from itertools import product
from types import SimpleNamespace

import pytest

from safe_benchmark.enforcers.transaction import TransactionGuardEnforcer
from safe_benchmark.trace_schema import ToolCall


def synthetic_guard():
    address = {
        "address1": "1 Old Road", "address2": "", "city": "Town",
        "state": "CA", "country": "USA", "zip": "12345",
    }
    db = SimpleNamespace(
        users={"u": {"user_id": "u", "address": address.copy()}},
        orders={
            "#W1": {
                "order_id": "#W1", "user_id": "u", "status": "pending",
                "address": address.copy(), "items": [], "payment_history": [],
            },
        },
        products={},
    )
    guard = TransactionGuardEnforcer()
    guard.bind_env(SimpleNamespace(tools=SimpleNamespace(db=db)), "retail")
    guard.pre_user_turn("Update my order address.", None, 0)
    guard.post_tool_call(ToolCall(name="find_user_id_by_email"), "u", None, 0)
    guard.post_tool_call(
        ToolCall(name="get_order_details", arguments={"order_id": "#W1"}),
        "#W1", None, 0,
    )
    call = ToolCall(
        name="modify_pending_order_address",
        arguments={**address, "address1": "2 New Road", "order_id": "#W1"},
    )
    return guard, call


EVENTS = ("prepare", "present", "yes", "qualified", "consume", "mutate")


@pytest.mark.parametrize("events", product(EVENTS, repeat=5))
def test_only_presented_current_unconsumed_approval_dispatches(events):
    guard, proposed = synthetic_guard()
    pending = False
    presented = False
    approved = False
    snapshot_version = 0
    prepared_version = None
    version = 0

    for turn, event in enumerate(events, 1):
        if event == "prepare":
            decision, _ = guard.pre_tool_call(proposed, None, [], turn)
            if approved and prepared_version == version:
                assert decision.action == "allow"
                approved = False
            else:
                assert decision.action == "block"
                approved = False
                if not pending:
                    prepared_version = version
                pending = True
                presented = False
        elif event == "present":
            guard.observe_assistant(guard.render_assistant("untrusted summary"))
            presented = pending
        elif event in ("yes", "qualified"):
            guard.pre_user_turn("yes" if event == "yes" else "yes, but wait", None, turn)
            approved = pending and presented and event == "yes"
            pending = False
            presented = False
        elif event == "consume":
            if approved and prepared_version == version:
                assert not guard._check_confirmation(proposed.name, proposed.arguments)
                assert guard.pre_tool_call(proposed, None, [], turn)[0].action == "allow"
                guard.post_tool_call(proposed, "Error: backend failure", None, turn)
                approved = False
        elif event == "mutate":
            snapshot_version += 1
            guard.state.db.orders["#W1"]["address"]["zip"] = f"{snapshot_version:05d}"
            version += 1

        accepted = not guard._check_confirmation(proposed.name, proposed.arguments)
        assert accepted == (approved and prepared_version == version)
        substituted = {**proposed.arguments, "address1": "9 Other Road"}
        assert guard._check_confirmation(proposed.name, substituted)


@pytest.mark.parametrize("payload", [
    ["a", "b"], {"items": ["a", "b"]}, {"details": {"amount": 1}},
])
def test_nested_argument_values_are_bound(payload):
    guard, proposed = synthetic_guard()
    proposed.arguments["extension"] = payload
    guard.pre_tool_call(proposed, None, [], 1)
    guard.observe_assistant(guard.render_assistant(""))
    guard.pre_user_turn("yes", None, 2)
    assert not guard._check_confirmation(proposed.name, proposed.arguments)
    assert guard._check_confirmation(
        proposed.name, {**proposed.arguments, "extension": ["different"]},
    )


def test_json_key_order_is_not_an_argument_substitution():
    guard, proposed = synthetic_guard()
    guard.pre_tool_call(proposed, None, [], 1)
    guard.observe_assistant(guard.render_assistant(""))
    guard.pre_user_turn("yes", None, 2)
    reordered = dict(reversed(list(proposed.arguments.items())))
    assert not guard._check_confirmation(proposed.name, reordered)


def test_array_order_is_an_argument_substitution():
    guard, proposed = synthetic_guard()
    proposed.arguments["extension"] = ["a", "b"]
    guard.pre_tool_call(proposed, None, [], 1)
    guard.observe_assistant(guard.render_assistant(""))
    guard.pre_user_turn("yes", None, 2)
    changed = {**proposed.arguments, "extension": ["b", "a"]}
    assert guard._check_confirmation(proposed.name, changed)
