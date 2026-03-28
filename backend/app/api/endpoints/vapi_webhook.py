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

    if message_type == "tool-calls":
        tool_calls = payload.get("message", {}).get("toolCallList", [])
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
            logger.info("tool-call: %s | query=%s ts=%s",
                        name, params.get("query", "-"), params.get("timestamp_seconds", "-"))
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
            results.append({
                "toolCallId": tool_call_id,
                "name": name,
                "result": result.get("result", ""),
            })
        return {"results": results}
    return {"ok": True}
