import httpx

from app.core.config import settings
from app.services.rag import rag_service

VAPI_BASE_URL = "https://api.vapi.ai"


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
    """Bootstrap service for Vapi voice chatbot integration."""

    def get_assistant_config(self) -> dict:
        """Return the assistant configuration for Vapi assistant-request webhooks."""
        webhook_url = settings.VAPI_WEBHOOK_URL.rstrip("/")
        return {
            "assistant": {
                "firstMessage": "Hey, welcome to the Huberman Lab. What can I help you with today?",
                "model": {
                    "provider": "google",
                    "model": "gemini-2.0-flash",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You ARE Andrew Huberman — neuroscientist, tenured professor of neurobiology "
                                "and ophthalmology at Stanford School of Medicine, and host of the Huberman Lab podcast. "
                                "You have deep expertise in neuroscience, physiology, human performance, "
                                "sleep, stress, hormones, neuroplasticity, and science-based health protocols.\n\n"
                                "PERSONALITY & SPEAKING STYLE:\n"
                                "- Speak in first person as Andrew. Be warm, curious, and enthusiastic about science.\n"
                                "- Use your signature style: explain mechanisms clearly, reference specific studies, "
                                "and give actionable protocols when relevant.\n"
                                "- Use phrases natural to you like 'what the data show is...', "
                                "'the really interesting thing here is...', 'so the protocol would be...', "
                                "'there's beautiful work from [lab/researcher] showing...'.\n"
                                "- Be conversational but precise. Break down complex science into accessible language.\n"
                                "- When appropriate, connect topics back to practical tools and protocols people can use.\n\n"
                                "ANSWERING QUESTIONS:\n"
                                "- Use the search tools to ground your answers in the knowledge base.\n"
                                "- When your answer comes from a search result, naturally weave in the source — "
                                "e.g., 'there's a really nice paper on this that shows...' or "
                                "'we actually covered this in a previous episode...'. "
                                "Don't read out full titles or URLs.\n"
                                "- If no knowledge base results are found, answer from your general scientific knowledge "
                                "but be upfront: 'from what I recall...' or 'based on the literature I'm familiar with...'.\n"
                                "- Keep answers concise and conversational — this is a voice interaction, not a lecture."
                            ),
                        }
                    ],
                },
                "voice": {
                    "provider": "11labs",
                    "voiceId": settings.ELEVENLABS_VOICE_ID,
                },
                "transcriber": {
                    "provider": "deepgram",
                    "model": "nova-2",
                    "language": "en",
                },
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "search_knowledge",
                            "description": "Search articles for factual knowledge about a topic. Use when the caller asks a factual question.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "The search query based on what the user is asking",
                                    },
                                    "conversation_context": {
                                        "type": "string",
                                        "description": "Last 30 seconds of conversation for additional context",
                                    },
                                },
                                "required": ["query"],
                            },
                        },
                        "server": {
                            "url": f"{webhook_url}/api/vapi/webhook",
                        },
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "search_previous_episodes",
                            "description": "Search previous podcast episodes. Use when the caller asks about something discussed in a past episode or wants to hear a previous discussion.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "The search query based on what the user is asking",
                                    },
                                    "conversation_context": {
                                        "type": "string",
                                        "description": "Last 30 seconds of conversation for additional context",
                                    },
                                },
                                "required": ["query"],
                            },
                        },
                        "server": {
                            "url": f"{webhook_url}/api/vapi/webhook",
                        },
                    },
                ],
                "endCallFunctionEnabled": True,
                "endCallMessage": "Goodbye! Have a great day.",
            }
        }

    def get_podcast_assistant_config(self, podcast_id: str) -> dict:
        """Return the assistant configuration for the podcast interactive mode."""
        webhook_url = settings.VAPI_WEBHOOK_URL.rstrip("/")
        return {
            "assistant": {
                "firstMessage": "Hey, I'm here listening along with you. If anything comes up, just ask — I'll pause and break it down for you.",
                "model": {
                    "provider": "google",
                    "model": "gemini-2.0-flash",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You ARE Andrew Huberman — neuroscientist, tenured professor of neurobiology "
                                "and ophthalmology at Stanford School of Medicine, and host of the Huberman Lab podcast. "
                                "You have deep expertise in neuroscience, physiology, human performance, "
                                "sleep, stress, hormones, neuroplasticity, and science-based health protocols.\n\n"
                                "The user is currently listening to one of your podcast episodes. "
                                "You are their interactive companion — ready to pause, clarify, and expand on anything they hear.\n\n"
                                "PERSONALITY & SPEAKING STYLE:\n"
                                "- Speak in first person as Andrew. Be warm, curious, and enthusiastic about science.\n"
                                "- Use your signature style: explain mechanisms clearly, reference specific studies, "
                                "and give actionable protocols when relevant.\n"
                                "- Use phrases natural to you like 'what the data show is...', "
                                "'the really interesting thing here is...', 'so the protocol would be...', "
                                "'there's beautiful work from [lab/researcher] showing...'.\n"
                                "- Be conversational but precise. Break down complex science into accessible language.\n\n"
                                "IMPORTANT RULES:\n"
                                "1. When the user asks ANY question or says something that sounds like a question "
                                "(e.g., 'hey andrew, what is HRV?', 'what did he mean by that?'), "
                                "IMMEDIATELY call the stop_player tool to pause the podcast, "
                                "then call search_knowledge or search_previous_episodes with their question.\n"
                                "2. Use search_knowledge for factual questions about topics. "
                                "Use search_previous_episodes for questions about what was discussed in the podcast.\n"
                                "3. When the user says something like 'thank you', 'thanks', 'got it', 'resume', "
                                "'continue', 'play', or any dismissal phrase, call start_player to resume the podcast.\n"
                                "4. When your answer comes from a search result, naturally weave in the source — "
                                "e.g., 'there's a really nice paper on this...' or "
                                "'we actually talked about this in a previous episode...'. "
                                "Don't read out full titles or URLs.\n"
                                "5. If no knowledge base results are found, answer from your general scientific knowledge "
                                "but note it: 'from what I recall...' or 'based on the literature...'.\n"
                                "6. Keep answers concise and conversational — this is a voice interaction, not a lecture."
                            ),
                        }
                    ],
                    "tools": [
                        {
                            "type": "function",
                            "function": {
                                "name": "stop_player",
                                "description": "Pause the podcast player. Call this immediately when the user asks a question.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {},
                                    "required": [],
                                },
                            },
                            "async": True,
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "start_player",
                                "description": "Resume the podcast player. Call this when the user is done with their question and wants to continue listening.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {},
                                    "required": [],
                                },
                            },
                            "async": True,
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "search_knowledge",
                                "description": "Search articles for factual knowledge about a topic. Use when the caller asks a factual question.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "query": {
                                            "type": "string",
                                            "description": "The search query based on what the user is asking",
                                        },
                                        "conversation_context": {
                                            "type": "string",
                                            "description": "Last 30 seconds of conversation for additional context",
                                        },
                                        "timestamp_seconds": {
                                            "type": "integer",
                                            "description": "The podcast playback position in seconds when the user asked. Get this from the system message.",
                                        },
                                    },
                                    "required": ["query"],
                                },
                            },
                            "server": {
                                "url": f"{webhook_url}/api/vapi/webhook",
                            },
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "search_previous_episodes",
                                "description": "Search previous podcast episodes. Use when the caller asks about something discussed in a past episode.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "query": {
                                            "type": "string",
                                            "description": "The search query based on what the user is asking",
                                        },
                                        "conversation_context": {
                                            "type": "string",
                                            "description": "Last 30 seconds of conversation for additional context",
                                        },
                                        "timestamp_seconds": {
                                            "type": "integer",
                                            "description": "The podcast playback position in seconds when the user asked. Get this from the system message.",
                                        },
                                    },
                                    "required": ["query"],
                                },
                            },
                            "server": {
                                "url": f"{webhook_url}/api/vapi/webhook",
                            },
                        },
                    ],
                },
                "voice": {
                    "provider": "11labs",
                    "voiceId": settings.ELEVENLABS_VOICE_ID,
                },
                "transcriber": {
                    "provider": "deepgram",
                    "model": "nova-2",
                    "language": "en",
                },
                "silenceTimeoutSeconds": 600,
                "backgroundDenoisingEnabled": True,
                "clientMessages": ["tool-calls", "transcript"],
                "endCallFunctionEnabled": True,
                "endCallMessage": "Goodbye! Enjoy the rest of the podcast.",
                "metadata": {
                    "podcast_id": podcast_id,
                },
            }
        }

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

    async def create_web_call(self) -> dict:
        """Create a Vapi web call and return the call object for frontend to connect."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{VAPI_BASE_URL}/call/web",
                headers={
                    "Authorization": f"Bearer {settings.VAPI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "assistant": {
                        "firstMessage": "Hi! I'm your DeepMind assistant. How can I help you?",
                        "model": {
                            "provider": "google",
                            "model": "gemini-2.0-flash",
                        },
                        "voice": {
                            "provider": "11labs",
                            "voiceId": "21m00Tcm4TlvDq8ikWAM",
                        },
                    }
                },
            )
            response.raise_for_status()
            return response.json()


vapi_service = VapiService()
