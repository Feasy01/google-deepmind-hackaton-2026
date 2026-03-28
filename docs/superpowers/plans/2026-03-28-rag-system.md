# RAG System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Qdrant-based RAG to the VAPI voice agent with two tools — article knowledge search and podcast episode search.

**Architecture:** Qdrant vector DB stores two collections (articles, podcast_episodes) with 768-dim embeddings from Google `text-embedding-004`. A `RagService` in the backend handles embedding queries and searching Qdrant. VAPI webhook routes two new function calls (`search_knowledge`, `search_previous_episodes`) to this service. A Jupyter notebook handles data ingestion.

**Tech Stack:** Python 3.12, FastAPI, Qdrant (Docker), google-genai (text-embedding-004), qdrant-client, Jupyter

---

## File Structure

| File | Responsibility |
|------|----------------|
| `db/docker-compose.yml` | Qdrant + Postgres services |
| `backend/pyproject.toml` | Dependencies |
| `backend/.env.example` | Environment variable template |
| `backend/app/core/config.py` | App settings including QDRANT_URL |
| `backend/app/services/rag.py` | RAG service — embed queries, search Qdrant |
| `backend/app/services/vapi.py` | VAPI assistant config with tool definitions |
| `backend/app/api/endpoints/vapi_webhook.py` | Webhook handler routing function calls |
| `notebooks/rag_ingestion.ipynb` | Data ingestion notebook |
| `data/articles/.gitkeep` | Article source files directory |
| `data/podcasts/.gitkeep` | Podcast transcript files directory |

---

### Task 1: Infrastructure — Qdrant Docker + Dependencies

**Files:**
- Modify: `db/docker-compose.yml`
- Modify: `backend/pyproject.toml`
- Modify: `backend/.env.example`
- Modify: `backend/app/core/config.py`

- [ ] **Step 1: Add Qdrant service to docker-compose**

In `db/docker-compose.yml`, add the qdrant service after the existing `db` service:

```yaml
  qdrant:
    image: qdrant/qdrant:latest
    container_name: hackathon_qdrant
    ports:
      - "0.0.0.0:6333:6333"
      - "0.0.0.0:6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

volumes:
  qdrant_data:
```

- [ ] **Step 2: Add qdrant-client to pyproject.toml**

Add `"qdrant-client>=1.12.0"` to the `dependencies` list in `backend/pyproject.toml`.

- [ ] **Step 3: Add QDRANT_URL to config**

In `backend/app/core/config.py`, add to the `Settings` class:

```python
QDRANT_URL: str = "http://192.168.10.191:6333"
```

- [ ] **Step 4: Update .env.example**

Add to `backend/.env.example`:

```
QDRANT_URL=http://192.168.10.191:6333
```

- [ ] **Step 5: Install dependencies**

Run: `cd /home/szymon/google-deepmind-hackaton-2026/backend && uv sync`

- [ ] **Step 6: Start Qdrant**

Run: `cd /home/szymon/google-deepmind-hackaton-2026/db && docker compose up -d qdrant`

Verify: `curl http://192.168.10.191:6333/healthz` should return `ok` or similar.

- [ ] **Step 7: Commit**

```bash
git add db/docker-compose.yml backend/pyproject.toml backend/.env.example backend/app/core/config.py backend/uv.lock
git commit -m "feat: add Qdrant infrastructure and qdrant-client dependency"
```

---

### Task 2: RAG Service — Embedding + Search

**Files:**
- Create: `backend/app/services/rag.py`

- [ ] **Step 1: Create the RAG service**

Create `backend/app/services/rag.py`:

```python
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
```

- [ ] **Step 2: Verify import works**

Run: `cd /home/szymon/google-deepmind-hackaton-2026/backend && uv run python -c "from app.services.rag import rag_service; print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/rag.py
git commit -m "feat: add RAG service with Qdrant search and Google embeddings"
```

---

### Task 3: VAPI Integration — Tool Definitions + Webhook Routing

**Files:**
- Modify: `backend/app/services/vapi.py`
- Modify: `backend/app/api/endpoints/vapi_webhook.py`

- [ ] **Step 1: Add tool definitions to VAPI assistant config**

In `backend/app/services/vapi.py`, update `get_assistant_config()` to include tools in the assistant dict. Add after the `"transcriber"` block:

```python
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
```

- [ ] **Step 2: Update webhook handler to route RAG function calls**

Replace the contents of `backend/app/api/endpoints/vapi_webhook.py` with:

```python
from fastapi import APIRouter, Request

from app.services.rag import rag_service
from app.services.vapi import vapi_service

router = APIRouter()


def _format_article_results(results: list[dict]) -> str:
    """Format article search results for the voice agent."""
    if not results:
        return "No relevant articles found."
    parts = []
    for r in results:
        source = f" (source: {r['article_title']})"
        parts.append(f"{r['chunk_text']}{source}")
    return "\n\n".join(parts)


def _format_podcast_results(results: list[dict]) -> str:
    """Format podcast search results for the voice agent."""
    if not results:
        return "No relevant podcast episodes found."
    parts = []
    for r in results:
        header = f"From episode '{r['episode_title']}' at {r['timestamp_start']}–{r['timestamp_end']}:"
        parts.append(f"{header}\n{r['window_text']}")
    return "\n\n".join(parts)


@router.post("/webhook")
async def vapi_webhook(request: Request):
    """Handle incoming Vapi webhook events (assistant-request, function-call, etc.)."""
    payload = await request.json()
    message_type = payload.get("message", {}).get("type")

    if message_type == "assistant-request":
        return vapi_service.get_assistant_config()

    if message_type == "function-call":
        function_call = payload.get("message", {}).get("functionCall", {})
        name = function_call.get("name")
        parameters = function_call.get("parameters", {})

        if name == "search_knowledge":
            query = parameters.get("query", "")
            context = parameters.get("conversation_context", "")
            results = rag_service.search_articles(query=query, context=context)
            return {"result": _format_article_results(results)}

        if name == "search_previous_episodes":
            query = parameters.get("query", "")
            context = parameters.get("conversation_context", "")
            results = rag_service.search_podcasts(query=query, context=context)
            return {"result": _format_podcast_results(results)}

        return {"result": f"Unknown function: {name}"}

    return {"ok": True}
```

- [ ] **Step 3: Remove the old ask_deepmind handler from vapi.py**

Remove the `handle_function_call` method from `VapiService` in `backend/app/services/vapi.py` since function call routing is now handled entirely in the webhook endpoint. Also remove the `from app.services.deepmind import deepmind_service` import if it's no longer used elsewhere in the file.

- [ ] **Step 4: Verify the app starts**

Run: `cd /home/szymon/google-deepmind-hackaton-2026/backend && uv run python -c "from app.api.endpoints.vapi_webhook import router; print('OK')"`

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/vapi.py backend/app/api/endpoints/vapi_webhook.py
git commit -m "feat: add search_knowledge and search_previous_episodes VAPI tools"
```

---

### Task 4: Data Directories + Sample Data

**Files:**
- Create: `data/articles/.gitkeep`
- Create: `data/podcasts/.gitkeep`

- [ ] **Step 1: Create data directories**

```bash
mkdir -p /home/szymon/google-deepmind-hackaton-2026/data/articles
mkdir -p /home/szymon/google-deepmind-hackaton-2026/data/podcasts
touch /home/szymon/google-deepmind-hackaton-2026/data/articles/.gitkeep
touch /home/szymon/google-deepmind-hackaton-2026/data/podcasts/.gitkeep
```

- [ ] **Step 2: Create a sample article for testing**

Create `data/articles/what-is-reinforcement-learning.md`:

```markdown
# What is Reinforcement Learning

Reinforcement learning (RL) is a type of machine learning where an agent learns to make decisions by interacting with an environment. The agent receives rewards or penalties based on its actions and learns to maximize cumulative reward over time.

Unlike supervised learning, where the model learns from labeled examples, RL agents learn from experience through trial and error. The agent observes the current state of the environment, takes an action, and receives feedback in the form of a reward signal.

Key concepts in reinforcement learning include the policy (the agent's strategy for choosing actions), the value function (estimating how good a state or action is), and the reward signal (immediate feedback from the environment).

Common RL algorithms include Q-learning, SARSA, and policy gradient methods. Deep reinforcement learning combines neural networks with RL, enabling agents to handle complex, high-dimensional state spaces. Notable successes include AlphaGo, which defeated world champions in the game of Go, and robotics applications where agents learn to walk, grasp objects, and navigate environments.
```

- [ ] **Step 3: Create a sample podcast transcript for testing**

Create `data/podcasts/episode-01-intro-to-ai.txt`:

```
[00:00:00] Host: Welcome to the AI Deep Dive podcast. Today we're going to talk about the fundamentals of artificial intelligence.
[00:00:12] Host: Let's start with the basics. What exactly is artificial intelligence?
[00:00:18] Guest: Great question. AI is essentially the simulation of human intelligence by machines. It encompasses everything from simple rule-based systems to complex neural networks.
[00:00:35] Guest: The field has evolved dramatically over the past decade, largely driven by advances in deep learning and the availability of large datasets.
[00:00:48] Host: Can you explain what deep learning is for our listeners who might be new to this?
[00:00:55] Guest: Sure. Deep learning is a subset of machine learning that uses artificial neural networks with multiple layers. These layers allow the model to learn increasingly abstract representations of the data.
[00:01:12] Guest: For example, in image recognition, the first layers might detect edges, the next layers detect shapes, and the final layers recognize objects.
[00:01:25] Host: That's fascinating. And how does this relate to large language models like the ones powering chatbots today?
[00:01:33] Guest: Large language models are a specific application of deep learning. They use transformer architectures trained on massive amounts of text data to understand and generate human language.
[00:01:50] Host: We'll dive deeper into transformers in our next episode. For now, let's talk about the ethical considerations of AI.
[00:02:00] Guest: Ethics in AI is crucial. We need to consider bias in training data, transparency in decision-making, and the societal impact of automation.
```

- [ ] **Step 4: Commit**

```bash
git add data/
git commit -m "feat: add data directories with sample article and podcast transcript"
```

---

### Task 5: Ingestion Jupyter Notebook

**Files:**
- Create: `notebooks/rag_ingestion.ipynb`

- [ ] **Step 1: Create the notebook directory**

```bash
mkdir -p /home/szymon/google-deepmind-hackaton-2026/notebooks
```

- [ ] **Step 2: Create the ingestion notebook**

Create `notebooks/rag_ingestion.ipynb` with the following cells:

**Cell 1 — Setup (markdown):**
```markdown
# RAG Ingestion Pipeline
Connect to Qdrant, initialize Google embedder, create collections.
```

**Cell 2 — Setup (code):**
```python
import os
import re
import uuid
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass

from google import genai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

# Configuration
QDRANT_URL = os.environ.get("QDRANT_URL", "http://192.168.10.191:6333")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIM = 768
ARTICLES_COLLECTION = "articles"
PODCASTS_COLLECTION = "podcast_episodes"

DATA_DIR = Path("../data")
ARTICLES_DIR = DATA_DIR / "articles"
PODCASTS_DIR = DATA_DIR / "podcasts"

# Clients
qdrant = QdrantClient(url=QDRANT_URL)
genai_client = genai.Client(api_key=GOOGLE_API_KEY)

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


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Handles batching for large lists."""
    all_embeddings = []
    batch_size = 100  # Google API limit per request
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = genai_client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=batch,
        )
        all_embeddings.extend([e.values for e in response.embeddings])
    return all_embeddings
```

**Cell 3 — Transcript Parser (markdown):**
```markdown
## Transcript Parser
Pluggable parser for podcast transcripts. Default implementation handles `[HH:MM:SS] Speaker: text` format.
```

**Cell 4 — Transcript Parser (code):**
```python
@dataclass
class TranscriptSegment:
    """A single parsed segment from a transcript."""
    timestamp: str  # "HH:MM:SS"
    seconds: int  # timestamp in total seconds
    speaker: str
    text: str


class TranscriptParser(ABC):
    """Base class for transcript parsers. Subclass to support different formats."""

    @abstractmethod
    def parse(self, content: str) -> list[TranscriptSegment]:
        ...


class TimestampSpeakerParser(TranscriptParser):
    """Parses transcripts in [HH:MM:SS] Speaker: text format."""

    PATTERN = re.compile(r"\[(\d{2}:\d{2}:\d{2})\]\s*([^:]+):\s*(.*)")

    def parse(self, content: str) -> list[TranscriptSegment]:
        segments = []
        for line in content.strip().splitlines():
            match = self.PATTERN.match(line.strip())
            if not match:
                continue
            timestamp, speaker, text = match.groups()
            h, m, s = map(int, timestamp.split(":"))
            segments.append(
                TranscriptSegment(
                    timestamp=timestamp,
                    seconds=h * 3600 + m * 60 + s,
                    speaker=speaker.strip(),
                    text=text.strip(),
                )
            )
        return segments


def build_sliding_windows(
    segments: list[TranscriptSegment],
    window_seconds: int = 30,
    overlap_seconds: int = 10,
) -> list[dict]:
    """Build sliding windows from parsed transcript segments."""
    if not segments:
        return []

    windows = []
    start_idx = 0

    while start_idx < len(segments):
        window_start = segments[start_idx].seconds
        window_end = window_start + window_seconds

        # Collect segments within this window
        window_segments = []
        for seg in segments[start_idx:]:
            if seg.seconds < window_end:
                window_segments.append(seg)
            else:
                break

        if not window_segments:
            start_idx += 1
            continue

        window_text = " ".join(
            f"{seg.speaker}: {seg.text}" for seg in window_segments
        )

        windows.append(
            {
                "timestamp_start": window_segments[0].timestamp,
                "timestamp_end": window_segments[-1].timestamp,
                "segment_texts": [seg.text for seg in window_segments],
                "window_text": window_text,
            }
        )

        # Advance by (window - overlap)
        advance_to = window_start + window_seconds - overlap_seconds
        new_start = start_idx
        for i, seg in enumerate(segments[start_idx:], start=start_idx):
            if seg.seconds >= advance_to:
                new_start = i
                break
        else:
            break  # No more segments to process

        if new_start == start_idx:
            start_idx += 1  # Ensure progress
        else:
            start_idx = new_start

    return windows


# Default parser
parser = TimestampSpeakerParser()
```

**Cell 5 — Article Ingestion (markdown):**
```markdown
## Article Ingestion
Load articles from `data/articles/`, chunk semantically, embed, and upsert.
```

**Cell 6 — Article Ingestion (code):**
```python
def chunk_article(text: str, max_tokens: int = 500, min_tokens: int = 100) -> list[str]:
    """Split article text into semantic chunks by paragraphs, with size limits.

    Approximates tokens as words (rough but sufficient for chunking).
    """
    # Split on double newlines or markdown headings
    raw_chunks = re.split(r"\n\s*\n|(?=^#{1,3}\s)", text.strip(), flags=re.MULTILINE)
    raw_chunks = [c.strip() for c in raw_chunks if c.strip()]

    merged: list[str] = []
    buffer = ""

    for chunk in raw_chunks:
        word_count = len(chunk.split())

        if word_count > max_tokens:
            # Flush buffer first
            if buffer:
                merged.append(buffer.strip())
                buffer = ""
            # Split large chunk at sentence boundaries
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

    # Merge small trailing chunks
    final: list[str] = []
    for chunk in merged:
        if final and len(chunk.split()) < min_tokens:
            final[-1] = final[-1] + "\n\n" + chunk
        else:
            final.append(chunk)

    return final


# Ingest articles
article_files = list(ARTICLES_DIR.glob("*.md")) + list(ARTICLES_DIR.glob("*.txt"))
print(f"Found {len(article_files)} article(s)")

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
```

**Cell 7 — Podcast Ingestion (markdown):**
```markdown
## Podcast Ingestion
Load transcripts from `data/podcasts/`, parse, build sliding windows, embed, and upsert.
```

**Cell 8 — Podcast Ingestion (code):**
```python
podcast_files = list(PODCASTS_DIR.glob("*.txt"))
print(f"Found {len(podcast_files)} podcast transcript(s)")

all_podcast_points: list[PointStruct] = []

for filepath in podcast_files:
    episode_title = filepath.stem.replace("-", " ").replace("_", " ").title()
    episode_id = filepath.stem
    content = filepath.read_text()

    segments = parser.parse(content)
    windows = build_sliding_windows(segments)
    print(f"  {episode_title}: {len(segments)} segment(s) -> {len(windows)} window(s)")

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
```

**Cell 9 — Verification (markdown):**
```markdown
## Verification
Check collection counts and run test queries.
```

**Cell 10 — Verification (code):**
```python
# Collection stats
for name in [ARTICLES_COLLECTION, PODCASTS_COLLECTION]:
    info = qdrant.get_collection(name)
    print(f"{name}: {info.points_count} points")

# Test article search
print("\n--- Article search: 'What is reinforcement learning?' ---")
test_query = embed_texts(["What is reinforcement learning?"])[0]
results = qdrant.query_points(
    collection_name=ARTICLES_COLLECTION,
    query=test_query,
    limit=3,
    with_payload=True,
)
for point in results.points:
    print(f"  [{point.score:.3f}] {point.payload['article_title']}: {point.payload['chunk_text'][:100]}...")

# Test podcast search
print("\n--- Podcast search: 'What is deep learning?' ---")
test_query = embed_texts(["What is deep learning?"])[0]
results = qdrant.query_points(
    collection_name=PODCASTS_COLLECTION,
    query=test_query,
    limit=3,
    with_payload=True,
)
for point in results.points:
    print(f"  [{point.score:.3f}] {point.payload['episode_title']} ({point.payload['timestamp_start']}): {point.payload['window_text'][:100]}...")
```

- [ ] **Step 3: Commit**

```bash
git add notebooks/
git commit -m "feat: add RAG ingestion Jupyter notebook"
```

---

### Task 6: End-to-End Verification

- [ ] **Step 1: Ensure Qdrant is running**

Run: `curl http://192.168.10.191:6333/healthz`

Expected: healthy response

- [ ] **Step 2: Run the ingestion notebook**

Run: `cd /home/szymon/google-deepmind-hackaton-2026/notebooks && uv run --directory ../backend jupyter execute rag_ingestion.ipynb`

Or open it in Jupyter and run all cells. Verify output shows:
- Collections created
- Articles chunked and upserted
- Podcast windows created and upserted
- Test queries return relevant results

- [ ] **Step 3: Verify the FastAPI app starts with RAG service**

Run: `cd /home/szymon/google-deepmind-hackaton-2026/backend && uv run python -c "from app.services.rag import rag_service; rag_service.ensure_collections(); print('Collections OK')"`

Expected: `Collections OK`

- [ ] **Step 4: Test search via RAG service directly**

Run:
```bash
cd /home/szymon/google-deepmind-hackaton-2026/backend && uv run python -c "
from app.services.rag import rag_service
results = rag_service.search_articles(query='reinforcement learning')
for r in results:
    print(f'[{r[\"score\"]:.3f}] {r[\"article_title\"]}: {r[\"chunk_text\"][:80]}...')
"
```

Expected: Results from the sample article with reasonable similarity scores.

- [ ] **Step 5: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: address issues found during end-to-end verification"
```
