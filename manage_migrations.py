#!/usr/bin/env python3
"""
Database migration management script for Mina
Uses Flask-Migrate (Alembic) for safe database schema changes

This script uses a lightweight app factory that initializes only the database,
avoiding heavy subsystems like Socket.IO, middleware, and background services.
"""

import os
import sys
from flask import Flask
from models import db
from flask_migrate import Migrate, init, migrate, upgrade, downgrade, current, stamp, history
from config import Config


def create_migration_app():
    """
    Create a minimal Flask app for database migrations.
    Only initializes database and configuration - no Socket.IO, no middleware, no services.
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Set session secret (required by Flask)
    app.secret_key = os.environ.get("SESSION_SECRET") or "migration-secret-key"
    
    # Database configuration
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Initialize database
    db.init_app(app)
    
    # Import all models to ensure they're registered with db.metadata for autogeneration
    # This is critical for flask-migrate's autogeneration to detect model changes
    with app.app_context():
        import models  # noqa: F401 - Importing for side effects (model registration)
    
    return app


# Create minimal app for migrations
app = create_migration_app()

# Initialize Flask-Migrate
migrate_obj = Migrate(app, db)


def run_command(command, *args):
    """Run a Flask-Migrate command"""
    with app.app_context():
        if command == "init":
            print("Initializing migration repository...")
            init()
            print("✅ Migration repository initialized at: migrations/")
            
        elif command == "migrate":
            message = args[0] if args else "Auto-generated migration"
            print(f"Creating new migration: {message}")
            migrate(message=message)
            print("✅ Migration created. Review the file in migrations/versions/ before applying.")
            
        elif command == "upgrade":
            revision = args[0] if args else "head"
            print(f"Upgrading database to: {revision}")
            upgrade(revision=revision)
            print("✅ Database upgraded successfully")
            
        elif command == "downgrade":
            revision = args[0] if args else "-1"
            print(f"Downgrading database to: {revision}")
            downgrade(revision=revision)
            print("✅ Database downgraded successfully")
            
        elif command == "current":
            print("Current database migration version:")
            current(verbose=True)
            
        elif command == "stamp":
            revision = args[0] if args else "head"
            print(f"Stamping database to revision: {revision}")
            stamp(revision=revision)
            print("✅ Database stamped successfully")
            
        elif command == "history":
            print("Migration history:")
            history(verbose=True)
            
        else:
            print(f"Unknown command: {command}")
            print_usage()
            sys.exit(1)


def print_usage():
    """Print usage information"""
    print("\nUsage: python manage_migrations.py <command> [args]")
    print("\nCommands:")
    print("  current                    - Show current migration version")
    print("  migrate [message]          - Create new migration (auto-detected from models)")
    print("  upgrade [revision]         - Apply migrations (default: head)")
    print("  downgrade [revision]       - Revert migrations (default: -1)")
    print("  stamp [revision]           - Mark database as at specific version without running migrations")
    print("  history                    - Show migration history")
    print("  init                       - Initialize migrations directory (first-time setup)")
    print("\nExamples:")
    print("  python manage_migrations.py current")
    print("  python manage_migrations.py migrate 'Add user email verification'")
    print("  python manage_migrations.py upgrade")
    print("  python manage_migrations.py upgrade 6f9f2dd343f5")
    print("  python manage_migrations.py downgrade")
    print("  python manage_migrations.py downgrade -1")
    print("  python manage_migrations.py stamp head")
    print("  python manage_migrations.py history")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    try:
        run_command(command, *args)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
