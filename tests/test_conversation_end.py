import pytest

from safe_benchmark.agent_runner import _user_ended_conversation


@pytest.mark.parametrize("text", [
    "No, that's all for now. Thank you for your help.",
    "No, that\u2019s all for now. Thank you for your help.",
    "That\u2018s all.",
    "GOODBYE",
    "Thank you, bye.",
    "Nothing else.",
])
def test_recognized_user_end_signals(text):
    assert _user_ended_conversation(text)


@pytest.mark.parametrize("text", [
    "Yes.",
    "Thanks. One more thing: return the backpack.",
    "Thank you.",
    "Please update my address.",
])
def test_nonterminal_replies_are_not_end_signals(text):
    assert not _user_ended_conversation(text)
