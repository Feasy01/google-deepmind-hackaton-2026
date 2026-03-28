from google import genai

from app.core.config import settings
from app.models.chat import ChatMessage


class DeepMindService:
    def __init__(self):
        self._client: genai.Client | None = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        return self._client

    async def generate_response(
        self,
        message: str,
        conversation_history: list[ChatMessage] | None = None,
    ) -> str:
        contents = []
        for msg in conversation_history or []:
            contents.append(
                genai.types.Content(
                    role="user" if msg.role == "user" else "model",
                    parts=[genai.types.Part(text=msg.content)],
                )
            )
        contents.append(
            genai.types.Content(
                role="user",
                parts=[genai.types.Part(text=message)],
            )
        )

        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
        )
        return response.text


deepmind_service = DeepMindService()
