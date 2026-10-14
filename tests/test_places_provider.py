import asyncio
import json
from pathlib import Path

import httpx
import pytest

from providers import FallbackProvider
from providers.google_places import FIELD_MASK, GooglePlacesProvider, PlacesError
from providers.mock import MockProvider

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name):
    return json.loads((FIXTURES / name).read_text())


def provider(handler):
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return GooglePlacesProvider("test-key", client=client)


def ok(name):
    return lambda request: httpx.Response(200, json=fixture(name))


def run(coro):
    return asyncio.run(coro)


def test_attractions_mapping_and_limit():
    result = run(provider(ok("places_attractions.json")).get_attractions("Tokyo", "sightseeing"))
    assert result.source == "google_places" and len(result.items) == 5
    assert result.items[0] == {"title": "Sample Temple", "type": "Buddhist temple", "rating": "4.6", "cost": "Not listed"}
    assert result.items[2] == {"title": "Sample Park", "type": "Not listed", "rating": "Not listed", "cost": "Not listed"}


def test_restaurant_price_levels():
    items = run(provider(ok("places_restaurants.json")).get_restaurants("Tokyo", "sushi")).items
    assert [i["price"] for i in items] == ["$$$$", "$$", "Not listed"]
    assert items[0]["cuisine"] == "Sushi restaurant"


def test_request_shape():
    seen = {}

    def handler(request):
        seen["headers"], seen["body"] = request.headers, json.loads(request.content)
        return httpx.Response(200, json=fixture("places_restaurants.json"))

    run(provider(handler).get_restaurants("Tokyo", "sushi"))
    assert seen["body"] == {"textQuery": "sushi restaurants in Tokyo", "pageSize": 5}
    assert seen["headers"]["x-goog-fieldmask"] == FIELD_MASK
    assert seen["headers"]["x-goog-api-key"] == "test-key"


def test_errors_raise_places_error():
    for handler in (
        lambda r: httpx.Response(403, json={"error": "denied"}),
        lambda r: httpx.Response(200, json={}),
        lambda r: httpx.Response(200, text="not json"),
    ):
        with pytest.raises(PlacesError):
            run(provider(handler).get_attractions("Tokyo", "x"))


def test_wrong_key_falls_back_to_labelled_mock():
    live = provider(lambda r: httpx.Response(401, json={"error": "bad key"}))
    result = run(FallbackProvider(live, MockProvider("data")).get_attractions("Tokyo", "x"))
    assert result.source == "mock" and result.fallback_reason == "Places returned HTTP 401"
    assert result.items[0]["title"] == "Senso-ji Temple"
    assert "bad key" not in result.fallback_reason


def test_timeout_falls_back():
    def handler(request):
        raise httpx.ReadTimeout("slow")

    result = run(FallbackProvider(provider(handler), MockProvider("data")).get_restaurants("Paris", "x"))
    assert result.source == "mock" and "timed out" in result.fallback_reason
