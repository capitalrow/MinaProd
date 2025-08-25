# Gunicorn configuration for stable WebSocket support
import eventlet
eventlet.monkey_patch()

# Server configuration
bind = "0.0.0.0:5000"
worker_class = "eventlet"  # Use eventlet workers for WebSocket support
workers = 1  # Single worker for Socket.IO compatibility
worker_connections = 1000
timeout = 120  # Longer timeout for WebSocket connections
keepalive = 2
preload_app = True
reload = True

# Logging
accesslog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'