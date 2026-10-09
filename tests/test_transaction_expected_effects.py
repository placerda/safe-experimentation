"""Approved sequences bind exact predicted local effects, not fresh arbitrary state."""

from types import SimpleNamespace

import pytest

from safe_benchmark.enforcers.transaction import TransactionGuardEnforcer
from safe_benchmark.trace_schema import ToolCall
from tau2.domains.retail.data_model import GiftCard, RetailDB
from tau2.domains.retail.tools import RetailTools


def backend_guard():
    address = {
        "address1": "1 Old Road", "address2": "", "city": "Town",
        "state": "CA", "country": "USA", "zip": "12345",
    }
    db = RetailDB.model_validate({
        "products": {},
        "users": {"u": {
            "user_id": "u", "name": {"first_name": "Test", "last_name": "User"},
            "address": address, "email": "test@example.invalid",
            "payment_methods": {
                "gift_card_1": {"id": "gift_card_1", "source": "gift_card", "balance": 4.01},
            },
            "orders": ["#W1", "#W2"],
        }},
        "orders": {oid: {
            "order_id": oid, "user_id": "u", "address": address, "items": [],
            "status": "pending", "fulfillments": [],
            "payment_history": [{
                "transaction_type": "payment", "amount": amount,
                "payment_method_id": "gift_card_1",
            }],
        } for oid, amount in [("#W1", 7.32), ("#W2", 2.21)]},
    })
    tools = RetailTools(db)
    guard = TransactionGuardEnforcer()
    guard.bind_env(SimpleNamespace(tools=tools), "retail")
    guard.pre_user_turn("Update my addresses or cancel my orders.", None, 0)
    guard.post_tool_call(ToolCall(name="find_user_id_by_email"), "u", None, 0)
    for oid in db.orders:
        guard.post_tool_call(
            ToolCall(name="get_order_details", arguments={"order_id": oid}),
            oid, None, 0,
        )
    return guard, tools


def address_call(street, user=False):
    return ToolCall(
        name="modify_user_address" if user else "modify_pending_order_address",
        arguments={
            "user_id" if user else "order_id": "u" if user else "#W1",
            "address1": street, "address2": "", "city": "Town",
            "state": "CA", "country": "USA", "zip": "12345",
        },
    )


def stage(guard, calls):
    for call in calls:
        assert guard.pre_tool_call(call, None, [], 1)[0].action == "block"
    manifest = guard.render_assistant("")
    guard.observe_assistant(manifest)
    guard.pre_user_turn("yes", None, 2)
    return manifest


@pytest.mark.parametrize("user", [False, True])
def test_exact_address_effect_matches_real_backend_and_no_preparation_mutation(user):
    guard, tools = backend_guard()
    first, second = address_call("2 New Road", user), address_call("3 Final Road")
    before = tools.db.model_dump()
    manifest = stage(guard, [first, second])
    assert tools.db.model_dump() == before
    assert "earlier listed" in manifest
    assert guard.pre_tool_call(first, None, [], 3)[0].action == "allow"
    getattr(tools, first.name)(**first.arguments)
    assert not guard._check_confirmation(second.name, second.arguments)
    assert guard.pre_tool_call(second, None, [], 4)[0].action == "allow"


def test_gift_card_refund_effect_matches_real_backend():
    guard, tools = backend_guard()
    first, second = [
        ToolCall(
            name="cancel_pending_order",
            arguments={"order_id": oid, "reason": "no longer needed"},
        ) for oid in ("#W1", "#W2")
    ]
    before = tools.db.model_dump()
    stage(guard, [first, second])
    assert tools.db.model_dump() == before
    assert guard.pre_tool_call(first, None, [], 3)[0].action == "allow"
    tools.cancel_pending_order(**first.arguments)
    assert tools.db.users["u"].payment_methods["gift_card_1"].balance == 11.33
    assert not guard._check_confirmation(second.name, second.arguments)
    assert guard.pre_tool_call(second, None, [], 4)[0].action == "allow"
    tools.cancel_pending_order(**second.arguments)
    assert tools.db.orders["#W2"].status == "cancelled"


@pytest.mark.parametrize("effect", ["missing", "wrong-address", "extra-user-change"])
def test_missing_or_unexpected_effect_is_not_authorized(effect):
    guard, tools = backend_guard()
    first, second = address_call("2 New Road"), address_call("3 Final Road")
    stage(guard, [first, second])
    assert guard.pre_tool_call(first, None, [], 3)[0].action == "allow"
    if effect != "missing":
        tools.modify_pending_order_address(**first.arguments)
    if effect == "wrong-address":
        tools.db.orders["#W1"].address.zip = "99999"
    if effect == "extra-user-change":
        tools.db.users["u"].email = "changed@example.invalid"
    decision, events = guard.pre_tool_call(second, None, [], 4)
    assert decision.action == "block"
    assert "F:transaction_stale" in events[0].extra["rules"]


def test_extra_refund_balance_change_requires_new_authorization():
    guard, tools = backend_guard()
    first = ToolCall(
        name="cancel_pending_order",
        arguments={"order_id": "#W1", "reason": "ordered by mistake"},
    )
    second = address_call("3 Final Road")
    stage(guard, [first, second])
    assert guard.pre_tool_call(first, None, [], 3)[0].action == "allow"
    tools.cancel_pending_order(**first.arguments)
    tools.db.users["u"].payment_methods["gift_card_1"].balance += 1
    assert guard._check_confirmation(second.name, second.arguments)[0].rule == "transaction_stale"


def test_refund_display_distinguishes_original_method_from_selected_method():
    guard, tools = backend_guard()
    original_args = {
        "order_id": "#W1", "item_ids": [], "payment_method_id": "gift_card_1",
    }
    display = guard._display("return_delivered_order_items", original_args)
    assert 'Recorded original payment method IDs' in display
    assert '["gift_card_1"]' in display
    assert "selected method is a recorded original payment method" in display

    tools.db.users["u"].payment_methods["gift_card_2"] = GiftCard(
        source="gift_card", id="gift_card_2", balance=1,
    )
    other_args = {**original_args, "payment_method_id": "gift_card_2"}
    other_display = guard._display("return_delivered_order_items", other_args)
    assert '"gift_card_2"' in other_display
    assert '["gift_card_1"]' in other_display
    assert "selected method is a recorded original payment method" not in other_display
