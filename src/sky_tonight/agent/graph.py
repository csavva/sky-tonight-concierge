"""LangGraph state machine: parse_request -> compute -> explain."""

import json
import re
from collections.abc import Awaitable, Callable, Mapping
from datetime import date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import ValidationError

from sky_tonight.agent import prompts
from sky_tonight.agent.state import ParsedRequest, SkyState

# A tool takes keyword arguments and returns the tool's JSON result as a dict.
Tool = Callable[..., Awaitable[dict[str, Any]]]
REQUIRED_TOOLS = ("geocode", "visible_planets", "moon_info")

# Local time used to sample the sky. Late enough that twilight has ended at mid latitudes
# even in summer; a twilight-aware choice is on the roadmap.
OBSERVING_HOUR = 22


class RequestParseError(ValueError):
    pass


def parse_request_json(text: str) -> ParsedRequest:
    """Validate the LLM's reply, tolerating code fences or surrounding prose."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise RequestParseError(f"Could not find a JSON object in the model reply: {text!r}")
    try:
        return ParsedRequest.model_validate_json(match.group(0))
    except ValidationError as exc:
        raise RequestParseError(f"The model reply was not a valid request: {exc}") from exc


def build_graph(llm: BaseChatModel, tools: Mapping[str, Tool]) -> CompiledStateGraph:
    missing = [name for name in REQUIRED_TOOLS if name not in tools]
    if missing:
        raise ValueError(f"Missing tools: {', '.join(missing)}")

    async def parse_request(state: SkyState) -> SkyState:
        system = prompts.PARSE_SYSTEM.format(today=state["today"])
        reply = await llm.ainvoke([SystemMessage(system), HumanMessage(state["question"])])
        return {"request": parse_request_json(reply.text)}

    async def compute(state: SkyState) -> SkyState:
        request = state["request"]
        location = await tools["geocode"](place=request.place)
        lat, lon, tz = location["latitude"], location["longitude"], location["timezone"]

        day = request.date or date.fromisoformat(state["today"])
        when = datetime.combine(day, time(OBSERVING_HOUR), ZoneInfo(tz))
        planets = await tools["visible_planets"](lat=lat, lon=lon, when=when.isoformat())
        moon = await tools["moon_info"](lat=lat, lon=lon, day=day.isoformat(), timezone=tz)
        return {
            "location": location,
            "observing_time": when.isoformat(),
            "planets": planets,
            "moon": moon,
        }

    async def explain(state: SkyState) -> SkyState:
        facts = {
            "location": state["location"],
            "observing_time": state["observing_time"],
            "visible_planets": [p for p in state["planets"]["planets"] if p["visible"]],
            "sky_dark_enough": state["planets"]["sky_dark_enough"],
            "moon": state["moon"],
        }
        user = prompts.EXPLAIN_USER.format(question=state["question"], facts=json.dumps(facts))
        reply = await llm.ainvoke([SystemMessage(prompts.EXPLAIN_SYSTEM), HumanMessage(user)])
        return {"answer": reply.text.strip()}

    graph = StateGraph(SkyState)
    graph.add_node("parse_request", parse_request)
    graph.add_node("compute", compute)
    graph.add_node("explain", explain)
    graph.add_edge(START, "parse_request")
    graph.add_edge("parse_request", "compute")
    graph.add_edge("compute", "explain")
    graph.add_edge("explain", END)
    return graph.compile()
