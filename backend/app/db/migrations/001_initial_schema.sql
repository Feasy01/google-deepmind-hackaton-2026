-- Enable pgvector extension for embedding storage
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable uuid generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- Source types: article, book, person
-- ============================================================

CREATE TYPE source_type AS ENUM ('article', 'book', 'person');

-- ============================================================
-- Sources: metadata about each ingested document / entity
-- ============================================================

CREATE TABLE sources (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type source_type NOT NULL,
    title       TEXT NOT NULL,                -- article title, book title, person name
    author      TEXT,                         -- author or NULL for person records
    url         TEXT,                         -- optional origin URL
    metadata    JSONB NOT NULL DEFAULT '{}',  -- flexible extra fields (isbn, birth_date, etc.)
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sources_type ON sources (source_type);

-- ============================================================
-- Chunks: text segments extracted from sources
-- ============================================================

CREATE TABLE chunks (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id   UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,                 -- ordering within the source
    content     TEXT NOT NULL,                 -- raw text of the chunk
    token_count INT,                          -- optional token count for budget tracking
    metadata    JSONB NOT NULL DEFAULT '{}',  -- page number, section heading, etc.
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chunks_source ON chunks (source_id);

-- ============================================================
-- Embeddings: vector representations of chunks
-- ============================================================

CREATE TABLE embeddings (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chunk_id    UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    model       TEXT NOT NULL,                -- e.g. 'text-embedding-004'
    embedding   vector(768) NOT NULL,         -- Gemini text-embedding-004 outputs 768-d
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_embeddings_chunk ON embeddings (chunk_id);

-- HNSW index for fast cosine-similarity search
CREATE INDEX idx_embeddings_vector ON embeddings
    USING hnsw (embedding vector_cosine_ops);
