"""FastAPI entry point. Monday skeleton: /health and a /api/chat stub; ADK wiring comes next."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Smart Travel & Local Experience Concierge")


class ChatRequest(BaseModel):
    user_id: str = "demo_user"
    session_id: str = "session_001"
    message: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(request: ChatRequest) -> dict:
    raise HTTPException(status_code=501, detail="Chat is not implemented yet.")
