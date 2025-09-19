import os
from datetime import timedelta

def _normalize_pg(uri: str) -> str:
    # SQLAlchemy accepts postgresql+psycopg2://; normalize if needed
    if uri and uri.startswith("postgresql://"):
        return uri.replace("postgresql://", "postgresql+psycopg2://", 1)
    return uri

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = ENV == "development"

    # Prefer DATABASE_URL from Replit Secrets; fall back to SQLALCHEMY_DATABASE_URI; else use local SQLite
    _env_uri = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_DATABASE_URI = _normalize_pg(_env_uri) if _env_uri else "sqlite:///mina.db"

    # Neon often requires SSL; keep query string as-is (you already have ?sslmode=require)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sessions / limits
    SESSION_TTL_MINUTES = int(os.getenv("SESSION_TTL_MINUTES", "60"))
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=SESSION_TTL_MINUTES)
    MAX_SESSION_SECONDS = int(os.getenv("MAX_SESSION_SECONDS", "1800"))
    MAX_CHUNKS_PER_MINUTE = int(os.getenv("MAX_CHUNKS_PER_MINUTE", "120"))

    # HTTP request safety
    MAX_JSON_BODY_BYTES = int(os.getenv("MAX_JSON_BODY_BYTES", "200000"))   # ~200 KB
    MAX_FORM_BODY_BYTES = int(os.getenv("MAX_FORM_BODY_BYTES", "20000000")) # ~20 MB for final upload
    RATE_LIMIT_PER_IP_MIN = int(os.getenv("RATE_LIMIT_PER_IP_MIN", "120"))

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")
    SUMMARY_MODEL = os.getenv("SUMMARY_MODEL", "gpt-4o-mini")
    AUTO_SUMMARY = os.getenv("AUTO_SUMMARY", "true").lower() == "true"
    LANGUAGE_HINT = os.getenv("LANGUAGE_HINT") or None  # None => auto-detect

    # Realtime
    INTERIM_INTERVAL_MS = int(os.getenv("INTERIM_INTERVAL_MS", "800"))
    MAX_CHUNK_BYTES = int(os.getenv("MAX_CHUNK_BYTES", "350000"))

    # Safety / Redaction
    REDACT_PII = os.getenv("REDACT_PII", "true").lower() == "true"

    # Circuit breaker (interims)
    CB_WINDOW_SEC = int(os.getenv("CB_WINDOW_SEC", "20"))
    CB_FAIL_THRESHOLD = int(os.getenv("CB_FAIL_THRESHOLD", "3"))
    CB_COOLDOWN_SEC = int(os.getenv("CB_COOLDOWN_SEC", "10"))

    # Metrics
    METRICS_DIR = os.getenv("METRICS_DIR", "./data")

    # Internal endpoints
    INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")  # empty => disabled

    # Logging
    JSON_LOGS = os.getenv("JSON_LOGS", "false").lower() == "true"

    # CORS
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []