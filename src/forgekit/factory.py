"""Factory helpers."""

from __future__ import annotations

from pathlib import Path

from forgekit.memory.store import FrozenMemory
from forgekit.runtime import AgentRuntime
from forgekit.skills.loader import SkillLibrary
from forgekit.tools.registry import build_default_tools


def default_skill_roots() -> list[Path]:
    root = Path(__file__).resolve().parents[2]
    return [
        root / "examples" / "skills",
        root / "hermes" / "skills",
    ]


def build_runtime(
    *,
    memory_budget: int = 320,
    skill_roots: list[Path] | None = None,
) -> AgentRuntime:
    memory = FrozenMemory(budget_tokens=memory_budget)
    memory.seed(
        [
            ("user", "Prefers concise technical answers"),
            ("project", "Building an open-source agent framework"),
        ]
    )
    skills = SkillLibrary(skill_roots or default_skill_roots())
    return AgentRuntime(tools=build_default_tools(), memory=memory, skills=skills)
