from fastapi import APIRouter

from app.models.chat import ChatRequest, ChatResponse
from app.services.deepmind import deepmind_service

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    reply = await deepmind_service.generate_response(
        message=request.message,
        conversation_history=request.history,
    )
    return ChatResponse(reply=reply)
