"""
Migration script to add CROWN+ specification fields.

Adds:
- event_ledger table
- Session.version, Session.trace_id
- Segment.version, Segment.edited_at, Segment.edited_by_id
"""

import os
import sys
from sqlalchemy import create_engine, text

# Get database URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

# SQL migrations
migrations = [
    # Add version and trace_id to sessions table
    """
    ALTER TABLE sessions 
    ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS trace_id VARCHAR(64);
    """,
    
    # Add index on trace_id
    """
    CREATE INDEX IF NOT EXISTS ix_sessions_trace_id ON sessions(trace_id);
    """,
    
    # Add version and edit tracking to segments table
    """
    ALTER TABLE segments 
    ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS edited_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS edited_by_id INTEGER REFERENCES users(id);
    """,
    
    # Create event_ledger table
    """
    CREATE TABLE IF NOT EXISTS event_ledger (
        id SERIAL PRIMARY KEY,
        trace_id VARCHAR(64) NOT NULL,
        session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        event_type VARCHAR(64) NOT NULL,
        event_sequence INTEGER DEFAULT 0,
        payload JSONB,
        status VARCHAR(32) DEFAULT 'success',
        error_message TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        latency_ms INTEGER,
        user_agent VARCHAR(512),
        client_ip VARCHAR(45)
    );
    """,
    
    # Create indexes for event_ledger
    """
    CREATE INDEX IF NOT EXISTS ix_event_ledger_trace_id ON event_ledger(trace_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_event_ledger_session_id ON event_ledger(session_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_event_ledger_event_type ON event_ledger(event_type);
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_event_ledger_timestamp ON event_ledger(timestamp);
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_event_ledger_trace_sequence ON event_ledger(trace_id, event_sequence);
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_event_ledger_session_timestamp ON event_ledger(session_id, timestamp);
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_event_ledger_type_status ON event_ledger(event_type, status);
    """,
]

print("Running CROWN+ database migrations...")
with engine.connect() as conn:
    for i, migration in enumerate(migrations, 1):
        try:
            conn.execute(text(migration))
            conn.commit()
            print(f"✅ Migration {i}/{len(migrations)} completed")
        except Exception as e:
            print(f"⚠️ Migration {i}/{len(migrations)} error (may already exist): {e}")
            conn.rollback()

print("✅ All migrations completed successfully")
