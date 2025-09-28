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

# ---------- Config (fallback if config.Config not present)
try:
    from config import Config  # type: ignore
except Exception:
    class Config:
        JSON_LOGS: bool = os.getenv("JSON_LOGS", "false").lower() == "true"
        METRICS_DIR: str = os.getenv("METRICS_DIR", "./metrics")
        SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me")
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

# ---------- Create the SocketIO singleton first (threading = Replit-safe)
socketio = SocketIO(
    cors_allowed_origins="*",          # narrowed in handshake check below
    async_mode="threading",
    ping_timeout=60,
    ping_interval=25,
    path=os.getenv("SOCKETIO_PATH", "/socket.io"),
    max_http_buffer_size=int(os.getenv("SIO_MAX_HTTP_BUFFER", str(10 * 1024 * 1024))),  # 10 MB per message
)

def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)
    app.secret_key = getattr(Config, "SECRET_KEY", "change-me")
    app.config["MAX_CONTENT_LENGTH"] = getattr(Config, "MAX_CONTENT_LENGTH", 32 * 1024 * 1024)

    # logging
    _configure_logging(json_logs=getattr(Config, "JSON_LOGS", False))
    app.logger.info("Booting Mina…")

    # reverse proxy (Replit)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    # gzip (optional)
    try:
        from flask_compress import Compress  # type: ignore
        Compress(app)
        app.logger.info("Compression enabled")
    except Exception:
        app.logger.info("Compression unavailable (flask-compress not installed)")

    # middlewares (guarded imports)
    try:
        from middleware.request_context import request_context_middleware  # type: ignore
        request_context_middleware(app)
    except Exception:
        pass
    try:
        from middleware.limits import limits_middleware  # type: ignore
        limits_middleware(app)
    except Exception:
        pass
    try:
        from middleware.cors import cors_middleware  # type: ignore
        cors_middleware(app)
    except Exception:
        pass

    # per-request id for tracing
    @app.before_request
    def assign_request_id():
        g.request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())

    # stricter CSP (keeps your allowances; adds jsdelivr for CSS libs)
    @app.after_request
    def add_security_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self' *.replit.dev *.replit.app; "
            "connect-src 'self' https: wss: ws:; "
            "script-src 'self' 'unsafe-inline' https://cdn.socket.io; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' blob: data:; "
            "media-src 'self' blob:; "
            "worker-src 'self' blob:;"
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
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
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
    try:
        from routes.transcription_api import transcription_api_bp
        app.register_blueprint(transcription_api_bp)
        app.logger.info("Transcription API registered")
    except Exception as e:
        app.logger.warning(f"Failed to register transcription API: {e}")
    
    try:
        from routes.unified_transcription_api import unified_api_bp
        app.register_blueprint(unified_api_bp)
        app.logger.info("Unified Transcription API registered")
    except Exception as e:
        app.logger.warning(f"Failed to register unified transcription API: {e}")
    
    try:
        from routes.enhanced_transcription_api import enhanced_api_bp
        app.register_blueprint(enhanced_api_bp)
        app.logger.info("Enhanced Transcription API registered")
    except Exception as e:
        app.logger.warning(f"Failed to register enhanced transcription API: {e}")
    
    try:
        from routes.comprehensive_transcription_api import comprehensive_bp
        app.register_blueprint(comprehensive_bp)
        app.logger.info("Comprehensive Transcription API registered")
    except Exception as e:
        app.logger.warning(f"Failed to register comprehensive transcription API: {e}")
    
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

    # Settings routes
    try:
        from routes.settings import settings_bp
        app.register_blueprint(settings_bp)
        app.logger.info("Settings routes registered")
    except Exception as e:
        app.logger.error(f"Failed to register settings routes: {e}")

    # other blueprints (guarded)
    _optional = [
        ("routes.final_upload", "final_bp", "/api"),
        ("routes.export", "export_bp", "/api"),
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
    socketio.init_app(
        app,
        cors_allowed_origins=getattr(Config, "CORS_ALLOWLIST", "*"),
        path=getattr(Config, "SOCKETIO_PATH", "/socket.io"),
        max_http_buffer_size=int(os.getenv("SIO_MAX_HTTP_BUFFER", str(10 * 1024 * 1024))),
    )
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
    