"""Agent execution loops: ReAct and plan-then-act."""

from __future__ import annotations

from forgekit.brain import SimBrain
from forgekit.memory.store import FrozenMemory
from forgekit.models import AgentEvent, LoopMode, RunResult, ToolCall
from forgekit.skills.loader import SkillLibrary
from forgekit.tools.registry import ToolRegistry


class AgentRuntime:
    def __init__(
        self,
        tools: ToolRegistry,
        memory: FrozenMemory,
        skills: SkillLibrary,
        brain: SimBrain | None = None,
        max_turns: int = 6,
    ) -> None:
        self.tools = tools
        self.memory = memory
        self.skills = skills
        self.brain = brain or SimBrain()
        self.max_turns = max_turns

    async def run(self, goal: str, mode: LoopMode = LoopMode.REACT) -> RunResult:
        events: list[AgentEvent] = []
        tool_results = []
        prior_outputs: list[str] = []
        skills_loaded: list[str] = []

        events.append(AgentEvent(kind="goal", detail=goal, data={"mode": mode.value}))
        events.append(AgentEvent(kind="memory", detail=self.memory.prompt_block()))
        events.append(AgentEvent(kind="skills_index", detail=self.skills.index_prompt()))

        matched = self.skills.match(goal)
        for skill in matched:
            skills_loaded.append(skill.name)
            events.append(
                AgentEvent(
                    kind="skill_hydrate",
                    detail=f"Loaded full skill: {skill.name}",
                    data={"body_preview": skill.body[:240]},
                )
            )

        final = ""
        turns = 0
        for turn in range(self.max_turns):
            turns = turn + 1
            decision = self.brain.plan(goal, mode, turn=turn, prior_outputs=prior_outputs)
            if decision.thought:
                events.append(AgentEvent(kind="thought", detail=decision.thought))
            if decision.plan:
                events.append(
                    AgentEvent(kind="plan", detail=" ; ".join(decision.plan), data={"steps": decision.plan})
                )
                # plan-then-act: continue to acting turn without counting as done
                if mode == LoopMode.PLAN_THEN_ACT and turn == 0 and not decision.tool_calls:
                    continue

            if decision.final and not decision.tool_calls:
                final = decision.final
                events.append(AgentEvent(kind="final", detail=final))
                break

            for call in decision.tool_calls:
                events.append(
                    AgentEvent(
                        kind="tool_call",
                        detail=f"{call.name}({call.arguments})",
                        data=call.model_dump(),
                    )
                )
                result = await self.tools.execute(call)
                tool_results.append(result)
                events.append(
                    AgentEvent(
                        kind="tool_result",
                        detail=result.output if result.ok else (result.error or "error"),
                        data=result.model_dump(),
                    )
                )
                if result.ok:
                    prior_outputs.append(result.output)
                    if call.name == "remember":
                        key = str(call.arguments.get("key", "note"))
                        value = str(call.arguments.get("value", ""))
                        msg = self.memory.propose(key, value)
                        events.append(AgentEvent(kind="memory_propose", detail=msg))
                    if call.name == "finalize":
                        final = result.output
                        events.append(AgentEvent(kind="final", detail=final))
                        return RunResult(
                            goal=goal,
                            mode=mode,
                            final=final,
                            events=events,
                            tool_results=tool_results,
                            skills_loaded=skills_loaded,
                            memory_tokens=self.memory.tokens,
                            turns=turns,
                        )

            if decision.final:
                final = decision.final
                events.append(AgentEvent(kind="final", detail=final))
                break

        if not final:
            final = prior_outputs[-1] if prior_outputs else "No answer produced."
            events.append(AgentEvent(kind="final", detail=final))

        return RunResult(
            goal=goal,
            mode=mode,
            final=final,
            events=events,
            tool_results=tool_results,
            skills_loaded=skills_loaded,
            memory_tokens=self.memory.tokens,
            turns=turns,
        )

    async def run_tool(self, name: str, arguments: dict) -> dict:
        result = await self.tools.execute(ToolCall(name=name, arguments=arguments))
        return result.model_dump()
