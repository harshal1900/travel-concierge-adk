import asyncio
import pytest
from fastapi.testclient import TestClient

import main
from agents.attractions_agent import search_attractions
from agents.dining_agent import find_restaurants

client = TestClient(main.app)


def fake_turn(text, results):
    async def run_turn(request):
        return text, results

    return run_turn


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_missing_message_422():
    assert client.post("/api/chat", json={}).status_code == 422


def test_combined(monkeypatch):
    monkeypatch.setattr(main, "run_turn", fake_turn("ok", [asyncio.run(search_attractions("tokyo")), asyncio.run(find_restaurants("tokyo"))]))
    body = client.post("/api/chat", json={"message": "tokyo sightseeing and dinner"}).json()
    assert body["status"] == "success" and body["agent_text"] == "ok"
    assert [c["id"] for c in body["a2ui_payload"]["components"]] == ["attractions_card_list", "dining_card_list"]


def test_dining_only(monkeypatch):
    monkeypatch.setattr(main, "run_turn", fake_turn("ok", [asyncio.run(find_restaurants("tokyo"))]))
    body = client.post("/api/chat", json={"message": "sushi"}).json()
    assert [c["id"] for c in body["a2ui_payload"]["components"]] == ["dining_card_list"]


def test_fallback(monkeypatch):
    monkeypatch.setattr(main, "run_turn", fake_turn("plain answer", []))
    comp = client.post("/api/chat", json={"message": "hi"}).json()["a2ui_payload"]["components"][0]
    assert comp == {"id": "fallback_text_card", "type": "TextCard", "content": "plain answer"}


def test_500_is_safe(monkeypatch):
    async def boom(request):
        raise RuntimeError("api key abc123 traceback")

    monkeypatch.setattr(main, "run_turn", boom)
    r = client.post("/api/chat", json={"message": "hi"})
    assert r.status_code == 500 and "abc123" not in r.text
