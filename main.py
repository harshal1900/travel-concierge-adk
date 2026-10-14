"""FastAPI entry point: routes, ADK runner/session lifecycle, event extraction, error mapping."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from agents.coordinator import travel_coordinator
from config import settings
from observability import configure_logging, correlation_middleware
from schemas import ChatResponse, build_response, routing_of
from security import guard

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
    problems = settings.validate()
    if problems:
        raise RuntimeError("Invalid configuration: " + "; ".join(problems))
    yield


configure_logging()
app = FastAPI(title="Smart Travel & Local Experience Concierge", lifespan=lifespan)
app.middleware("http")(correlation_middleware)
if settings.allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["POST", "GET"],
        allow_headers=["Content-Type", "X-API-Key"],
    )


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        {"detail": exc.detail, "correlation_id": getattr(request.state, "correlation_id", None)},
        status_code=exc.status_code,
        headers=getattr(exc, "headers", None),
    )


class ChatRequest(BaseModel):
    user_id: str = Field(default="demo_user", max_length=64)
    session_id: str = Field(default="session_001", max_length=64)
    message: str = Field(min_length=1, max_length=2000)


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


@app.post("/api/chat", response_model=ChatResponse, dependencies=[Depends(guard)])
async def chat(chat_request: ChatRequest, request: Request) -> ChatResponse:
    request.state.log.update(user_id=chat_request.user_id, session_id=chat_request.session_id)
    try:
        async with asyncio.timeout(settings.request_timeout_seconds):
            agent_text, tool_results = await run_turn(chat_request)
    except TimeoutError:
        logger.warning("Chat turn timed out")
        raise HTTPException(status_code=504, detail="The assistant took too long to answer. Please try again.")
    except Exception:
        logger.exception("Chat turn failed")
        raise HTTPException(status_code=500, detail="Something went wrong. Please try again.")
    request.state.log["routing"] = routing_of(tool_results)
    return build_response(agent_text, tool_results)
