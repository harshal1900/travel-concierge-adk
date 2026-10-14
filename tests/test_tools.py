import asyncio
import inspect

from agents.attractions_agent import search_attractions
from agents.coordinator import travel_coordinator
from agents.dining_agent import find_restaurants


def test_signatures():
    a = inspect.signature(search_attractions).parameters
    d = inspect.signature(find_restaurants).parameters
    assert list(a) == ["city", "category"] and a["category"].default == "sightseeing"
    assert list(d) == ["city", "cuisine"] and d["cuisine"].default == "local"


def test_attractions_payload():
    r = asyncio.run(search_attractions("tokyo"))
    c = r["components"][0]
    assert r["a2ui_surface"] == "main_view"
    assert (c["id"], c["type"], c["title"]) == ("attractions_card_list", "CardList", "Top Attractions in Tokyo")
    assert r["data_source"] == "mock"


def test_dining_payload():
    c = asyncio.run(find_restaurants("Paris", "french"))["components"][0]
    assert (c["id"], c["title"]) == ("dining_card_list", "Recommended Dining in Paris")


def test_tool_error_is_explicit(monkeypatch):
    def boom():
        raise RuntimeError("secret")

    monkeypatch.setattr("agents.dining_agent.get_provider", boom)
    r = asyncio.run(find_restaurants("tokyo"))
    assert r["status"] == "error" and "components" not in r and "secret" not in str(r)


def test_coordinator_registers_both_specialists():
    assert [a.name for a in travel_coordinator.sub_agents] == ["AttractionsSpecialist", "DiningSpecialist"]


def test_live_fallback_is_labelled_demo(monkeypatch):
    import providers
    from providers.base import ProviderResult

    class P:
        async def get_attractions(self, city, category):
            return ProviderResult([{"title": "x", "type": "t", "rating": "1", "cost": "Free"}], "mock", "Places returned HTTP 401")

    monkeypatch.setattr("agents.attractions_agent.get_provider", lambda: P())
    r = asyncio.run(search_attractions("tokyo"))
    assert r["data_source"] == "mock" and r["demo_fallback"] is True
