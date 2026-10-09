import pytest

from safe_benchmark.enforcers.transaction import _confirms_manifest
from tests.test_authorization_sequences import synthetic_guard


@pytest.mark.parametrize("text", [
    "yes",
    "Yes, that all looks right... yes, I authorize all of those actions "
    "with those exact values in that order.",
    "I approve all listed actions with the exact values in the order.",
])
def test_controlled_exact_manifest_assent(text):
    assert _confirms_manifest(text)


@pytest.mark.parametrize("text", [
    "Yes, but use another address.",
    "I approve all listed actions with the exact values in the order, except the return.",
    "Yes, that all looks right.",
    "No, I authorize all those actions with those exact values in that order.",
    "I authorize some of those actions with those exact values in that order.",
])
def test_qualification_or_partial_assent_is_not_manifest_approval(text):
    assert not _confirms_manifest(text)


def test_exact_wording_without_displayed_manifest_never_authorizes():
    guard, _ = synthetic_guard()
    guard.pre_user_turn(
        "I authorize all those actions with those exact values in that order.", None, 1,
    )
    assert not guard.authorization.approved


def test_complete_exact_assent_authorizes_only_current_one_use_payload():
    guard, proposed = synthetic_guard()
    assert guard.pre_tool_call(proposed, None, [], 1)[0].action == "block"
    guard.observe_assistant(guard.render_assistant(""))
    guard.pre_user_turn(
        "Yes, that all looks right... yes, I authorize all of those actions "
        "with those exact values in that order.", None, 2,
    )
    assert not guard._check_confirmation(proposed.name, proposed.arguments)
    assert guard._check_confirmation(
        proposed.name, {**proposed.arguments, "address1": "Other Road"},
    )
    assert guard.pre_tool_call(proposed, None, [], 3)[0].action == "allow"
    assert guard._check_confirmation(proposed.name, proposed.arguments)


def test_complete_exact_assent_cannot_authorize_tampered_manifest():
    guard, proposed = synthetic_guard()
    guard.pre_tool_call(proposed, None, [], 1)
    guard.observe_assistant(guard.render_assistant(""))
    guard.authorization.pending[0].arguments["address1"] = "Changed After Display"
    guard.pre_user_turn(
        "I authorize all those actions with those exact values in that order.", None, 2,
    )
    assert not guard.authorization.approved
