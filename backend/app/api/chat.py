"""Chat API: sessions and messages (AI research assistant)."""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter()

# In-memory store for MVP (replace with PostgreSQL in production)
_sessions: dict = {}
_messages: dict = {}  # session_id -> list of {role, content}


class CreateSessionResponse(BaseModel):
    session_id: str


class MessageIn(BaseModel):
    content: str


class MessageOut(BaseModel):
    role: str
    content: str


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session():
    sid = str(uuid.uuid4())
    _sessions[sid] = {"title": "New chat"}
    _messages[sid] = []
    return CreateSessionResponse(session_id=sid)


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "title": _sessions[session_id]["title"],
        "messages": _messages.get(session_id, []),
    }


@router.post("/sessions/{session_id}/messages")
async def add_message(session_id: str, body: MessageIn, request: Request):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    user_content = body.content.strip()
    if not user_content:
        raise HTTPException(status_code=400, detail="Empty message")
    _messages[session_id].append({"role": "user", "content": user_content})
    agent = getattr(request.app.state, "ai_agent", None)
    if not agent:
        reply = "AI agent not configured. Set OPENAI_API_KEY to enable research assistant."
    else:
        history = _messages[session_id][:-1]
        reply = await agent.ask(user_content, history=history)
    _messages[session_id].append({"role": "assistant", "content": reply})
    if _sessions[session_id]["title"] == "New chat":
        _sessions[session_id]["title"] = user_content[:50] + ("..." if len(user_content) > 50 else "")
    return {"role": "assistant", "content": reply}


class AskIn(BaseModel):
    message: str


@router.post("/ask")
async def ask_one_off(body: AskIn, request: Request):
    """One-off question without session."""
    agent = getattr(request.app.state, "ai_agent", None)
    if not agent:
        return {"reply": "AI agent not configured. Set OPENAI_API_KEY."}
    reply = await agent.ask(body.message)
    return {"reply": reply}
