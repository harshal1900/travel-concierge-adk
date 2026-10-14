import asyncio
from agents.attractions_agent import search_attractions
from agents.dining_agent import find_restaurants
from schemas import build_response, merge_components


def ids(resp):
    return [c.id for c in resp.a2ui_payload.components]


def test_merge_both_in_order():
    resp = build_response("hi", [asyncio.run(find_restaurants("tokyo")), asyncio.run(search_attractions("tokyo"))])
    assert ids(resp) == ["attractions_card_list", "dining_card_list"]


def test_single_specialist():
    assert ids(build_response("hi", [asyncio.run(find_restaurants("tokyo"))])) == ["dining_card_list"]


def test_failed_specialist_keeps_other():
    err = {"status": "error", "message": "unavailable"}
    assert ids(build_response("hi", [asyncio.run(search_attractions("tokyo")), err])) == ["attractions_card_list"]


def test_dedup_by_id():
    r = asyncio.run(search_attractions("tokyo"))
    assert len(merge_components([r, r])) == 1


def test_empty_falls_back_to_text_card():
    resp = build_response("just text", [])
    assert ids(resp) == ["fallback_text_card"]
    assert resp.a2ui_payload.components[0].content == "just text"


def test_malformed_falls_back():
    bad = {"components": [{"id": "dining_card_list", "type": "CardList", "title": "x", "items": [{"nope": 1}]}]}
    assert ids(build_response("text", [bad, "junk", None])) == ["fallback_text_card"]
