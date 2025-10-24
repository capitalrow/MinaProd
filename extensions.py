"""
Flask extensions and shared instances.
Provides centralized access to database and other extensions.
"""

from models import db

__all__ = ['db']
