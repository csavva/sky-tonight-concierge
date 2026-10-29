# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Sky Tonight Concierge is an astronomy assistant for the general public. A user asks "What can I see tonight from São Paulo?" (any place, optional date) and gets a short plain-language plan for the night sky. It is a personal open-source project (github.com/csavva/sky-tonight-concierge, MIT, copyright Christos Savva). Nothing in it relates to any employer or client. Deployment is local only. Favor clean, readable, well-tested code over polish.

Planned work lives in `ROADMAP.md`, grouped into milestones whose items are sized to become GitHub issues. Work one milestone at a time. Do not start the next milestone unless asked.

## Commands

```bash
uv sync --all-extras                       # install everything incl. dev + provider extras
uv run ruff check . && uv run ruff format --check .
uv run pytest                              # full suite
uv run pytest tests/test_moon.py::test_illumination -q   # single test
uv run sky-tonight setup                   # pre-download the JPL ephemeris
uv run sky-tonight "what can I see tonight from Lisbon"
uv run sky-tonight-mcp                     # run the MCP server standalone (stdio)
```

## Architecture

The code has three layers. Each layer only depends on the one below it.

1. **Tools** (`src/sky_tonight/tools/`). Plain, synchronous Python functions returning Pydantic models from `tools/models.py`. All astronomy (Skyfield) and HTTP (httpx → Open-Meteo, Celestrak) code lives here. Deterministic, no LLM.
2. **MCP server** (`src/sky_tonight/mcp_server.py`). A thin `FastMCP` wrapper (official `mcp` SDK) around the tool functions, with no logic of its own. It must keep working standalone, for example from Claude Desktop.
3. **Agent** (`src/sky_tonight/agent/`). A LangGraph state machine. `build_graph(llm, tools)` receives the chat model and a dict of tool callables, so tests inject a fake LLM and stub tools. The CLI (`cli.py`) loads the real tools from the MCP server over stdio through `langchain-mcp-adapters`. In production the agent therefore always goes through MCP, never by importing `tools/` directly.

Current graph (Milestone 1): `parse_request → compute → explain`. Later milestones add a weather check with a conditional edge to a "best night in the next 7 days" node, plus more tools (ISS passes, bright targets) and a deterministic ranking step. See ROADMAP.md.

## Decisions and conventions

- **The LLM is used only for language**: parsing the request into structured fields and writing the final explanation. Visibility, ranking and weather logic stay deterministic Python.
- **The parse step asks the model for JSON and validates it with Pydantic**, instead of using provider-specific structured output. This behaves the same across providers and with fake models.
- **LLM selection is config only.** `LLM_MODEL="provider:model"` is passed to LangChain's `init_chat_model`. The default is `openai:gpt-6-luna`, verified on OpenAI's models page in Oct 2026; re-check before changing it, and don't assume model names. Provider packages are optional extras (`openai` now; `anthropic` and `gemini` planned).
- **The Skyfield ephemeris (`de421.bsp`) is downloaded on first use** into `SKY_TONIGHT_CACHE` (default `~/.cache/sky-tonight`). Never commit `.bsp` files.
- **Tests are deterministic.** They use a fixed location and datetime, mock external HTTP with `respx`, and use `GenericFakeChatModel` for graph tests. Astronomy tests use real Skyfield math against the cached ephemeris.
- **Langfuse tracing (planned)** must stay inactive unless Langfuse keys are present in the environment.
- **Stack**: Python 3.12, uv, pytest, ruff, Typer. A FastAPI endpoint is a later roadmap item.

## Repo rules

- No secrets anywhere. `.env` is gitignored, and `.env.example` holds placeholders only. Never read aloud, print or commit keys.
- No real personal data. All sample data is invented.
- Make small, logical commits with clear conventional messages (`feat(tools): …`, `docs: …`), using the existing git config. Never squash, rewrite published history or force push.
- Keep README (what/who/stack/Mermaid diagram/run/provider switch/Langfuse) and ROADMAP.md current as features land.
