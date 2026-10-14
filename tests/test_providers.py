import json

from providers.mock import MockProvider


def test_tokyo_attractions():
    items = MockProvider("data").get_attractions(" Tokyo ", "sightseeing")
    assert items[0] == {"title": "Senso-ji Temple", "type": "Culture", "rating": "4.8", "cost": "Free"}
    assert {"title", "type", "rating", "cost"} == set(items[0])


def test_tokyo_restaurants():
    items = MockProvider("data").get_restaurants("TOKYO", "local")
    assert items[0]["title"] == "Ichiran Ramen"
    assert {"title", "cuisine", "rating", "price"} == set(items[0])


def test_paris_data():
    p = MockProvider("data")
    assert p.get_attractions("paris", "x")[0]["title"] == "Louvre Museum"
    assert p.get_restaurants("paris", "x")


def test_generic_fallback():
    p = MockProvider("data")
    assert p.get_attractions("Atlantis", "x")[0]["title"] == "City Center Walk"
    assert p.get_restaurants("Atlantis", "x")[0]["title"] == "Local Bistro"


def test_new_city_needs_only_json(tmp_path):
    (tmp_path / "attractions.json").write_text(json.dumps({"rome": [{"title": "Colosseum"}], "_default": []}))
    assert MockProvider(str(tmp_path)).get_attractions("Rome", "x") == [{"title": "Colosseum"}]
