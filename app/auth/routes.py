"""
Authentication API endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException
from typing import List
from pydantic import BaseModel

from .models import (
    LoginRequest, LoginResponse, CreateUserRequest,
    UserInfo, AuditLog, UserRole
)
from .auth_service import get_auth_service, AuthService, SESSION_WARNING_MINUTES
from .dependencies import get_current_user, require_role
from .models import Session

router = APIRouter(prefix="/auth", tags=["Authentication"])


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str
    new_password: str


class ResetPasswordRequest(BaseModel):
    """Reset user password request"""
    new_password: str


class PasswordResponse(BaseModel):
    """Password view response"""
    user_id: int
    username: str
    password: str


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    credentials: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    User login endpoint.
    Returns session token on success.
    """
    ip_address = request.client.host if request.client else None
    
    response = auth_service.authenticate(
        credentials.username,
        credentials.password,
        ip_address
    )
    
    if not response.success:
        raise HTTPException(status_code=401, detail=response.message)
    
    return response


@router.post("/logout")
async def logout(
    current_user: Session = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    User logout endpoint.
    Destroys current session.
    """
    auth_service.logout(current_user.session_id)
    return {"message": "Logged out successfully"}


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: Session = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Change own password. All users can change their own password.
    """
    # Verify current password
    if not auth_service.verify_user_password(current_user.user_id, request.current_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    
    # Validate new password
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Change password
    if not auth_service.change_user_password(current_user.user_id, request.new_password):
        raise HTTPException(status_code=500, detail="Failed to change password")
    
    # Log the action
    auth_service._log_action(
        current_user.user_id,
        current_user.username,
        current_user.role,
        "change_password",
        "User changed their password"
    )
    
    return {"message": "Password changed successfully"}


@router.get("/me", response_model=Session)
async def get_current_user_info(
    current_user: Session = Depends(get_current_user)
):
    """
    Get current user info from session.
    """
    return current_user


@router.post("/validate")
async def validate_session(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Validate session without extending expiry.
    Returns remaining time until auto-logout.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_id = auth_header.replace("Bearer ", "")
    session = auth_service.validate_session(session_id, update_activity=False)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    
    remaining_seconds = int((session.expires_at - datetime.now()).total_seconds())
    warning_seconds = SESSION_WARNING_MINUTES * 60
    
    return {
        "valid": True,
        "username": session.username,
        "role": session.role,
        "remaining_seconds": max(0, remaining_seconds),
        "warning_seconds": warning_seconds
    }


@router.get("/users", response_model=List[UserInfo])
async def get_users(
    current_user: Session = Depends(require_role(UserRole.ADMIN, UserRole.SUPERADMIN)),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get all users (Admin only).
    """
    return auth_service.get_all_users()


@router.post("/users", response_model=UserInfo)
async def create_user(
    user_data: CreateUserRequest,
    current_user: Session = Depends(require_role(UserRole.ADMIN, UserRole.SUPERADMIN)),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Create new user (Admin only).
    """
    try:
        # Ensure role is UserRole enum
        if isinstance(user_data.role, str):
            user_data.role = UserRole(user_data.role)
        
        user_id = auth_service.create_user(
            user_data.username,
            user_data.password,
            user_data.role
        )
        
        if not user_id:
            raise HTTPException(status_code=400, detail="Username already exists or creation failed")
        
        # Log the action
        role_str = user_data.role.value if isinstance(user_data.role, UserRole) else str(user_data.role)
        auth_service._log_action(
            current_user.user_id,
            current_user.username,
            current_user.role,
            "create_user",
            f"Created user: {user_data.username} (role: {role_str})"
        )
        
        # Return created user info
        users = auth_service.get_all_users()
        for user in users:
            if user.id == user_id:
                return user
        
        raise HTTPException(status_code=500, detail="User created but could not retrieve info")
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid role: {str(e)}")
    except Exception as e:
        import logging
        logging.error(f"Error creating user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.get("/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(
    limit: int = 1000,
    days: int = 7,
    current_user: Session = Depends(require_role(UserRole.ADMIN, UserRole.SUPERADMIN)),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get audit logs (Admin only) within the specified number of days.
    Admin sees only non-superadmin logs, Superadmin sees all logs.
    """
    # Get user role for filtering
    cursor = auth_service.conn.cursor()
    cursor.execute("SELECT role FROM users WHERE id = ?", (current_user.user_id,))
    user_role = UserRole(cursor.fetchone()['role'])
    
    return auth_service.get_audit_logs(limit, days, user_role)


@router.get("/stats")
async def get_stats(
    current_user: Session = Depends(require_role(UserRole.ADMIN, UserRole.SUPERADMIN)),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get system statistics (Admin only).
    """
    import sqlite3
    from datetime import datetime, timedelta
    
    conn = auth_service.conn
    cursor = conn.cursor()
    
    # Get current user role
    cursor.execute("SELECT role FROM users WHERE id = ?", (current_user.user_id,))
    user_role = cursor.fetchone()['role']
    is_superadmin = (user_role == UserRole.SUPERADMIN.value)
    
    # Total users
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    total_users = cursor.fetchone()[0]
    
    # Active sessions today
    today = datetime.now().date().isoformat()
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM sessions WHERE DATE(last_activity) = ?", (today,))
    active_today = cursor.fetchone()[0]
    
    # Total queries (from audit logs)
    cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE action LIKE '%question%' OR action LIKE '%chat%'")
    total_queries = cursor.fetchone()[0]
    
    # Recent activity (last hour)
    one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
    cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE timestamp > ?", (one_hour_ago,))
    recent_activity = cursor.fetchone()[0]
    
    return {
        "total_users": total_users,
        "active_today": active_today,
        "total_queries": total_queries,
        "recent_activity": recent_activity,
        "active_sessions": active_today,
        "total_actions": total_queries + recent_activity,
        "access_level": "superadmin" if is_superadmin else "admin"
    }


@router.get("/users/{user_id}/password", response_model=PasswordResponse)
async def view_user_password(
    user_id: int,
    current_user: Session = Depends(require_role(UserRole.ADMIN, UserRole.SUPERADMIN)),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    View user's password (decrypted):
    - SUPERADMIN: can view technicians and admins (not other superadmins)
    - ADMIN: can view only technicians
    """
    import sqlite3
    
    conn = auth_service.conn
    cursor = conn.cursor()
    
    cursor.execute("SELECT username, role FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    username, role = user
    
    # Check permissions
    if current_user.role == UserRole.ADMIN:
        if role != UserRole.TECHNICIAN.value:
            raise HTTPException(status_code=403, detail="Admin can only view technician passwords")
    else:  # SUPERADMIN
        if role == UserRole.SUPERADMIN.value:
            raise HTTPException(status_code=403, detail="Cannot view other superadmin passwords")
    
    # Get decrypted password
    password = auth_service.get_user_password(user_id)
    if not password:
        raise HTTPException(status_code=500, detail="Failed to retrieve password")
    
    # Log the action
    auth_service._log_action(
        current_user.user_id,
        current_user.username,
        current_user.role,
        "view_password",
        f"Viewed password for user: {username} (role: {role})",
        target_user_id=user_id,
        target_username=username
    )
    
    return PasswordResponse(
        user_id=user_id,
        username=username,
        password=password
    )


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    request: ResetPasswordRequest,
    current_user: Session = Depends(require_role(UserRole.ADMIN, UserRole.SUPERADMIN)),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Reset user's password:
    - SUPERADMIN: can reset technicians and admins (not other superadmins)
    - ADMIN: can reset only technicians
    """
    import sqlite3
    
    conn = auth_service.conn
    cursor = conn.cursor()
    
    cursor.execute("SELECT username, role FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    username, role = user
    
    # Check permissions
    if current_user.role == UserRole.ADMIN:
        if role != UserRole.TECHNICIAN.value:
            raise HTTPException(status_code=403, detail="Admin can only reset technician passwords")
    else:  # SUPERADMIN
        if role == UserRole.SUPERADMIN.value:
            raise HTTPException(status_code=403, detail="Cannot reset other superadmin passwords")
    
    # Validate new password
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Change password
    if not auth_service.change_user_password(user_id, request.new_password):
        raise HTTPException(status_code=500, detail="Failed to reset password")
    
    # Log the action
    auth_service._log_action(
        current_user.user_id,
        current_user.username,
        current_user.role,
        "reset_password",
        f"Reset password for user: {username} (role: {role})",
        target_user_id=user_id,
        target_username=username
    )
    
    return {
        "message": f"Password reset successfully for user '{username}'",
        "new_password": request.new_password  # Return so admin can share it
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: Session = Depends(require_role(UserRole.ADMIN, UserRole.SUPERADMIN)),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Delete a user (Admin only). Cannot delete developer account.
    """
    import sqlite3
    
    conn = auth_service.conn
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT username, role FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    username, role = user
    
    # Prevent deleting master account
    if username == "master":
        raise HTTPException(status_code=403, detail="Cannot delete master account")
    
    # Delete user
    try:
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        conn.commit()
        
        # Log the action
        auth_service._log_action(
            user_id=current_user.user_id,
            username=current_user.username,
            action=f"DELETED USER: {username} (role: {role})",
            role=current_user.role
        )
        
        return {"message": f"User '{username}' deleted successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")
