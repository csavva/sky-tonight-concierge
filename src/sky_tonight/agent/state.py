"""Graph state and the request model the LLM fills in."""

import datetime as dt
from typing import Any, TypedDict

from pydantic import BaseModel


class ParsedRequest(BaseModel):
    place: str
    date: dt.date | None = None


class SkyState(TypedDict, total=False):
    question: str
    today: str  # ISO date, used to resolve "tonight" / "tomorrow"
    request: ParsedRequest
    observing_time: str  # ISO datetime in the location's timezone
    location: dict[str, Any]
    planets: dict[str, Any]
    moon: dict[str, Any]
    answer: str
