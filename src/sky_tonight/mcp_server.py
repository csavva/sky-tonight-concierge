"""MCP server exposing the Sky Tonight tools. Run standalone with `sky-tonight-mcp` (stdio)."""

from datetime import date, datetime

from mcp.server.fastmcp import FastMCP

from sky_tonight.tools import geocode as geocode_tool
from sky_tonight.tools import sky
from sky_tonight.tools.models import Location, MoonInfo, PlanetsReport

# WARNING keeps per-request INFO logs off stderr, so the CLI output stays clean.
mcp = FastMCP("sky-tonight", log_level="WARNING")


@mcp.tool()
def geocode(place: str) -> Location:
    """Look up a place name and return its latitude, longitude and IANA timezone."""
    return geocode_tool.geocode(place)


@mcp.tool()
def visible_planets(lat: float, lon: float, when: str) -> PlanetsReport:
    """Positions of the planets from a location at a moment in time.

    `when` is an ISO 8601 datetime with a UTC offset, e.g. "2026-06-15T22:00:00+01:00".
    A planet is marked visible when the sky is dark enough and it is at least 10 degrees up.
    """
    return sky.visible_planets(lat, lon, datetime.fromisoformat(when))


@mcp.tool()
def moon_info(lat: float, lon: float, day: str, timezone: str = "UTC") -> MoonInfo:
    """Moon phase, illumination and rise/set times for a local date ("YYYY-MM-DD").

    `timezone` is an IANA name such as "Europe/Lisbon", as returned by `geocode`.
    """
    return sky.moon_info(lat, lon, date.fromisoformat(day), timezone)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
