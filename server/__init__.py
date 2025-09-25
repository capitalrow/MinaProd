import os
from flask import Flask, send_from_directory, current_app, Response
from flask_cors import CORS
from .models import db
from .api import bp_api
from .auth import bp_auth
from .uploads import bp_uploads

def create_app():
    app = Flask(__name__, static_folder="../static", static_url_path="/static")
    app.config.from_object("config.Config")

    os.makedirs("data", exist_ok=True)
    db.init_app(app)
    with app.app_context():
        db.create_all()

    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ALLOW"]}}, supports_credentials=True)

    @app.after_request
    def _sec(resp: Response):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["Permissions-Policy"] = "microphone=(self)"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        csp = ("default-src 'self'; img-src 'self' data:; script-src 'self' https://cdn.tailwindcss.com https://cdn.socket.io 'unsafe-inline'; "
               "style-src 'self' 'unsafe-inline'; connect-src 'self' https://cdn.socket.io; frame-ancestors 'none'; base-uri 'self'")
        if current_app.config.get("ENABLE_CSP_REPORT_ONLY", True):
            resp.headers["Content-Security-Policy-Report-Only"] = csp
        else:
            resp.headers["Content-Security-Policy"] = csp
        return resp

    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_api)
    app.register_blueprint(bp_uploads)

    @app.route("/")
    def welcome():
        return send_from_directory(app.static_folder + "/ui", "welcome.html")

    @app.route("/terms")
    def terms():
        return send_from_directory(app.static_folder + "/ui", "terms.html")

    @app.route("/privacy")
    def privacy():
        return send_from_directory(app.static_folder + "/ui", "privacy.html")

    @app.route("/app")
    def app_spa():
        return send_from_directory(app.static_folder + "/ui", "index.html")

    @app.route("/s/<_token>")
    def share_view(_token):
        return send_from_directory(app.static_folder + "/ui", "share.html")

    @app.route("/healthz")
    def healthz():
        return "ok", 200

    @app.route("/readyz")
    def readyz():
        try:
            db.session.execute("SELECT 1")
            return "ok", 200
        except Exception:
            return "not ready", 503

    return app