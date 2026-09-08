"""Deterministic offline brain — no API key required for demos/tests."""

from __future__ import annotations

import re

from forgekit.models import AgentTurn, LoopMode, ToolCall


class SimBrain:
    """Rule-based planner that exercises tools for offline runs."""

    def plan(self, goal: str, mode: LoopMode, *, turn: int, prior_outputs: list[str]) -> AgentTurn:
        goal_l = goal.lower()
        joined = "\n".join(prior_outputs).lower()

        # Already have enough context → finalize
        if turn >= 2 or any(k in joined for k in ("hermes agent", "openclaw is", "forgekit is", "=")):
            answer = self._compose_answer(goal, prior_outputs)
            return AgentTurn(
                thought="Synthesize tool results into a final answer.",
                final=answer,
                tool_calls=[ToolCall(name="finalize", arguments={"answer": answer})],
            )

        if mode == LoopMode.PLAN_THEN_ACT and turn == 0:
            steps = self._plan_steps(goal_l)
            return AgentTurn(thought="Draft a short plan before acting.", plan=steps)

        # Math
        expr = self._extract_math(goal)
        if expr and "calc" not in joined:
            return AgentTurn(
                thought=f"Compute expression {expr}.",
                tool_calls=[ToolCall(name="calc", arguments={"expression": expr})],
            )

        # Knowledge lookup
        topic = self._topic(goal_l)
        if topic and topic not in joined:
            calls = [ToolCall(name="lookup", arguments={"topic": topic})]
            if "remember" in goal_l or "note" in goal_l:
                calls.append(
                    ToolCall(
                        name="remember",
                        arguments={"key": topic, "value": f"user asked about {topic}"},
                    )
                )
            return AgentTurn(thought=f"Lookup curated notes for {topic}.", tool_calls=calls)

        answer = self._compose_answer(goal, prior_outputs)
        return AgentTurn(
            thought="No more tools needed.",
            final=answer,
            tool_calls=[ToolCall(name="finalize", arguments={"answer": answer})],
        )

    def _plan_steps(self, goal_l: str) -> list[str]:
        steps = ["Clarify goal and choose tools"]
        if self._extract_math(goal_l):
            steps.append("Use calc for arithmetic")
        if self._topic(goal_l):
            steps.append("Use lookup for curated knowledge")
        steps.append("Finalize a concise answer")
        return steps

    def _extract_math(self, text: str) -> str | None:
        match = re.search(r"(\d+\s*[\+\-\*/]\s*\d+(?:\s*[\+\-\*/]\s*\d+)*)", text)
        return match.group(1).replace(" ", "") if match else None

    def _topic(self, goal_l: str) -> str | None:
        for key in ("hermes", "openclaw", "forgekit", "rdma"):
            if key in goal_l:
                return key
        return None

    def _compose_answer(self, goal: str, prior_outputs: list[str]) -> str:
        useful = [o for o in prior_outputs if o and not o.startswith("queued_memory")]
        if useful:
            return " | ".join(useful[-3:])
        return f"Acknowledged: {goal}"
