"""Runtime guardrail enforcers for v4.

Each enforcer is a small, single-responsibility object that hooks into the
agent_runner loop at well-defined points. The agent always sees the same
baseline system prompt — what differs across variants is which enforcers are
active.

Hooks (all optional; default to pass-through):

  - ``filter_tools(openai_tools, task)``:
      Modify the OpenAI tool catalog before it is passed to the LLM.
      Used by the ``BindingEnforcer`` to remove disallowed tools entirely.

  - ``pre_tool_call(tool_call, task, history)``:
      Inspect a tool call the agent just emitted, BEFORE it is dispatched
      to the τ³ environment. Return a ``Decision`` of ALLOW, BLOCK or
      REWRITE. A BLOCK decision causes the runner to fabricate a synthetic
      tool result (the ``reason``) instead of executing the call.

  - ``post_tool_call(tool_call, result, task, history)``:
      Update enforcer-internal state after a successful execution.

  - ``pre_user_turn(user_msg, task, history)``:
      Inspect the user's incoming message before the agent replies.
      Return an optional system-style reminder string.

Events emitted by enforcers are appended to ``trace.metadata['guardrail_events']``
so the analysis phase can audit how often each enforcer fired.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from safe_benchmark.task_loader import AnnotatedTask
    from safe_benchmark.trace_schema import ToolCall


@dataclass
class Decision:
    action: str = "allow"  # "allow" | "block" | "rewrite"
    reason: str = ""
    replacement: dict[str, Any] | None = None
    enforcer: str = ""


@dataclass
class GuardrailEvent:
    turn: int
    enforcer: str
    hook: str  # "filter_tools" | "pre_tool_call" | "post_tool_call" | "pre_user_turn"
    action: str  # "allow" | "block" | "rewrite" | "remind" | "filter"
    tool_name: str = ""
    reason: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


class Enforcer:
    """Base class. Subclasses override only the hooks they need."""

    name: str = "noop"

    def filter_tools(
        self,
        openai_tools: list[dict[str, Any]],
        task: "AnnotatedTask",
    ) -> tuple[list[dict[str, Any]], list[GuardrailEvent]]:
        return openai_tools, []

    def pre_tool_call(
        self,
        tool_call: "ToolCall",
        task: "AnnotatedTask",
        history: list["ToolCall"],
        turn: int,
    ) -> tuple[Decision, list[GuardrailEvent]]:
        return Decision(action="allow", enforcer=self.name), []

    def post_tool_call(
        self,
        tool_call: "ToolCall",
        result: str,
        task: "AnnotatedTask",
        turn: int,
    ) -> list[GuardrailEvent]:
        return []

    def pre_user_turn(
        self,
        user_msg: str,
        task: "AnnotatedTask",
        turn: int,
    ) -> tuple[str | None, list[GuardrailEvent]]:
        return None, []


def build_stack(names: list[str]) -> list[Enforcer]:
    """Instantiate enforcers in canonical order: binding -> evidence -> flow -> escalation.

    Unknown names are silently dropped. Order matters: binding shapes the
    catalog first; evidence runs before flow because evidence-gated calls
    may also be out-of-order; flow runs before escalation.
    """
    from safe_benchmark.enforcers.binding import BindingEnforcer
    from safe_benchmark.enforcers.escalation import EscalationGateEnforcer
    from safe_benchmark.enforcers.evidence import EvidenceBinderEnforcer
    from safe_benchmark.enforcers.flow_fsm import FlowFSMEnforcer

    registry: dict[str, type[Enforcer]] = {
        "binding": BindingEnforcer,
        "evidence": EvidenceBinderEnforcer,
        "flow": FlowFSMEnforcer,
        "escalation": EscalationGateEnforcer,
    }
    canonical = ["binding", "evidence", "flow", "escalation"]
    requested = set(names)
    return [registry[n]() for n in canonical if n in requested and n in registry]
