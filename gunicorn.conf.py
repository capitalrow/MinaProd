# Gunicorn configuration file for Mina with Socket.IO support
# Uses eventlet workers with proper configuration

import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes - use 1 worker for Socket.IO compatibility
workers = 1
worker_class = "eventlet"
worker_connections = 1000
timeout = 60
keepalive = 2

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "mina_app"

# Server mechanics  
preload_app = False  # IMPORTANT: Set to False for Socket.IO
reload = True
reuse_port = True

# Environment variable to detect we're running under Gunicorn
def when_ready(server):
    os.environ['SERVER_SOFTWARE'] = 'gunicorn'
