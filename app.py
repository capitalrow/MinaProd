# app.py
import logging
import os
from flask import Flask, render_template, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

db = SQLAlchemy()
migrate = Migrate()

SOCKETIO_PATH = os.getenv("SOCKETIO_PATH", "/socket.io")
FORCE_POLLING = os.getenv("FORCE_POLLING", "true").lower() == "true"

# Replit-safe: run gunicorn -k eventlet; Socket.IO in threading mode (no monkey patch headaches)
socketio = SocketIO(
-    async_mode="threading",
+    async_mode="eventlet",
    cors_allowed_origins="*",
    ping_interval=25,
    ping_timeout=60,
    logger=False,
    engineio_logger=False,
    path=SOCKETIO_PATH,
)

class DefaultConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///instance/mina_dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(DefaultConfig)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, path=SOCKETIO_PATH)

    @app.get("/live")
    def live():
        return render_template("pages/live.html", force_polling=FORCE_POLLING, sio_path=SOCKETIO_PATH)

    @app.get("/healthz")
    def healthz():
        return jsonify({"ok": True}), 200

    # WebSocket routes (after socketio init)
    from routes.websocket import ws_bp  # noqa: F401
    app.register_blueprint(ws_bp)

    app.logger.info("SocketIO ready async_mode=%s path=%s polling=%s",
                    socketio.async_mode, SOCKETIO_PATH, FORCE_POLLING)
    return app

app = create_app()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)