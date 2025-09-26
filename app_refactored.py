"""
Mina — Flask app factory with Socket.IO
"""
from flask import Flask
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config

# One global Socket.IO
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="eventlet",
    ping_interval=25,
    ping_timeout=60,
    logger=False,
    engineio_logger=False,
)

def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    # init socket once
    socketio.init_app(app)

    # register HTTP routes
    from routes.http import http_bp
    app.register_blueprint(http_bp)

    # import WS handlers so decorators bind
    import routes.websocket  # noqa: F401

    return app