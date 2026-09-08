"""Core models for ForgeKit."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LoopMode(str, Enum):
    REACT = "react"
    PLAN_THEN_ACT = "plan_then_act"


class ToolSpec(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)


class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    name: str
    ok: bool
    output: str
    error: str | None = None


class SkillIndexEntry(BaseModel):
    name: str
    description: str
    path: str
    tokens_estimate: int = 40


class SkillBody(BaseModel):
    name: str
    description: str
    body: str
    path: str


class MemoryNote(BaseModel):
    key: str
    value: str
    tokens: int = 0


class AgentEvent(BaseModel):
    kind: str
    detail: str
    data: dict[str, Any] = Field(default_factory=dict)


class AgentTurn(BaseModel):
    thought: str | None = None
    plan: list[str] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    final: str | None = None


class RunResult(BaseModel):
    goal: str
    mode: LoopMode
    final: str
    events: list[AgentEvent] = Field(default_factory=list)
    tool_results: list[ToolResult] = Field(default_factory=list)
    skills_loaded: list[str] = Field(default_factory=list)
    memory_tokens: int = 0
    turns: int = 0
