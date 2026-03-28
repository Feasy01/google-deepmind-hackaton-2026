import httpx

from app.core.config import settings
from app.services.deepmind import deepmind_service

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

    async def handle_function_call(self, payload: dict) -> dict:
        """Process function calls from Vapi."""
        function_call = payload.get("message", {}).get("functionCall", {})
        name = function_call.get("name")
        parameters = function_call.get("parameters", {})

        if name == "ask_deepmind":
            question = parameters.get("question", "")
            answer = await deepmind_service.generate_response(message=question)
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
