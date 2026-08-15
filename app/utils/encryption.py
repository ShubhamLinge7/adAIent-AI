"""
Password encryption utilities using AES-256.
Allows reversible encryption for admin password viewing.
"""
from cryptography.fernet import Fernet
import base64
import hashlib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Encryption key storage
KEY_FILE = Path(__file__).parent.parent.parent / "data" / "encryption.key"


def get_or_create_key() -> bytes:
    """
    Get existing encryption key or create new one.
    Key is stored in data/encryption.key file.
    """
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    if KEY_FILE.exists():
        with open(KEY_FILE, 'rb') as f:
            return f.read()
    else:
        # Generate new key
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
        logger.info(f"Generated new encryption key: {KEY_FILE}")
        return key


def encrypt_password(password: str) -> str:
    """
    Encrypt password using AES-256.
    Returns base64 encoded encrypted password.
    """
    key = get_or_create_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(password.encode())
    return base64.b64encode(encrypted).decode()


def decrypt_password(encrypted_password: str) -> str:
    """
    Decrypt password from base64 encoded encrypted string.
    Returns original plaintext password.
    """
    try:
        key = get_or_create_key()
        fernet = Fernet(key)
        encrypted_bytes = base64.b64decode(encrypted_password.encode())
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Failed to decrypt password: {e}")
        raise ValueError("Failed to decrypt password")


def hash_password(password: str) -> str:
    """
    Create SHA-256 hash for password verification (one-way).
    Used for backward compatibility and additional security layer.
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, encrypted_password: str) -> bool:
    """
    Verify password against encrypted stored password.
    """
    try:
        decrypted = decrypt_password(encrypted_password)
        return password == decrypted
    except:
        return False
