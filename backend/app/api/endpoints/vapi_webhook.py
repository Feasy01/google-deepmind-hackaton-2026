from fastapi import APIRouter, Request

from app.services.vapi import vapi_service

router = APIRouter()


@router.post("/webhook")
async def vapi_webhook(request: Request):
    """Handle incoming Vapi webhook events (assistant-request, function-call, etc.)."""
    payload = await request.json()
    message_type = payload.get("message", {}).get("type")

    if message_type == "assistant-request":
        return vapi_service.get_assistant_config()

    if message_type == "function-call":
        result = await vapi_service.handle_function_call(payload)
        return result

    return {"ok": True}
