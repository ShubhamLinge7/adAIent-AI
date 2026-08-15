"""
Authentication module for adAIent.
Handles user login, session management, and authorization.
"""

from .models import User, Session, AuditLog
from .auth_service import AuthService, get_auth_service
from .dependencies import get_current_user, require_role

__all__ = [
    "User",
    "Session",
    "AuditLog",
    "AuthService",
    "get_auth_service",
    "get_current_user",
    "require_role"
]
