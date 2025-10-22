"""
Compatibility shim for legacy tests and scripts.

Exposes `create_app`, `db`, and `socketio` from `legacy.app_refactored` at the
repository root as `app_refactored`.
"""

from legacy.app_refactored import create_app, db, socketio  # re-export

__all__ = ["create_app", "db", "socketio"]
