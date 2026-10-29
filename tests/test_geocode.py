import httpx
import pytest
import respx

from sky_tonight.tools.geocode import GEOCODING_URL, PlaceNotFoundError, geocode

LISBON_RESPONSE = {
    "results": [
        {
            "id": 2267057,
            "name": "Lisbon",
            "latitude": 38.71667,
            "longitude": -9.13333,
            "country": "Portugal",
            "timezone": "Europe/Lisbon",
        }
    ]
}


@respx.mock
def test_geocode_returns_first_match():
    route = respx.get(GEOCODING_URL).mock(return_value=httpx.Response(200, json=LISBON_RESPONSE))

    location = geocode("Lisbon")

    assert route.calls.last.request.url.params["name"] == "Lisbon"
    assert location.name == "Lisbon"
    assert location.country == "Portugal"
    assert location.latitude == pytest.approx(38.71667)
    assert location.longitude == pytest.approx(-9.13333)
    assert location.timezone == "Europe/Lisbon"


@respx.mock
def test_geocode_raises_when_nothing_matches():
    respx.get(GEOCODING_URL).mock(return_value=httpx.Response(200, json={"generationtime_ms": 0.1}))

    with pytest.raises(PlaceNotFoundError):
        geocode("Nowhereville Xyz")


@respx.mock
def test_geocode_propagates_http_errors():
    respx.get(GEOCODING_URL).mock(return_value=httpx.Response(503))

    with pytest.raises(httpx.HTTPStatusError):
        geocode("Lisbon")
