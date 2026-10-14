"""Pydantic models for the simplified A2UI-style payload returned by /api/chat."""

from typing import Any, Literal

from pydantic import BaseModel, ValidationError

ATTRACTIONS_ID = "attractions_card_list"
DINING_ID = "dining_card_list"
FALLBACK_ID = "fallback_text_card"
COMPONENT_ORDER = [ATTRACTIONS_ID, DINING_ID]


class AttractionItem(BaseModel):
    title: str
    type: str
    rating: str
    cost: str


class DiningItem(BaseModel):
    title: str
    cuisine: str
    rating: str
    price: str


class CardList(BaseModel):
    id: str
    type: Literal["CardList"] = "CardList"
    title: str
    items: list[AttractionItem] | list[DiningItem]


class TextCard(BaseModel):
    id: str = FALLBACK_ID
    type: Literal["TextCard"] = "TextCard"
    content: str


class A2UIPayload(BaseModel):
    a2ui_surface: Literal["main_view"] = "main_view"
    components: list[CardList | TextCard]


class ChatResponse(BaseModel):
    status: Literal["success"] = "success"
    agent_text: str
    a2ui_payload: A2UIPayload


def merge_components(tool_results: list[Any]) -> list[dict[str, Any]]:
    """Merge components from every specialist result by component ID (first wins)."""
    merged: dict[str, dict[str, Any]] = {}
    for result in tool_results:
        if not isinstance(result, dict):
            continue
        for component in result.get("components") or []:
            if isinstance(component, dict) and isinstance(component.get("id"), str):
                merged.setdefault(component["id"], component)
    ordered = [merged.pop(cid) for cid in COMPONENT_ORDER if cid in merged]
    return ordered + list(merged.values())


def build_response(agent_text: str, tool_results: list[Any]) -> ChatResponse:
    """Validate merged components; fall back to a TextCard if none are valid."""
    try:
        components = merge_components(tool_results)
        if components:
            payload = A2UIPayload.model_validate({"components": components})
            return ChatResponse(agent_text=agent_text, a2ui_payload=payload)
    except ValidationError:
        pass
    text = agent_text or "No recommendations were available for this request."
    return ChatResponse(
        agent_text=text,
        a2ui_payload=A2UIPayload(components=[TextCard(content=text)]),
    )
