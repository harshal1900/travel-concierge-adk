"""FastAPI entry point: routes, ADK runner/session lifecycle, event extraction, error mapping."""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel

from agents.coordinator import travel_coordinator
from config import settings
from schemas import ChatResponse, build_response

logger = logging.getLogger(__name__)

APP_NAME = "travel_concierge"

# Sessions are in-memory: process-local and reset on restart.
session_service = InMemorySessionService()
runner = Runner(
    app_name=APP_NAME,
    agent=travel_coordinator,
    session_service=session_service,
    auto_create_session=True,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not settings.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set; copy .env.example to .env and add your key.")
    yield


app = FastAPI(title="Smart Travel & Local Experience Concierge", lifespan=lifespan)


class ChatRequest(BaseModel):
    user_id: str = "demo_user"
    session_id: str = "session_001"
    message: str


async def run_turn(request: ChatRequest) -> tuple[str, list[Any]]:
    """Run one turn; return the agent text and every specialist function response."""
    message = types.Content(role="user", parts=[types.Part(text=request.message)])
    texts: list[str] = []
    tool_results: list[Any] = []
    async for event in runner.run_async(
        user_id=request.user_id, session_id=request.session_id, new_message=message
    ):
        for response in event.get_function_responses():
            tool_results.append(response.response)
        if event.content and event.content.parts and not event.get_function_calls():
            text = "".join(p.text for p in event.content.parts if p.text and not p.thought)
            if text.strip() and not event.partial:
                texts.append(text.strip())
    return "\n\n".join(texts), tool_results


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        agent_text, tool_results = await run_turn(request)
    except Exception:
        logger.exception("Chat turn failed")
        raise HTTPException(status_code=500, detail="Something went wrong. Please try again.")
    return build_response(agent_text, tool_results)
