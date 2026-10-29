"""LLM config, the stdio MCP connection and the CLI entry point."""

import sys

import pytest

from sky_tonight import cli
from sky_tonight.agent import llm
from sky_tonight.agent.mcp_tools import ToolCallError, mcp_tools


def test_load_llm_rejects_unknown_provider(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "acme:some-model")
    with pytest.raises(llm.LLMConfigError, match="Unsupported"):
        llm.load_llm()


def test_load_llm_requires_api_key(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "openai:gpt-6-luna")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(llm.LLMConfigError, match="OPENAI_API_KEY"):
        llm.load_llm()


def test_load_llm_builds_openai_model(monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    model = llm.load_llm()
    assert model.model_name == "gpt-6-luna"


async def test_mcp_tools_round_trip_over_stdio():
    async with mcp_tools() as tools:
        assert set(tools) == {"geocode", "visible_planets", "moon_info"}
        moon = await tools["moon_info"](
            lat=38.72, lon=-9.14, day="2026-06-29", timezone="Europe/Lisbon"
        )
        assert moon["phase_name"] == "Full Moon"

        with pytest.raises(ToolCallError, match="timezone-aware"):
            await tools["visible_planets"](lat=38.72, lon=-9.14, when="2026-06-15T22:00:00")


def test_cli_question_defaults_to_ask(monkeypatch, capsys):
    async def fake_run_query(question):
        return f"answer to: {question}"

    monkeypatch.setattr(cli, "run_query", fake_run_query)
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    monkeypatch.setattr(sys, "argv", ["sky-tonight", "what can I see from Lisbon"])

    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == "answer to: what can I see from Lisbon"


def test_cli_reports_config_errors(monkeypatch, capsys):
    monkeypatch.setenv("LLM_MODEL", "acme:some-model")
    monkeypatch.setattr(sys, "argv", ["sky-tonight", "anything"])
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)

    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == 1
    assert "Unsupported LLM_MODEL" in capsys.readouterr().err
