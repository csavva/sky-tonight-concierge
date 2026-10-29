"""Result models returned by the tools (and serialised as JSON over MCP)."""

from datetime import datetime

from pydantic import BaseModel


class Location(BaseModel):
    name: str
    country: str | None
    latitude: float
    longitude: float
    timezone: str


class PlanetPosition(BaseModel):
    name: str
    altitude_deg: float
    azimuth_deg: float
    direction: str
    magnitude: float | None
    visible: bool
    naked_eye: bool  # bright enough to see without binoculars from a dark site


class PlanetsReport(BaseModel):
    when: datetime
    sun_altitude_deg: float
    sky_dark_enough: bool
    planets: list[PlanetPosition]


class MoonInfo(BaseModel):
    date: str
    phase_name: str
    phase_angle_deg: float
    illumination_pct: float
    moonrise: datetime | None
    moonset: datetime | None
