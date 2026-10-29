"""The MCP server registers the tools and serves them over a real client session."""

import httpx
import respx
from mcp.shared.memory import create_connected_server_and_client_session

from sky_tonight.mcp_server import mcp
from sky_tonight.tools.geocode import GEOCODING_URL


async def test_lists_the_three_tools():
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        tools = (await client.list_tools()).tools

    assert {t.name for t in tools} == {"geocode", "visible_planets", "moon_info"}
    assert all(t.description for t in tools)


async def test_moon_info_over_mcp():
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        args = {"lat": 38.72, "lon": -9.14, "day": "2026-06-29", "timezone": "Europe/Lisbon"}
        result = await client.call_tool("moon_info", args)

    assert not result.isError
    assert result.structuredContent["phase_name"] == "Full Moon"


async def test_visible_planets_over_mcp():
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        result = await client.call_tool(
            "visible_planets", {"lat": 38.72, "lon": -9.14, "when": "2026-06-15T22:30:00+01:00"}
        )

    visible = [p["name"] for p in result.structuredContent["planets"] if p["visible"]]
    assert visible == ["Venus"]


@respx.mock
async def test_geocode_errors_are_reported_not_raised():
    respx.get(GEOCODING_URL).mock(return_value=httpx.Response(200, json={}))

    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        result = await client.call_tool("geocode", {"place": "Nowhereville Xyz"})

    assert result.isError
