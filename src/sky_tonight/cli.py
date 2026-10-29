"""Command line entry point: `sky-tonight "what can I see tonight from Lisbon"`."""

import asyncio
import sys
from datetime import date
from typing import Annotated

import typer
from dotenv import load_dotenv

from sky_tonight.agent.graph import RequestParseError, build_graph
from sky_tonight.agent.llm import LLMConfigError, load_llm
from sky_tonight.agent.mcp_tools import ToolCallError, mcp_tools
from sky_tonight.tools.ephemeris import cache_dir, ephemeris

app = typer.Typer(help="Find out what you can see in the night sky.", no_args_is_help=True)


async def run_query(question: str) -> str:
    llm = load_llm()
    async with mcp_tools() as tools:
        graph = build_graph(llm, tools)
        result = await graph.ainvoke({"question": question, "today": date.today().isoformat()})
    return result["answer"]


@app.command()
def ask(question: Annotated[str, typer.Argument(help="Your question, in plain language.")]):
    """Ask what you can see, e.g. "what can I see tonight from Lisbon"."""
    try:
        answer = asyncio.run(run_query(question))
    except (LLMConfigError, RequestParseError, ToolCallError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from None
    typer.echo(answer)


@app.command()
def setup():
    """Download the JPL ephemeris now instead of on the first query."""
    ephemeris()
    typer.echo(f"Ephemeris ready in {cache_dir()}")


def main() -> None:
    """Make `ask` the default command, so `sky-tonight "question"` just works."""
    load_dotenv()
    args = sys.argv[1:]
    commands = {"ask", "setup"}
    if args and args[0] not in commands and not args[0].startswith("-"):
        sys.argv.insert(1, "ask")
    app()
