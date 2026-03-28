"""Placeholder RAG client for podcast Q&A.

Another team implements the real retrieval-augmented generation pipeline.
This module provides the interface and returns placeholder responses.
"""


class RAGClient:
    """Retrieve and answer questions using podcast transcript context."""

    async def retrieve(
        self, query: str, podcast_id: str, timestamp_seconds: int = 0
    ) -> list[str]:
        """Retrieve relevant transcript chunks near the given timestamp.

        Args:
            query: The user's question.
            podcast_id: Identifier for the podcast episode.
            timestamp_seconds: Position in the podcast where the user paused.

        Returns:
            List of relevant transcript chunks.
        """
        # TODO: Implement real retrieval against vector DB
        return [
            f"[Placeholder chunk near {timestamp_seconds}s in podcast '{podcast_id}' "
            f"relevant to: {query}]"
        ]

    async def query_with_context(
        self, question: str, podcast_id: str, timestamp_seconds: int = 0
    ) -> str:
        """Answer a question using RAG context from the podcast transcript.

        Args:
            question: The user's question.
            podcast_id: Identifier for the podcast episode.
            timestamp_seconds: Position in the podcast where the user paused.

        Returns:
            Generated answer string.
        """
        chunks = await self.retrieve(question, podcast_id, timestamp_seconds)
        context = "\n".join(chunks)

        # TODO: Replace with real LLM call using retrieved context
        return (
            f"[Placeholder RAG answer] Based on the podcast context near "
            f"{timestamp_seconds}s: The answer to '{question}' would be generated "
            f"here using the following retrieved context:\n{context}"
        )


rag_client = RAGClient()
