import os
from flask import Flask, send_from_directory
from flask_cors import CORS

def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    # Load Config if present
    try:
        app.config.from_object("config.Config")
    except Exception:
        pass

    # CORS (adjust origins as needed)
    CORS(app, resources={r"/api/*": {"origins": os.environ.get("CORS_ALLOW","*")}}, supports_credentials=True)

    # Register blueprints if files exist/importable
    def _try_register(bpmod, bpname):
        try:
            mod = __import__(bpmod, fromlist=[bpname])
            bp = getattr(mod, bpname)
            app.register_blueprint(bp)
            print(f"[init] registered blueprint: {bpmod}.{bpname}")
        except Exception as e:
            print(f"[init] could not register {bpmod}.{bpname}: {e}")

    _try_register("auth", "bp_auth")
    _try_register("api", "bp_api")
    _try_register("uploads", "bp_uploads")

    @app.route("/")
    def welcome():
        return send_from_directory(app.static_folder + "/ui", "welcome.html")

    @app.route("/app")
    def app_spa():
        return send_from_directory(app.static_folder + "/ui", "index.html")

    @app.route("/terms")
    def terms():
        return send_from_directory(app.static_folder + "/ui", "terms.html")

    @app.route("/privacy")
    def privacy():
        return send_from_directory(app.static_folder + "/ui", "privacy.html")

    @app.route("/healthz")
    def healthz():
        return "ok", 200

    @app.route("/readyz")
    def readyz():
        try:
            # optional DB check if models available
            from models import db
            db.session.execute("SELECT 1")
            return "ok", 200
        except Exception:
            return "not ready", 503

    return app
