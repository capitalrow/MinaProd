# middleware/cors.py
from flask import request, current_app

def cors_middleware(app):
    allowed = [o.strip() for o in current_app.config.get("ALLOWED_ORIGINS", []) if o.strip()]

    @app.after_request
    def _cors(resp):
        origin = request.headers.get("Origin")
        if not origin:
            return resp
        if not allowed or "*" in allowed or origin in allowed:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Vary"] = "Origin"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Request-ID"
            resp.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
            resp.headers["Access-Control-Allow-Credentials"] = "true"
        return resp