"""Connect to the Sky Tonight MCP server over stdio and adapt its tools for the graph."""

import json
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from sky_tonight.agent.graph import Tool

SERVER_NAME = "sky-tonight"


class ToolCallError(RuntimeError):
    pass


def _result_text(result: Any) -> str:
    """Flatten the adapter's content blocks (or a plain string) into text."""
    if isinstance(result, str):
        return result
    return "".join(block.get("text", "") for block in result if isinstance(block, dict))


def adapt(tool: BaseTool) -> Tool:
    async def call(**kwargs: Any) -> dict[str, Any]:
        text = _result_text(await tool.ainvoke(kwargs))
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Tool errors come back as plain text, e.g. "Error executing tool geocode: ...".
            raise ToolCallError(text) from None

    return call


@asynccontextmanager
async def mcp_tools() -> AsyncIterator[dict[str, Tool]]:
    """Start the MCP server as a subprocess and yield its tools for the lifetime of the block."""
    client = MultiServerMCPClient(
        {
            SERVER_NAME: {
                "transport": "stdio",
                "command": sys.executable,
                "args": ["-m", "sky_tonight.mcp_server"],
            }
        }
    )
    async with client.session(SERVER_NAME) as session:
        tools = await load_mcp_tools(session)
        yield {tool.name: adapt(tool) for tool in tools}
