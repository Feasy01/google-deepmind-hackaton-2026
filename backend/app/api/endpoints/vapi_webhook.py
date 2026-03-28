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

    if message_type == "tool-calls":
        tool_calls = payload.get("message", {}).get("toolCallList", [])
        logger.info("tool-calls: %d calls, raw keys: %s", len(tool_calls),
                    [tc.get("function", {}).get("name") for tc in tool_calls])
        results = []
        for tc in tool_calls:
            tool_call_id = tc.get("id", "")
            fn = tc.get("function", {})
            name = fn.get("name", "")
            raw_args = fn.get("arguments", "{}")
            # arguments is a JSON string per Vapi SDK (ToolCallFunction.arguments: str)
            if isinstance(raw_args, str):
                try:
                    params = json.loads(raw_args)
                except json.JSONDecodeError:
                    params = {}
            else:
                params = raw_args  # already a dict (defensive)
            logger.info("  tool-call: id=%s name=%s params=%s", tool_call_id, name, params)
            compat_payload = {
                "message": {
                    **payload.get("message", {}),
                    "functionCall": {
                        "name": name,
                        "parameters": params,
                    },
                }
            }
            result = await vapi_service.handle_function_call(compat_payload)
            logger.info("  tool-call result: %s", result)
            results.append({
                "toolCallId": tool_call_id,
                "name": name,
                "result": result.get("result", ""),
            })
        return {"results": results}

    logger.info("Unhandled webhook type: %s", message_type)
    return {"ok": True}
