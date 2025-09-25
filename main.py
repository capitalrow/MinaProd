# main.py
import os
from app_refactored import create_app, socketio

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    host = "0.0.0.0"
    if socketio:
        socketio.run(app, host=host, port=port)
    else:
        app.run(host=host, port=port, debug=False)