import os
from datetime import timedelta

class Config:
    # Core
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get("MINA_DB_URL", "sqlite:///data/mina.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Live only (no mocks)
    USE_TRANSCRIPTION_PIPELINE = os.environ.get("USE_TRANSCRIPTION_PIPELINE", "true").lower() == "true"
    ENABLE_MOCK = False  # hard off – real world only

    # Cookies & CSRF
    ACCESS_COOKIE_NAME = "mina_access"
    REFRESH_COOKIE_NAME = "mina_refresh"
    CSRF_COOKIE_NAME = "mina_csrf"
    COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"  # set true on HTTPS
    COOKIE_SAMESITE = os.environ.get("COOKIE_SAMESITE", "Lax")
    ACCESS_EXPIRES = timedelta(minutes=int(os.environ.get("ACCESS_EXPIRES_MIN", "20")))
    REFRESH_EXPIRES = timedelta(days=int(os.environ.get("REFRESH_EXPIRES_DAYS", "14")))

    # Sharing
    SHARE_TOKEN_BYTES = int(os.environ.get("SHARE_TOKEN_BYTES", "16"))

    # Limits
    MAX_JSON_BYTES = int(os.environ.get("MAX_JSON_BYTES", "1048576"))  # 1MB JSON
    MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "100"))        # 100MB audio/video

    # CORS (set your Replit origin in prod)
    CORS_ALLOW = os.environ.get("CORS_ALLOW", "*")

    # Security headers
    ENABLE_CSP_REPORT_ONLY = os.environ.get("CSP_REPORT_ONLY", "true").lower() == "true"

    # Mail
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"
    MAIL_FROM = os.environ.get("MAIL_FROM", "noreply@mina.app")
    PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:8080")  # set your public URL