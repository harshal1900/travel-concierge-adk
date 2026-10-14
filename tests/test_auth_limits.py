import asyncio

from fastapi.testclient import TestClient

import main
from agents.dining_agent import find_restaurants

client = TestClient(main.app)


def stub(monkeypatch, text="ok"):
    results = [asyncio.run(find_restaurants("tokyo"))]

    async def run_turn(request):
        return text, results

    monkeypatch.setattr(main, "run_turn", run_turn)


def test_no_key_configured_allows(monkeypatch):
    stub(monkeypatch)
    assert client.post("/api/chat", json={"message": "hi"}).status_code == 200


def test_missing_and_wrong_key_rejected(monkeypatch, configure):
    stub(monkeypatch)
    configure(service_api_key="secret")
    for headers in ({}, {"X-API-Key": "nope"}):
        r = client.post("/api/chat", json={"message": "hi"}, headers=headers)
        assert r.status_code == 401 and "secret" not in r.text and r.json()["correlation_id"]


def test_valid_key_accepted_and_health_open(monkeypatch, configure):
    stub(monkeypatch)
    configure(service_api_key="secret")
    assert client.post("/api/chat", json={"message": "hi"}, headers={"X-API-Key": "secret"}).status_code == 200
    assert client.get("/health").status_code == 200


def test_message_length_limits():
    assert client.post("/api/chat", json={"message": ""}).status_code == 422
    assert client.post("/api/chat", json={"message": "x" * 2001}).status_code == 422
    assert client.post("/api/chat", json={"message": "hi", "session_id": "s" * 65}).status_code == 422
    assert client.post("/api/chat", json={"message": "hi", "user_id": "u" * 65}).status_code == 422


def test_rate_limit(monkeypatch, configure):
    stub(monkeypatch)
    configure(rate_limit="2/minute")
    codes = [client.post("/api/chat", json={"message": "hi"}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]
    r = client.post("/api/chat", json={"message": "hi"})
    assert int(r.headers["Retry-After"]) >= 1


def test_rate_limit_is_per_key(monkeypatch, configure):
    stub(monkeypatch)
    configure(rate_limit="1/minute", service_api_key="")
    a = client.post("/api/chat", json={"message": "hi"}, headers={"X-API-Key": "a"})
    b = client.post("/api/chat", json={"message": "hi"}, headers={"X-API-Key": "b"})
    assert a.status_code == b.status_code == 200


def test_cors_middleware_limits_origins():
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI()
    app.add_middleware(CORSMiddleware, allow_origins=["https://app.example"], allow_methods=["POST"])
    app.get("/x")(lambda: {})
    c = TestClient(app)
    ok = c.get("/x", headers={"Origin": "https://app.example"})
    bad = c.get("/x", headers={"Origin": "https://evil.example"})
    assert ok.headers.get("access-control-allow-origin") == "https://app.example"
    assert "access-control-allow-origin" not in bad.headers
