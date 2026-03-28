import json
import logging

from fastapi import APIRouter, Request

from app.services.vapi import vapi_service

logger = logging.getLogger("vapi_webhook")
router = APIRouter()


@router.post("/webhook")
async def vapi_webhook(request: Request):
    """Handle incoming Vapi webhook events (assistant-request, function-call, etc.)."""
    payload = await request.json()
    message_type = payload.get("message", {}).get("type")

    logger.info("Webhook received: type=%s", message_type)
    logger.debug("Webhook payload: %s", json.dumps(payload, indent=2, default=str))

    if message_type == "function-call":
        function_call = payload.get("message", {}).get("functionCall", {})
        logger.info("function-call: name=%s params=%s", function_call.get("name"), function_call.get("parameters"))
        result = await vapi_service.handle_function_call(payload)
        logger.info("function-call result: %s", result)
        return result

    logger.info("Unhandled webhook type: %s", message_type)
    return {"ok": True}
