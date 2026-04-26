"""POC: run τ³-bench official evaluator on one of our existing traces.

This proves we can reproduce the reward without re-running the agent.
Usage: python scripts/t3_eval_poc.py [trace_path]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# tau2 imports
from tau2.data_model.message import (
    AssistantMessage,
    ToolCall as Tau2ToolCall,
    ToolMessage,
    UserMessage,
)
from tau2.data_model.simulation import SimulationRun, TerminationReason
from tau2.data_model.tasks import Task
from tau2.evaluator.evaluator import EvaluationType, evaluate_simulation


def load_tau2_task(task_id: str, source_task_id: str, domain: str) -> Task:
    """Load the corresponding tau2 Task object from the source tasks file."""
    domain_file = Path(f"data/t3/data/tau2/domains/{domain}/tasks.json")
    with open(domain_file, encoding="utf-8") as f:
        raw = json.load(f)
    # source_task_id is the int 'id' in tau2 tasks
    source_id = str(source_task_id)
    for t in raw:
        if str(t.get("id")) == source_id:
            return Task.model_validate(t)
    raise ValueError(f"Task {source_task_id} not found in {domain_file}")


def trace_to_tau2_messages(trace: dict[str, Any]) -> list:
    """Convert our trace messages into a list of tau2 Message subclasses."""
    out: list = []
    # Build a lookup of tool results by call: our trace records tool_calls on the
    # assistant message, then a sequence of "tool" messages with content. Pair them
    # up in order.
    msgs = trace["messages"]
    pending_tool_call_ids: list[str] = []
    tool_call_counter = 0

    for m in msgs:
        role = m["role"]
        content = m.get("content")
        tool_calls = m.get("tool_calls") or []

        if role == "user":
            out.append(UserMessage(role="user", content=content or ""))
        elif role == "assistant":
            tcs = []
            for tc in tool_calls:
                tool_call_counter += 1
                tc_id = f"call_{tool_call_counter:04d}"
                pending_tool_call_ids.append(tc_id)
                tcs.append(
                    Tau2ToolCall(
                        id=tc_id,
                        name=tc["name"],
                        arguments=tc.get("arguments") or {},
                        requestor="assistant",
                    )
                )
            out.append(
                AssistantMessage(
                    role="assistant",
                    content=content,
                    tool_calls=tcs or None,
                )
            )
        elif role == "tool":
            tc_id = pending_tool_call_ids.pop(0) if pending_tool_call_ids else f"call_unknown_{tool_call_counter}"
            out.append(
                ToolMessage(
                    role="tool",
                    id=tc_id,
                    content=content or "",
                    requestor="assistant",
                )
            )
    return out


def evaluate_trace_with_tau2(trace_path: Path) -> dict[str, Any]:
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    domain = trace["domain"]
    # Find the source_task_id from selected tasks
    selected_path = Path(f"data/selected_tasks/{domain}.jsonl")
    source_task_id = None
    raw_bytes = selected_path.read_bytes().decode("utf-8", errors="replace")
    for line in raw_bytes.splitlines():
        if not line.strip():
            continue
        st = json.loads(line)
        if st["task_id"] == trace["task_id"]:
            source_task_id = st["source_task_id"]
            break
    if source_task_id is None:
        raise ValueError(f"task_id {trace['task_id']} not found in {selected_path}")

    tau2_task = load_tau2_task(trace["task_id"], source_task_id, domain)
    tau2_messages = trace_to_tau2_messages(trace)

    sim = SimulationRun(
        id=f"poc_{trace['task_id']}_{trace['agent_variant']}",
        task_id=str(source_task_id),
        start_time="2026-01-01T00:00:00",
        end_time="2026-01-01T00:00:00",
        duration=0.0,
        termination_reason=TerminationReason.AGENT_STOP if trace["task_completed"] else TerminationReason.MAX_STEPS,
        messages=tau2_messages,
    )

    reward_info = evaluate_simulation(
        simulation=sim,
        task=tau2_task,
        evaluation_type=EvaluationType.ALL,
        solo_mode=False,
        domain=domain,
    )

    return {
        "task_id": trace["task_id"],
        "variant": trace["agent_variant"],
        "tau2_reward": reward_info.reward,
        "reward_basis": [r.value if hasattr(r, "value") else r for r in (reward_info.reward_basis or [])],
        "reward_breakdown": reward_info.reward_breakdown,
        "info": reward_info.info,
        "db_check": reward_info.db_check.model_dump() if reward_info.db_check else None,
        "communicate_checks": [c.model_dump() for c in (reward_info.communicate_checks or [])],
        "action_checks": [c.model_dump() for c in (reward_info.action_checks or [])],
    }


def main():
    if len(sys.argv) > 1:
        traces = [Path(sys.argv[1])]
    else:
        # Default: try a handful of existing traces from the gpt-4o run
        traces = [
            Path("outputs/runs/20260425_112848/traces/baseline_airline_000.json"),
            Path("outputs/runs/20260425_112848/traces/safe-aware_airline_000.json"),
            Path("outputs/runs/20260425_112848/traces/baseline_retail_000.json"),
            Path("outputs/runs/20260425_112848/traces/safe-aware_retail_000.json"),
        ]

    for tp in traces:
        if not tp.exists():
            print(f"SKIP (not found): {tp}")
            continue
        try:
            result = evaluate_trace_with_tau2(tp)
            print(f"\n=== {tp.name} ===")
            print(json.dumps(result, indent=2, default=str)[:1500])
        except Exception as e:
            print(f"\n=== {tp.name} ===")
            print(f"ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
