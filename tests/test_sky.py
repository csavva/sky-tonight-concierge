"""Deterministic checks against the real ephemeris for Lisbon in June 2026."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from sky_tonight.tools.sky import compass_direction, moon_info, phase_name, visible_planets

LISBON = (38.72, -9.14)
LISBON_TZ = "Europe/Lisbon"
EVENING = datetime(2026, 6, 15, 22, 30, tzinfo=ZoneInfo(LISBON_TZ))


def planets_by_name(report):
    return {p.name: p for p in report.planets}


def test_visible_planets_venus_low_in_the_west():
    report = visible_planets(*LISBON, EVENING)

    assert report.sky_dark_enough
    assert report.sun_altitude_deg < -6
    planets = planets_by_name(report)
    assert set(planets) == {"Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"}

    venus = planets["Venus"]
    assert venus.visible
    assert venus.direction == "W"
    assert venus.altitude_deg == pytest.approx(11.8, abs=0.5)
    assert venus.magnitude == pytest.approx(-4.0, abs=0.2)


def test_visible_planets_excludes_low_and_set_planets():
    planets = planets_by_name(visible_planets(*LISBON, EVENING))

    assert not planets["Jupiter"].visible  # above the horizon but below 10 degrees
    assert planets["Jupiter"].altitude_deg > 0
    assert not planets["Saturn"].visible  # below the horizon
    assert [p.name for p in planets.values() if p.visible] == ["Venus"]


def test_visible_planets_nothing_visible_in_daylight():
    noon = datetime(2026, 6, 15, 13, 0, tzinfo=ZoneInfo(LISBON_TZ))
    report = visible_planets(*LISBON, noon)

    assert not report.sky_dark_enough
    assert not any(p.visible for p in report.planets)


def test_visible_planets_requires_aware_datetime():
    with pytest.raises(ValueError):
        visible_planets(*LISBON, datetime(2026, 6, 15, 22, 30))


def test_moon_info_new_moon():
    info = moon_info(*LISBON, date(2026, 6, 15), LISBON_TZ)

    assert info.phase_name == "New Moon"
    assert info.illumination_pct < 2
    assert info.moonset is not None
    assert (info.moonset.hour, info.moonset.minute) == (22, 2)


def test_moon_info_full_moon():
    info = moon_info(*LISBON, date(2026, 6, 29), LISBON_TZ)

    assert info.phase_name == "Full Moon"
    assert info.illumination_pct == pytest.approx(99.8, abs=1)
    assert info.moonrise is not None
    assert info.moonrise.hour == 21


@pytest.mark.parametrize(
    ("azimuth", "expected"),
    [(0, "N"), (44, "NE"), (90, "E"), (200, "S"), (290, "W"), (350, "N")],
)
def test_compass_direction(azimuth, expected):
    assert compass_direction(azimuth) == expected


@pytest.mark.parametrize(
    ("angle", "expected"),
    [(5, "New Moon"), (90, "First Quarter"), (180, "Full Moon"), (225, "Waning Gibbous")],
)
def test_phase_name(angle, expected):
    assert phase_name(angle) == expected
