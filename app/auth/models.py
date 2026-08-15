"""
Database models for authentication.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from enum import Enum


class UserRole(str, Enum):
    """User role definitions"""
    SUPERADMIN = "superadmin"  # Developer account - full access
    ADMIN = "admin"            # Company admin - manage users/manuals
    TECHNICIAN = "technician"  # Regular user - chat only


class User(BaseModel):
    """User model"""
    id: Optional[int] = None
    username: str
    password_hash: str
    role: UserRole
    created_at: datetime = datetime.now()
    last_login: Optional[datetime] = None
    is_locked: bool = False  # Locked accounts cannot be deleted
    is_active: bool = True
    
    class Config:
        use_enum_values = True


class Session(BaseModel):
    """User session model"""
    session_id: str
    user_id: int
    username: str
    role: UserRole
    created_at: datetime = datetime.now()
    last_activity: datetime = datetime.now()
    expires_at: datetime
    ip_address: Optional[str] = None
    
    class Config:
        use_enum_values = True


class AuditLog(BaseModel):
    """Audit log entry"""
    id: Optional[int] = None
    timestamp: datetime = datetime.now()
    user_id: int
    username: str
    role: UserRole
    action: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    is_dev_access: bool = False  # Mark if accessed by superadmin
    target_user_id: Optional[int] = None  # ID of user affected by this action
    target_username: Optional[str] = None  # Username of user affected by this action
    
    class Config:
        use_enum_values = True


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    """Login response model"""
    success: bool
    session_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[UserRole] = None
    message: Optional[str] = None
    
    class Config:
        use_enum_values = True


class CreateUserRequest(BaseModel):
    """Create user request"""
    username: str
    password: str
    role: UserRole
    
    class Config:
        use_enum_values = True


class UserInfo(BaseModel):
    """User information (without password)"""
    id: int
    username: str
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    
    class Config:
        use_enum_values = True
