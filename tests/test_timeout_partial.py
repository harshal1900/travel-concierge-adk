import asyncio

from fastapi.testclient import TestClient

import main
from agents.attractions_agent import search_attractions
from agents.dining_agent import find_restaurants
from schemas import ATTRIBUTION_NOTE, build_response

client = TestClient(main.app)


def test_timeout_returns_504_with_correlation_id(monkeypatch, configure):
    async def slow(request):
        await asyncio.sleep(1)

    monkeypatch.setattr(main, "run_turn", slow)
    configure(request_timeout_seconds=0.05)
    r = client.post("/api/chat", json={"message": "hi"})
    assert r.status_code == 504
    body = r.json()
    assert body["correlation_id"] == r.headers["X-Correlation-ID"]
    assert "Traceback" not in r.text


def test_500_has_correlation_id(monkeypatch):
    async def boom(request):
        raise RuntimeError("internal detail")

    monkeypatch.setattr(main, "run_turn", boom)
    r = client.post("/api/chat", json={"message": "hi"})
    assert r.status_code == 500 and r.json()["correlation_id"] and "internal detail" not in r.text


def test_partial_failure_keeps_other_specialist():
    err = {"status": "error", "unavailable": "dining", "message": "x"}
    resp = build_response("Here are attractions.", [asyncio.run(search_attractions("tokyo")), err])
    assert [c.id for c in resp.a2ui_payload.components] == ["attractions_card_list"]
    assert "Dining recommendations are currently unavailable" in resp.agent_text
    assert "demo records" in resp.agent_text


def test_all_failed_gives_text_card():
    err = {"status": "error", "unavailable": "attractions", "message": "x"}
    resp = build_response("", [err])
    assert resp.a2ui_payload.components[0].type == "TextCard"
    assert "Attractions recommendations are currently unavailable" in resp.agent_text


def test_demo_note_not_duplicated():
    resp = build_response("These are demo records.", [asyncio.run(find_restaurants("tokyo"))])
    assert resp.agent_text.lower().count("demo") == 1


def test_live_results_get_attribution():
    live = {"status": "success", "data_source": "google_places", "components": [
        {"id": "dining_card_list", "type": "CardList", "title": "t",
         "items": [{"title": "a", "cuisine": "b", "rating": "4", "price": "$"}]}]}
    resp = build_response("Here you go.", [live])
    assert ATTRIBUTION_NOTE in resp.agent_text and "demo" not in resp.agent_text.lower()


def test_correlation_id_header_on_success(monkeypatch):
    async def ok(request):
        return "hi", []

    monkeypatch.setattr(main, "run_turn", ok)
    assert client.post("/api/chat", json={"message": "hi"}).headers["X-Correlation-ID"]
