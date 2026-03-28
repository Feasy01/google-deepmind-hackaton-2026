#!/usr/bin/env python3
"""RAG Ingestion Pipeline

Connect to Qdrant, initialize Google embedder, create collections,
ingest articles and podcast transcripts.
"""

import os
import re
import uuid
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from google import genai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

# Configuration
QDRANT_URL = os.environ.get("QDRANT_URL", "http://192.168.10.191:6333")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 3072
ARTICLES_COLLECTION = "articles"
PODCASTS_COLLECTION = "podcast_episodes"

ASSETS_DIR = Path(__file__).parent / "assets"
ARTICLES_DIRS = [Path(__file__).parent.parent / "data" / "articles"]

# Clients
qdrant = QdrantClient(url=QDRANT_URL)
genai_client = genai.Client(api_key=GOOGLE_API_KEY)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Handles batching for large lists."""
    all_embeddings = []
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = genai_client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=batch,
        )
        all_embeddings.extend([e.values for e in response.embeddings])
    return all_embeddings


# --- Transcript Parser ---

@dataclass
class TranscriptSegment:
    timestamp: str
    seconds: int
    text: str


class TranscriptParser(ABC):
    @abstractmethod
    def parse(self, content: str) -> list[TranscriptSegment]:
        ...


class TimestampNewlineParser(TranscriptParser):
    TIMESTAMP_RE = re.compile(r"^(\d{1,2}:\d{2}(?::\d{2})?)$")

    @staticmethod
    def _ts_to_seconds(ts: str) -> int:
        parts = list(map(int, ts.split(":")))
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        return parts[0] * 3600 + parts[1] * 60 + parts[2]

    def parse(self, content: str) -> list[TranscriptSegment]:
        lines = [l.rstrip() for l in content.splitlines()]
        segments = []
        i = 0
        while i < len(lines):
            match = self.TIMESTAMP_RE.match(lines[i].strip())
            if match:
                ts = match.group(1)
                text_parts = []
                i += 1
                while i < len(lines):
                    if self.TIMESTAMP_RE.match(lines[i].strip()):
                        break
                    if lines[i].strip():
                        text_parts.append(lines[i].strip())
                    i += 1
                text = " ".join(text_parts)
                if text:
                    segments.append(
                        TranscriptSegment(
                            timestamp=ts,
                            seconds=self._ts_to_seconds(ts),
                            text=text,
                        )
                    )
            else:
                i += 1
        return segments


def build_sliding_windows(
    segments: list[TranscriptSegment],
    window_seconds: int = 30,
    overlap_seconds: int = 10,
) -> list[dict]:
    if not segments:
        return []

    windows = []
    start_idx = 0

    while start_idx < len(segments):
        window_start = segments[start_idx].seconds
        window_end = window_start + window_seconds

        window_segments = []
        for seg in segments[start_idx:]:
            if seg.seconds < window_end:
                window_segments.append(seg)
            else:
                break

        if not window_segments:
            start_idx += 1
            continue

        window_text = " ".join(seg.text for seg in window_segments)

        windows.append(
            {
                "timestamp_start": window_segments[0].timestamp,
                "timestamp_end": window_segments[-1].timestamp,
                "segment_texts": [seg.text for seg in window_segments],
                "window_text": window_text,
            }
        )

        advance_to = window_start + window_seconds - overlap_seconds
        new_start = start_idx
        for i, seg in enumerate(segments[start_idx:], start=start_idx):
            if seg.seconds >= advance_to:
                new_start = i
                break
        else:
            break

        if new_start == start_idx:
            start_idx += 1
        else:
            start_idx = new_start

    return windows


parser = TimestampNewlineParser()


# --- Article chunking ---

def chunk_article(text: str, max_tokens: int = 500, min_tokens: int = 100) -> list[str]:
    raw_chunks = re.split(r"\n\s*\n|(?=^#{1,3}\s)", text.strip(), flags=re.MULTILINE)
    raw_chunks = [c.strip() for c in raw_chunks if c.strip()]

    merged: list[str] = []
    buffer = ""

    for chunk in raw_chunks:
        word_count = len(chunk.split())

        if word_count > max_tokens:
            if buffer:
                merged.append(buffer.strip())
                buffer = ""
            sentences = re.split(r"(?<=[.!?])\s+", chunk)
            sub_buffer = ""
            for sentence in sentences:
                if len((sub_buffer + " " + sentence).split()) > max_tokens and sub_buffer:
                    merged.append(sub_buffer.strip())
                    sub_buffer = sentence
                else:
                    sub_buffer = (sub_buffer + " " + sentence).strip()
            if sub_buffer:
                merged.append(sub_buffer.strip())
        elif buffer and len((buffer + "\n\n" + chunk).split()) > max_tokens:
            merged.append(buffer.strip())
            buffer = chunk
        else:
            buffer = (buffer + "\n\n" + chunk).strip() if buffer else chunk

    if buffer:
        merged.append(buffer.strip())

    final: list[str] = []
    for chunk in merged:
        if final and len(chunk.split()) < min_tokens:
            final[-1] = final[-1] + "\n\n" + chunk
        else:
            final.append(chunk)

    return final


def parse_episode_filename(stem: str) -> dict:
    dash_idx = stem.find("-")
    if dash_idx == -1:
        return {"episode_id": stem, "name": stem}
    name = stem[dash_idx + 1:].replace("-", " ").title()
    return {"episode_id": stem, "name": name}


# --- Main ---

def main():
    # Create or recreate collections
    for name in [ARTICLES_COLLECTION, PODCASTS_COLLECTION]:
        existing = [c.name for c in qdrant.get_collections().collections]
        if name in existing:
            qdrant.delete_collection(name)
            print(f"Deleted existing collection: {name}")
        qdrant.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        print(f"Created collection: {name}")

    # --- Ingest articles ---
    article_files = []
    for articles_dir in ARTICLES_DIRS:
        if articles_dir.exists():
            found = list(articles_dir.glob("*.md")) + list(articles_dir.glob("*.txt"))
            print(f"Found {len(found)} article(s) in {articles_dir}")
            article_files.extend(found)
        else:
            print(f"Skipping {articles_dir} (not found)")
    print(f"Total: {len(article_files)} article(s)")

    all_article_points: list[PointStruct] = []

    for filepath in article_files:
        title = filepath.stem.replace("-", " ").replace("_", " ").title()
        content = filepath.read_text()
        chunks = chunk_article(content)
        print(f"  {title}: {len(chunks)} chunk(s)")

        embeddings = embed_texts(chunks)

        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            all_article_points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "article_title": title,
                        "article_url": None,
                        "chunk_text": chunk_text,
                        "chunk_index": i,
                    },
                )
            )

    if all_article_points:
        qdrant.upsert(collection_name=ARTICLES_COLLECTION, points=all_article_points, wait=True)
        print(f"\nUpserted {len(all_article_points)} article point(s)")
    else:
        print("\nNo articles to ingest")

    # --- Ingest podcasts ---
    podcaster_dirs = [
        d for d in sorted(ASSETS_DIR.iterdir())
        if d.is_dir() and d.name != "articles"
    ]
    print(f"Found {len(podcaster_dirs)} podcaster(s): {[d.name for d in podcaster_dirs]}")

    all_podcast_points: list[PointStruct] = []

    for podcaster_dir in podcaster_dirs:
        podcaster_name = podcaster_dir.name
        transcript_files = sorted([
            f for f in podcaster_dir.glob("*.txt")
            if f.name != "podcast.txt"
        ])
        print(f"\n  {podcaster_name}: {len(transcript_files)} transcript(s)")

        for filepath in transcript_files:
            ep = parse_episode_filename(filepath.stem)
            episode_id = ep["episode_id"]
            episode_title = ep["name"]
            content = filepath.read_text()

            segments = parser.parse(content)
            windows = build_sliding_windows(segments)
            print(f"    {episode_title}: {len(segments)} segment(s) -> {len(windows)} window(s)")

            window_texts = [w["window_text"] for w in windows]
            if not window_texts:
                continue

            embeddings = embed_texts(window_texts)

            for window, embedding in zip(windows, embeddings):
                all_podcast_points.append(
                    PointStruct(
                        id=str(uuid.uuid4()),
                        vector=embedding,
                        payload={
                            "episode_title": episode_title,
                            "episode_id": episode_id,
                            "podcaster": podcaster_name,
                            "timestamp_start": window["timestamp_start"],
                            "timestamp_end": window["timestamp_end"],
                            "segment_texts": window["segment_texts"],
                            "window_text": window["window_text"],
                        },
                    )
                )

    if all_podcast_points:
        qdrant.upsert(collection_name=PODCASTS_COLLECTION, points=all_podcast_points, wait=True)
        print(f"\nUpserted {len(all_podcast_points)} podcast point(s)")
    else:
        print("\nNo podcasts to ingest")

    # --- Verification ---
    for name in [ARTICLES_COLLECTION, PODCASTS_COLLECTION]:
        info = qdrant.get_collection(name)
        print(f"{name}: {info.points_count} points")

    print("\n--- Article search: 'lymphatic drainage techniques' ---")
    test_query = embed_texts(["lymphatic drainage techniques"])[0]
    results = qdrant.query_points(
        collection_name=ARTICLES_COLLECTION,
        query=test_query,
        limit=3,
        with_payload=True,
    )
    for point in results.points:
        print(f"  [{point.score:.3f}] {point.payload['article_title']}: {point.payload['chunk_text'][:100]}...")

    print("\n--- Podcast search: 'lymphatic system health' ---")
    test_query = embed_texts(["lymphatic system health"])[0]
    results = qdrant.query_points(
        collection_name=PODCASTS_COLLECTION,
        query=test_query,
        limit=3,
        with_payload=True,
    )
    for point in results.points:
        print(f"  [{point.score:.3f}] {point.payload['episode_title']} [{point.payload['podcaster']}] ({point.payload['timestamp_start']}): {point.payload['window_text'][:100]}...")


if __name__ == "__main__":
    main()
