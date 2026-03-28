from google import genai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings

EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIM = 768
ARTICLES_COLLECTION = "articles"
PODCASTS_COLLECTION = "podcast_episodes"


class RagService:
    def __init__(self):
        self._qdrant: QdrantClient | None = None
        self._genai: genai.Client | None = None

    @property
    def qdrant(self) -> QdrantClient:
        if self._qdrant is None:
            self._qdrant = QdrantClient(url=settings.QDRANT_URL)
        return self._qdrant

    @property
    def genai_client(self) -> genai.Client:
        if self._genai is None:
            self._genai = genai.Client(api_key=settings.GOOGLE_API_KEY)
        return self._genai

    def ensure_collections(self) -> None:
        """Create collections if they don't exist."""
        existing = [c.name for c in self.qdrant.get_collections().collections]
        for name in [ARTICLES_COLLECTION, PODCASTS_COLLECTION]:
            if name not in existing:
                self.qdrant.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=EMBEDDING_DIM, distance=Distance.COSINE
                    ),
                )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts using Google text-embedding-004."""
        response = self.genai_client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=texts,
        )
        return [e.values for e in response.embeddings]

    def embed_query(self, query: str, context: str = "") -> list[float]:
        """Embed a search query, optionally combined with conversation context."""
        text = f"{query} {context}".strip() if context else query
        return self.embed_texts([text])[0]

    def search_articles(self, query: str, context: str = "", top_k: int = 5) -> list[dict]:
        """Search the articles collection and return results with source attribution."""
        vector = self.embed_query(query, context)
        results = self.qdrant.query_points(
            collection_name=ARTICLES_COLLECTION,
            query=vector,
            limit=top_k,
            with_payload=True,
        )
        return [
            {
                "article_title": point.payload.get("article_title", "Unknown"),
                "article_url": point.payload.get("article_url"),
                "chunk_text": point.payload.get("chunk_text", ""),
                "score": point.score,
            }
            for point in results.points
        ]

    def search_podcasts(self, query: str, context: str = "", top_k: int = 5) -> list[dict]:
        """Search the podcast episodes collection and return results with timestamps."""
        vector = self.embed_query(query, context)
        results = self.qdrant.query_points(
            collection_name=PODCASTS_COLLECTION,
            query=vector,
            limit=top_k,
            with_payload=True,
        )
        return [
            {
                "episode_title": point.payload.get("episode_title", "Unknown"),
                "episode_id": point.payload.get("episode_id", ""),
                "timestamp_start": point.payload.get("timestamp_start", ""),
                "timestamp_end": point.payload.get("timestamp_end", ""),
                "window_text": point.payload.get("window_text", ""),
                "score": point.score,
            }
            for point in results.points
        ]


rag_service = RagService()
