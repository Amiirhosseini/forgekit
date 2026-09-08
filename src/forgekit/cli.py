"""Typer CLI."""

from __future__ import annotations

import asyncio

import typer
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from forgekit.factory import build_runtime
from forgekit.models import LoopMode

app = typer.Typer(name="forgekit", help="Minimal agent framework runtime.", no_args_is_help=True)
console = Console()


@app.command()
def run(
    goal: str = typer.Argument(..., help="User goal"),
    mode: str = typer.Option("react", help="react | plan_then_act"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Run the agent loop offline (SimBrain)."""
    runtime = build_runtime()
    result = asyncio.run(runtime.run(goal, mode=LoopMode(mode)))
    if json_out:
        console.print_json(data=result.model_dump(mode="json"))
        return
    console.print(Panel(result.final, title="Final"))
    table = Table(title="Trace")
    table.add_column("Kind")
    table.add_column("Detail")
    for ev in result.events:
        table.add_row(ev.kind, ev.detail[:120])
    console.print(table)
    console.print(
        f"mode={result.mode.value} turns={result.turns} "
        f"skills={result.skills_loaded or '-'} mem_tokens={result.memory_tokens}"
    )


@app.command("tools")
def tools_cmd() -> None:
    """List registered tools."""
    runtime = build_runtime()
    for spec in runtime.tools.list_specs():
        console.print(f"[bold]{spec.name}[/bold] — {spec.description}")


@app.command()
def skills() -> None:
    """Show progressive skill index."""
    runtime = build_runtime()
    console.print(runtime.skills.index_prompt())


@app.command()
def memory(
    rebuild: bool = typer.Option(False, help="Apply pending memory notes"),
) -> None:
    """Show frozen memory snapshot."""
    runtime = build_runtime()
    if rebuild:
        applied = runtime.memory.rebuild()
        console.print({"applied": applied})
    console.print_json(data=runtime.memory.snapshot())


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8766) -> None:
    """Serve FastAPI."""
    uvicorn.run("forgekit.api:app", host=host, port=port, reload=False)


@app.command()
def mcp() -> None:
    """Run MCP server."""
    from forgekit.agent.mcp_server import main

    main()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
