import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from services.ai_service import AIService
from services.auth import get_current_user_optional, check_limit, increment_usage
from models.schemas import ChatRequest

router = APIRouter(prefix="/api", tags=["chat"])


def get_ai_service():
    from main import get_ai_svc
    return get_ai_svc()


@router.post("/chat")
async def chat(request: ChatRequest, user=Depends(get_current_user_optional)):
    user_id = user["id"] if user else None

    allowed, reason = check_limit(user_id, "ai_message")
    if not allowed:
        async def limit_stream():
            yield f"data: {json.dumps({'content': reason, 'limit_reached': True})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(limit_stream(), media_type="text/event-stream")

    ai = get_ai_service()

    async def event_stream():
        async for chunk in ai.stream_chat(request.message, request.context):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield "data: [DONE]\n\n"
        if user_id:
            increment_usage(user_id, "ai_messages")

    return StreamingResponse(event_stream(), media_type="text/event-stream")
