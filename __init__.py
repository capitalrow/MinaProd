import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from models import db
from config import Config
from extensions import socketio

def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.from_object(Config)
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ALLOW","*")}}, supports_credentials=True)
    
    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # Register blueprints if files exist/importable
    def _try_register(bpmod, bpname):
        try:
            mod = __import__(bpmod, fromlist=[bpname])
            bp = getattr(mod, bpname)
            app.register_blueprint(bp)
            print(f"[init] registered blueprint: {bpmod}.{bpname}")
        except Exception as e:
            print(f"[init] could not register {bpmod}.{bpname}: {e}")

    _try_register("server.auth", "bp_auth")
    _try_register("api", "bp_api")
    _try_register("uploads", "bp_uploads")
    _try_register("routes.api_transcription", "transcription_bp")
    _try_register("routes.audio_transcription_http", "audio_bp")
    
    # Initialize WebSocket routes
    try:
        import routes.websocket  # noqa: F401 - Socket.IO event handlers
        print("[init] registered websocket routes")
    except Exception as e:
        print(f"[init] could not register websocket routes: {e}")

    # Ensure static folder exists
    static_folder = app.static_folder or "static"
    ui_folder = os.path.join(static_folder, "ui")
    
    @app.route("/")
    def welcome():
        return send_from_directory(ui_folder, "welcome.html")

    @app.route("/app")
    def app_spa():
        return send_from_directory(ui_folder, "app.html")

    @app.route("/terms")
    def terms():
        return send_from_directory(ui_folder, "terms.html")

    @app.route("/privacy")
    def privacy():
        return send_from_directory(ui_folder, "privacy.html")

    @app.route("/healthz")
    def healthz():
        return "ok", 200

    @app.route("/readyz")
    def readyz():
        try:
            with app.app_context():
                db.session.execute(db.text("SELECT 1"))
            return "ok", 200
        except Exception:
            return "not ready", 503

    return app, socketio