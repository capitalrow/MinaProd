"""
services/memory_persistence.py
Persistent conversation memory layer for Mina
"""

import os
import datetime as dt
import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Any

DB_PATH = os.getenv("MINA_MEMORY_DB", "instance/mina_memory.db")

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

def init_db():
    """Initialises the persistence database."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id TEXT NOT NULL,
                user_id TEXT,
                summary TEXT,
                sentiment TEXT,
                impact_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    print("✅ Memory persistence DB initialised.")

def save_memory(meeting_id: str, user_id: str, summary: str,
                sentiment: str, impact_score: float) -> None:
    """Stores meeting memory."""
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO conversation_memory (meeting_id, user_id, summary, sentiment, impact_score)
            VALUES (?, ?, ?, ?, ?);
        """, (meeting_id, user_id, summary, sentiment, impact_score))

def get_memory(meeting_id: str) -> List[Dict[str, Any]]:
    """Retrieves all stored summaries for a meeting."""
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT user_id, summary, sentiment, impact_score, created_at
            FROM conversation_memory
            WHERE meeting_id = ?
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
    """Removes entries older than N days."""
    cutoff = (dt.datetime.utcnow() - dt.timedelta(days=days)).isoformat()
    with get_conn() as conn:
        conn.execute("DELETE FROM conversation_memory WHERE created_at < ?", (cutoff,))