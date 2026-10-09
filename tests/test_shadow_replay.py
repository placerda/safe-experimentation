"""Replay must reproduce observed states, not hypothetical guarded states."""

from types import SimpleNamespace

import pytest

from scripts import shadow_replay as replay
from safe_benchmark.trace_schema import AgentTrace, Message, ToolCall
from safe_benchmark.task_loader import SelectedTask


class FakeEnvironment:
    def __init__(self):
        self.executed = []
        self.tools = SimpleNamespace(db={})

    def get_response(self, call):
        self.executed.append(call.name)
        return SimpleNamespace(content="observed")


class FakeGuard:
    instances = []

    def __init__(self):
        self.instances.append(self)
        self.turns = []
        self.seen_counts = []
        self.post_calls = []

    def bind_env(self, env, domain):
        from collections import Counter
        self.state = SimpleNamespace(blocks_since_user_turn=Counter(), total_blocks=0)

    def observe_assistant(self, text):
        self.turns.append(("assistant", text))

    def pre_user_turn(self, text, task, turn):
        self.turns.append(("user", text))

    def pre_tool_call(self, call, task, history, turn):
        self.seen_counts.append(self.state.total_blocks)
        self.state.total_blocks += 1
        self.state.blocks_since_user_turn[call.name] += 1
        return SimpleNamespace(action="block"), []

    def post_tool_call(self, call, result, task, turn):
        self.post_calls.append(call.name)


def fixtures(monkeypatch, blocked=False, raw="observed"):
    monkeypatch.setattr(replay, "SafeGuardEnforcer", FakeGuard)
    calls = [
        ToolCall(name="modify_user_address", arguments={"user_id": "u"}, result="blocked",
                 blocked=blocked, raw_result=None if blocked else raw),
        ToolCall(name="modify_user_address", arguments={"user_id": "u"}, result="observed",
                 raw_result="observed"),
    ]
    trace = AgentTrace(task_id="synthetic", domain="retail", agent_variant="baseline",
                       system_prompt="", tool_calls_log=calls, messages=[
                           Message(role="user", content="hello"),
                           Message(role="assistant", content="confirm?"),
                           Message(role="user", content="yes"),
                           Message(role="assistant", tool_calls=calls),
                       ])
    task = SelectedTask(task_id="synthetic", source="synthetic", source_task_id="1",
                        domain="retail", user_goal="offline only")
    return trace, task, FakeEnvironment()


def test_hypothetical_blocks_do_not_change_later_state(monkeypatch):
    trace, task, env = fixtures(monkeypatch)
    decisions = replay.replay_trace(trace, task, env)
    g = FakeGuard.instances[-1]
    assert g.seen_counts == [0, 0]
    assert env.executed == ["modify_user_address"] * 2
    assert g.post_calls == env.executed
    assert len(decisions) == 2
    assert [decision.call_index for decision in decisions] == [0, 1]
    assert g.turns == [("user", "hello"), ("assistant", "confirm?"), ("user", "yes")]


def test_original_blocks_are_skipped_and_counted(monkeypatch):
    trace, task, env = fixtures(monkeypatch, blocked=True)
    replay.replay_trace(trace, task, env)
    assert env.executed == ["modify_user_address"]
    assert FakeGuard.instances[-1].seen_counts == [0, 1]


def test_result_mismatch_is_explicit(monkeypatch):
    trace, task, env = fixtures(monkeypatch, raw="wrong")
    with pytest.raises(ValueError, match="result mismatch"):
        replay.replay_trace(trace, task, env)


def test_flat_log_mismatch_is_explicit(monkeypatch):
    trace, task, env = fixtures(monkeypatch)
    trace.tool_calls_log = []
    with pytest.raises(ValueError, match="flat log"):
        replay.replay_trace(trace, task, env)


def test_source_errors_are_not_valid_replay(monkeypatch):
    trace, task, env = fixtures(monkeypatch)
    trace.error = "API error"
    with pytest.raises(ValueError, match="invalid source"):
        replay.replay_trace(trace, task, env)
