"""MCP server for ForgeKit."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from forgekit.factory import build_runtime
from forgekit.models import LoopMode

mcp = FastMCP("forgekit")


@mcp.tool()
async def forge_run(goal: str, mode: str = "react") -> str:
    """Run ForgeKit agent loop on a goal (react or plan_then_act)."""
    runtime = build_runtime()
    loop = LoopMode(mode)
    result = await runtime.run(goal, mode=loop)
    return json.dumps(result.model_dump(mode="json"), indent=2)


@mcp.tool()
def forge_tools() -> str:
    """List ForgeKit tool schemas."""
    runtime = build_runtime()
    return json.dumps([s.model_dump() for s in runtime.tools.list_specs()], indent=2)


@mcp.tool()
def forge_skills() -> str:
    """Show progressive skill index."""
    runtime = build_runtime()
    return runtime.skills.index_prompt()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
