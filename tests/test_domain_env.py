"""Regression test for the `_load_domain_env` unpack bug.

Runs from 20260426_140718 onward unpacked `(toolkit, env, tools)` while the
function returns `(env, toolkit, tools)`, so ~all tool calls errored. This test
pins the return order and checks a real read tool succeeds.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("tau2")

DOMAINS_DIR = Path("data/t3/data/tau2/domains")

pytestmark = pytest.mark.skipif(
    not (DOMAINS_DIR / "airline" / "tasks.json").exists(),
    reason="T3/tau2 domain data not available",
)


@pytest.mark.parametrize("domain", ["airline", "retail"])
def test_load_domain_env_return_order_and_tool_execution(domain: str) -> None:
    from tau2.data_model.message import ToolCall

    from safe_benchmark.agent_runner import _load_domain_env

    env, toolkit, tools = _load_domain_env(domain)

    assert toolkit is env.tools
    assert isinstance(tools, list) and tools
    assert all(isinstance(t, dict) for t in tools)

    user_id = next(iter(env.tools.db.users))
    response = env.get_response(
        ToolCall(
            id="t1",
            name="get_user_details",
            arguments={"user_id": user_id},
            requestor="assistant",
        )
    )
    assert not response.error
    assert not str(response.content).startswith("Error")
    assert user_id in str(response.content)
