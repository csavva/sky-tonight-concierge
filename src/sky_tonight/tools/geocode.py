"""Turn a place name into coordinates and a timezone via the Open-Meteo geocoding API."""

import httpx

from sky_tonight.tools.models import Location

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
TIMEOUT_SECONDS = 10.0


class PlaceNotFoundError(LookupError):
    pass


def geocode(place: str) -> Location:
    """Return the best match for `place`. Raises PlaceNotFoundError if there is none."""
    response = httpx.get(
        GEOCODING_URL,
        params={"name": place, "count": 1, "language": "en", "format": "json"},
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    results = response.json().get("results") or []
    if not results:
        raise PlaceNotFoundError(f"No place found matching {place!r}")

    hit = results[0]
    return Location(
        name=hit["name"],
        country=hit.get("country"),
        latitude=hit["latitude"],
        longitude=hit["longitude"],
        timezone=hit.get("timezone") or "UTC",
    )
