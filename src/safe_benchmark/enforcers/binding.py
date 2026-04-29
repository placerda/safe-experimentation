"""BindingEnforcer (Scope dimension).

Filters the OpenAI tool catalog so disallowed_actions are completely
removed before the catalog is sent to the LLM. This is "true" tool binding:
the model literally cannot emit a disallowed tool call because the function
does not exist in its API surface.

This contrasts with v3's "binding" variant which only appended the
allowed-tools list to the system prompt as text — the model could still
ignore the prompt and call any tool. By removing the tools from the
catalog we make scope violations on disallowed tools impossible by
construction (modulo the model trying to call something we forgot to list).

If ``allowed_actions`` is non-empty, only those tools are kept. Otherwise
only ``disallowed_actions`` are removed (open-world default).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from safe_benchmark.enforcers import Enforcer, GuardrailEvent

if TYPE_CHECKING:
    from safe_benchmark.task_loader import AnnotatedTask


class BindingEnforcer(Enforcer):
    name = "binding"

    def filter_tools(
        self,
        openai_tools: list[dict[str, Any]],
        task: "AnnotatedTask",
    ) -> tuple[list[dict[str, Any]], list[GuardrailEvent]]:
        scope = task.annotation.safe.scope
        allowed = set(scope.allowed_actions or [])
        disallowed = set(scope.disallowed_actions or [])

        if not allowed and not disallowed:
            return openai_tools, []

        kept: list[dict[str, Any]] = []
        removed: list[str] = []
        for t in openai_tools:
            tname = t.get("function", {}).get("name", "")
            if tname in disallowed:
                removed.append(tname)
                continue
            if allowed and tname not in allowed:
                removed.append(tname)
                continue
            kept.append(t)

        events: list[GuardrailEvent] = []
        if removed:
            events.append(
                GuardrailEvent(
                    turn=0,
                    enforcer=self.name,
                    hook="filter_tools",
                    action="filter",
                    reason=f"Removed {len(removed)} tools out of scope",
                    extra={
                        "removed": removed,
                        "kept_count": len(kept),
                        "original_count": len(openai_tools),
                    },
                )
            )
        return kept, events
