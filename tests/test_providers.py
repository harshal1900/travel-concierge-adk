import asyncio
import json

from providers.mock import MockProvider


def run(coro):
    return asyncio.run(coro)


def test_tokyo_attractions():
    result = run(MockProvider("data").get_attractions(" Tokyo ", "sightseeing"))
    assert result.source == "mock" and result.fallback_reason is None
    assert result.items[0] == {"title": "Senso-ji Temple", "type": "Culture", "rating": "4.8", "cost": "Free"}
    assert {"title", "type", "rating", "cost"} == set(result.items[0])


def test_tokyo_restaurants():
    items = run(MockProvider("data").get_restaurants("TOKYO", "local")).items
    assert items[0]["title"] == "Ichiran Ramen"
    assert {"title", "cuisine", "rating", "price"} == set(items[0])


def test_paris_data():
    p = MockProvider("data")
    assert run(p.get_attractions("paris", "x")).items[0]["title"] == "Louvre Museum"
    assert run(p.get_restaurants("paris", "x")).items


def test_generic_fallback():
    p = MockProvider("data")
    assert run(p.get_attractions("Atlantis", "x")).items[0]["title"] == "City Center Walk"
    assert run(p.get_restaurants("Atlantis", "x")).items[0]["title"] == "Local Bistro"


def test_new_city_needs_only_json(tmp_path):
    (tmp_path / "attractions.json").write_text(json.dumps({"rome": [{"title": "Colosseum"}], "_default": []}))
    assert run(MockProvider(str(tmp_path)).get_attractions("Rome", "x")).items == [{"title": "Colosseum"}]
