from fastapi import APIRouter

from app.api.endpoints import health, chat, vapi_webhook, podcast

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(vapi_webhook.router, prefix="/vapi", tags=["vapi"])
api_router.include_router(podcast.router, prefix="/podcast", tags=["podcast"])
