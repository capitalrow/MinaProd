# app_refactored.py
import os
from flask import Flask
from flask_cors import CORS

try:
    from flask_socketio import SocketIO
    HAVE_SOCKET = True
except Exception:
    SocketIO = None
    HAVE_SOCKET = False

socketio = None

def create_app():
    global socketio
    base_dir = os.path.dirname(__file__)

    app = Flask(
        __name__,
        static_folder=os.path.join(base_dir, "static"),
        static_url_path="/static",
        template_folder=os.path.join(base_dir, "templates"),
    )
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Zero-cache so the preview can’t serve stale HTML
    @app.after_request
    def _nocache(resp):
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        return resp

    if HAVE_SOCKET:
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
        try:
            import routes.websocket  # noqa: F401 (your @socketio.on handlers)
        except Exception as e:
            print("[mina] websocket module not loaded:", e)
    else:
        socketio = None

    # Register ONLY the new UI blueprint
    from routes.ui import ui_bp
    app.register_blueprint(ui_bp)

    # Do NOT register any other legacy blueprints that map "/" or "/live"
    return app