# RAG System Design for VAPI Agent

## Overview

Add retrieval-augmented generation (RAG) to the existing VAPI voice agent. The agent gains two new tools: one for searching article knowledge and one for searching previous podcast episodes. Uses Qdrant as the vector store and Google's `text-embedding-004` (768 dimensions) for embeddings.

## Infrastructure

### Qdrant

- Added as a service in `db/docker-compose.yml` alongside existing Postgres
- Ports: `6333` (HTTP API), `6334` (gRPC)
- Persistent volume for data durability
- Config: `QDRANT_URL` added to `app/core/config.py` (default `http://192.168.10.191:6333`)

### Collections

Two separate Qdrant collections, both using 768-dimensional vectors with cosine similarity:

1. **`articles`** — educational article chunks
2. **`podcast_episodes`** — sliding-window podcast transcript chunks

### Dependencies

- `qdrant-client` added to `pyproject.toml`
- `google-genai` already present (used for embedding via `text-embedding-004`)

## Data Model

### Articles Collection

Each point payload:

| Field           | Type         | Description                              |
|-----------------|--------------|------------------------------------------|
| `article_title` | `str`        | Source attribution label                  |
| `article_url`   | `str | null` | Optional link back to source              |
| `chunk_text`    | `str`        | The text chunk content                    |
| `chunk_index`   | `int`        | Position within the article for ordering  |

### Podcast Episodes Collection

Each point payload:

| Field            | Type         | Description                                        |
|------------------|--------------|----------------------------------------------------|
| `episode_title`  | `str`        | Episode name                                       |
| `episode_id`     | `str`        | Unique episode identifier                          |
| `timestamp_start`| `str`        | Start time of the window, e.g., `"00:12:34"`       |
| `timestamp_end`  | `str`        | End time of the window                              |
| `segment_texts`  | `list[str]`  | Raw parsed segments composing this window           |
| `window_text`    | `str`        | Merged sliding window text (the embedded content)   |

## Chunking Strategies

### Articles

- Split by paragraphs/sections (double newline or heading boundaries)
- If a chunk exceeds ~500 tokens, split further at sentence boundaries
- If a chunk is too small (<100 tokens), merge with the next chunk
- No overlap needed since splits occur at semantic boundaries

### Podcast Transcripts

- Parse timestamped segments from transcripts (default format: `[HH:MM:SS] Speaker: text`)
- Parser is pluggable — base interface with swappable implementations for different formats
- Build ~30-second sliding windows with ~10-second overlap
- Each window stores start/end timestamps for replay linking

## Ingestion (Jupyter Notebook)

Located at `notebooks/rag_ingestion.ipynb` with self-contained cells:

1. **Setup** — Connect to Qdrant, initialize Google embedder, create/recreate collections
2. **Transcript parser** — Pluggable parser class; default parses `[HH:MM:SS] Speaker: text` format
3. **Article ingestion** — Load from `data/articles/` (one `.txt` or `.md` per article, title derived from filename), chunk, embed, upsert to `articles` collection
4. **Podcast ingestion** — Load from `data/podcasts/`, parse transcripts, build sliding windows, embed, upsert to `podcast_episodes` collection
5. **Verification** — Collection counts and test queries against each collection

## Backend RAG Service

### New file: `app/services/rag.py`

`RagService` class with:

- Qdrant client and Google embedder initialization
- `search_articles(query: str, top_k: int = 5) -> list[dict]` — embeds query, searches `articles` collection, returns chunks with `article_title` for source attribution
- `search_podcasts(query: str, top_k: int = 5) -> list[dict]` — embeds query, searches `podcast_episodes`, returns windows with replay timestamps

### VAPI Tool Definitions

Two new tools added to the assistant config in `app/services/vapi.py`:

#### `search_knowledge`

```json
{
    "type": "function",
    "function": {
        "name": "search_knowledge",
        "description": "Search articles for factual knowledge. Use when the caller asks a question about a topic.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query based on what the user is asking"
                },
                "conversation_context": {
                    "type": "string",
                    "description": "Last 30 seconds of conversation for additional context"
                }
            },
            "required": ["query"]
        }
    },
    "server": {"url": "<webhook_url>"}
}
```

#### `search_previous_episodes`

```json
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
                    "description": "The search query based on what the user is asking"
                },
                "conversation_context": {
                    "type": "string",
                    "description": "Last 30 seconds of conversation for additional context"
                }
            },
            "required": ["query"]
        }
    },
    "server": {"url": "<webhook_url>"}
}
```

### Webhook Handler

`app/api/endpoints/vapi_webhook.py` updated to route `search_knowledge` and `search_previous_episodes` function calls to the RAG service. Query and conversation_context are combined before embedding for richer retrieval.

Results are formatted with:
- **Articles:** chunk text + article title (for the agent to quote the source)
- **Podcasts:** window text + episode title + timestamps (for replay linking)

## File Changes Summary

### New Files

| File | Purpose |
|------|---------|
| `notebooks/rag_ingestion.ipynb` | Jupyter notebook for data ingestion |
| `app/services/rag.py` | RAG service (Qdrant + embeddings) |
| `data/articles/.gitkeep` | Directory for article source files |
| `data/podcasts/.gitkeep` | Directory for podcast transcript files |

### Modified Files

| File | Changes |
|------|---------|
| `db/docker-compose.yml` | Add Qdrant service |
| `app/core/config.py` | Add `QDRANT_URL` setting |
| `app/services/vapi.py` | Add tool definitions, handle new function calls |
| `app/api/endpoints/vapi_webhook.py` | Route new function calls to RAG service |
| `backend/pyproject.toml` | Add `qdrant-client` dependency |
| `.env.example` | Add `QDRANT_URL` |

### Unchanged

- Frontend
- Existing Postgres setup
- Existing `/api/vapi/chat` endpoint
