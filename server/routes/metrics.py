# server/routes/metrics.py
from flask import Blueprint, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time

metrics_bp = Blueprint("metrics", __name__)

# --- Prometheus metrics ---
REQUEST_COUNT = Counter("mina_requests_total", "Total API requests processed", ["method", "endpoint"])
REQUEST_LATENCY = Histogram("mina_request_latency_seconds", "Request latency (seconds)", ["endpoint"])
WEBSOCKET_CONNECTIONS = Gauge("mina_ws_connections", "Number of active WebSocket connections")
AUDIO_CHUNKS_PROCESSED = Counter("mina_audio_chunks_processed_total", "Total audio chunks processed")
ERROR_COUNT = Counter("mina_errors_total", "Total number of errors", ["endpoint", "status_code"])

# --- Middleware-style helpers ---
def track_request(endpoint):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            REQUEST_COUNT.labels(method="GET", endpoint=endpoint).inc()
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                ERROR_COUNT.labels(endpoint=endpoint, status_code=500).inc()
                raise e
            finally:
                elapsed = time.time() - start_time
                REQUEST_LATENCY.labels(endpoint=endpoint).observe(elapsed)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

@metrics_bp.route("/internal/metrics")
def internal_metrics():
    try:
        data = generate_latest()
        return Response(data, mimetype=CONTENT_TYPE_LATEST)
    except Exception as e:
        app.logger.error(f"Metrics endpoint error: {e}", exc_info=True)
        return jsonify({"error": "metrics_unavailable"}), 500