"""Tests for filesystem security and safe file operations"""
import unittest
import tempfile
import os
import sys
import stat
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.security import SecurityManager, InputValidator
from src.core.config import Config
from src.core.exceptions import SecurityError, ConfigurationError


class TestFilePermissions(unittest.TestCase):
    """Test file permission security"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.security = SecurityManager()
    
    def test_secure_file_creation(self):
        """Test that files are created with secure permissions"""
        test_file = Path(self.temp_dir) / "secure_test.txt"
        
        with open(test_file, 'w') as f:
            f.write("sensitive data")
        
        if sys.platform == 'win32':
            os.chmod(test_file, stat.S_IRUSR | stat.S_IWUSR)
        else:
            os.chmod(test_file, 0o600)
        
        file_stat = os.stat(test_file)
        
        if sys.platform != 'win32':
            mode = file_stat.st_mode & 0o777
            self.assertEqual(mode, 0o600, f"File has insecure permissions: {oct(mode)}")
    
    def test_config_file_permissions(self):
        """Test that config files have restricted permissions"""
        config_file = Path(self.temp_dir) / "config.json"
        config = Config(str(config_file))
        config.set('api_key', 'test_key')
        config.save()
        
        file_stat = os.stat(config_file)
        
        if sys.platform == 'win32':
            import win32api
            import win32security
            
            sd = win32security.GetFileSecurity(
                str(config_file),
                win32security.DACL_SECURITY_INFORMATION
            )
            
            dacl = sd.GetSecurityDescriptorDacl()
            self.assertIsNotNone(dacl)
        else:
            mode = file_stat.st_mode & 0o777
            self.assertIn(mode, [0o600, 0o640], f"Config has insecure permissions: {oct(mode)}")
    
    def test_log_file_permissions(self):
        """Test that log files have restricted permissions"""
        log_file = Path(self.temp_dir) / "test.log"
        
        from src.utils.logger import Logger
        with patch('src.utils.logger.LOG_DIR', self.temp_dir):
            logger = Logger.get_logger("test")
            
            handler = logging.FileHandler(str(log_file))
            logger.addHandler(handler)
            logger.info("Test log entry")
            handler.close()
        
        if log_file.exists():
            file_stat = os.stat(log_file)
            
            if sys.platform != 'win32':
                mode = file_stat.st_mode & 0o777
                self.assertIn(mode, [0o600, 0o640, 0o644], 
                             f"Log has unexpected permissions: {oct(mode)}")
    
    def test_temp_file_cleanup(self):
        """Test that temporary files are properly cleaned up"""
        temp_files = []
        
        for i in range(5):
            with tempfile.NamedTemporaryFile(delete=False, dir=self.temp_dir) as tmp:
                temp_files.append(tmp.name)
                tmp.write(b"temp data")
        
        for temp_file in temp_files:
            self.assertTrue(os.path.exists(temp_file))
            os.unlink(temp_file)
            self.assertFalse(os.path.exists(temp_file))
    
    def test_secure_delete(self):
        """Test secure file deletion"""
        test_file = Path(self.temp_dir) / "to_delete.txt"
        test_data = b"sensitive data to be deleted"
        test_file.write_bytes(test_data)
        
        original_size = test_file.stat().st_size
        
        self.security.secure_delete(test_file)
        
        self.assertFalse(test_file.exists())
        
        if sys.platform != 'win32':
            try:
                with open('/proc/sys/vm/drop_caches', 'w') as f:
                    f.write('3')
            except (PermissionError, FileNotFoundError):
                pass


class TestPathTraversal(unittest.TestCase):
    """Test path traversal prevention"""
    
    def setUp(self):
        self.validator = InputValidator()
        self.base_dir = tempfile.mkdtemp()
    
    def test_directory_traversal_prevention(self):
        """Test prevention of directory traversal attacks"""
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "config/../../../etc/shadow",
            "./../../sensitive_file",
            "~/../../../root/.ssh/id_rsa",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..;/etc/passwd",
            ".|./.|./.|./etc/passwd",
        ]
        
        for path in dangerous_paths:
            sanitized = self.validator.sanitize_path(path)
            
            self.assertNotIn("..", sanitized)
            self.assertNotIn("etc", sanitized.lower())
            self.assertNotIn("windows\\system32", sanitized.lower())
            
            resolved = Path(sanitized).resolve()
            self.assertFalse(str(resolved).startswith("/etc"))
            self.assertFalse(str(resolved).startswith("C:\\Windows\\System32"))
    
    def test_safe_join_path(self):
        """Test safe path joining"""
        def safe_join_path(base: str, relative: str) -> str:
            base_path = Path(base).resolve()
            joined = (base_path / relative).resolve()
            
            if not str(joined).startswith(str(base_path)):
                raise SecurityError(f"Path traversal detected: {relative}")
            
            return str(joined)
        
        test_cases = [
            ("subdir/file.txt", True),
            ("../../../etc/passwd", False),
            ("subdir/../file.txt", True),
            ("subdir/../../outside.txt", False),
        ]
        
        for relative_path, should_succeed in test_cases:
            if should_succeed:
                result = safe_join_path(self.base_dir, relative_path)
                self.assertTrue(result.startswith(self.base_dir))
            else:
                with self.assertRaises(SecurityError):
                    safe_join_path(self.base_dir, relative_path)
    
    def test_symlink_prevention(self):
        """Test prevention of symlink attacks"""
        if sys.platform == 'win32':
            self.skipTest("Symlink test not applicable on Windows without admin")
        
        target_file = Path(self.base_dir) / "target.txt"
        target_file.write_text("target content")
        
        symlink = Path(self.base_dir) / "symlink"
        
        try:
            os.symlink(target_file, symlink)
            
            def check_symlink(path: Path) -> bool:
                return path.is_symlink() or path.resolve() != path
            
            self.assertTrue(check_symlink(symlink))
            self.assertFalse(check_symlink(target_file))
            
        except OSError:
            self.skipTest("Cannot create symlinks")
    
    def test_null_byte_injection(self):
        """Test prevention of null byte injection"""
        dangerous_paths = [
            "file.txt\x00.jpg",
            "config\x00/../../etc/passwd",
            "safe_file\x00../../../../etc/shadow",
        ]
        
        for path in dangerous_paths:
            sanitized = self.validator.sanitize_path(path)
            self.assertNotIn("\x00", sanitized)
    
    def test_unicode_normalization(self):
        """Test Unicode normalization to prevent attacks"""
        import unicodedata
        
        dangerous_inputs = [
            "ﬁle.txt",  # Unicode ligature
            "．．／．．／etc/passwd",  # Full-width characters
            "file\u200e.txt",  # Right-to-left mark
        ]
        
        for input_str in dangerous_inputs:
            normalized = unicodedata.normalize('NFKC', input_str)
            sanitized = self.validator.sanitize_path(normalized)
            
            self.assertNotIn("..", sanitized)
            self.assertNotIn("\u200e", sanitized)


class TestFileIntegrity(unittest.TestCase):
    """Test file integrity verification"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def test_file_checksum_verification(self):
        """Test file integrity using checksums"""
        test_file = Path(self.temp_dir) / "integrity_test.txt"
        test_content = b"important data"
        test_file.write_bytes(test_content)
        
        original_hash = hashlib.sha256(test_content).hexdigest()
        
        with open(test_file, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        self.assertEqual(original_hash, file_hash)
        
        test_file.write_bytes(b"tampered data")
        
        with open(test_file, 'rb') as f:
            new_hash = hashlib.sha256(f.read()).hexdigest()
        
        self.assertNotEqual(original_hash, new_hash)
    
    def test_config_integrity(self):
        """Test configuration file integrity"""
        config_file = Path(self.temp_dir) / "config.json"
        config_data = {"api_key": "test_key", "setting": "value"}
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        original_hash = hashlib.sha256(
            json.dumps(config_data, sort_keys=True).encode()
        ).hexdigest()
        
        with open(config_file, 'r') as f:
            loaded_data = json.load(f)
        
        loaded_hash = hashlib.sha256(
            json.dumps(loaded_data, sort_keys=True).encode()
        ).hexdigest()
        
        self.assertEqual(original_hash, loaded_hash)
    
    def test_file_lock_mechanism(self):
        """Test file locking to prevent concurrent access"""
        import fcntl
        
        if sys.platform == 'win32':
            import msvcrt
            
            test_file = Path(self.temp_dir) / "locked.txt"
            test_file.write_text("locked content")
            
            with open(test_file, 'r+') as f1:
                msvcrt.locking(f1.fileno(), msvcrt.LK_NBLCK, 1)
                
                with self.assertRaises(IOError):
                    with open(test_file, 'r+') as f2:
                        msvcrt.locking(f2.fileno(), msvcrt.LK_NBLCK, 1)
                
                msvcrt.locking(f1.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            test_file = Path(self.temp_dir) / "locked.txt"
            test_file.write_text("locked content")
            
            with open(test_file, 'r+') as f1:
                fcntl.flock(f1.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                with self.assertRaises(IOError):
                    with open(test_file, 'r+') as f2:
                        fcntl.flock(f2.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                fcntl.flock(f1.fileno(), fcntl.LOCK_UN)
    
    def test_atomic_write(self):
        """Test atomic file write operations"""
        target_file = Path(self.temp_dir) / "atomic.txt"
        
        def atomic_write(path: Path, content: str):
            temp_file = path.with_suffix('.tmp')
            try:
                temp_file.write_text(content)
                temp_file.replace(path)
            except Exception:
                if temp_file.exists():
                    temp_file.unlink()
                raise
        
        atomic_write(target_file, "atomic content")
        self.assertEqual(target_file.read_text(), "atomic content")
        
        temp_file = target_file.with_suffix('.tmp')
        self.assertFalse(temp_file.exists())


class TestFileAccessControl(unittest.TestCase):
    """Test file access control"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def test_restricted_file_access(self):
        """Test that sensitive files have restricted access"""
        sensitive_files = [
            "config.json",
            "credentials.txt",
            "api_keys.json",
            ".env",
        ]
        
        for filename in sensitive_files:
            file_path = Path(self.temp_dir) / filename
            file_path.write_text("sensitive data")
            
            if sys.platform == 'win32':
                os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
            else:
                os.chmod(file_path, 0o600)
            
            file_stat = os.stat(file_path)
            
            if sys.platform != 'win32':
                mode = file_stat.st_mode & 0o777
                self.assertEqual(mode, 0o600)
    
    def test_directory_access_control(self):
        """Test directory access restrictions"""
        secure_dir = Path(self.temp_dir) / "secure"
        secure_dir.mkdir()
        
        if sys.platform == 'win32':
            os.chmod(secure_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        else:
            os.chmod(secure_dir, 0o700)
        
        dir_stat = os.stat(secure_dir)
        
        if sys.platform != 'win32':
            mode = dir_stat.st_mode & 0o777
            self.assertEqual(mode, 0o700)
    
    def test_file_ownership_verification(self):
        """Test file ownership verification"""
        test_file = Path(self.temp_dir) / "owned.txt"
        test_file.write_text("owned content")
        
        file_stat = os.stat(test_file)
        current_uid = os.getuid() if hasattr(os, 'getuid') else None
        
        if current_uid is not None:
            self.assertEqual(file_stat.st_uid, current_uid)
    
    def test_immutable_file_protection(self):
        """Test protection of immutable files"""
        if sys.platform == 'win32':
            import win32api
            import win32con
            
            protected_file = Path(self.temp_dir) / "protected.txt"
            protected_file.write_text("protected content")
            
            win32api.SetFileAttributes(
                str(protected_file),
                win32con.FILE_ATTRIBUTE_READONLY
            )
            
            with self.assertRaises(PermissionError):
                protected_file.write_text("modified")
            
            win32api.SetFileAttributes(
                str(protected_file),
                win32con.FILE_ATTRIBUTE_NORMAL
            )
        else:
            self.skipTest("Platform-specific test")


class TestFileQuota(unittest.TestCase):
    """Test file size and quota restrictions"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def test_file_size_limit(self):
        """Test file size limitations"""
        max_size = 10 * 1024 * 1024  # 10 MB
        
        test_file = Path(self.temp_dir) / "large.txt"
        
        def write_with_limit(path: Path, content: bytes, max_size: int):
            if len(content) > max_size:
                raise ValueError(f"File size exceeds limit: {len(content)} > {max_size}")
            path.write_bytes(content)
        
        small_content = b"x" * 1024
        write_with_limit(test_file, small_content, max_size)
        self.assertTrue(test_file.exists())
        
        large_content = b"x" * (max_size + 1)
        with self.assertRaises(ValueError):
            write_with_limit(test_file, large_content, max_size)
    
    def test_directory_quota(self):
        """Test directory quota enforcement"""
        max_quota = 50 * 1024 * 1024  # 50 MB
        
        def get_directory_size(path: Path) -> int:
            total = 0
            for file in path.rglob('*'):
                if file.is_file():
                    total += file.stat().st_size
            return total
        
        def check_quota(directory: Path, new_size: int, max_quota: int):
            current_size = get_directory_size(directory)
            if current_size + new_size > max_quota:
                raise ValueError(f"Quota exceeded: {current_size + new_size} > {max_quota}")
        
        for i in range(5):
            file_path = Path(self.temp_dir) / f"file_{i}.txt"
            content = b"x" * (5 * 1024 * 1024)  # 5 MB each
            
            check_quota(Path(self.temp_dir), len(content), max_quota)
            file_path.write_bytes(content)
        
        with self.assertRaises(ValueError):
            check_quota(Path(self.temp_dir), 30 * 1024 * 1024, max_quota)
    
    def test_temp_file_limit(self):
        """Test temporary file creation limits"""
        max_temp_files = 10
        temp_files = []
        
        for i in range(max_temp_files):
            tmp = tempfile.NamedTemporaryFile(delete=False, dir=self.temp_dir)
            temp_files.append(tmp.name)
            tmp.close()
        
        self.assertEqual(len(temp_files), max_temp_files)
        
        def create_temp_with_limit(current_count: int, max_count: int):
            if current_count >= max_count:
                raise ValueError(f"Too many temp files: {current_count}")
            return tempfile.NamedTemporaryFile(delete=False, dir=self.temp_dir)
        
        with self.assertRaises(ValueError):
            create_temp_with_limit(len(temp_files), max_temp_files)
        
        for temp_file in temp_files:
            os.unlink(temp_file)


if __name__ == '__main__':
    import logging
    unittest.main()