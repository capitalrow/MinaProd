# app.py (hardened, SPA mounted at /app, live kept at /live)
import os
import json
import signal
import logging
import uuid
from typing import Optional
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, render_template, request, g, jsonify
from flask_socketio import SocketIO

# ---------- Config (fallback if config.Config not present)
try:
    from config import Config  # type: ignore
except Exception:
    class Config:
        SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me")
        JSON_LOGS: bool = os.getenv("JSON_LOGS", "false").lower() == "true"
        SOCKETIO_PATH: str = os.getenv("SOCKETIO_PATH", "/socket.io")
        CORS_ALLOWLIST: str = os.getenv("CORS_ALLOWLIST", "*")
        MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", str(32 * 1024 * 1024)))  # 32 MB

# ---------- Logging
class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {"level": record.levelname, "name": record.name, "msg": record.getMessage()}
        rid = getattr(g, "request_id", None)
        if rid:
            payload["request_id"] = rid
        return json.dumps(payload, ensure_ascii=False)

def _configure_logging(json_logs: bool = False) -> None:
    root = logging.getLogger()
    root.handlers[:] = []  # reset
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter() if json_logs else logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root.addHandler(handler)
    root.setLevel(logging.INFO)

# ---------- Create the SocketIO singleton first (threading = Replit-safe)
socketio = SocketIO(
    cors_allowed_origins="*",
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

    # Request id (nice-to-have)
    @app.before_request
    def _rid():
        g.request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())

    # health dirs
    metrics_dir = getattr(Config, "METRICS_DIR", "./metrics")
    os.makedirs(metrics_dir, exist_ok=True)
    os.makedirs(os.path.join(metrics_dir, "sessions"), exist_ok=True)

    # --- SPA UI at /app + root redirect ---
    try:
        from routes.ui import ui_bp  # type: ignore
        app.register_blueprint(ui_bp)
        app.logger.info("UI blueprint mounted at /app (root redirects to /app)")
    except Exception as e:
        app.logger.warning("UI blueprint not mounted: %s", e)

    # --- Live page (kept at /live) ---
    try:
        from routes.pages import pages_bp  # type: ignore
        app.register_blueprint(pages_bp)
        app.logger.info("Pages blueprint mounted (/live)")
    except Exception:
        @app.route("/live")
        def live():
            return render_template("live.html")

    # --- WebSocket routes (required) ---
    from routes.websocket import ws_bp  # type: ignore
    app.register_blueprint(ws_bp)

    # --- Optional blueprints ---
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
    @app.errorhandler(404)
    def not_found(_e):
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

    # tighten origins if configured
    allowed = [o.strip() for o in str(getattr(Config, "CORS_ALLOWLIST", "*")).split(",") if o.strip()]
    if allowed and allowed != ["*"]:
        @socketio.on("connect")
        def _check_origin(auth: Optional[dict] = None):
            origin = request.headers.get("Origin") or ""
            if not any(origin.endswith(x) or origin == x for x in allowed):
                app.logger.warning("Rejecting WS from origin=%s", origin)
                return False

    app.logger.info("Mina app ready")
    return app

# WSGI entrypoints
app = create_app()

def _shutdown(*_):
    app.logger.info("Shutting down gracefully…")
signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)

if __name__ == "__main__":
    app.logger.info("🚀 Mina at http://0.0.0.0:5000  (Socket.IO path %s)", app.config.get("SOCKETIO_PATH", "/socket.io"))
    socketio.run(app, host="0.0.0.0", port=5000)