"""Trace schema — Pydantic models for capturing agent execution traces."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """A single tool call made by the agent."""

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: str | None = None


class Message(BaseModel):
    """A single message in the conversation."""

    role: str  # "system", "user", "assistant", "tool"
    content: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)


class AgentTrace(BaseModel):
    """Complete trace of an agent execution on a single task."""

    task_id: str
    domain: str
    agent_variant: str  # "baseline" or "safe-aware"
    system_prompt: str
    messages: list[Message] = Field(default_factory=list)
    tool_calls_log: list[ToolCall] = Field(default_factory=list, description="Flat list of all tool calls made")
    final_response: str = ""
    task_completed: bool = False
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
