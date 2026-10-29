"""Graph run with a fake LLM and stub tools: no network, no API keys."""

import pytest
from langchain_core.language_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from sky_tonight.agent.graph import RequestParseError, build_graph, parse_request_json

LOCATION = {
    "name": "Lisbon",
    "country": "Portugal",
    "latitude": 38.72,
    "longitude": -9.14,
    "timezone": "Europe/Lisbon",
}
PLANETS = {
    "sky_dark_enough": True,
    "planets": [
        {"name": "Venus", "visible": True, "direction": "W", "altitude_deg": 11.8},
        {"name": "Saturn", "visible": False, "direction": "NE", "altitude_deg": -42.5},
    ],
}
MOON = {"phase_name": "New Moon", "illumination_pct": 0.9}


def fake_llm(*replies: str) -> GenericFakeChatModel:
    return GenericFakeChatModel(messages=iter(AIMessage(r) for r in replies))


def stub_tools(calls: list):
    async def geocode(**kwargs):
        calls.append(("geocode", kwargs))
        return LOCATION

    async def visible_planets(**kwargs):
        calls.append(("visible_planets", kwargs))
        return PLANETS

    async def moon_info(**kwargs):
        calls.append(("moon_info", kwargs))
        return MOON

    return {"geocode": geocode, "visible_planets": visible_planets, "moon_info": moon_info}


async def test_graph_happy_path():
    calls = []
    llm = fake_llm('{"place": "Lisbon", "date": "2026-06-15"}', "Look west for Venus.")
    graph = build_graph(llm, stub_tools(calls))

    result = await graph.ainvoke({"question": "What can I see from Lisbon?", "today": "2026-06-14"})

    assert result["answer"] == "Look west for Venus."
    assert calls == [
        ("geocode", {"place": "Lisbon"}),
        (
            "visible_planets",
            {"lat": 38.72, "lon": -9.14, "when": "2026-06-15T22:00:00+01:00"},
        ),
        (
            "moon_info",
            {"lat": 38.72, "lon": -9.14, "day": "2026-06-15", "timezone": "Europe/Lisbon"},
        ),
    ]


async def test_graph_defaults_to_tonight_when_no_date():
    calls = []
    graph = build_graph(fake_llm('{"place": "Lisbon", "date": null}', "ok"), stub_tools(calls))

    result = await graph.ainvoke({"question": "Tonight in Lisbon?", "today": "2026-06-14"})

    assert result["observing_time"] == "2026-06-14T22:00:00+01:00"
    assert calls[2][1]["day"] == "2026-06-14"


def test_build_graph_requires_all_tools():
    with pytest.raises(ValueError, match="moon_info"):
        build_graph(fake_llm(), {"geocode": None, "visible_planets": None})


def test_parse_request_json_tolerates_code_fences():
    parsed = parse_request_json('```json\n{"place": "São Paulo", "date": null}\n```')
    assert parsed.place == "São Paulo"
    assert parsed.date is None


@pytest.mark.parametrize("reply", ["I don't know", '{"date": "2026-06-15"}'])
def test_parse_request_json_rejects_bad_replies(reply):
    with pytest.raises(RequestParseError):
        parse_request_json(reply)
