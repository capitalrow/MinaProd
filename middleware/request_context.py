import time
import uuid
from flask import g, request
from typing import Callable

def request_context_middleware(app):
    @app.before_request
    def _before():
        g.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        g._t0 = time.time()

    @app.after_request
    def _after(resp):
        try:
            dur_ms = int((time.time() - getattr(g, "_t0", time.time())) * 1000)
            resp.headers["X-Request-ID"] = getattr(g, "request_id", "")
            # lightweight access log (let the logger formatter decide output format)
            app.logger.info(
                "http",
                extra={
                    "event": "http",
                    "request_id": getattr(g, "request_id", ""),
                    "path": request.path,
                    "method": request.method,
                    "status": resp.status_code,
                    "lat_ms": dur_ms,
                    "remote_ip": request.headers.get("x-forwarded-for", request.remote_addr),
                },
            )
        except Exception:
            pass
        return resp