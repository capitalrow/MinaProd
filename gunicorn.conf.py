# Gunicorn configuration file for Mina with Socket.IO support
# Uses eventlet workers with proper configuration

import os

# Note: monkey_patch is handled automatically by gunicorn eventlet worker

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
reload = False  # Set to False for production
reuse_port = True

# Environment variable to detect we're running under Gunicorn
def when_ready(server):
    os.environ['SERVER_SOFTWARE'] = 'gunicorn'
    server.log.info("Mina transcription service is ready to accept connections")

def on_exit(server):
    server.log.info("Mina transcription service shutting down")