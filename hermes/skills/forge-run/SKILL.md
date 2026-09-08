---
name: forge-run
description: Run the ForgeKit agent runtime on a goal using react or plan_then_act loops.
---

# Forge run

## Steps
1. Clarify goal and loop mode (`react` default, `plan_then_act` for explicit planning).
2. Run `forgekit run "<goal>" --mode react` or MCP `forge_run`.
3. Inspect trace events: thought → tool_call → tool_result → final.
4. Note which skills hydrated (progressive disclosure).

## Verification
- Final answer present.
- Tool validation errors should be visible in the trace.
