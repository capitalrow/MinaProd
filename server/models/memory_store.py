import os
import time
import psycopg2
from psycopg2.extras import execute_values
from openai import OpenAI
from dotenv import load_dotenv
import numpy as np

load_dotenv()
client = OpenAI()
# -----------------------------
# MEMORY STORE (PRODUCTION-GRADE)
# -----------------------------

class MemoryStore:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        self.api_key = os.getenv("OPENAI_API_KEY")

        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)

        # Create DB connection
        self.conn = self._connect()

        # Define model fallback order (auto-resilient)
        self.embedding_models = [
            "text-embedding-3-large",  # 3072-dim, matches DB schema
            "text-embedding-3-small",  # Fallback
            "text-embedding-ada-002"   # Legacy fallback
        ]

    # -----------------------------
    # Internal helpers
    # -----------------------------

    def _connect(self):
        """Create a new DB connection."""
        try:
            conn = psycopg2.connect(self.db_url)
            conn.autocommit = True
            return conn
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise

    def _ensure_connection(self):
        """Reconnect if DB connection drops."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT 1;")
        except (Exception, psycopg2.InterfaceError):
            print("🔁 Reconnecting to database...")
            self.conn = self._connect()

    # -----------------------------------------
    # Embedding generation
    # -----------------------------------------
    def _generate_embedding(self, content: str):
        """Generate an embedding for the given content with fallback."""
        for model in self.embedding_models:
            try:
                print(f"🧠 Generating embedding using {model}...")
                response = self.client.embeddings.create(
                    model=model,
                    input=content,
                    encoding_format="float"
                )
                emb = np.array(response.data[0].embedding)
                print(f"✅ Success with {model} ({len(emb)} dims)")
                return emb
            except Exception as e:
                print(f"[ERROR] {model} failed: {e}")
                time.sleep(1)
                continue

        print("❌ All embedding models failed.")
        return None
    # -----------------------------
    # Public methods
    # -----------------------------

    def add_memory(self, session_id, user_id, content, source_type="transcript"):
        """Store a text snippet with embedding in DB."""
        try:
            self._ensure_connection()
            embedding = self._generate_embedding(content)

            with self.conn.cursor() as cur:
                # Convert NumPy array → Python list → Postgres vector string
                embedding_list = embedding.tolist()
                embedding_str = "[" + ",".join(map(str, embedding_list)) + "]"

                cur.execute("""
                    INSERT INTO memory_embeddings (session_id, user_id, content, embedding, source_type)
                    VALUES (%s, %s, %s, %s::vector, %s)
                """, (session_id, user_id, content, embedding_str, source_type))
            print(f"✅ Memory stored successfully for session {session_id}")
        except Exception as e:
            print(f"❌ ERROR in add_memory: {e}")
            raise

    def search_memory(self, query, top_k=5):
        """Semantic search by vector similarity."""
        try:
            self._ensure_connection()
            query_emb = self._generate_embedding(query)

            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, content, session_id, user_id, created_at,
                           1 - (embedding <-> %s) AS similarity
                    FROM memory_embeddings
                    ORDER BY embedding <-> %s
                    LIMIT %s;
                    """,
                    (query_emb, query_emb, top_k)
                )
                rows = cur.fetchall()

            results = [
                {
                    "id": r[0],
                    "content": r[1],
                    "session_id": r[2],
                    "user_id": r[3],
                    "created_at": r[4],
                    "similarity": float(r[5]),
                }
                for r in rows
            ]

            print(f"🔍 {len(results)} memories retrieved for query.")
            return results

        except Exception as e:
            print(f"❌ ERROR in search_memory: {e}")
            return []

    # -----------------------------------------
    # Retrieval / debug
    # -----------------------------------------
    def latest_memories(self, limit=5):
        """Fetch recent memory entries for debugging."""
        try:
            self._ensure_connection()
            cur = self.conn.cursor()
            cur.execute("""
                SELECT id, user_id, LEFT(content, 50), created_at
                FROM memory_embeddings
                ORDER BY id DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()
        except Exception as e:
            print(f"[DB READ ERROR] {e}")
            return []