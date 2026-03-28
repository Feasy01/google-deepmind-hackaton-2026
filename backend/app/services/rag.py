import logging
import time

from google import genai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

from app.core.config import settings

logger = logging.getLogger("rag")

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 3072
ARTICLES_COLLECTION = "articles"
PODCASTS_COLLECTION = "podcast_episodes"
SCORE_THRESHOLD = 0.35


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
        t0 = time.perf_counter()
        response = self.genai_client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=texts,
        )
        elapsed = (time.perf_counter() - t0) * 1000
        logger.info("embed_texts: %d text(s), %.0fms", len(texts), elapsed)
        return [e.values for e in response.embeddings]

    def embed_query(self, query: str, context: str = "") -> list[float]:
        """Embed a search query, optionally combined with conversation context."""
        text = f"{query} {context}".strip() if context else query
        logger.debug("embed_query: query=%r context_len=%d", query, len(context))
        return self.embed_texts([text])[0]

    @staticmethod
    def _timestamp_to_seconds(ts: str) -> int:
        """Convert 'HH:MM:SS' to total seconds."""
        parts = ts.split(":")
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return 0

    def get_transcript_context(self, episode_id: str, timestamp_seconds: int) -> str:
        """Get the transcript window closest to the given timestamp for an episode."""
        logger.debug("get_transcript_context: episode_id=%s ts=%ds", episode_id, timestamp_seconds)
        results, _ = self.qdrant.scroll(
            collection_name=PODCASTS_COLLECTION,
            scroll_filter=Filter(
                must=[FieldCondition(key="episode_id", match=MatchValue(value=episode_id))]
            ),
            limit=500,
            with_payload=True,
        )
        if not results:
            logger.warning("get_transcript_context: no windows found for episode_id=%s", episode_id)
            return ""

        # Find the window whose midpoint is closest to the requested timestamp
        best = min(
            results,
            key=lambda p: abs(
                (self._timestamp_to_seconds(p.payload.get("timestamp_start", "00:00:00"))
                 + self._timestamp_to_seconds(p.payload.get("timestamp_end", "00:00:00"))) / 2
                - timestamp_seconds
            ),
        )
        window_text = best.payload.get("window_text", "")
        logger.debug("get_transcript_context: matched window %s–%s (%d chars)",
                      best.payload.get("timestamp_start"), best.payload.get("timestamp_end"), len(window_text))
        return window_text

    def search_articles(
        self, query: str, context: str = "", top_k: int = 5, score_threshold: float = SCORE_THRESHOLD
    ) -> list[dict]:
        """Search the articles collection and return results with source attribution."""
        logger.info("search_articles: query=%r top_k=%d threshold=%.2f", query, top_k, score_threshold)
        vector = self.embed_query(query, context)
        t0 = time.perf_counter()
        results = self.qdrant.query_points(
            collection_name=ARTICLES_COLLECTION,
            query=vector,
            limit=top_k,
            with_payload=True,
            score_threshold=score_threshold,
        )
        elapsed = (time.perf_counter() - t0) * 1000
        hits = [
            {
                "article_title": point.payload.get("article_title", "Unknown"),
                "article_url": point.payload.get("article_url"),
                "chunk_text": point.payload.get("chunk_text", ""),
                "score": point.score,
            }
            for point in results.points
        ]
        scores = [h["score"] for h in hits]
        logger.info("search_articles: %d result(s) in %.0fms | scores=%s",
                     len(hits), elapsed, [round(s, 3) for s in scores])
        for h in hits:
            logger.debug("  -> [%.3f] %s: %.120s", h["score"], h["article_title"], h["chunk_text"])
        return hits

    def search_podcasts(
        self, query: str, context: str = "", top_k: int = 5, score_threshold: float = SCORE_THRESHOLD
    ) -> list[dict]:
        """Search the podcast episodes collection and return results with timestamps."""
        logger.info("search_podcasts: query=%r top_k=%d threshold=%.2f", query, top_k, score_threshold)
        vector = self.embed_query(query, context)
        t0 = time.perf_counter()
        results = self.qdrant.query_points(
            collection_name=PODCASTS_COLLECTION,
            query=vector,
            limit=top_k,
            with_payload=True,
            score_threshold=score_threshold,
        )
        elapsed = (time.perf_counter() - t0) * 1000
        hits = [
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
        scores = [h["score"] for h in hits]
        logger.info("search_podcasts: %d result(s) in %.0fms | scores=%s",
                     len(hits), elapsed, [round(s, 3) for s in scores])
        for h in hits:
            logger.debug("  -> [%.3f] %s %s–%s: %.120s",
                          h["score"], h["episode_title"], h["timestamp_start"], h["timestamp_end"], h["window_text"])
        return hits


rag_service = RagService()
