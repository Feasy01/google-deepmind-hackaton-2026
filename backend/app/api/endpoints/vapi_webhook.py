from fastapi import APIRouter, Request

from app.services.rag import rag_service
from app.services.vapi import vapi_service

router = APIRouter()


def _format_article_results(results: list[dict]) -> str:
    """Format article search results for the voice agent."""
    if not results:
        return "No relevant articles found."
    parts = []
    for r in results:
        source = f" (source: {r['article_title']})"
        parts.append(f"{r['chunk_text']}{source}")
    return "\n\n".join(parts)


def _format_podcast_results(results: list[dict]) -> str:
    """Format podcast search results for the voice agent."""
    if not results:
        return "No relevant podcast episodes found."
    parts = []
    for r in results:
        header = f"From episode '{r['episode_title']}' at {r['timestamp_start']}–{r['timestamp_end']}:"
        parts.append(f"{header}\n{r['window_text']}")
    return "\n\n".join(parts)


@router.post("/webhook")
async def vapi_webhook(request: Request):
    """Handle incoming Vapi webhook events (assistant-request, function-call, etc.)."""
    payload = await request.json()
    message_type = payload.get("message", {}).get("type")

    if message_type == "assistant-request":
        return vapi_service.get_assistant_config()

    if message_type == "function-call":
        function_call = payload.get("message", {}).get("functionCall", {})
        name = function_call.get("name")
        parameters = function_call.get("parameters", {})

        if name == "search_knowledge":
            query = parameters.get("query", "")
            context = parameters.get("conversation_context", "")
            results = rag_service.search_articles(query=query, context=context)
            return {"result": _format_article_results(results)}

        if name == "search_previous_episodes":
            query = parameters.get("query", "")
            context = parameters.get("conversation_context", "")
            results = rag_service.search_podcasts(query=query, context=context)
            return {"result": _format_podcast_results(results)}

        return {"result": f"Unknown function: {name}"}

    return {"ok": True}
