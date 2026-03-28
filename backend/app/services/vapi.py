import httpx

from app.core.config import settings
from app.services.deepmind import deepmind_service
from app.services.rag import rag_client

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
                "endCallFunctionEnabled": True,
                "endCallMessage": "Goodbye! Have a great day.",
            }
        }

    def get_podcast_assistant_config(self, podcast_id: str) -> dict:
        """Return the assistant configuration for the podcast interactive mode."""
        webhook_url = settings.VAPI_WEBHOOK_URL.rstrip("/")
        return {
            "assistant": {
                "firstMessage": "I'm listening along with you. Feel free to ask me anything about the podcast!",
                "model": {
                    "provider": "google",
                    "model": "gemini-2.0-flash",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are an interactive podcast companion assistant. "
                                "The user is listening to a podcast and may ask questions about what they're hearing.\n\n"
                                "IMPORTANT RULES:\n"
                                "1. When the user asks ANY question or says something that sounds like a question "
                                "(e.g., 'hey andrew, what is HRV?', 'what did he mean by that?'), "
                                "IMMEDIATELY call the stop_player tool to pause the podcast, "
                                "then call ask_podcast with their question and the timestamp from the system message.\n"
                                "2. When the user says something like 'thank you', 'thanks', 'got it', 'resume', "
                                "'continue', 'play', or any dismissal phrase, call start_player to resume the podcast.\n"
                                "3. After getting the answer from ask_podcast, speak the answer naturally to the user.\n"
                                "4. Keep your answers concise and conversational.\n"
                                "5. The podcast_id for this session is: " + podcast_id
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
                                "name": "ask_podcast",
                                "description": "Ask a question about the podcast content. Uses RAG to find relevant context from the transcript near the current playback position.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "question": {
                                            "type": "string",
                                            "description": "The user's question about the podcast.",
                                        },
                                        "timestamp_seconds": {
                                            "type": "integer",
                                            "description": "The podcast playback position in seconds when the user asked the question. Get this from the system message injected after pausing.",
                                        },
                                    },
                                    "required": ["question", "timestamp_seconds"],
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
                    "voiceId": "21m00Tcm4TlvDq8ikWAM",  # Rachel
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

    async def handle_function_call(self, payload: dict) -> dict:
        """Process function calls from Vapi."""
        function_call = payload.get("message", {}).get("functionCall", {})
        name = function_call.get("name")
        parameters = function_call.get("parameters", {})

        if name == "ask_deepmind":
            question = parameters.get("question", "")
            answer = await deepmind_service.generate_response(message=question)
            return {"result": answer}

        if name == "ask_podcast":
            question = parameters.get("question", "")
            timestamp = parameters.get("timestamp_seconds", 0)
            # Extract podcast_id from call metadata
            call = payload.get("message", {}).get("call", {})
            podcast_id = (
                call.get("assistantOverrides", {})
                .get("metadata", {})
                .get("podcast_id", "unknown")
            )
            # Fall back to top-level metadata
            if podcast_id == "unknown":
                podcast_id = (
                    call.get("metadata", {}).get("podcast_id", "unknown")
                )
            answer = await rag_client.query_with_context(
                question=question,
                podcast_id=podcast_id,
                timestamp_seconds=timestamp,
            )
            return {"result": answer}

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
