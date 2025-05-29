"""
Dependencies package initialization.
This package contains all the FastAPI dependencies used across the application.
"""

from .database import get_db
from .auth import get_current_user

__all__ = ["get_db", "get_current_user"] 