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

# ---------- Create the SocketIO singleton with eventlet for production WebSocket support
socketio = SocketIO(
    cors_allowed_origins=["http://localhost:5000", "https://*.replit.dev", "https://*.replit.app"],
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
    # Enforce SESSION_SECRET is set - fail fast in production
    app.secret_key = os.environ.get("SESSION_SECRET") or getattr(Config, "SECRET_KEY")
    if not app.secret_key:
        # Only allow fallback in development
        if os.getenv("REPLIT_DEV_ENV") or os.getenv("REPLIT_RUNTIME_TYPE") == "interactivedev":
            app.secret_key = "dev-session-secret-only-for-testing-change-in-production"
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
    app.config["WTF_CSRF_SSL_STRICT"] = False  # Allow behind proxy
    # Disable CSRF for JSON requests (APIs should use token auth)
    app.config["WTF_CSRF_CHECK_DEFAULT"] = False  # We'll manually check where needed

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

    # Set sensible defaults for rate limiting
    app.config.setdefault("RATE_LIMIT_PER_IP_MIN", 120)  # 120 requests per minute
    app.config.setdefault("MAX_JSON_BODY_BYTES", 5 * 1024 * 1024)  # 5MB
    app.config.setdefault("MAX_FORM_BODY_BYTES", 50 * 1024 * 1024)  # 50MB
    
    try:
        from middleware.limits import limits_middleware  # type: ignore
        limits_middleware(app)
        app.logger.info("✅ Rate limiting middleware enabled")
    except Exception as e:
        app.logger.warning(f"⚠️ Rate limiting middleware failed to load: {e}")

    # Set CORS defaults - secure for production, permissive for development
    env = os.environ.get("FLASK_ENV", "development")
    if env == "production":
        app.config.setdefault("ALLOWED_ORIGINS", [])  # Require explicit config in production
    else:
        app.config.setdefault("ALLOWED_ORIGINS", ["*"])  # Allow all origins for development
    
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

    # stricter CSP (keeps your allowances; adds jsdelivr for CSS libs)
    @app.after_request
    def add_security_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        resp.headers["X-XSS-Protection"] = "1; mode=block"
        resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Add strong caching for static assets to prevent favicon storm
        if request.endpoint == 'static':
            if 'favicon' in request.path.lower():
                # Strong caching for favicon to prevent Android WebView storm
                resp.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
                resp.headers['Expires'] = 'Thu, 31 Dec 2037 23:55:55 GMT'
            elif request.path.endswith(('.css', '.js', '.svg', '.png', '.jpg', '.jpeg', '.gif', '.woff', '.woff2')):
                # Cache other static assets for 24 hours
                resp.headers['Cache-Control'] = 'public, max-age=86400'
        resp.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        resp.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self' *.replit.dev *.replit.app; "
            "connect-src 'self' https: wss: ws: wss://*.replit.dev wss://*.replit.app ws://localhost:5000; "
            "script-src 'self' 'unsafe-inline' https://cdn.socket.io https://cdnjs.cloudflare.com https://cdn.replit.com https://unpkg.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://cdn.replit.com; "
            "font-src 'self' https://cdnjs.cloudflare.com data:; "
            "img-src 'self' blob: data:; "
            "media-src 'self' blob:; "
            "worker-src 'self' blob:; "
            "frame-ancestors 'self' *.replit.dev *.replit.app; "
            "base-uri 'self';"
        )
        return resp

    # ensure metrics directories
    metrics_dir = getattr(Config, "METRICS_DIR", "./metrics")
    os.makedirs(metrics_dir, exist_ok=True)
    os.makedirs(os.path.join(metrics_dir, "sessions"), exist_ok=True)

    # Database configuration (optional for graceful degradation)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "5")),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
            "pool_recycle": 300,
            "pool_pre_ping": True,
            "pool_use_lifo": True
        }
        
        # Initialize database models
        try:
            from models import db
            db.init_app(app)
            
            with app.app_context():
                db.create_all()
            app.logger.info("Database connected and initialized")
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
        from routes.dashboard import dashboard_bp, register_dashboard_socketio_handlers
        app.register_blueprint(dashboard_bp)
        register_dashboard_socketio_handlers(socketio)
        app.logger.info("Dashboard routes registered")
    except Exception as e:
        app.logger.warning(f"Failed to register dashboard routes: {e}")

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
        from routes.simple_settings import simple_settings_bp
        app.register_blueprint(simple_settings_bp)
        app.logger.info("Settings routes registered")
    except Exception as e:
        app.logger.error(f"Failed to register settings routes: {e}")

    # Calendar routes
    try:
        from routes.calendar_pages import calendar_bp
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

    # Export routes (with minimal implementation to avoid circular imports)
    try:
        # Create a minimal export blueprint without complex dependencies
        from flask import Blueprint
        export_bp_minimal = Blueprint("export", __name__, url_prefix="/api/export")
        
        @export_bp_minimal.route("/ping", methods=["GET", "POST"])
        def export_ping():
            return {"ok": True}
            
        app.register_blueprint(export_bp_minimal)
        app.logger.info("Export routes registered (minimal)")
    except Exception as e:
        app.logger.error(f"Failed to register export routes: {e}")
    
    # other blueprints (guarded)
    _optional = [
        ("routes.final_upload", "final_bp", "/api"),
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
    