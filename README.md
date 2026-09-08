# ForgeKit

**Minimal open-source agent framework** — typed tools, progressive skill disclosure, frozen session memory, and dual loops (ReAct / plan-then-act). Offline SimBrain for demos and tests; Hermes skills + MCP included.

> **Live demo:** open [`docs/index.html`](docs/index.html) or Pages after publish  
> Toggle tools, switch loop modes, watch the trace hydrate skills and queue memory.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-green.svg)](pyproject.toml)

## Why it exists

Most “agent demos” hide the runtime. ForgeKit makes the runtime the product:

- **Progressive skills** — cheap index in the prompt; full `SKILL.md` only on match (Hermes idea)
- **Frozen memory budget** — tiny always-on notes; updates queue until rebuild (Hermes idea)
- **Dual loops** — ReAct vs plan-then-act, same tool surface
- **Typed tool gate** — schema validation before execution

Pairs with **[HermesLens](https://amiirhosseini.com/HermesLens/)** (dissect → steal → spike here).

## Quick start

```bash
git clone https://github.com/Amiirhosseini/forgekit.git
cd forgekit
python -m venv .venv && .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

forgekit run "Explain Hermes learning loop and remember it" --mode plan_then_act
forgekit run "Compute 12 + 30"
forgekit tools
forgekit skills
```

## Live demo walkthrough

1. Open the Pages demo (or `docs/index.html`)
2. Click **Goal: Hermes** — see plan → lookup → remember queue → finalize
3. Disable `lookup`, re-run — watch validation/path change
4. Switch **ReAct** vs **Plan → Act**

## Hermes / MCP

```bash
forgekit mcp
# /forge-run  /forge-skill
```

## Layout

```text
forgekit/
  src/forgekit/     # runtime, tools, memory, skills, CLI, API, MCP
  examples/skills/  # sample SKILL.md library
  hermes/skills/    # Hermes Agent skills
  docs/             # interactive Pages demo
  tests/
```

## License

Apache-2.0
