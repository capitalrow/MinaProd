# wsgi.py — production/server entry; uses the same create_app()
# This is what gunicorn/eventlet runs. We keep monkey_patch **here** only.
import eventlet
eventlet.monkey_patch()

from app_refactored import create_app, socketio  # your existing socket/socketio instance

app = create_app()

# If you run with "python wsgi.py" for dev:
if __name__ == "__main__":
    # eventlet web server via socketio for local tests (optional)
    # Avoid using this on Replit if you already use gunicorn -k eventlet
    socketio.run(app, host="0.0.0.0", port=8000)