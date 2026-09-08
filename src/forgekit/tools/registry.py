"""Typed tool registry with JSON-schema-ish validation."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any

from forgekit.models import ToolCall, ToolResult, ToolSpec

ToolHandler = Callable[[dict[str, Any]], Awaitable[str] | str]


class ToolRegistry:
    def __init__(self) -> None:
        self._specs: dict[str, ToolSpec] = {}
        self._handlers: dict[str, ToolHandler] = {}

    def register(self, spec: ToolSpec, handler: ToolHandler) -> None:
        self._specs[spec.name] = spec
        self._handlers[spec.name] = handler

    def list_specs(self) -> list[ToolSpec]:
        return list(self._specs.values())

    def schema_prompt(self) -> str:
        lines = ["Available tools (JSON):"]
        for spec in self._specs.values():
            payload = {
                "name": spec.name,
                "description": spec.description,
                "parameters": spec.parameters,
                "required": spec.required,
            }
            lines.append(json.dumps(payload, ensure_ascii=False))
        return "\n".join(lines)

    def validate(self, call: ToolCall) -> str | None:
        spec = self._specs.get(call.name)
        if not spec:
            return f"Unknown tool: {call.name}"
        for key in spec.required:
            if key not in call.arguments:
                return f"Missing required argument '{key}' for {call.name}"
        return None

    async def execute(self, call: ToolCall) -> ToolResult:
        err = self.validate(call)
        if err:
            return ToolResult(name=call.name, ok=False, output="", error=err)
        handler = self._handlers[call.name]
        try:
            result = handler(call.arguments)
            if hasattr(result, "__await__"):
                output = await result  # type: ignore[misc]
            else:
                output = result
            return ToolResult(name=call.name, ok=True, output=str(output))
        except Exception as exc:  # noqa: BLE001 — surface tool errors to agent
            return ToolResult(name=call.name, ok=False, output="", error=str(exc))


def build_default_tools() -> ToolRegistry:
    """Offline-friendly tools for demos and tests."""
    registry = ToolRegistry()

    async def calc(args: dict[str, Any]) -> str:
        expr = str(args.get("expression", "")).strip()
        allowed = set("0123456789+-*/().% ")
        if not expr or any(ch not in allowed for ch in expr):
            raise ValueError("expression must be a simple arithmetic string")
        return str(eval(expr, {"__builtins__": {}}, {}))

    async def lookup(args: dict[str, Any]) -> str:
        topic = str(args.get("topic", "")).lower()
        kb = {
            "hermes": "Hermes Agent centers on a learning loop that distills SKILL.md files.",
            "openclaw": "OpenClaw is gateway-first: channels, credentials, and policy in one daemon.",
            "forgekit": "ForgeKit is a minimal Python agent runtime with dual loops and progressive skills.",
            "rdma": "RDMA enables low-latency remote memory access used in disaggregated storage stacks.",
        }
        for key, value in kb.items():
            if key in topic:
                return value
        return f"No curated note for '{topic}'. Try hermes, openclaw, forgekit, or rdma."

    async def remember(args: dict[str, Any]) -> str:
        return f"queued_memory:{args.get('key')}={args.get('value')}"

    async def finalize(args: dict[str, Any]) -> str:
        return str(args.get("answer", ""))

    registry.register(
        ToolSpec(
            name="calc",
            description="Evaluate a simple arithmetic expression.",
            parameters={"expression": {"type": "string"}},
            required=["expression"],
        ),
        calc,
    )
    registry.register(
        ToolSpec(
            name="lookup",
            description="Lookup a curated knowledge snippet by topic.",
            parameters={"topic": {"type": "string"}},
            required=["topic"],
        ),
        lookup,
    )
    registry.register(
        ToolSpec(
            name="remember",
            description="Propose a durable memory note (key/value).",
            parameters={
                "key": {"type": "string"},
                "value": {"type": "string"},
            },
            required=["key", "value"],
        ),
        remember,
    )
    registry.register(
        ToolSpec(
            name="finalize",
            description="Return the final answer to the user.",
            parameters={"answer": {"type": "string"}},
            required=["answer"],
        ),
        finalize,
    )
    return registry
