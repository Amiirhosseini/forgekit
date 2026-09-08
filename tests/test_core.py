"""ForgeKit tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from forgekit.api import app as api_app
from forgekit.factory import build_runtime
from forgekit.memory.store import FrozenMemory
from forgekit.models import LoopMode, ToolCall
from forgekit.tools.registry import build_default_tools


@pytest.mark.asyncio
async def test_react_lookup_hermes() -> None:
    runtime = build_runtime()
    result = await runtime.run("Explain Hermes learning loop", mode=LoopMode.REACT)
    assert result.final
    assert any(t.name == "lookup" for t in result.tool_results)
    assert "research-brief" in result.skills_loaded
    assert any("Hermes" in (t.output or "") or "learning" in (t.output or "").lower() for t in result.tool_results) or "Hermes" in result.final


@pytest.mark.asyncio
async def test_plan_then_act_emits_plan() -> None:
    runtime = build_runtime()
    result = await runtime.run("What is OpenClaw gateway?", mode=LoopMode.PLAN_THEN_ACT)
    assert any(e.kind == "plan" for e in result.events)
    assert result.final


@pytest.mark.asyncio
async def test_calc_tool() -> None:
    runtime = build_runtime()
    result = await runtime.run("Compute 12 + 30", mode=LoopMode.REACT)
    assert "42" in result.final or any("42" in (t.output or "") for t in result.tool_results)


@pytest.mark.asyncio
async def test_tool_validation() -> None:
    tools = build_default_tools()
    bad = await tools.execute(ToolCall(name="calc", arguments={}))
    assert bad.ok is False
    assert bad.error


def test_frozen_memory_budget_and_queue() -> None:
    mem = FrozenMemory(budget_tokens=40)
    mem.seed([("a", "one")])
    assert mem.frozen is True
    msg = mem.propose("b", "queued value that should wait")
    assert "queued" in msg
    assert mem.snapshot()["pending"]
    applied = mem.rebuild()
    assert applied
    assert mem.tokens <= mem.budget_tokens


def test_progressive_skill_index_cheaper_than_body() -> None:
    runtime = build_runtime()
    index = runtime.skills.index_prompt()
    assert "SKILLS INDEX" in index
    matched = runtime.skills.match("research brief on hermes agent frameworks")
    assert matched
    assert len(matched[0].body) > len(matched[0].description)


def test_api_run() -> None:
    client = TestClient(api_app)
    assert client.get("/health").json()["ok"] is True
    resp = client.post("/run", json={"goal": "Tell me about ForgeKit", "mode": "react"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["final"]
    assert body["events"]
