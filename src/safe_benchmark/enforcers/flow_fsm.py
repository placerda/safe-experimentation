"""FlowFSMEnforcer (Flow Integrity dimension).

Soft-warns (V1) when the agent calls a tool that violates a
``critical_order_constraints`` entry. The warning is injected as a
synthetic tool result asking the agent to do step X first, but the
original call is still executed (advisory mode).

Rationale (per plan §Open question Q3): start advisory to avoid
deadlocks with stacked enforcers; switch to hard-block in a follow-up
sweep if the effect is too small.

Step matching uses a coarse keyword-bucket heuristic: each step string
in ``expected_steps`` is split into tokens; a tool call is said to
"belong to step S" if any non-stopword token from S appears in the tool
name. Constraints have the form "X before Y" — we parse them with a
small regex and emit a warning if Y is called while no tool yet seen
matches X.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from safe_benchmark.enforcers import Decision, Enforcer, GuardrailEvent

if TYPE_CHECKING:
    from safe_benchmark.task_loader import AnnotatedTask
    from safe_benchmark.trace_schema import ToolCall


_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with",
    "by", "is", "be", "are", "was", "were", "step", "user", "agent",
    "first", "then", "before", "after", "must", "should", "would",
}

_BEFORE_RE = re.compile(
    r"^\s*(?P<x>.+?)\s+(?:must\s+come\s+)?before\s+(?P<y>.+?)\s*$",
    re.IGNORECASE,
)
_NEGATIVE_PREFIX_RE = re.compile(
    r"^\s*(?:do\s+not|don'?t|never)\s+",
    re.IGNORECASE,
)


_SUFFIXES = ("ization", "ation", "ising", "izing", "ing", "tion", "ion",
             "ment", "ness", "ies", "ed", "es", "ly", "al", "s")


def _stem(token: str) -> str:
    t = token.lower()
    if len(t) < 5:
        return t
    for suf in _SUFFIXES:
        if t.endswith(suf) and len(t) - len(suf) >= 3:
            return t[: -len(suf)]
    return t


def _tokens(text: str) -> set[str]:
    # Split on non-alphanumeric AND on underscores so tool names like
    # 'check_cancellation_eligibility' decompose into three tokens.
    parts = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {_stem(p) for p in parts if len(p) > 2 and p not in _STOPWORDS}


def _fuzzy_match(a: str, b: str, min_len: int = 4) -> bool:
    """True if either token shares a prefix of length min_len with the other."""
    if len(a) < min_len or len(b) < min_len:
        return a == b
    return a[:min_len] == b[:min_len]


def _tool_matches_step(tool_name: str, step_tokens: set[str]) -> bool:
    name_tokens = _tokens(tool_name)
    if name_tokens & step_tokens:
        return True
    for nt in name_tokens:
        for st in step_tokens:
            if _fuzzy_match(nt, st):
                return True
    return False


def _parse_constraint(constraint: str) -> tuple[set[str], set[str]] | None:
    """Return (prerequisite_tokens, dependent_tokens) or None.

    Handles three patterns:
    - "X before Y" -> X is prereq, Y is dependent
    - "Do not X before Y" / "Don't X before Y" -> SWAP: Y becomes prereq,
      X becomes dependent (because "do not X before Y" = "Y must precede X")
    - "After X, do Y" / "First X then Y" -> not yet matched, returns None
    """
    text = constraint.strip()
    is_negative = bool(_NEGATIVE_PREFIX_RE.match(text))
    text = _NEGATIVE_PREFIX_RE.sub("", text)
    m = _BEFORE_RE.match(text)
    if not m:
        return None
    x_tokens = _tokens(m.group("x"))
    y_tokens = _tokens(m.group("y"))
    if not x_tokens or not y_tokens:
        return None
    if is_negative:
        # "do not X before Y" => Y must happen before X
        # so Y is prereq, X is dependent.
        return y_tokens, x_tokens
    return x_tokens, y_tokens


class FlowFSMEnforcer(Enforcer):
    name = "flow"

    def pre_tool_call(
        self,
        tool_call: "ToolCall",
        task: "AnnotatedTask",
        history: list["ToolCall"],
        turn: int,
    ) -> tuple[Decision, list[GuardrailEvent]]:
        flow = task.annotation.safe.flow_integrity
        constraints = list(flow.critical_order_constraints or [])
        if not constraints:
            return Decision(action="allow", enforcer=self.name), []

        violated: list[str] = []
        for c in constraints:
            parsed = _parse_constraint(c)
            if parsed is None:
                continue
            x_tokens, y_tokens = parsed
            if not _tool_matches_step(tool_call.name, y_tokens):
                continue
            x_seen = any(_tool_matches_step(prev.name, x_tokens) for prev in history)
            if not x_seen:
                violated.append(c)

        if not violated:
            return Decision(action="allow", enforcer=self.name), []

        # V1: advisory only — allow but inject reminder via a guardrail event
        # the runner will surface as a synthetic system reminder on next turn.
        reason = (
            "[flow-fsm warning] The following step-order constraint(s) appear to be "
            "violated by tool '" + tool_call.name + "': " + "; ".join(violated)
            + ". Consider doing the prerequisite step(s) first."
        )
        ev = GuardrailEvent(
            turn=turn,
            enforcer=self.name,
            hook="pre_tool_call",
            action="remind",
            tool_name=tool_call.name,
            reason="out-of-order tool call",
            extra={"violated_constraints": violated, "advisory": True},
        )
        # action='allow' but reason carries the warning that the runner appends
        # to the tool result content as a postscript.
        return (
            Decision(action="allow", reason=reason, enforcer=self.name),
            [ev],
        )
