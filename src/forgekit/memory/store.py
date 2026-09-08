"""Tiny frozen always-on memory with hard token budget (Hermes-inspired)."""

from __future__ import annotations

from forgekit.models import MemoryNote


def estimate_tokens(text: str) -> int:
    # Cheap heuristic: ~4 chars/token
    return max(1, (len(text) + 3) // 4)


class FrozenMemory:
    """Session-frozen memory: updates queue until rebuild/next session."""

    def __init__(self, budget_tokens: int = 320) -> None:
        self.budget_tokens = budget_tokens
        self._notes: list[MemoryNote] = []
        self._pending: list[MemoryNote] = []
        self.frozen = True

    @property
    def tokens(self) -> int:
        return sum(n.tokens for n in self._notes)

    def seed(self, notes: list[tuple[str, str]]) -> None:
        self._notes = []
        for key, value in notes:
            self._append(self._notes, key, value)
        self.frozen = True

    def prompt_block(self) -> str:
        if not self._notes:
            return "MEMORY: (empty)"
        lines = [f"MEMORY ({self.tokens}/{self.budget_tokens} tokens, frozen={self.frozen}):"]
        for note in self._notes:
            lines.append(f"- {note.key}: {note.value}")
        return "\n".join(lines)

    def propose(self, key: str, value: str) -> str:
        note = MemoryNote(key=key, value=value, tokens=estimate_tokens(f"{key}:{value}"))
        if self.frozen:
            self._pending.append(note)
            return f"queued until rebuild ({note.tokens} tok)"
        return self._append(self._notes, key, value)

    def rebuild(self) -> list[str]:
        """Apply pending notes into active memory (new session)."""
        applied: list[str] = []
        self.frozen = False
        for note in self._pending:
            applied.append(self._append(self._notes, note.key, note.value))
        self._pending.clear()
        self.frozen = True
        return applied

    def snapshot(self) -> dict:
        return {
            "budget": self.budget_tokens,
            "tokens": self.tokens,
            "frozen": self.frozen,
            "notes": [n.model_dump() for n in self._notes],
            "pending": [n.model_dump() for n in self._pending],
        }

    def _append(self, bucket: list[MemoryNote], key: str, value: str) -> str:
        tokens = estimate_tokens(f"{key}:{value}")
        # Replace existing key
        bucket[:] = [n for n in bucket if n.key != key]
        used = sum(n.tokens for n in bucket)
        while bucket and used + tokens > self.budget_tokens:
            dropped = bucket.pop(0)
            used -= dropped.tokens
        if used + tokens > self.budget_tokens:
            return "rejected: exceeds budget"
        bucket.append(MemoryNote(key=key, value=value, tokens=tokens))
        return f"stored {key} ({tokens} tok)"
