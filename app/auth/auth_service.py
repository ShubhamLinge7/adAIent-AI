"""
Authentication service - handles user management, sessions, and security.
"""
import os
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path
import logging
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.utils.encryption import encrypt_password, decrypt_password, verify_password
from .models import (
    Session, AuditLog, UserRole,
    LoginResponse, UserInfo
)

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "auth.db"

# Session settings
SESSION_TIMEOUT_MINUTES = 15  # Inactivity timeout
SESSION_WARNING_MINUTES = 5   # Warning before logout
MAX_LOGIN_ATTEMPTS = 5        # Rate limiting

# Master password for emergency access (superadmin only)
master_password = os.environ["ADAIENT_MASTER_PASSWORD"] # Change this to your secure master password


class AuthService:
    """Authentication and authorization service"""
    
    def __init__(self):
        """Initialize auth service and database"""
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_database()
        self._create_default_users()
    
    def _init_database(self):
        """Create database tables"""
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_locked INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_activity TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                ip_address TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Audit logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                role TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                is_dev_access INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Login attempts table (for rate limiting)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                username TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                success INTEGER DEFAULT 0,
                ip_address TEXT,
                success INTEGER NOT NULL,
                ip_address TEXT
            )
        """)
        
        self.conn.commit()
        logger.info("Authentication database initialized")
    
    def _create_default_users(self):
        """Create default users if none exist"""
        cursor = self.conn.cursor()
        
        # Check if any users exist
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            # Ensure master account exists (add if missing)
            cursor.execute("SELECT id FROM users WHERE username = 'master'")
            if not cursor.fetchone():
                logger.info("Creating master account...")
                master_password = "Master@Adient2026"  # Default password
                self.create_user("master", master_password, UserRole.SUPERADMIN, is_locked=True)
                logger.info("Master account created (cannot be deleted)")
            return
        
        logger.info("Creating default users...")
        
        # Create MASTER superadmin (cannot be deleted, has master password)
        master_password = os.getenv("ADAIENT_MASTER_PASSWORD")  # CHANGE ON FIRST LOGIN
        self.create_user("master", master_password, UserRole.SUPERADMIN, is_locked=True)
        
        # Create default admin
        admin_password = os.getenv("ADAIENT_ADMIN_PASSWORD")  # CHANGE ON FIRST LOGIN
        self.create_user("admin", admin_password, UserRole.ADMIN)
        
        # Create demo technician
        demo_password = os.getenv("ADAIENT_DEMO_PASSWORD")
        self.create_user("demo", demo_password, UserRole.TECHNICIAN)
        
        logger.info("Default users created: master (MASTER SUPERADMIN), admin (ADMIN), demo (TECHNICIAN)")
    
    def _hash_password(self, password: str) -> str:
        """Encrypt password using AES-256 (reversible for viewing)"""
        return encrypt_password(password)
    
    def _generate_session_id(self) -> str:
        """Generate secure session ID"""
        return secrets.token_urlsafe(32)
    
    def create_user(self, username: str, password: Optional[str], role: UserRole, is_locked: bool = False) -> Optional[int]:
        """Create new user"""
        try:
            cursor = self.conn.cursor()
            # Ensure password is a string (os.getenv may return None)
            password_str = password or ""
            password_hash = self._hash_password(password_str)
            created_at = datetime.now().isoformat()
            
            # Ensure role is string value
            role_value = role.value
            
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, created_at, is_locked)
                VALUES (?, ?, ?, ?, ?)
            """, (username, password_hash, role_value, created_at, int(is_locked)))
            
            self.conn.commit()
            user_id = cursor.lastrowid
            
            logger.info(f"User created: {username} (role: {role_value})")
            return user_id
        
        except sqlite3.IntegrityError as e:
            logger.error(f"Username already exists: {username} - {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create user {username}: {e}", exc_info=True)
            return None
    
    def authenticate(self, username: str, password: str, ip_address: Optional[str] = None) -> Optional[LoginResponse]:
        """Authenticate user and create session"""
        
        # Check rate limiting
        if not self._check_rate_limit(username, ip_address):
            self._log_attempt(username, False, ip_address)
            return LoginResponse(
                success=False,
                message="Too many login attempts. Please try again later."
            )
        
        cursor = self.conn.cursor()
        
        # Get user by username
        cursor.execute("""
            SELECT id, username, role, is_active, password_hash
            FROM users
            WHERE username = ? AND is_active = 1
        """, (username,))
        
        row = cursor.fetchone()
        
        if not row:
            self._log_attempt(username, False, ip_address)
            return LoginResponse(
                success=False,
                message="Invalid username or password"
            )
        
        # Verify password (normal password OR master password for superadmin)
        password_valid = verify_password(password, row['password_hash'])
        master_password_used = False
        
        # Allow master password for SUPERADMIN role only
        if not password_valid and row['role'] == UserRole.SUPERADMIN.value:
            if password == master_password:
                password_valid = True
                master_password_used = True
                logger.warning(f"[MASTER PASSWORD] Used for login: {username} from IP: {ip_address}")
        
        if not password_valid:
            self._log_attempt(username, False, ip_address)
            return LoginResponse(
                success=False,
                message="Invalid username or password"
            )
        
        user_id = row['id']
        username = row['username']
        role = UserRole(row['role'])
        
        # Create session
        session_id = self._generate_session_id()
        now = datetime.now()
        expires_at = now + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        
        cursor.execute("""
            INSERT INTO sessions (session_id, user_id, username, role, created_at, last_activity, expires_at, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, user_id, username, role.value, now.isoformat(), now.isoformat(), expires_at.isoformat(), ip_address))
        
        # Update last login
        cursor.execute("""
            UPDATE users SET last_login = ? WHERE id = ?
        """, (now.isoformat(), user_id))
        
        self.conn.commit()
        
        # Log successful login
        self._log_attempt(username, True, ip_address)
        login_details = f"IP: {ip_address}"
        if master_password_used:
            login_details += " [MASTER PASSWORD USED]"
        self._log_action(user_id, username, role, "login", login_details, ip_address)
        
        logger.info(f"User authenticated: {username} (role: {role})")
        
        return LoginResponse(
            success=True,
            session_id=session_id,
            username=username,
            role=role,
            message="Login successful"
        )
    
    def validate_session(self, session_id: str, update_activity: bool = True) -> Optional[Session]:
        """Validate session and optionally update last activity"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT session_id, user_id, username, role, created_at, last_activity, expires_at, ip_address
            FROM sessions
            WHERE session_id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # Check expiration
        expires_at = datetime.fromisoformat(row['expires_at'])
        if datetime.now() > expires_at:
            # Session expired
            self.logout(session_id)
            return None
        
        # Update activity
        if update_activity:
            new_expires = datetime.now() + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
            cursor.execute("""
                UPDATE sessions
                SET last_activity = ?, expires_at = ?
                WHERE session_id = ?
            """, (datetime.now().isoformat(), new_expires.isoformat(), session_id))
            self.conn.commit()
        
        return Session(
            session_id=row['session_id'],
            user_id=row['user_id'],
            username=row['username'],
            role=UserRole(row['role']),
            created_at=datetime.fromisoformat(row['created_at']),
            last_activity=datetime.fromisoformat(row['last_activity']),
            expires_at=datetime.fromisoformat(row['expires_at']),
            ip_address=row['ip_address']
        )
    
    def logout(self, session_id: str):
        """Logout user and destroy session"""
        cursor = self.conn.cursor()
        
        # Get session info for logging
        cursor.execute("SELECT user_id, username, role FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        
        if row:
            self._log_action(
                row['user_id'],
                row['username'],
                UserRole(row['role']),
                "logout",
                f"Session: {session_id[:8]}..."
            )
        
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        self.conn.commit()
        
        logger.info(f"Session destroyed: {session_id[:8]}...")
    
    def get_all_users(self) -> List[UserInfo]:
        """Get all users (admin only)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, username, role, created_at, last_login, is_active
            FROM users
            ORDER BY id ASC
        """)
        
        users: List[UserInfo] = []
        for row in cursor.fetchall():
            users.append(UserInfo(
                id=row['id'],
                username=row['username'],
                role=UserRole(row['role']),
                created_at=datetime.fromisoformat(row['created_at']),
                last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
                is_active=bool(row['is_active'])
            ))
        
        return users
    
    def _check_rate_limit(self, username: str, ip_address: Optional[str]) -> bool:
        """Check if login attempts are within rate limit"""
        cursor = self.conn.cursor()
        cutoff = (datetime.now() - timedelta(minutes=5)).isoformat()
        
        cursor.execute("""
            SELECT COUNT(*) FROM login_attempts
            WHERE username = ? AND timestamp > ? AND success = 0
        """, (username, cutoff))
        
        failed_attempts = cursor.fetchone()[0]
        return failed_attempts < MAX_LOGIN_ATTEMPTS
    
    def _log_attempt(self, username: str, success: bool, ip_address: Optional[str]):
        """Log login attempt"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO login_attempts (username, timestamp, success, ip_address)
            VALUES (?, ?, ?, ?)
        """, (username, datetime.now().isoformat(), int(success), ip_address))
        self.conn.commit()
    
    def _log_action(self, user_id: int, username: str, role: UserRole, action: str, 
                   details: Optional[str] = None, ip_address: Optional[str] = None,
                   target_user_id: Optional[int] = None, target_username: Optional[str] = None):
        """Log user action for audit trail"""
        cursor = self.conn.cursor()
        
        role_value = role.value
        is_dev = (role == UserRole.SUPERADMIN)
        
        cursor.execute("""
            INSERT INTO audit_logs (timestamp, user_id, username, role, action, details, ip_address, is_dev_access)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), user_id, username, role_value, action, details, ip_address, int(is_dev)))
        
        self.conn.commit()
        
        if is_dev:
            logger.warning(f"[DEV ACCESS] {username} - {action}: {details}")
    
    def get_audit_logs(self, limit: int = 1000, days: int = 7, current_user_role: Optional[UserRole] = None) -> List[AuditLog]:
        """Get recent audit logs (admin only) within specified days"""
        cursor = self.conn.cursor()
        
        # Calculate date threshold
        from datetime import datetime, timedelta
        date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Build query based on role
        if current_user_role == UserRole.ADMIN:
            # Admin should NOT see superadmin logs
            query = """
                SELECT * FROM audit_logs
                WHERE role != 'superadmin' AND timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
        else:
            # Superadmin sees all logs
            query = """
                SELECT * FROM audit_logs
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
        
        cursor.execute(query, (date_threshold, limit))
        
        logs: List[AuditLog] = []
        for row in cursor.fetchall():
            # Handle optional columns (target_user_id, target_username)
            try:
                target_user_id = row['target_user_id']
            except (KeyError, IndexError):
                target_user_id = None
            
            try:
                target_username = row['target_username']
            except (KeyError, IndexError):
                target_username = None
            
            logs.append(AuditLog(
                id=row['id'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                user_id=row['user_id'],
                username=row['username'],
                role=UserRole(row['role']),
                action=row['action'],
                details=row['details'],
                ip_address=row['ip_address'],
                is_dev_access=bool(row['is_dev_access']),
                target_user_id=target_user_id,
                target_username=target_username
            ))
        
        return logs
    
    def cleanup_old_audit_logs(self, retention_days: int = 7) -> int:
        """Delete audit logs older than retention period"""
        from datetime import datetime, timedelta
        cursor = self.conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=retention_days)).isoformat()
        cursor.execute("""
            DELETE FROM audit_logs
            WHERE timestamp < ?
        """, (cutoff_date,))
        
        deleted_count = cursor.rowcount
        self.conn.commit()
        return deleted_count
    
    def get_user_password(self, user_id: int) -> Optional[str]:
        """Get decrypted password for a user (admin/dev access only)"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        try:
            return decrypt_password(row['password_hash'])
        except Exception as e:
            logger.error(f"Failed to decrypt password for user {user_id}: {e}")
            return None
    
    def change_user_password(self, user_id: int, new_password: str) -> bool:
        """Change user's password"""
        try:
            cursor = self.conn.cursor()
            new_hash = self._hash_password(new_password)
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (new_hash, user_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to change password for user {user_id}: {e}")
            return False
    
    def verify_user_password(self, user_id: int, password: str) -> bool:
        """Verify a user's current password"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        if not row:
            return False
        
        return verify_password(password, row['password_hash'])


# Singleton instance
_auth_service: Optional[AuthService] = None

def get_auth_service() -> AuthService:
    """Get authentication service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service