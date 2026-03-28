from fastapi import APIRouter

from app.api.endpoints import health, chat, vapi_webhook

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(vapi_webhook.router, prefix="/vapi", tags=["vapi"])
