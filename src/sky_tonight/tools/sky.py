"""Planet and Moon calculations with Skyfield."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from skyfield import almanac
from skyfield.api import wgs84
from skyfield.magnitudelib import planetary_magnitude

from sky_tonight.tools.ephemeris import ephemeris, timescale
from sky_tonight.tools.models import MoonInfo, PlanetPosition, PlanetsReport

# Display name -> ephemeris key. DE421 only has barycenters for the outer planets.
PLANETS = {
    "Mercury": "mercury",
    "Venus": "venus",
    "Mars": "mars",
    "Jupiter": "jupiter barycenter",
    "Saturn": "saturn barycenter",
    "Uranus": "uranus barycenter",
    "Neptune": "neptune barycenter",
}

MIN_ALTITUDE_DEG = 10.0
# Civil twilight ends at -6 degrees: bright planets are easy to spot from then on.
DARK_SUN_ALTITUDE_DEG = -6.0
# Faintest magnitude visible to the unaided eye under dark skies (Uranus is borderline).
NAKED_EYE_MAGNITUDE = 6.0

_COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def compass_direction(azimuth_deg: float) -> str:
    return _COMPASS[round(azimuth_deg / 45) % 8]


def _observer(lat: float, lon: float):
    return ephemeris()["earth"] + wgs84.latlon(lat, lon)


def visible_planets(lat: float, lon: float, when: datetime) -> PlanetsReport:
    """Altitude, direction and brightness of each planet at `when` (timezone-aware)."""
    if when.tzinfo is None:
        raise ValueError("`when` must be timezone-aware")

    t = timescale().from_datetime(when)
    observer = _observer(lat, lon).at(t)
    sun_alt = observer.observe(ephemeris()["sun"]).apparent().altaz()[0].degrees
    dark = sun_alt < DARK_SUN_ALTITUDE_DEG

    planets = []
    for name, key in PLANETS.items():
        astrometric = observer.observe(ephemeris()[key])
        alt, az, _ = astrometric.apparent().altaz()
        magnitude = float(planetary_magnitude(astrometric))
        planets.append(
            PlanetPosition(
                name=name,
                altitude_deg=round(alt.degrees, 1),
                azimuth_deg=round(az.degrees, 1),
                direction=compass_direction(az.degrees),
                magnitude=round(magnitude, 1),
                visible=dark and alt.degrees > MIN_ALTITUDE_DEG,
                naked_eye=magnitude <= NAKED_EYE_MAGNITUDE,
            )
        )

    return PlanetsReport(
        when=when,
        sun_altitude_deg=round(sun_alt, 1),
        sky_dark_enough=dark,
        planets=planets,
    )


def phase_name(phase_angle_deg: float) -> str:
    """Name for a Moon phase angle (0 = new, 90 = first quarter, 180 = full, 270 = last quarter)."""
    names = [
        "New Moon",
        "Waxing Crescent",
        "First Quarter",
        "Waxing Gibbous",
        "Full Moon",
        "Waning Gibbous",
        "Last Quarter",
        "Waning Crescent",
    ]
    return names[round(phase_angle_deg / 45) % 8]


def moon_info(lat: float, lon: float, day: date, timezone: str = "UTC") -> MoonInfo:
    """Moon phase, illumination and rise/set times on the local calendar day `day`."""
    tz = ZoneInfo(timezone)
    ts = timescale()
    eph = ephemeris()

    evening = ts.from_datetime(datetime.combine(day, time(21, 0), tz))
    phase = almanac.moon_phase(eph, evening).degrees
    illumination = almanac.fraction_illuminated(eph, "moon", evening) * 100

    start = ts.from_datetime(datetime.combine(day, time(0, 0), tz))
    end = ts.from_datetime(datetime.combine(day + timedelta(days=1), time(0, 0), tz))
    observer = _observer(lat, lon)
    risings, _ = almanac.find_risings(observer, eph["moon"], start, end)
    settings, _ = almanac.find_settings(observer, eph["moon"], start, end)

    def first_local(times) -> datetime | None:
        return times[0].utc_datetime().astimezone(tz) if len(times) else None

    return MoonInfo(
        date=day.isoformat(),
        phase_name=phase_name(phase),
        phase_angle_deg=round(phase, 1),
        illumination_pct=round(illumination, 1),
        moonrise=first_local(risings),
        moonset=first_local(settings),
    )
