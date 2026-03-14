import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from services.auth import get_current_user_optional, check_limit, increment_usage
from models.schemas import ChatRequest

router = APIRouter(prefix="/api", tags=["research"])


def _get_dexter():
    from main import get_dexter_agent
    return get_dexter_agent()


@router.post("/research")
async def deep_research(request: ChatRequest, user=Depends(get_current_user_optional)):
    user_id = user["id"] if user else None

    allowed, reason = check_limit(user_id, "ai_message")
    if not allowed:
        async def limit_stream():
            yield f"data: {json.dumps({'type': 'answer', 'content': reason, 'limit_reached': True})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'iterations': 0, 'tools_called': 0, 'time_ms': 0})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(limit_stream(), media_type="text/event-stream")

    agent = _get_dexter()

    if not agent or not agent.is_available():
        async def unavailable_stream():
            msg = (
                "Deep Research requires both OPENAI_API_KEY and FINANCIAL_DATASETS_API_KEY. "
                "Add them to your .env file to enable Dexter-powered research."
            )
            yield f"data: {json.dumps({'type': 'answer', 'content': msg})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'iterations': 0, 'tools_called': 0, 'time_ms': 0})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(unavailable_stream(), media_type="text/event-stream")

    async def event_stream():
        async for event in agent.run(request.message):
            yield f"data: {json.dumps(event, default=str)}\n\n"
        yield "data: [DONE]\n\n"
        if user_id:
            increment_usage(user_id, "ai_messages")

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/research/status")
async def research_status():
    agent = _get_dexter()
    return {
        "available": agent is not None and agent.is_available(),
        "provider": "Financial Datasets API + OpenAI",
    }
