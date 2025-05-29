"""
Database dependencies module.
This module provides database-related dependencies for FastAPI.
"""

from backend.db.session import get_db

__all__ = ["get_db"] 