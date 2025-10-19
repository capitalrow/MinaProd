CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS memory_embeddings (
    id SERIAL PRIMARY KEY,
    session_id TEXT,
    user_id TEXT,
    content TEXT,
    embedding VECTOR(1536),
    source_type TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memory_embeddings_embedding
ON memory_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);