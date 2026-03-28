import httpx

from app.core.config import settings

VAPI_BASE_URL = "https://api.vapi.ai"


class VapiService:
    """Bootstrap service for Vapi voice chatbot integration."""

    def get_assistant_config(self) -> dict:
        """Return the assistant configuration for Vapi assistant-request webhooks."""
        return {
            "assistant": {
                "firstMessage": "Hi! I'm your DeepMind assistant. How can I help you today?",
                "model": {
                    "provider": "custom-llm",
                    "url": "",  # Set to your deployed server URL + /api/vapi/chat
                    "model": "gemini-2.0-flash",
                },
                "voice": {
                    "provider": "11labs",
                    "voiceId": "21m00Tcm4TlvDq8ikWAM",  # Rachel
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
                            "url": "",  # Set to your deployed server URL + /api/vapi/webhook
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
                            "url": "",  # Set to your deployed server URL + /api/vapi/webhook
                        },
                    },
                ],
                "endCallFunctionEnabled": True,
                "endCallMessage": "Goodbye! Have a great day.",
            }
        }

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
