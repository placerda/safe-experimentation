"""τ³-bench official-reward evaluator integration.

Wraps tau2's `evaluate_simulation()` so we can score our recorded
traces against the official τ³-bench reward (action-matching,
DB-state, communicate-info, NL-assertions). This is a parallel
evaluator to the four SAFE evaluators — it answers the question
"did the agent complete the task per τ³-bench's own criteria?"
which is what reviewers will look for when we claim "no task
completion cost".

For NL_ASSERTION evaluation we route tau2's litellm calls through
the user's Azure OpenAI deployment via Entra ID, so all 60+ traces
can be scored without configuring a separate OpenAI/Anthropic key.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from safe_benchmark.task_loader import AnnotatedTask
from safe_benchmark.trace_schema import AgentTrace

# tau2 imports are lazy so importing this module doesn't pay the registry cost
# unless someone actually calls evaluate_tau2_reward.

_TAU2_TASKS_CACHE: dict[str, dict[str, Any]] = {}
_AZURE_AD_TOKEN: dict[str, Any] = {"token": None, "exp": 0.0}


def _load_tau2_task_dict(domain: str, source_task_id: str) -> dict[str, Any]:
    cache_key = f"{domain}:{source_task_id}"
    if cache_key in _TAU2_TASKS_CACHE:
        return _TAU2_TASKS_CACHE[cache_key]
    domain_file = Path("data/t3/data/tau2/domains") / domain / "tasks.json"
    with open(domain_file, encoding="utf-8") as f:
        raw = json.load(f)
    target = str(source_task_id)
    for t in raw:
        if str(t.get("id")) == target:
            _TAU2_TASKS_CACHE[cache_key] = t
            return t
    raise ValueError(f"τ³-bench task id={source_task_id} not in {domain_file}")


def _configure_azure_judge() -> None:
    """Configure tau2 + litellm to use the Azure OpenAI judge for NL assertions.

    Requirements (read from os.environ):
      - AZURE_OPENAI_ENDPOINT          (e.g. https://aif-...openai.azure.com/)
      - AZURE_OPENAI_JUDGE_DEPLOYMENT  (e.g. gpt-4.1)
      - AZURE_OPENAI_API_VERSION       (defaults to 2024-12-01-preview)

    Auth: prefers AZURE_OPENAI_API_KEY if set; otherwise uses
    DefaultAzureCredential to mint an Entra ID token (refreshed on demand).
    """
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
    deployment = os.environ.get(
        "AZURE_OPENAI_JUDGE_DEPLOYMENT", os.environ.get("AZURE_OPENAI_DEPLOYMENT", "")
    )
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    if not endpoint or not deployment:
        return  # judge unavailable; tau2 will hit its own auth path and likely fail

    # Override tau2 defaults so its evaluator targets the Azure deployment via litellm.
    from tau2 import config as _tau2_config

    azure_model = f"azure/{deployment}"
    _tau2_config.DEFAULT_LLM_NL_ASSERTIONS = azure_model
    _tau2_config.DEFAULT_LLM_ENV_INTERFACE = azure_model

    # The evaluator submodules do `from tau2.config import DEFAULT_LLM_NL_ASSERTIONS`
    # which captures the value at import time. We must overwrite their bindings
    # too if they have already been imported.
    try:
        from tau2.evaluator import evaluator_nl_assertions as _nl_mod

        _nl_mod.DEFAULT_LLM_NL_ASSERTIONS = azure_model
    except Exception:  # pragma: no cover
        pass

    os.environ["AZURE_API_BASE"] = endpoint
    os.environ["AZURE_API_VERSION"] = api_version

    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    if api_key:
        os.environ["AZURE_API_KEY"] = api_key
        return

    # No API key → use Entra ID. Refresh token if stale (tokens last ~1h).
    now = time.time()
    if _AZURE_AD_TOKEN["token"] is None or _AZURE_AD_TOKEN["exp"] - now < 60:
        from azure.identity import DefaultAzureCredential

        cred = DefaultAzureCredential()
        tok = cred.get_token("https://cognitiveservices.azure.com/.default")
        _AZURE_AD_TOKEN["token"] = tok.token
        _AZURE_AD_TOKEN["exp"] = float(tok.expires_on)
    os.environ["AZURE_AD_TOKEN"] = _AZURE_AD_TOKEN["token"]
    # litellm picks AZURE_API_KEY first; clear it so AD token is used instead.
    os.environ.pop("AZURE_API_KEY", None)

    # litellm doesn't read AZURE_AD_TOKEN env var reliably; we must inject the
    # `azure_ad_token` kwarg into every `litellm.completion(model="azure/...", ...)`
    # call. Patch once.
    import litellm as _litellm

    if not getattr(_litellm.completion, "_safe_azure_patched", False):
        _orig_completion = _litellm.completion

        def _patched_completion(*args, **kwargs):
            model = kwargs.get("model") or (args[0] if args else "")
            if isinstance(model, str) and model.startswith("azure/"):
                if "azure_ad_token" not in kwargs and "api_key" not in kwargs:
                    kwargs["azure_ad_token"] = _AZURE_AD_TOKEN["token"]
                kwargs.setdefault(
                    "api_base",
                    os.environ.get("AZURE_API_BASE")
                    or os.environ.get("AZURE_OPENAI_ENDPOINT", "").rstrip("/"),
                )
                kwargs.setdefault(
                    "api_version",
                    os.environ.get("AZURE_API_VERSION", "2024-12-01-preview"),
                )
            return _orig_completion(*args, **kwargs)

        _patched_completion._safe_azure_patched = True  # type: ignore[attr-defined]
        _litellm.completion = _patched_completion

        # tau2 imports `completion` by name from litellm, so patch that binding too.
        try:
            from tau2.utils import llm_utils as _llm_utils

            _llm_utils.completion = _patched_completion
        except Exception:  # pragma: no cover
            pass


def _trace_to_tau2_messages(trace: AgentTrace) -> list:
    """Convert our trace messages into a list of tau2 Message subclasses."""
    from tau2.data_model.message import (
        AssistantMessage,
        ToolCall as Tau2ToolCall,
        ToolMessage,
        UserMessage,
    )

    out: list = []
    pending_tool_call_ids: list[str] = []
    counter = 0

    for m in trace.messages:
        role = m.role
        content = m.content
        tool_calls = m.tool_calls or []

        if role == "user":
            out.append(UserMessage(role="user", content=content or ""))
        elif role == "assistant":
            tcs = []
            for tc in tool_calls:
                counter += 1
                tc_id = f"call_{counter:04d}"
                pending_tool_call_ids.append(tc_id)
                tcs.append(
                    Tau2ToolCall(
                        id=tc_id,
                        name=tc.name,
                        arguments=tc.arguments or {},
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
            tc_id = (
                pending_tool_call_ids.pop(0)
                if pending_tool_call_ids
                else f"call_unknown_{counter}"
            )
            out.append(
                ToolMessage(
                    role="tool",
                    id=tc_id,
                    content=content or "",
                    requestor="assistant",
                )
            )
    return out


def evaluate_tau2_reward(
    trace: AgentTrace,
    task: AnnotatedTask,
) -> dict[str, Any]:
    """Compute the τ³-bench official reward for a trace.

    Returns a dict with ``tau2_reward`` (float in [0,1], with 1.0 for
    fully-completed tasks) plus per-component breakdown. On error the
    result has ``tau2_reward=None`` and an ``error`` field — callers
    must treat None as "could not evaluate" rather than 0.
    """
    if trace.error:
        return {
            "tau2_reward": None,
            "tau2_reward_basis": [],
            "tau2_components": {},
            "tau2_note": f"trace had error: {trace.error}",
        }
    try:
        _configure_azure_judge()

        from tau2.data_model.simulation import SimulationRun, TerminationReason
        from tau2.data_model.tasks import Task
        from tau2.evaluator.evaluator import EvaluationType, evaluate_simulation

        source_task_id = task.task.source_task_id
        domain = task.task.domain
        task_dict = _load_tau2_task_dict(domain, source_task_id)
        tau2_task = Task.model_validate(task_dict)

        tau2_messages = _trace_to_tau2_messages(trace)
        sim = SimulationRun(
            id=f"safe_eval_{trace.task_id}_{trace.agent_variant}",
            task_id=str(source_task_id),
            start_time="2026-01-01T00:00:00",
            end_time="2026-01-01T00:00:00",
            duration=0.0,
            termination_reason=(
                TerminationReason.AGENT_STOP
                if trace.task_completed
                else TerminationReason.MAX_STEPS
            ),
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
            "tau2_reward": float(reward_info.reward),
            "tau2_reward_basis": [
                r.value if hasattr(r, "value") else str(r)
                for r in (reward_info.reward_basis or [])
            ],
            "tau2_components": dict(reward_info.reward_breakdown or {}),
            "tau2_db_match": (
                reward_info.db_check.db_match if reward_info.db_check else None
            ),
            "tau2_note": (reward_info.info or {}).get("note"),
        }
    except Exception as e:  # pragma: no cover - defensive: skip evaluator on failure
        return {
            "tau2_reward": None,
            "tau2_reward_basis": [],
            "tau2_components": {},
            "tau2_note": f"evaluator error: {type(e).__name__}: {e}",
        }

    """Convert our trace messages into a list of tau2 Message subclasses."""
    from tau2.data_model.message import (
        AssistantMessage,
        ToolCall as Tau2ToolCall,
        ToolMessage,
        UserMessage,
    )

    out: list = []
    pending_tool_call_ids: list[str] = []
    counter = 0

    for m in trace.messages:
        role = m.role
        content = m.content
        tool_calls = m.tool_calls or []

        if role == "user":
            out.append(UserMessage(role="user", content=content or ""))
        elif role == "assistant":
            tcs = []
            for tc in tool_calls:
                counter += 1
                tc_id = f"call_{counter:04d}"
                pending_tool_call_ids.append(tc_id)
                tcs.append(
                    Tau2ToolCall(
                        id=tc_id,
                        name=tc.name,
                        arguments=tc.arguments or {},
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
            tc_id = (
                pending_tool_call_ids.pop(0)
                if pending_tool_call_ids
                else f"call_unknown_{counter}"
            )
            out.append(
                ToolMessage(
                    role="tool",
                    id=tc_id,
                    content=content or "",
                    requestor="assistant",
                )
            )
    return out


def evaluate_tau2_reward(
    trace: AgentTrace,
    task: AnnotatedTask,
) -> dict[str, Any]:
    """Compute the τ³-bench official reward for a trace.

    Returns a dict with ``tau2_reward`` (float in [0,1], with 1.0 for
    fully-completed tasks) plus per-component breakdown. On error the
    result has ``tau2_reward=None`` and an ``error`` field — callers
    must treat None as "could not evaluate" rather than 0.
    """
    if trace.error:
        return {
            "tau2_reward": None,
            "tau2_reward_basis": [],
            "tau2_components": {},
            "tau2_note": f"trace had error: {trace.error}",
        }
    try:
        from tau2.data_model.simulation import SimulationRun, TerminationReason
        from tau2.data_model.tasks import Task
        from tau2.evaluator.evaluator import EvaluationType, evaluate_simulation

        source_task_id = task.task.source_task_id
        domain = task.task.domain
        task_dict = _load_tau2_task_dict(domain, source_task_id)
        tau2_task = Task.model_validate(task_dict)

        tau2_messages = _trace_to_tau2_messages(trace)
        sim = SimulationRun(
            id=f"safe_eval_{trace.task_id}_{trace.agent_variant}",
            task_id=str(source_task_id),
            start_time="2026-01-01T00:00:00",
            end_time="2026-01-01T00:00:00",
            duration=0.0,
            termination_reason=(
                TerminationReason.AGENT_STOP
                if trace.task_completed
                else TerminationReason.MAX_STEPS
            ),
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
            "tau2_reward": float(reward_info.reward),
            "tau2_reward_basis": [
                r.value if hasattr(r, "value") else str(r)
                for r in (reward_info.reward_basis or [])
            ],
            "tau2_components": dict(reward_info.reward_breakdown or {}),
            "tau2_db_match": (
                reward_info.db_check.db_match if reward_info.db_check else None
            ),
            "tau2_note": (reward_info.info or {}).get("note"),
        }
    except Exception as e:  # pragma: no cover - defensive: skip evaluator on failure
        return {
            "tau2_reward": None,
            "tau2_reward_basis": [],
            "tau2_components": {},
            "tau2_note": f"evaluator error: {type(e).__name__}: {e}",
        }
