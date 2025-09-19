# scripts/create_tables.py
from pathlib import Path
import os, sys

# Ensure project root is on the import path (so we can import app_refactored)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app_refactored import create_app, db  # <-- this file is at project root

app = create_app()
with app.app_context():
    db.create_all()
    print("✅ Tables created in SQLite:", os.getenv("DATABASE_URL"))