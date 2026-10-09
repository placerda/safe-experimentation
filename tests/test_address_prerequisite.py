"""Bounded recognized address obligations precede one-time item changes."""

from safe_benchmark.enforcers.intent import _address_prerequisite, check_intent
from tests.test_intent_binding import setup as item_setup
from tests.test_transaction_expected_effects import address_call, backend_guard


def setup():
    guard, tools = backend_guard()
    order = tools.db.orders["#W1"]
    order.items = []
    tools.db.users["u"].address.address1 = "2 New Road"
    return guard, tools, order


def rules(guard, tools, order, requests):
    return {violation.rule for violation in _address_prerequisite(
        guard, order, list(tools.db.orders.values()), requests, set(),
    )}


def test_profile_address_precedes_irreversible_item_change():
    guard, tools, order = setup()
    assert rules(guard, tools, order, [
        "Change the items and shipping address on #W1 to my default profile address.",
    ]) == {"address_prerequisite"}


def test_correct_address_already_applied_needs_no_reapproval():
    guard, tools, order = setup()
    order.address.address1 = "2 New Road"
    assert not rules(guard, tools, order, [
        "Change the items and shipping address on #W1 to my default address.",
    ])


def test_earlier_staged_address_allows_preparing_item_change():
    guard, tools, order = setup()
    address = address_call("2 New Road")
    assert guard.pre_tool_call(address, None, [], 1)[0].action == "block"
    assert not rules(guard, tools, order, [
        "Change shipping address on #W1 to my default address.",
    ])
    guard.authorization.pending[0].arguments["address1"] = "Wrong Street"
    assert rules(guard, tools, order, [
        "Change shipping address on #W1 to my default address.",
    ]) == {"address_prerequisite"}


def test_other_order_address_request_does_not_block():
    guard, tools, order = setup()
    assert not rules(guard, tools, order, [
        "Change shipping address on #W2 to my default address.",
    ])


def test_explicit_withdrawal_removes_address_prerequisite():
    guard, tools, order = setup()
    assert not rules(guard, tools, order, [
        "Update shipping address on #W1 to my default address.",
        "For #W1, do not update the shipping address.",
    ])


def test_existing_address_description_is_not_an_update_request():
    guard, tools, order = setup()
    assert not rules(guard, tools, order, [
        "The shipping address on #W1 is my default address. Return the items.",
    ])


def test_unretrieved_or_ambiguous_nyc_source_requires_resolution():
    guard, tools, order = setup()
    request = "Update #W1 to my NYC address, which is on another order."
    assert rules(guard, tools, order, [request]) == {"address_prerequisite_unresolved"}
    tools.db.orders["#W2"].address.city = "New York"
    assert rules(guard, tools, order, [request]) == {"address_prerequisite"}


def test_generic_pending_order_request_requires_unique_pending_target():
    guard, tools, order = setup()
    request = "Change the pending order items and address to my default profile address."
    assert not rules(guard, tools, order, [request])
    tools.db.orders["#W2"].status = "cancelled"
    assert rules(guard, tools, order, [request]) == {"address_prerequisite"}


def test_policy_entry_point_blocks_only_item_mutation_not_exchange():
    guard, _, _ = item_setup()
    user = guard._get_user(guard._get("orders", "#W2")["user_id"])
    user["address"] = {"address1": "New Street", "city": "Town"}
    request = "Change the camera order to my default profile address."
    args = {"order_id": "#W2", "item_ids": ["item_b"], "new_item_ids": ["item_b"]}
    violations = check_intent(guard, "modify_pending_order_items", args, [request])
    assert "address_prerequisite" in {violation.rule for violation in violations}
    assert "address_prerequisite" not in {
        violation.rule for violation in check_intent(
            guard, "exchange_delivered_order_items", args, [request],
        )
    }


def test_multiline_same_message_pending_address_obligation_survives_yes():
    guard, tools, order = setup()
    tools.db.orders["#W2"].status = "cancelled"
    request = (
        "Yes, please return the backpack only.\n"
        "Also I still need:\n- change my pending order item to red\n"
        "- change the order address to my default Chicago home in my profile"
    )
    guard.pre_user_turn(request, None, 1)
    assert request in guard.authorization.independent_requests
    assert not guard.authorization.approved
    assert rules(guard, tools, order, guard.authorization.independent_requests) == {
        "address_prerequisite",
    }


def test_unrelated_explicit_order_does_not_bind_generic_address_clause():
    guard, tools, order = setup()
    tools.db.orders["#W2"].status = "cancelled"
    assert not rules(guard, tools, order, [
        "Change my pending order item to red. "
        "For #W2 change the order address to my default address.",
    ])
