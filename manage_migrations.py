#!/usr/bin/env python3
"""
Database migration management script for Mina
Uses Flask-Migrate (Alembic) for safe database schema changes
"""

import sys
from app import create_app, socketio
from models import db
from flask_migrate import Migrate, init, migrate, upgrade, downgrade

# Create Flask app
app = create_app()

# Initialize Flask-Migrate
migrate_obj = Migrate(app, db)

def run_command(command, *args):
    """Run a Flask-Migrate command"""
    with app.app_context():
        if command == "init":
            print("Initializing migration repository...")
            init()
        elif command == "migrate":
            message = args[0] if args else "Auto-generated migration"
            print(f"Creating new migration: {message}")
            migrate(message=message)
        elif command == "upgrade":
            print("Upgrading database to latest version...")
            upgrade()
        elif command == "downgrade":
            print("Downgrading database one revision...")
            downgrade()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: init, migrate, upgrade, downgrade")
            sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manage_migrations.py <command> [args]")
        print("Commands:")
        print("  init              - Initialize migrations directory")
        print("  migrate [message] - Create a new migration")
        print("  upgrade           - Apply migrations to database")
        print("  downgrade         - Revert last migration")
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    run_command(command, *args)
