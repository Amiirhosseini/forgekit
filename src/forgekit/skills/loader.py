"""Progressive skill disclosure — cheap index, hydrate on match."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from forgekit.memory.store import estimate_tokens
from forgekit.models import SkillBody, SkillIndexEntry

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


class SkillLibrary:
    def __init__(self, roots: list[Path] | None = None) -> None:
        self.roots = roots or []
        self._index: list[SkillIndexEntry] = []
        self._bodies: dict[str, SkillBody] = {}
        self.reload()

    def reload(self) -> None:
        self._index = []
        self._bodies = {}
        for root in self.roots:
            if not root.exists():
                continue
            for path in sorted(root.rglob("SKILL.md")):
                self._load_skill(path)

    def _load_skill(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(text)
        meta: dict = {}
        body = text
        if match:
            meta = yaml.safe_load(match.group(1)) or {}
            body = match.group(2).strip()
        name = str(meta.get("name") or path.parent.name)
        description = str(meta.get("description") or body.splitlines()[0][:120])
        entry = SkillIndexEntry(
            name=name,
            description=description,
            path=str(path),
            tokens_estimate=estimate_tokens(f"{name}:{description}"),
        )
        self._index.append(entry)
        self._bodies[name] = SkillBody(
            name=name,
            description=description,
            body=body,
            path=str(path),
        )

    def index_prompt(self) -> str:
        if not self._index:
            return "SKILLS INDEX: (none)"
        total = sum(e.tokens_estimate for e in self._index)
        lines = [f"SKILLS INDEX (~{total} tokens — descriptions only):"]
        for e in self._index:
            lines.append(f"- {e.name}: {e.description}")
        lines.append("Load full skill body only when the goal matches.")
        return "\n".join(lines)

    def match(self, goal: str, limit: int = 2) -> list[SkillBody]:
        goal_l = goal.lower()
        scored: list[tuple[int, SkillBody]] = []
        for entry in self._index:
            body = self._bodies[entry.name]
            score = 0
            for token in re.findall(r"[a-z0-9]+", entry.name.lower() + " " + entry.description.lower()):
                if len(token) > 3 and token in goal_l:
                    score += 1
            if score:
                scored.append((score, body))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [b for _, b in scored[:limit]]

    def list_index(self) -> list[SkillIndexEntry]:
        return list(self._index)
