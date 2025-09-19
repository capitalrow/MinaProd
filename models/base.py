"""
SQLAlchemy Base Model
Base class for all models using SQLAlchemy 2.0 declarative mapping.
"""

from sqlalchemy.orm import DeclarativeBase
from extensions import db

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass