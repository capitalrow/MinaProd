# cli.py — Flask CLI app for Alembic/Flask-Migrate only
import os
from app_refactored import create_app, db  # uses the same factory as your server

# IMPORTANT: do NOT import or initialize socketio/eventlet here.
# We want a plain Flask app so Flask CLI can manage app/app_context properly.

app = create_app()

# If you need shell context (optional):
@app.shell_context_processor
def make_shell_context():
    from models import Meeting, Summary, Task  # exported by models/__init__.py
    return {"db": db, "Meeting": Meeting, "Summary": Summary, "Task": Task}