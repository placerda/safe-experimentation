"""Diagnose guard decisions on recorded states, without claiming live outcomes.

Every originally executed call is replayed even if the candidate guard would
block it. Original blocks are skipped. Consequently later states belong to
the original trajectory, not a counterfactual guarded trajectory. Gold actions
are used only for offline labels, never passed to the guard.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for directory in (ROOT, ROOT / "src"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from pydantic import BaseModel, Field  # noqa: E402

from safe_benchmark.agent_runner import _load_domain_env  # noqa: E402
from safe_benchmark.enforcers.safeguard import SafeGuardEnforcer, WRITE_TOOLS  # noqa: E402
from safe_benchmark.evaluators.safety_metrics import (  # noqa: E402
    _attr, _gold_actions, _is_effective, _signature,
)
from safe_benchmark.task_loader import SelectedTask, load_selected_tasks  # noqa: E402
from safe_benchmark.trace_schema import AgentTrace, ToolCall  # noqa: E402


class ReplayDecision(BaseModel):
    call_index: int
    tool: str
    originally_blocked: bool
    effective: bool
    gold_match: bool
    candidate_blocked: bool
    rules: list[str] = Field(default_factory=list)


def replay_trace(trace: AgentTrace, task: SelectedTask, env=None, guard_factory=None) -> list[ReplayDecision]:
    from tau2.data_model.message import ToolCall as TauCall

    flattened = [call for msg in trace.messages for call in msg.tool_calls]
    if flattened != trace.tool_calls_log:
        raise ValueError(f"{trace.task_id}: message calls differ from flat log")
    if trace.error:
        raise ValueError(f"{trace.task_id}: invalid source trace: {trace.error}")
    if env is None:
        env, _, _ = _load_domain_env(trace.domain)
    guard = (guard_factory or SafeGuardEnforcer)()
    guard.bind_env(env, trace.domain)
    gold = Counter(
        _signature(_attr(action, "name", ""), _attr(action, "arguments", {}))
        for action in _gold_actions(task)
        if _attr(action, "name", "") in WRITE_TOOLS[trace.domain]
    )
    decisions = []
    history: list[ToolCall] = []
    index = 0
    turn = 0
    for msg in trace.messages:
        if msg.role == "user":
            guard.pre_user_turn(msg.content, None, turn)
        elif msg.role == "assistant":
            if not msg.tool_calls:
                guard.observe_assistant(msg.content or "")
            for call in msg.tool_calls:
                counters = guard.state.blocks_since_user_turn.copy()
                total = guard.state.total_blocks
                decision, events = guard.pre_tool_call(call, None, history, turn)
                errors = [event.reason for event in events if event.action == "rule_error"]
                if errors:
                    raise ValueError(f"{trace.task_id} call {index}: {errors}")
                # Hypothetical blocks must not modify the observed trajectory.
                guard.state.blocks_since_user_turn = counters
                guard.state.total_blocks = total
                effective = _is_effective(call)
                signature = _signature(call.name, call.arguments)
                match = effective and gold[signature] > 0
                if match:
                    gold[signature] -= 1
                if call.name in WRITE_TOOLS[trace.domain]:
                    decisions.append(ReplayDecision(
                        call_index=index, tool=call.name,
                        originally_blocked=call.blocked, effective=effective,
                        gold_match=match, candidate_blocked=decision.action == "block",
                        rules=[rule for event in events
                               for rule in (event.extra or {}).get("rules", [])],
                    ))
                if call.blocked:
                    guard.state.blocks_since_user_turn[call.name] += 1
                    guard.state.total_blocks += 1
                else:
                    response = env.get_response(TauCall(
                        id=f"replay-{index}", name=call.name,
                        arguments=call.arguments, requestor="assistant",
                    ))
                    actual = response.content or ""
                    expected = call.raw_result if call.raw_result is not None else call.result
                    if actual != expected:
                        raise ValueError(
                            f"{trace.task_id} call {index} ({call.name}): result mismatch"
                        )
                    guard.post_tool_call(call, actual, None, turn)
                history.append(call)
                index += 1
            turn += 1
    return decisions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--tasks-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--guard", choices=("safeguard", "safeguard-transaction"), default="safeguard")
    args = parser.parse_args()
    tasks = {task.task_id: task for task in load_selected_tasks(args.tasks_dir)}
    paths = sorted((args.run_dir / "traces").glob("*.json"))
    if not paths:
        raise ValueError("No source traces found")
    records = []
    counts = Counter()
    rules = Counter()
    factory = SafeGuardEnforcer
    if args.guard == "safeguard-transaction":
        from safe_benchmark.enforcers.transaction import TransactionGuardEnforcer
        factory = TransactionGuardEnforcer
    for path in paths:
        trace = AgentTrace.model_validate_json(path.read_text(encoding="utf-8"))
        decisions = replay_trace(trace, tasks[trace.task_id], guard_factory=factory)
        counts["traces"] += 1
        for item in decisions:
            records.append({
                "trace": path.name, "task_id": trace.task_id,
                "variant": trace.agent_variant, "seed": trace.seed,
                **item.model_dump(),
            })
            if item.effective:
                counts["effective_writes"] += 1
                counts["gold_matches" if item.gold_match else "non_gold_writes"] += 1
                if item.candidate_blocked:
                    counts["blocked_gold_matches" if item.gold_match
                           else "blocked_non_gold_writes"] += 1
                    rules.update(item.rules)
    report = {
        "guard": args.guard,
        "interpretation": "Offline diagnostics, not live safety or task success.",
        "non_gold_caveat": "Non-gold writes are not necessarily unsafe.",
        "transaction_caveat": "Old traces have no trusted manifests. Unbound preparation "
                              "blocks are protocol differences, not detected unsafe writes.",
        "counts": dict(counts), "rules_on_effective_writes": dict(rules),
        "decisions": records,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "shadow.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "decisions"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
