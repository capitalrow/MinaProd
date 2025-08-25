# Production-ready Gunicorn configuration for Flask-SocketIO
# Based on industry best practices from research

import eventlet
eventlet.monkey_patch()

# Server socket
bind = "0.0.0.0:5000"

# Worker configuration - CRITICAL: Single worker required for Flask-SocketIO
worker_class = "eventlet"
workers = 1  # MUST be 1 for Flask-SocketIO
worker_connections = 1000

# Timeout settings optimized for WebSocket connections
timeout = 300  # 5 minutes for long-running connections
keepalive = 5  # Keep connections alive
graceful_timeout = 60

# Request limits
max_requests = 1000
max_requests_jitter = 100

# Process management
preload_app = True
reload = True

# Logging
loglevel = 'info'
accesslog = '-'
errorlog = '-'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# SSL (if needed)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'