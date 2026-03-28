from app.services.rag import rag_service


NO_MATCH_FALLBACK = (
    "No confident match found in the knowledge base. "
    "Please answer from your general knowledge and let the user know "
    "the answer is not based on a specific source."
)


def _format_article_results(results: list[dict]) -> str:
    """Format article search results for the voice agent."""
    if not results:
        return NO_MATCH_FALLBACK
    parts = []
    for r in results:
        source = f" (source: {r['article_title']})"
        parts.append(f"{r['chunk_text']}{source}")
    return "\n\n".join(parts)


def _format_podcast_results(results: list[dict]) -> str:
    """Format podcast search results for the voice agent."""
    if not results:
        return NO_MATCH_FALLBACK
    parts = []
    for r in results:
        header = f"From episode '{r['episode_title']}' at {r['timestamp_start']}–{r['timestamp_end']}:"
        parts.append(f"{header}\n{r['window_text']}")
    return "\n\n".join(parts)


class VapiService:
    """Webhook handler for Vapi voice chatbot function calls."""

    @staticmethod
    def _get_transcript_context(payload: dict) -> str:
        """Extract podcast_id and timestamp from the call metadata,
        then fetch the ~30s transcript window around that moment."""
        call = payload.get("message", {}).get("call", {})
        metadata = call.get("metadata", {})
        overrides_meta = call.get("assistantOverrides", {}).get("metadata", {})
        podcast_id = overrides_meta.get("podcast_id") or metadata.get("podcast_id")
        timestamp = payload.get("message", {}).get("functionCall", {}).get("parameters", {}).get("timestamp_seconds")
        if not podcast_id or timestamp is None:
            return ""
        return rag_service.get_transcript_context(podcast_id, int(timestamp))

    async def handle_function_call(self, payload: dict) -> dict:
        """Process function calls from Vapi."""
        function_call = payload.get("message", {}).get("functionCall", {})
        name = function_call.get("name")
        parameters = function_call.get("parameters", {})

        # In podcast mode, enrich context with the transcript around the current timestamp
        transcript_context = self._get_transcript_context(payload)
        conversation_context = parameters.get("conversation_context", "")
        if transcript_context:
            context = f"{transcript_context} {conversation_context}".strip()
        else:
            context = conversation_context

        if name == "search_knowledge":
            query = parameters.get("query", "")
            results = rag_service.search_articles(query=query, context=context)
            return {"result": _format_article_results(results)}

        if name == "search_previous_episodes":
            query = parameters.get("query", "")
            results = rag_service.search_podcasts(query=query, context=context)
            return {"result": _format_podcast_results(results)}

        return {"result": f"Unknown function: {name}"}


vapi_service = VapiService()
