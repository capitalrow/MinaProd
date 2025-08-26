-- Critical Performance Indexes for Production Readiness
-- These indexes significantly improve query performance for common operations

-- Session indexes for filtering and sorting
CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON sessions(started_at);
CREATE INDEX IF NOT EXISTS idx_sessions_completed_at ON sessions(completed_at) WHERE completed_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_status_started ON sessions(status, started_at);

-- Segment indexes for temporal ordering and session queries
CREATE INDEX IF NOT EXISTS idx_segments_created_at ON segments(created_at);
CREATE INDEX IF NOT EXISTS idx_segments_session_created ON segments(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_segments_kind ON segments(kind);
CREATE INDEX IF NOT EXISTS idx_segments_session_kind ON segments(session_id, kind);

-- User authentication indexes (if users table exists)
-- CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
-- CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Composite indexes for complex queries
CREATE INDEX IF NOT EXISTS idx_sessions_active_recent ON sessions(status, started_at DESC) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_segments_final_recent ON segments(session_id, created_at DESC) WHERE kind = 'final';

-- Performance monitoring indexes
CREATE INDEX IF NOT EXISTS idx_sessions_duration ON sessions((EXTRACT(EPOCH FROM (COALESCE(completed_at, NOW()) - started_at))));

-- Full-text search indexes for transcripts (if needed)
-- CREATE INDEX IF NOT EXISTS idx_segments_text_search ON segments USING gin(to_tsvector('english', text));

ANALYZE sessions;
ANALYZE segments;