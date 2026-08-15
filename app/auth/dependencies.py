"""
FastAPI dependencies for authentication.
"""
from typing import Optional
from fastapi import Header, HTTPException, Depends
from .auth_service import get_auth_service, AuthService
from .models import Session, UserRole


async def get_current_user(
    authorization: Optional[str] = Header(None),
    auth_service: AuthService = Depends(get_auth_service)
) -> Session:
    """
    Dependency to get current authenticated user from session token.
    Raises 401 if not authenticated.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_id = authorization.replace("Bearer ", "")
    session = auth_service.validate_session(session_id, update_activity=True)
    
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    
    return session


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory to require specific user role(s).
    Usage: Depends(require_role(UserRole.ADMIN))
    """
    async def role_checker(
        current_user: Session = Depends(get_current_user)
    ) -> Session:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required role: {', '.join(r.value for r in allowed_roles)}"
            )
        return current_user
    
    return role_checker
