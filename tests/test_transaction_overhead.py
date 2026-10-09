import json

import pytest

from safe_benchmark.trace_schema import AgentTrace, Message, ToolCall
from scripts.report_transaction_overhead import MANIFEST_PREFIX, measure, report


def trace(**kwargs):
    return AgentTrace(
        task_id="retail_example", domain="retail", system_prompt="",
        agent_variant=kwargs.pop("agent_variant", "safeguard-transaction"), **kwargs,
    )


def event(action, rules=(), enforcer="safeguard-transaction"):
    return {"action": action, "enforcer": enforcer, "extra": {"rules": list(rules)}}


def test_protocol_blocks_are_not_policy_blocks():
    row = measure(trace(
        metadata={"guardrail_events": [
            event("block", ["F:transaction_unbound"]), event("prepare"),
            event("block", ["F:transaction_stale"]),
            event("block", ["F:transaction_unbound", "A:intent_address_source"]),
            event("block", enforcer="another-monitor"),
        ]},
        tool_calls_log=[ToolCall(name="write", blocked=True)],
    ))
    assert row.preparations == 1
    assert row.protocol_blocks == 2
    assert row.other_block_events == 2
    assert row.blocked_tool_calls == 1


@pytest.mark.parametrize("reply, approvals", [("yes", 1), ("yes, but change it", 0)])
def test_manifest_reply_counts_are_controlled(reply, approvals):
    row = measure(trace(messages=[
        Message(role="user", content="initial request"),
        Message(role="assistant", content=MANIFEST_PREFIX + " exact arguments"),
        Message(role="user", content=reply),
        Message(role="user", content="yes"),
    ]))
    assert row.manifest_presentations == 1
    assert row.controlled_approvals == approvals
    assert row.user_turns == 3


def test_baseline_text_does_not_establish_a_trusted_manifest():
    row = measure(trace(agent_variant="baseline", messages=[
        Message(role="assistant", content=MANIFEST_PREFIX),
        Message(role="user", content="yes"),
    ]))
    assert row.manifest_presentations == row.controlled_approvals == 0


def test_errors_are_excluded_and_duplicate_trace_keys_rejected(tmp_path):
    folder = tmp_path / "traces"
    folder.mkdir()
    (folder / "a.json").write_text(trace(error="429").model_dump_json())
    out = tmp_path / "analysis"
    report(tmp_path, out)
    summary = json.loads((out / "overhead.json").read_text())["summary"]["safeguard-transaction"]
    assert summary["excluded_error_traces"] == 1
    assert summary["means"]["preparations"] is None
    (folder / "b.json").write_text(trace().model_dump_json())
    with pytest.raises(ValueError, match="Duplicate"):
        report(tmp_path, out)


def test_missing_traces_fail_explicitly(tmp_path):
    with pytest.raises(ValueError, match="No traces"):
        report(tmp_path, tmp_path / "analysis")
