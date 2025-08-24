"""
Mina Middleware Package
Middleware components for request processing, CORS, authentication, etc.
"""

from .cors import configure_cors

__all__ = ['configure_cors']
