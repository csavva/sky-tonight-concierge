# Roadmap

**Milestone 1 (done):**
- repo skeleton
- geocode, planets and Moon tools
- MCP server
- linear LangGraph graph (parse → compute → explain)
- OpenAI via `init_chat_model`
- Typer CLI

Each item below is sized to become one GitHub issue. Estimates are rough.

## Milestone 2: Weather and the cloudy branch (~7h)
- [ ] `cloud_forecast(lat, lon, date)` tool via Open-Meteo hourly `cloud_cover`, with respx tests (1.5h)
- [ ] Expose `cloud_forecast` on the MCP server (0.5h)
- [ ] Configurable night window (default 21:00–00:00 local) and cloudy threshold (default 60% mean cover) (1h)
- [ ] Weather check node and conditional edge: clear → compute, cloudy → best night (1h)
- [ ] Best night search over the next 7 days, including an "every night is cloudy" message (1.5h)
- [ ] Graph tests covering the clear and cloudy branches with a fake LLM (0.5h)
- [ ] Pick the observing time from twilight (sun below −12°) instead of a fixed 22:00 (1h)

## Milestone 3: More things to look at (~7h)
- [ ] `iss_passes(lat, lon, start, days)` using Celestrak TLEs, keeping only visible passes (ISS sunlit, observer in darkness) (2.5h)
- [ ] Cache TLEs locally with a max age (0.5h)
- [ ] Curated `bright_targets.json`: about 30 bright stars and showpiece objects from public catalogue data (1h)
- [ ] `bright_targets(lat, lon, datetime, limit)` tool and tests (1h)
- [ ] Deterministic ranking module: brightness, altitude, variety, Moon glare penalty (1.5h)
- [ ] Expose the new tools on the MCP server and wire them into the compute node (0.5h)

## Milestone 4: Provider flexibility and observability (~4h)
- [ ] Optional extras for `anthropic` and `gemini`; verify current model names (1h)
- [ ] README section on switching provider via `LLM_MODEL` (0.5h)
- [ ] Clear error messages for every provider when its package or API key is missing (0.5h)
- [ ] Langfuse LangChain callback handler, enabled only when keys are set; Cloud and self-hosted (1h)
- [ ] README section on enabling Langfuse (0.5h)
- [ ] Parse optional time windows ("around 4am", "after midnight") (0.5h)

## Milestone 5: Robustness and developer experience (~6h)
- [ ] Claude Desktop setup docs and config snippet for the standalone MCP server (0.5h)
- [ ] HTTP response caching for geocode and forecasts (1h)
- [ ] Retries, timeouts and friendly messages for upstream API failures (1h)
- [ ] Handle ambiguous places (several geocode hits: ask, or pick by population) (1h)
- [ ] GitHub Actions CI: ruff, pytest, cached ephemeris (1h)
- [ ] Polar day and night and other edge cases (no darkness, Moon never rises) (1h)
- [ ] `--json` output flag on the CLI (0.5h)

## Milestone 6: HTTP API (~4h)
- [ ] FastAPI `POST /plan` endpoint reusing the graph (1.5h)
- [ ] Request and response schemas, OpenAPI docs (0.5h)
- [ ] API tests with the fake LLM (1h)
- [ ] Run instructions and a Dockerfile for local use (1h)

## Later ideas
- [ ] Light pollution estimate (Bortle style) per location
- [ ] Seeing and transparency forecast
- [ ] Meteor shower calendar
- [ ] Eclipses and planetary conjunctions
- [ ] Small eval set for parse and explain quality
- [ ] Localised answers (Portuguese, Spanish, ...)
- [ ] Streaming CLI output
