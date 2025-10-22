"""
services/memory_persistence.py
Persistent conversation memory layer for Mina (PostgreSQL version)
"""

import os
import datetime as dt
import psycopg2
from contextlib import contextmanager
from typing import List, Dict, Any

# Use the same Neon PostgreSQL connection as the main app
DATABASE_URL = os.getenv("DATABASE_URL")

@contextmanager
def get_conn():
    """Yields a PostgreSQL connection using the DATABASE_URL."""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()


def init_db():
    """Initialises the persistence table in PostgreSQL."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS conversation_memory (
                    id SERIAL PRIMARY KEY,
                    meeting_id TEXT NOT NULL,
                    user_id TEXT,
                    summary TEXT,
                    sentiment TEXT,
                    impact_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
    print("✅ Memory persistence table initialised in PostgreSQL.")


def save_memory(meeting_id: str, user_id: str, summary: str,
                sentiment: str, impact_score: float) -> None:
    """Stores meeting memory in PostgreSQL."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO conversation_memory (meeting_id, user_id, summary, sentiment, impact_score)
                VALUES (%s, %s, %s, %s, %s);
            """, (meeting_id, user_id, summary, sentiment, impact_score))


def get_memory(meeting_id: str) -> List[Dict[str, Any]]:
    """Retrieves all stored summaries for a meeting from PostgreSQL."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, summary, sentiment, impact_score, created_at
                FROM conversation_memory
                WHERE meeting_id = %s
                ORDER BY created_at DESC;
            """, (meeting_id,))
            rows = cur.fetchall()
    return [
        {
            "user_id": r[0],
            "summary": r[1],
            "sentiment": r[2],
            "impact_score": r[3],
            "created_at": r[4],
        } for r in rows
    ]


def clear_old(days: int = 90) -> None:
    """Removes entries older than N days in PostgreSQL."""
    cutoff = (dt.datetime.utcnow() - dt.timedelta(days=days))
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM conversation_memory WHERE created_at < %s;", (cutoff,))
