# middleware/cors.py
from flask import request, current_app

def cors_middleware(app):
    @app.after_request
    def _cors(resp):
        # Get allowed origins from config at request time (not initialization time)
        allowed_origins = current_app.config.get("ALLOWED_ORIGINS", [])
        
        # Never use wildcard - it's a security vulnerability that allows origin reflection
        # If empty list, default to localhost for development safety
        if not allowed_origins:
            allowed = ["http://localhost:5000", "https://localhost:5000"]
        else:
            allowed = [o.strip() for o in allowed_origins if o.strip() and o.strip() != "*"]
        
        origin = request.headers.get("Origin")
        if not origin:
            return resp
        
        # Only allow explicitly whitelisted origins - never reflect arbitrary origins
        if origin in allowed:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Vary"] = "Origin"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Request-ID"
            resp.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
            resp.headers["Access-Control-Allow-Credentials"] = "true"
        
        return resp