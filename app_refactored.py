# app_refactored.py
import os
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO

# --- config flags from env
FORCE_POLLING = os.getenv("FORCE_POLLING", "false").lower() == "true"
SOCKETIO_PATH = os.getenv("SOCKETIO_PATH", "/socket.io")

db = SQLAlchemy()
migrate = Migrate()

# IMPORTANT: eventlet to match gunicorn -k eventlet
socketio = SocketIO(
    async_mode="eventlet",
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

    # Init Socket.IO
    socketio.init_app(app)

    # HTTP blueprints
    from routes.pages import pages_bp
    from routes.meetings import meetings_bp
    from routes.tasks import tasks_bp
    from routes.share import share_bp
    from routes.settings import settings_bp
    app.register_blueprint(pages_bp)
    app.register_blueprint(meetings_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(share_bp)
    app.register_blueprint(settings_bp)

    # Live page route (template under templates/pages/live.html)
    from flask import render_template
    @app.get("/live")
    def live():
        return render_template(
            "pages/live.html",
            force_polling=FORCE_POLLING,
            sio_path=SOCKETIO_PATH,
        )

    # Register websocket handlers AFTER socketio is ready (no circular import)
    from routes.websocket import ws_bp, register_socketio_handlers
    app.register_blueprint(ws_bp)
    register_socketio_handlers(socketio)

    return app

app = create_app()

if __name__ == "__main__":
    # Local dev runner; Replit uses gunicorn
    socketio.run(app, host="0.0.0.0", port=5000)