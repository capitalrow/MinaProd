# app.py (hardened)
import os
import json
import signal
import logging
import uuid
from typing import Optional
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, render_template, request, g, jsonify
from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

# ---------- Config (fallback if config.Config not present)
try:
    from config import Config  # type: ignore
except Exception:
    class Config:
        JSON_LOGS: bool = os.getenv("JSON_LOGS", "false").lower() == "true"
        METRICS_DIR: str = os.getenv("METRICS_DIR", "./metrics")
        SECRET_KEY: str = os.getenv("SESSION_SECRET", "")  # No fallback - must be set
        SOCKETIO_PATH: str = os.getenv("SOCKETIO_PATH", "/socket.io")
        CORS_ALLOWLIST: str = os.getenv("CORS_ALLOWLIST", "*")
        MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", str(32 * 1024 * 1024)))  # 32 MB

# ---------- Logging
class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "name": record.name,
            "msg": record.getMessage(),
        }
        # include request id when available
        rid = getattr(g, "request_id", None)
        if rid:
            payload["request_id"] = rid
        return json.dumps(payload, ensure_ascii=False)

def _configure_logging(json_logs: bool = False) -> None:
    root = logging.getLogger()
    root.handlers[:] = []  # reset
    handler = logging.StreamHandler()
    handler.setFormatter(
        _JsonFormatter() if json_logs
        else logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    root.addHandler(handler)
    root.setLevel(logging.INFO)

def _sentry_before_send(event, hint):
    """
    Filter function to sanitize events before sending to Sentry.
    
    This allows us to:
    - Filter out sensitive data
    - Ignore specific error types
    - Add custom context
    """
    # Don't send HTTP 404 errors (too noisy)
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        if isinstance(exc_value, Exception):
            # Filter out common non-critical exceptions
            exc_name = exc_value.__class__.__name__
            if exc_name in ['NotFound', 'Unauthorized', 'Forbidden']:
                return None
    
    # Sanitize sensitive data from request body
    if 'request' in event and 'data' in event['request']:
        sensitive_keys = ['password', 'token', 'api_key', 'secret', 'authorization']
        data = event['request']['data']
        if isinstance(data, dict):
            for key in sensitive_keys:
                if key in data:
                    data[key] = '[REDACTED]'
    
    return event

# ---------- Create the SocketIO singleton with eventlet for production WebSocket support
socketio = SocketIO(
    cors_allowed_origins="*",  # Allow all origins for development and dynamic Replit URLs
    async_mode="eventlet",  # Changed from threading to eventlet for proper WebSocket support
    ping_timeout=60,
    ping_interval=25,
    path="/socket.io",
    engineio_logger=False,
    socketio_logger=False,
    max_http_buffer_size=int(os.getenv("SIO_MAX_HTTP_BUFFER", str(10 * 1024 * 1024))),  # 10 MB per message
    allow_upgrades=True,  # Allow WebSocket upgrades
    transports=['websocket', 'polling']  # WebSocket first, polling fallback
)

def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)
    
    # Initialize Sentry error tracking
    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        sentry_environment = os.environ.get("SENTRY_ENVIRONMENT", "development")
        sentry_release = os.environ.get("SENTRY_RELEASE", "mina@unknown")
        
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                FlaskIntegration(),
                LoggingIntegration(
                    level=logging.INFO,  # Capture info and above as breadcrumbs
                    event_level=logging.ERROR  # Send errors as events
                ),
            ],
            environment=sentry_environment,
            release=sentry_release,
            traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),  # 10% of transactions
            profiles_sample_rate=float(os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),  # 10% profiling
            send_default_pii=False,  # Don't send personally identifiable information
            attach_stacktrace=True,
            before_send=_sentry_before_send,  # Custom filter function
        )
        app.logger.info(f"✅ Sentry initialized: env={sentry_environment}, release={sentry_release}")
    else:
        app.logger.warning("⚠️ SENTRY_DSN not set - error tracking disabled")
    
    # Enforce SESSION_SECRET is set - fail fast in production
    app.secret_key = os.environ.get("SESSION_SECRET") or getattr(Config, "SECRET_KEY")
    if not app.secret_key:
        # Only allow fallback in development
        if os.getenv("REPLIT_DEV_ENV") or os.getenv("REPLIT_RUNTIME_TYPE") == "interactivedev":
            app.secret_key = "dev-session-secret-only-for-testing-change-in-production"  # pragma: allowlist secret
            app.logger.warning("SESSION_SECRET not set, using development key")
        else:
            raise ValueError("SESSION_SECRET environment variable must be set for production")
    app.config["MAX_CONTENT_LENGTH"] = getattr(Config, "MAX_CONTENT_LENGTH", 32 * 1024 * 1024)

    # logging
    _configure_logging(json_logs=getattr(Config, "JSON_LOGS", False))
    app.logger.info("Booting Mina…")

    # reverse proxy (Replit)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    
    # Set security headers (production hardening)
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = 1800  # 30 minutes
    
    # Initialize CSRF protection  
    csrf = CSRFProtect(app)
    app.config["WTF_CSRF_TIME_LIMIT"] = None  # Don't expire tokens
    app.config["WTF_CSRF_SSL_STRICT"] = True  # Enforce HTTPS referer/origin checks (ProxyFix sets is_secure)
    app.config["WTF_CSRF_CHECK_DEFAULT"] = True  # Enable CSRF by default
    
    # Exempt Socket.IO Engine.IO endpoint from CSRF (polling/handshake POST requests)
    # Socket.IO uses its own connection-level authentication
    # We wrap the error handler to allow Socket.IO requests through
    original_error_handler = csrf._error_response
    def custom_csrf_error(reason):
        if request.path.startswith('/socket.io'):
            return None  # Allow request to proceed
        return original_error_handler(reason)
    csrf._error_response = custom_csrf_error

    # Configure Flask-Limiter for production-grade rate limiting
    # Use Redis if available, fallback to memory storage
    redis_url = os.environ.get("REDIS_URL")
    storage_uri = redis_url if redis_url else "memory://"
    
    limiter = Limiter(
        get_remote_address,
        app=app,
        storage_uri=storage_uri,
        default_limits=["100 per minute", "1000 per hour"],
        strategy="fixed-window",
        headers_enabled=True,  # Include X-RateLimit-* headers in responses
        swallow_errors=True,  # Don't crash app if rate limiter fails
    )
    
    # Make limiter available for route decorators
    app.limiter = limiter
    
    storage_type = "Redis" if redis_url else "Memory"
    app.logger.info(f"✅ Flask-Limiter configured ({storage_type} backend): 100/min, 1000/hour per IP")

    # gzip (optional)
    try:
        from flask_compress import Compress  # type: ignore
        Compress(app)
        app.logger.info("Compression enabled")
    except Exception:
        app.logger.info("Compression unavailable (flask-compress not installed)")

    # middlewares with proper error handling and logging
    try:
        from middleware.request_context import request_context_middleware  # type: ignore
        request_context_middleware(app)
        app.logger.info("✅ Request context middleware enabled")
    except Exception as e:
        app.logger.warning(f"⚠️ Request context middleware failed to load: {e}")

    # Body size limits (Flask-Limiter handles rate limiting now)
    app.config.setdefault("MAX_JSON_BODY_BYTES", 5 * 1024 * 1024)  # 5MB
    app.config.setdefault("MAX_FORM_BODY_BYTES", 50 * 1024 * 1024)  # 50MB
    
    # Apply body size checks via before_request (rate limiting now handled by Flask-Limiter)
    @app.before_request
    def check_body_size():
        cl = request.content_length or 0
        if request.method in ("POST", "PUT", "PATCH"):
            ct = (request.content_type or "").lower()
            max_json = app.config.get("MAX_JSON_BODY_BYTES", 5 * 1024 * 1024)
            max_form = app.config.get("MAX_FORM_BODY_BYTES", 50 * 1024 * 1024)
            
            if "application/json" in ct and cl > max_json:
                from flask import abort
                abort(413)
            if "multipart/form-data" in ct and cl > max_form:
                from flask import abort
                abort(413)

    # Set CORS defaults - secure for both production and development
    env = os.environ.get("FLASK_ENV", "development")
    if env == "production":
        app.config.setdefault("ALLOWED_ORIGINS", [])  # Require explicit config in production
    else:
        # Development: Allow localhost only, never use ["*"] to prevent reflection attacks
        app.config.setdefault("ALLOWED_ORIGINS", [
            "http://localhost:5000",
            "https://localhost:5000",
            "http://127.0.0.1:5000",
            "https://127.0.0.1:5000"
        ])
    
    try:
        from middleware.cors import cors_middleware  # type: ignore
        cors_middleware(app)
        app.logger.info("✅ CORS middleware enabled")
    except Exception as e:
        app.logger.warning(f"⚠️ CORS middleware failed to load: {e}")

    # per-request id for tracing
    @app.before_request
    def assign_request_id():
        g.request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())

    # Content Security Policy with nonce-based inline script protection
    try:
        from middleware.csp import csp_middleware  # type: ignore
        csp_middleware(app)
        app.logger.info("✅ CSP middleware enabled with nonce-based inline script protection")
    except Exception as e:
        app.logger.warning(f"⚠️ CSP middleware failed to load: {e}")
    
    # Session security configuration and middleware
    try:
        from middleware.session_security import configure_session_security, session_security_middleware  # type: ignore
        configure_session_security(app)
        session_security_middleware(app)
        app.logger.info("✅ Session security hardening enabled: timeouts, rotation, fixation prevention")
    except Exception as e:
        app.logger.warning(f"⚠️ Session security middleware failed to load: {e}")
    
    # HSTS (Strict Transport Security) - only for production HTTPS
    @app.after_request
    def add_hsts_header(resp):
        if app.config.get('ENV') == 'production':
            resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        return resp

    # ensure metrics directories
    metrics_dir = getattr(Config, "METRICS_DIR", "./metrics")
    os.makedirs(metrics_dir, exist_ok=True)
    os.makedirs(os.path.join(metrics_dir, "sessions"), exist_ok=True)

    # Database configuration (optional for graceful degradation)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }
        
        # Initialize database models
        try:
            from models import db
            from flask_migrate import Migrate
            
            db.init_app(app)
            
            # Initialize Flask-Migrate for database migrations
            migrate = Migrate(app, db)
            
            # Let Flask-Migrate handle schema creation via migrations
            # Comment out db.create_all() to avoid conflicts with migration system
            # with app.app_context():
            #     db.create_all()
            app.logger.info("Database connected and initialized (migrations enabled)")
        except Exception as e:
            app.logger.warning(f"Database initialization failed: {e}")
            app.logger.info("Continuing without database persistence")
        
        # Initialize Flask-Login
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'  # type: ignore
        login_manager.login_message = 'Please log in to access this page.'
        login_manager.login_message_category = 'info'
        
        @login_manager.user_loader
        def load_user(user_id):
            try:
                from models import User, db as models_db
                return models_db.session.query(User).get(int(user_id))
            except Exception:
                return None
    else:
        app.logger.info("No DATABASE_URL found, running without database persistence")

    # pages blueprint or fallback /live
    try:
        from routes.pages import pages_bp  # type: ignore
        app.register_blueprint(pages_bp)
    except Exception:
        @app.route("/live")
        def live():
            return render_template("live.html")

    # WebSocket routes (required) - import to bind handlers
    import routes.websocket  # noqa: F401
    import routes.transcription_websocket  # noqa: F401
    
    # Register enhanced WebSocket handlers
    try:
        from routes.enhanced_transcription_websocket import register_enhanced_websocket_handlers
        register_enhanced_websocket_handlers(socketio)
        app.logger.info("Enhanced WebSocket handlers registered")
    except Exception as e:
        app.logger.warning(f"Failed to register enhanced WebSocket handlers: {e}")
    
    # Register comprehensive WebSocket handlers
    try:
        from routes.comprehensive_transcription_api import register_comprehensive_websocket_handlers
        register_comprehensive_websocket_handlers(socketio)
        app.logger.info("Comprehensive WebSocket handlers registered")
    except Exception as e:
        app.logger.warning(f"Failed to register comprehensive WebSocket handlers: {e}")
    
    # Register live transcription Socket.IO handlers
    try:
        from routes.live_socketio import register_live_socketio
        register_live_socketio()
        app.logger.info("✅ Live transcription Socket.IO handlers registered")
    except Exception as e:
        app.logger.warning(f"Failed to register live Socket.IO handlers: {e}")

    # Register transcription APIs
    # FIXED: Only register the working unified transcription API to avoid route conflicts
    try:
        from routes.unified_transcription_api import unified_api_bp
        app.register_blueprint(unified_api_bp)
        app.logger.info("✅ Unified Transcription API registered (ACTIVE)")
    except Exception as e:
        app.logger.warning(f"Failed to register unified transcription API: {e}")
    
    # Disable conflicting transcription endpoints to prevent route conflicts
    # try:
    #     from routes.transcription_api import transcription_api_bp
    #     app.register_blueprint(transcription_api_bp)
    #     app.logger.info("Transcription API registered")
    # except Exception as e:
    #     app.logger.warning(f"Failed to register transcription API: {e}")
    
    # try:
    #     from routes.enhanced_transcription_api import enhanced_api_bp
    #     app.register_blueprint(enhanced_api_bp)
    #     app.logger.info("Enhanced Transcription API registered")
    # except Exception as e:
    #     app.logger.warning(f"Failed to register enhanced transcription API: {e}")
    
    # try:
    #     from routes.comprehensive_transcription_api import comprehensive_bp
    #     app.register_blueprint(comprehensive_bp)
    #     app.logger.info("Comprehensive Transcription API registered")
    # except Exception as e:
    #     app.logger.warning(f"Failed to register comprehensive transcription API: {e}")
    
    # Register WORKING live transcription API (priority)
    try:
        from routes.live_transcription_working import live_transcription_bp
        app.register_blueprint(live_transcription_bp)
        app.logger.info("✅ Working Live Transcription API registered")
    except Exception as e:
        app.logger.warning(f"Failed to register working live transcription API: {e}")

    # Register authentication and dashboard blueprints
    try:
        from routes.auth import auth_bp
        app.register_blueprint(auth_bp)
        app.logger.info("Authentication routes registered")
    except Exception as e:
        app.logger.warning(f"Failed to register auth routes: {e}")
    
    try:
        from routes.dashboard import dashboard_bp
        app.register_blueprint(dashboard_bp)
        app.logger.info("Dashboard routes registered")
    except Exception as e:
        app.logger.warning(f"Failed to register dashboard routes: {e}")
    
    # Note: sessions blueprint causes circular import (SessionService → app.db)
    # Meetings API (api_meetings_bp) provides equivalent functionality
    # Template fixes completed in routes/sessions.py for future use

    # Register API blueprints for REST endpoints
    try:
        from routes.api_meetings import api_meetings_bp
        app.register_blueprint(api_meetings_bp)
        app.logger.info("Meetings API routes registered")
    except Exception as e:
        app.logger.warning(f"Failed to register meetings API routes: {e}")
    
    try:
        from routes.api_tasks import api_tasks_bp
        app.register_blueprint(api_tasks_bp)
        app.logger.info("Tasks API routes registered")
    except Exception as e:
        app.logger.warning(f"Failed to register tasks API routes: {e}")
    
    try:
        from routes.api_analytics import api_analytics_bp
        app.register_blueprint(api_analytics_bp)
        app.logger.info("Analytics API routes registered")
    except Exception as e:
        app.logger.warning(f"Failed to register analytics API routes: {e}")
    
    try:
        from routes.api_markers import api_markers_bp
        app.register_blueprint(api_markers_bp)
        app.logger.info("Markers API routes registered")
    except Exception as e:
        app.logger.warning(f"Failed to register markers API routes: {e}")
    
    try:
        from routes.api_generate_insights import api_generate_insights_bp
        app.register_blueprint(api_generate_insights_bp)
        app.logger.info("API Generate Insights route registered")
    except Exception as e:
        app.logger.warning(f"Failed to register API Generate Insights route: {e}")

    # Settings routes
    try:
        from routes.settings import settings_bp
        app.register_blueprint(settings_bp)
        app.logger.info("Settings routes registered")
    except Exception as e:
        app.logger.error(f"Failed to register settings routes: {e}")

    # Calendar routes
    try:
        from routes.calendar import calendar_bp
        app.register_blueprint(calendar_bp)
        app.logger.info("Calendar routes registered")
    except Exception as e:
        app.logger.error(f"Failed to register calendar routes: {e}")
    
    # AI Copilot routes
    try:
        from routes.copilot import copilot_bp
        app.register_blueprint(copilot_bp)
        app.logger.info("AI Copilot routes registered")
    except Exception as e:
        app.logger.error(f"Failed to register AI Copilot routes: {e}")
    
    # Production Monitoring Dashboard
    try:
        from monitoring_dashboard import monitoring_bp
        app.register_blueprint(monitoring_bp)
        app.logger.info("Production Monitoring Dashboard registered")
    except Exception as e:
        app.logger.error(f"Failed to register Production Monitoring Dashboard: {e}")
    
    # Missing API endpoints - temporarily disabled due to circular import
    # Quick fix for analytics and meetings endpoints
    try:
        from routes.quick_analytics_fix import quick_analytics_bp
        app.register_blueprint(quick_analytics_bp)
        app.logger.info("Quick analytics fix registered")
    except Exception as e:
        app.logger.error(f"Failed to register quick analytics fix: {e}")
        
    try:
        from routes.meetings_api_fix import meetings_api_fix_bp
        app.register_blueprint(meetings_api_fix_bp)
        app.logger.info("Quick meetings API fix registered")
    except Exception as e:
        app.logger.error(f"Failed to register meetings API fix: {e}")

    # other blueprints (guarded)
    _optional = [
        ("routes.final_upload", "final_bp", "/api"),
        ("routes.export", "export_bp", "/api"),
        ("routes.insights", "insights_bp", "/api"),
        ("routes.nudges", "nudges_bp", "/api"),
        ("routes.team_collaboration", "team_bp", "/api"),
        ("routes.advanced_analytics", "analytics_bp", "/api"),
        ("routes.integration_marketplace", "integrations_bp", "/api"),
        ("routes.health", "health_bp", "/health"),
        ("routes.metrics_stream", "metrics_stream_bp", "/api"),
        ("routes.error_handlers", "errors_bp", None),
    ]
    for mod_name, bp_name, prefix in _optional:
        try:
            mod = __import__(mod_name, fromlist=[bp_name])
            bp = getattr(mod, bp_name)
            app.register_blueprint(bp, url_prefix=prefix) if prefix else app.register_blueprint(bp)
        except Exception:
            pass

    # basic /healthz if health blueprint absent
    @app.get("/healthz")
    def healthz():
        return {"ok": True, "uptime": True}, 200

    # unified error shape
    @app.errorhandler(413)  # RequestEntityTooLarge
    def too_large(e):
        return jsonify(error="payload_too_large", detail="Upload exceeded limit"), 413

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error="not_found"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Unhandled error")
        return jsonify(error="server_error"), 500

    # hook Socket.IO to app
    socketio.init_app(app)
    app.extensions["socketio"] = socketio

    # Socket.IO origin guard (optional tighten)
    allowed = [o.strip() for o in str(getattr(Config, "CORS_ALLOWLIST", "*")).split(",") if o.strip()]
    if allowed and allowed != ["*"]:
        @socketio.on("connect")
        def _check_origin(auth: Optional[dict] = None):
            origin = request.headers.get("Origin") or ""
            if not any(origin.endswith(x) or origin == x for x in allowed):
                app.logger.warning("Rejecting WS from origin=%s", origin)
                return False  # refuse connection

    # Start resource cleanup service to prevent memory leaks
    try:
        from services.resource_cleanup import resource_cleanup_manager
        
        # Register default cleanup tasks
        resource_cleanup_manager.register_cleanup_task('memory_gc', resource_cleanup_manager.force_garbage_collection, 60)
        resource_cleanup_manager.register_cleanup_task('temp_files', resource_cleanup_manager.cleanup_temp_files, 600)
        resource_cleanup_manager.register_cleanup_task('websocket_buffers', resource_cleanup_manager.cleanup_websocket_buffers, 300)
        
        # Start the background service
        resource_cleanup_manager.start_cleanup_service()
        app.logger.info("✅ Resource cleanup service started with default tasks registered")
    except Exception as e:
        app.logger.error(f"❌ Failed to start resource cleanup service: {e}")
    
    app.logger.info("Mina app ready")
    return app

# WSGI entrypoints
app = create_app()

# graceful shutdown for local/threading runs
def _shutdown(*_):
    app.logger.info("Shutting down gracefully…")
    # In threading mode, there is no socketio.stop(); process will exit.
signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)

if __name__ == "__main__":
    app.logger.info("🚀 Mina at http://0.0.0.0:5000  (Socket.IO path %s)", app.config.get("SOCKETIO_PATH", "/socket.io"))
    socketio.run(app, host="0.0.0.0", port=5000, use_reloader=False, log_output=True)
    