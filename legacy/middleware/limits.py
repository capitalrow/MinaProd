import time
from collections import defaultdict, deque
from flask import request, current_app, abort

# simple in-memory per-IP and per-path limiter (good enough for single-process dev/preview)
_IP_WINDOW: dict[str, deque] = defaultdict(deque)

def _rate_ok(ip: str, max_per_minute: int) -> bool:
    now = time.time()
    q = _IP_WINDOW[ip]
    while q and (now - q[0]) > 60.0:
        q.popleft()
    if len(q) >= max_per_minute:
        return False
    q.append(now)
    return True

def limits_middleware(app):
    @app.before_request
    def _limit_and_size():
        cfg = current_app.config
        ip = request.headers.get("x-forwarded-for", request.remote_addr) or "unknown"

        # apply simple per-IP rate limit for all HTTP requests
        if not _rate_ok(ip, cfg["RATE_LIMIT_PER_IP_MIN"]):
            abort(429)

        # body size caps
        cl = request.content_length or 0
        if request.method in ("POST", "PUT", "PATCH"):
            ct = (request.content_type or "").lower()
            if "application/json" in ct and cl > cfg["MAX_JSON_BODY_BYTES"]:
                abort(413)
            if "multipart/form-data" in ct and cl > cfg["MAX_FORM_BODY_BYTES"]:
                abort(413)