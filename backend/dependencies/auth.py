"""
Authentication dependencies module.
This module provides authentication-related dependencies for FastAPI.
"""

from backend.utils.auth import get_current_user

__all__ = ["get_current_user"] 