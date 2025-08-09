"""Security utilities for sensitive data handling"""
import os
import base64
import json
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from pathlib import Path
from typing import Optional, Dict, Any
import keyring
import secrets
import re

class SecurityManager:
    """Manages encryption and security for sensitive data"""
    
    def __init__(self):
        self.key_file = Path("config/.key")
        self.salt_file = Path("config/.salt")
        self.cipher = None
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption system"""
        # Ensure config directory exists
        self.key_file.parent.mkdir(exist_ok=True)
        
        # Get or create encryption key
        key = self._get_or_create_key()
        self.cipher = Fernet(key)
    
    def _get_or_create_key(self) -> bytes:
        """Get existing key or create new one"""
        try:
            # Try to get key from system keyring first
            stored_key = keyring.get_password("QuestionAssistant", "encryption_key")
            if stored_key:
                return base64.urlsafe_b64decode(stored_key.encode())
        except:
            pass
        
        # Generate new key if not found
        if not self.key_file.exists():
            key = Fernet.generate_key()
            
            # Store in system keyring if possible
            try:
                keyring.set_password("QuestionAssistant", "encryption_key", 
                                    base64.urlsafe_b64encode(key).decode())
            except:
                # Fallback to file storage with obfuscation
                self._store_key_locally(key)
            
            return key
        else:
            # Read from local file
            return self._read_local_key()
    
    def _store_key_locally(self, key: bytes):
        """Store key locally with obfuscation"""
        # Generate salt for additional security
        salt = secrets.token_bytes(32)
        self.salt_file.write_bytes(salt)
        
        # Obfuscate key before storing
        obfuscated = bytes(a ^ b for a, b in zip(key, salt * 2))
        self.key_file.write_bytes(obfuscated)
        
        # Set file permissions (Windows)
        import stat
        os.chmod(self.key_file, stat.S_IRUSR | stat.S_IWUSR)
        os.chmod(self.salt_file, stat.S_IRUSR | stat.S_IWUSR)
    
    def _read_local_key(self) -> bytes:
        """Read and deobfuscate local key"""
        if not self.salt_file.exists():
            # Old format without salt
            return self.key_file.read_bytes()
        
        salt = self.salt_file.read_bytes()
        obfuscated = self.key_file.read_bytes()
        
        # Deobfuscate
        key = bytes(a ^ b for a, b in zip(obfuscated, salt * 2))
        return key
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not data:
            return ""
        
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return ""
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            # Return as-is if decryption fails (might be unencrypted)
            return encrypted_data
    
    def secure_delete(self, file_path: Path):
        """Securely delete a file"""
        if not file_path.exists():
            return
        
        # Overwrite with random data before deletion
        file_size = file_path.stat().st_size
        with open(file_path, 'wb') as f:
            f.write(secrets.token_bytes(file_size))
        
        # Delete the file
        file_path.unlink()
    
    def hash_password(self, password: str) -> str:
        """Hash a password for storage"""
        salt = secrets.token_bytes(32)
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # Combine salt and hash for storage
        return base64.urlsafe_b64encode(salt + key).decode()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against hash"""
        try:
            decoded = base64.urlsafe_b64decode(hashed.encode())
            salt = decoded[:32]
            stored_hash = decoded[32:]
            
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            new_hash = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            return new_hash == stored_hash
        except:
            return False

class InputValidator:
    """Validates and sanitizes user input"""
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate API key format"""
        if not api_key:
            return False
        
        # Check for common API key patterns
        patterns = [
            r'^sk-[a-zA-Z0-9]{48}$',  # OpenAI format
            r'^[a-zA-Z0-9]{32,}$',     # Generic format
        ]
        
        for pattern in patterns:
            if re.match(pattern, api_key):
                return True
        
        return len(api_key) >= 20  # Minimum length check
    
    @staticmethod
    def sanitize_path(path: str) -> str:
        """Sanitize file path to prevent directory traversal"""
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>:"|?*]', '', path)
        
        # Prevent directory traversal
        sanitized = sanitized.replace('..', '')
        
        # Ensure absolute path
        return str(Path(sanitized).resolve())
    
    @staticmethod
    def validate_duration(duration: int) -> bool:
        """Validate session duration"""
        return 1 <= duration <= 600
    
    @staticmethod
    def sanitize_context(context: str) -> str:
        """Sanitize context input"""
        # Remove potential script tags or code
        sanitized = re.sub(r'<[^>]+>', '', context)
        
        # Limit length
        if len(sanitized) > 500:
            sanitized = sanitized[:500]
        
        return sanitized.strip()

class RateLimiter:
    """Rate limiting for API calls and operations"""
    
    def __init__(self):
        self.limits = {}
        self.attempts = {}
    
    def set_limit(self, operation: str, max_attempts: int, window_seconds: int):
        """Set rate limit for an operation"""
        self.limits[operation] = (max_attempts, window_seconds)
        if operation not in self.attempts:
            self.attempts[operation] = []
    
    def check_limit(self, operation: str) -> bool:
        """Check if operation is within rate limit"""
        if operation not in self.limits:
            return True
        
        max_attempts, window = self.limits[operation]
        now = time.time()
        
        # Clean old attempts
        self.attempts[operation] = [
            t for t in self.attempts[operation] 
            if now - t < window
        ]
        
        # Check limit
        if len(self.attempts[operation]) >= max_attempts:
            return False
        
        # Record attempt
        self.attempts[operation].append(now)
        return True
    
    def get_wait_time(self, operation: str) -> float:
        """Get time to wait before next attempt"""
        if operation not in self.limits:
            return 0
        
        max_attempts, window = self.limits[operation]
        if not self.attempts[operation]:
            return 0
        
        oldest_attempt = min(self.attempts[operation])
        wait_time = window - (time.time() - oldest_attempt)
        
        return max(0, wait_time)

# Global instances
security_manager = SecurityManager()
input_validator = InputValidator()
rate_limiter = RateLimiter()

# Set default rate limits
import time
rate_limiter.set_limit("api_call", max_attempts=60, window_seconds=60)
rate_limiter.set_limit("screenshot", max_attempts=120, window_seconds=60)
rate_limiter.set_limit("detection", max_attempts=100, window_seconds=60)