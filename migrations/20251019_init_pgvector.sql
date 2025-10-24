CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS memory_embeddings (
  id BIGSERIAL PRIMARY KEY,
  session_id TEXT,
  user_id TEXT,
  content TEXT NOT NULL,
  embedding VECTOR(3072) NOT NULL,
  source_type TEXT DEFAULT 'transcript',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS memory_embeddings_embedding_idx
  ON memory_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);