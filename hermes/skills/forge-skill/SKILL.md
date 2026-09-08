---
name: forge-skill
description: Inspect ForgeKit progressive skill index and understand cheap descriptors vs full SKILL.md hydration.
---

# Forge skill

## Steps
1. Run `forgekit skills` to see the cheap index.
2. Run a matching goal so the runtime hydrates full skill bodies.
3. Compare token cost of index vs hydrated skills in the event trace.

## Why
Progressive disclosure keeps prompt overhead near zero until a skill is relevant.
