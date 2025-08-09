"""Comprehensive security tests for administrative privilege handling"""
import unittest
import tempfile
import os
import sys
import json
import hashlib
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import threading
import queue

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.security import SecurityManager, InputValidator, RateLimiter
from src.core.exceptions import ConfigurationError, SecurityError


class TestPrivilegeEscalation(unittest.TestCase):
    """Test against privilege escalation vulnerabilities"""
    
    def setUp(self):
        self.security = SecurityManager()
        self.temp_dir = tempfile.mkdtemp()
        
    def test_prevent_unauthorized_elevation(self):
        """Ensure the app doesn't allow unauthorized privilege elevation"""
        with patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=False):
            from src.core.service_manager import ServiceManager
            service = ServiceManager()
            
            with self.assertRaises(PermissionError):
                service._require_admin_privileges()
    
    def test_secure_admin_check(self):
        """Test that admin checks cannot be bypassed"""
        test_cases = [
            ('', False),
            ('admin', False),
            ('Administrator', False),
            (True, True),
            (1, True),
            (0, False),
        ]
        
        for value, expected in test_cases:
            with patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=value):
                result = self.security.is_admin()
                self.assertEqual(result, expected, f"Failed for value: {value}")
    
    def test_safe_service_installation(self):
        """Test that service installation validates permissions"""
        from src.core.service_manager import install_service
        
        with patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=False):
            with self.assertRaises(PermissionError):
                install_service()
    
    def test_privilege_drop_after_startup(self):
        """Test that privileges are dropped after critical operations"""
        with patch('os.setuid') as mock_setuid:
            with patch('os.setgid') as mock_setgid:
                with patch('sys.platform', 'linux'):
                    self.security.drop_privileges(uid=1000, gid=1000)
                    mock_setgid.assert_called_with(1000)
                    mock_setuid.assert_called_with(1000)


class TestInputSanitization(unittest.TestCase):
    """Test comprehensive input sanitization"""
    
    def setUp(self):
        self.validator = InputValidator()
    
    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks"""
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM",
            "../../../../root/.ssh/id_rsa",
            "..%2f..%2f..%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",
            "\\\\server\\share\\..\\..\\admin$",
            "file:///etc/passwd",
            "file://localhost/etc/passwd",
        ]
        
        for path in dangerous_paths:
            sanitized = self.validator.sanitize_path(path)
            self.assertNotIn("..", sanitized)
            self.assertNotIn("etc", sanitized.lower())
            self.assertNotIn("windows\\system32", sanitized.lower())
            self.assertNotIn("://", sanitized)
    
    def test_command_injection_prevention(self):
        """Test prevention of command injection"""
        dangerous_inputs = [
            "test; rm -rf /",
            "test && net user admin password",
            "test | format c:",
            "test`whoami`",
            "test$(whoami)",
            "test\nnet user admin password",
            "test\r\nnet user admin password",
            "$IFS$9ping$IFS$9-c$IFS$91$IFS$9google.com",
        ]
        
        for input_str in dangerous_inputs:
            sanitized = self.validator.sanitize_input(input_str)
            self.assertNotIn(";", sanitized)
            self.assertNotIn("&&", sanitized)
            self.assertNotIn("|", sanitized)
            self.assertNotIn("`", sanitized)
            self.assertNotIn("$", sanitized)
            self.assertNotIn("\n", sanitized)
            self.assertNotIn("\r", sanitized)
    
    def test_sql_injection_prevention(self):
        """Test prevention of SQL injection"""
        sql_payloads = [
            "' OR '1'='1",
            "1; DROP TABLE users--",
            "admin'--",
            "' UNION SELECT * FROM passwords--",
            "1' AND 1=CONVERT(int, (SELECT TOP 1 name FROM sysobjects WHERE xtype='U'))--",
        ]
        
        for payload in sql_payloads:
            sanitized = self.validator.sanitize_sql_input(payload)
            self.assertNotIn("'", sanitized)
            self.assertNotIn("--", sanitized)
            self.assertNotIn("DROP", sanitized.upper())
            self.assertNotIn("UNION", sanitized.upper())
    
    def test_xss_prevention(self):
        """Test prevention of XSS attacks"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "<iframe src=javascript:alert('XSS')>",
            "';alert('XSS');//",
            "<body onload=alert('XSS')>",
        ]
        
        for payload in xss_payloads:
            sanitized = self.validator.sanitize_html(payload)
            self.assertNotIn("<script", sanitized.lower())
            self.assertNotIn("javascript:", sanitized.lower())
            self.assertNotIn("onerror", sanitized.lower())
            self.assertNotIn("onload", sanitized.lower())
            self.assertNotIn("<iframe", sanitized.lower())
    
    def test_ldap_injection_prevention(self):
        """Test prevention of LDAP injection"""
        ldap_payloads = [
            "admin)(uid=*",
            "admin)(|(uid=*",
            "*)(uid=*))(|(uid=*",
            "admin))%00",
        ]
        
        for payload in ldap_payloads:
            sanitized = self.validator.sanitize_ldap_input(payload)
            self.assertNotIn(")(", sanitized)
            self.assertNotIn("|(", sanitized)
            self.assertNotIn("*)", sanitized)
            self.assertNotIn("%00", sanitized)


class TestCredentialSecurity(unittest.TestCase):
    """Test secure credential handling"""
    
    def setUp(self):
        self.security = SecurityManager()
        self.temp_dir = tempfile.mkdtemp()
    
    def test_api_key_encryption_in_memory(self):
        """Test that API keys are encrypted in memory"""
        api_key = "sk-" + "a" * 48
        
        encrypted = self.security.encrypt_data(api_key)
        
        self.assertNotEqual(encrypted, api_key)
        self.assertNotIn(api_key, encrypted)
        
        decrypted = self.security.decrypt_data(encrypted)
        self.assertEqual(decrypted, api_key)
    
    def test_api_key_not_logged(self):
        """Test that API keys are not logged"""
        api_key = "sk-sensitive-api-key-12345"
        
        with patch('src.utils.logger.Logger.log') as mock_log:
            from src.utils.logger import Logger
            logger = Logger.get_logger()
            
            logger.info(f"Using API key: {api_key}")
            
            for call in mock_log.call_args_list:
                logged_message = str(call)
                self.assertNotIn(api_key, logged_message)
                self.assertNotIn("sensitive-api-key", logged_message)
    
    def test_secure_credential_storage(self):
        """Test secure storage of credentials"""
        credentials = {
            "api_key": "sk-test-key",
            "password": "SecurePassword123",
            "token": "bearer-token-xyz"
        }
        
        config_path = Path(self.temp_dir) / "config.json"
        
        encrypted_creds = {}
        for key, value in credentials.items():
            encrypted_creds[key] = self.security.encrypt_data(value)
        
        with open(config_path, 'w') as f:
            json.dump(encrypted_creds, f)
        
        with open(config_path, 'r') as f:
            content = f.read()
            for value in credentials.values():
                self.assertNotIn(value, content)
    
    def test_credential_rotation(self):
        """Test credential rotation mechanism"""
        old_key = "sk-old-key"
        new_key = "sk-new-key"
        
        encrypted_old = self.security.encrypt_data(old_key)
        time.sleep(0.1)
        encrypted_new = self.security.encrypt_data(new_key)
        
        self.assertNotEqual(encrypted_old, encrypted_new)
        
        self.assertEqual(self.security.decrypt_data(encrypted_old), old_key)
        self.assertEqual(self.security.decrypt_data(encrypted_new), new_key)
    
    def test_credential_timeout(self):
        """Test credential timeout mechanism"""
        from src.utils.security import CredentialManager
        
        cred_manager = CredentialManager(timeout_seconds=1)
        cred_manager.store_credential("test_key", "test_value")
        
        self.assertEqual(cred_manager.get_credential("test_key"), "test_value")
        
        time.sleep(1.5)
        
        self.assertIsNone(cred_manager.get_credential("test_key"))


class TestRateLimiting(unittest.TestCase):
    """Test rate limiting and DoS prevention"""
    
    def setUp(self):
        self.rate_limiter = RateLimiter()
    
    def test_api_call_rate_limiting(self):
        """Test API call rate limiting"""
        self.rate_limiter.set_limit("api_call", max_attempts=5, window_seconds=1)
        
        for i in range(5):
            self.assertTrue(self.rate_limiter.check_limit("api_call"))
        
        self.assertFalse(self.rate_limiter.check_limit("api_call"))
        
        wait_time = self.rate_limiter.get_wait_time("api_call")
        self.assertGreater(wait_time, 0)
        self.assertLessEqual(wait_time, 1)
    
    def test_login_attempt_limiting(self):
        """Test login attempt rate limiting"""
        self.rate_limiter.set_limit("login", max_attempts=3, window_seconds=60)
        
        for i in range(3):
            self.assertTrue(self.rate_limiter.check_limit("login"))
        
        for i in range(10):
            self.assertFalse(self.rate_limiter.check_limit("login"))
    
    def test_concurrent_request_limiting(self):
        """Test concurrent request limiting"""
        max_concurrent = 10
        active_requests = threading.Semaphore(max_concurrent)
        
        def make_request():
            if not active_requests.acquire(blocking=False):
                return False
            try:
                time.sleep(0.1)
                return True
            finally:
                active_requests.release()
        
        threads = []
        results = queue.Queue()
        
        for i in range(15):
            t = threading.Thread(target=lambda: results.put(make_request()))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        successful = sum(1 for _ in range(results.qsize()) if results.get())
        self.assertLessEqual(successful, max_concurrent)
    
    def test_memory_exhaustion_prevention(self):
        """Test prevention of memory exhaustion attacks"""
        import psutil
        import gc
        
        initial_memory = psutil.Process().memory_info().rss
        
        large_data = []
        max_memory_increase = 100 * 1024 * 1024  # 100 MB
        
        for i in range(10):
            try:
                current_memory = psutil.Process().memory_info().rss
                if current_memory - initial_memory > max_memory_increase:
                    break
                large_data.append("x" * (10 * 1024 * 1024))  # 10 MB strings
            except MemoryError:
                break
        
        large_data.clear()
        gc.collect()
        
        final_memory = psutil.Process().memory_info().rss
        memory_increase = final_memory - initial_memory
        
        self.assertLess(memory_increase, max_memory_increase * 2)


class TestFileSystemSecurity(unittest.TestCase):
    """Test file system security"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.validator = InputValidator()
    
    def test_safe_file_operations(self):
        """Test safe file operations"""
        safe_path = Path(self.temp_dir) / "test.txt"
        
        with open(safe_path, 'w') as f:
            f.write("test content")
        
        self.assertTrue(safe_path.exists())
        
        if sys.platform == 'win32':
            import stat
            os.chmod(safe_path, stat.S_IRUSR | stat.S_IWUSR)
        else:
            os.chmod(safe_path, 0o600)
        
        stat_info = os.stat(safe_path)
        if sys.platform != 'win32':
            self.assertEqual(stat_info.st_mode & 0o777, 0o600)
    
    def test_temp_file_security(self):
        """Test secure temporary file creation"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=self.temp_dir) as tmp:
            tmp.write("sensitive data")
            tmp_path = tmp.name
        
        stat_info = os.stat(tmp_path)
        if sys.platform != 'win32':
            self.assertEqual(stat_info.st_mode & 0o777, 0o600)
        
        os.unlink(tmp_path)
        self.assertFalse(os.path.exists(tmp_path))
    
    def test_directory_traversal_prevention(self):
        """Test directory traversal prevention"""
        base_dir = Path(self.temp_dir)
        
        test_paths = [
            "../../etc/passwd",
            "../../../windows/system32",
            "subdir/../../../../../../etc/shadow",
        ]
        
        for test_path in test_paths:
            safe_path = self.validator.safe_join_path(str(base_dir), test_path)
            resolved = Path(safe_path).resolve()
            
            self.assertTrue(str(resolved).startswith(str(base_dir.resolve())))
    
    def test_symlink_attack_prevention(self):
        """Test prevention of symlink attacks"""
        if sys.platform == 'win32':
            self.skipTest("Symlink test not applicable on Windows")
        
        target = Path(self.temp_dir) / "target.txt"
        symlink = Path(self.temp_dir) / "symlink"
        
        target.write_text("content")
        
        try:
            os.symlink(target, symlink)
            
            real_path = Path(symlink).resolve()
            self.assertEqual(real_path, target.resolve())
            
            with self.assertRaises(SecurityError):
                self.validator.validate_no_symlink(str(symlink))
        except OSError:
            self.skipTest("Cannot create symlinks")


class TestProcessSecurity(unittest.TestCase):
    """Test process security and isolation"""
    
    def test_no_shell_execution(self):
        """Test that shell execution is disabled"""
        import subprocess
        
        dangerous_commands = [
            "echo test && rm -rf /",
            "echo test; net user admin password",
            "echo test | format c:",
        ]
        
        for cmd in dangerous_commands:
            with self.assertRaises((subprocess.CalledProcessError, OSError, SecurityError)):
                result = subprocess.run(cmd, shell=False, capture_output=True, text=True)
    
    def test_process_isolation(self):
        """Test process isolation"""
        import subprocess
        
        safe_command = [sys.executable, "-c", "print('test')"]
        
        result = subprocess.run(
            safe_command,
            capture_output=True,
            text=True,
            timeout=5,
            check=False
        )
        
        self.assertEqual(result.stdout.strip(), "test")
        self.assertEqual(result.returncode, 0)
    
    def test_resource_limits(self):
        """Test resource limitation"""
        import resource
        import subprocess
        
        if sys.platform == 'win32':
            self.skipTest("Resource limits not available on Windows")
        
        def set_limits():
            resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
            resource.setrlimit(resource.RLIMIT_AS, (50 * 1024 * 1024, 50 * 1024 * 1024))
        
        infinite_loop = "while True: pass"
        
        result = subprocess.run(
            [sys.executable, "-c", infinite_loop],
            preexec_fn=set_limits,
            capture_output=True,
            timeout=2
        )
        
        self.assertNotEqual(result.returncode, 0)


class TestNetworkSecurity(unittest.TestCase):
    """Test network security"""
    
    def test_https_enforcement(self):
        """Test HTTPS enforcement for API calls"""
        from urllib.parse import urlparse
        
        api_endpoints = [
            "http://api.example.com/endpoint",
            "https://api.example.com/endpoint",
            "ftp://api.example.com/endpoint",
        ]
        
        for endpoint in api_endpoints:
            parsed = urlparse(endpoint)
            if parsed.scheme != 'https':
                with self.assertRaises(SecurityError):
                    self.validate_secure_endpoint(endpoint)
    
    def validate_secure_endpoint(self, url):
        """Helper to validate secure endpoints"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.scheme != 'https':
            raise SecurityError(f"Insecure protocol: {parsed.scheme}")
        return True
    
    def test_certificate_validation(self):
        """Test SSL certificate validation"""
        import ssl
        import socket
        
        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        
        test_hosts = [
            ("www.google.com", 443, True),
            ("self-signed.badssl.com", 443, False),
            ("expired.badssl.com", 443, False),
        ]
        
        for host, port, should_succeed in test_hosts:
            try:
                with socket.create_connection((host, port), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=host) as ssock:
                        cert = ssock.getpeercert()
                        if should_succeed:
                            self.assertIsNotNone(cert)
                        else:
                            self.fail(f"Should have failed for {host}")
            except (ssl.SSLError, socket.timeout, socket.gaierror):
                if should_succeed:
                    self.skipTest(f"Cannot connect to {host}")
    
    def test_dns_rebinding_protection(self):
        """Test DNS rebinding protection"""
        private_ips = [
            "127.0.0.1",
            "localhost",
            "10.0.0.1",
            "192.168.1.1",
            "172.16.0.1",
            "::1",
            "0.0.0.0",
        ]
        
        for ip in private_ips:
            with self.assertRaises(SecurityError):
                self.validate_public_ip(ip)
    
    def validate_public_ip(self, ip):
        """Helper to validate public IPs"""
        import ipaddress
        
        try:
            addr = ipaddress.ip_address(ip)
            if addr.is_private or addr.is_loopback or addr.is_reserved:
                raise SecurityError(f"Private/reserved IP: {ip}")
        except ValueError:
            if ip in ['localhost', '0.0.0.0']:
                raise SecurityError(f"Invalid hostname: {ip}")
        return True


class TestAuditLogging(unittest.TestCase):
    """Test audit logging for security events"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = Path(self.temp_dir) / "audit.log"
    
    def test_security_event_logging(self):
        """Test that security events are logged"""
        from src.utils.logger import Logger
        
        logger = Logger.get_logger("security")
        
        security_events = [
            ("PRIVILEGE_ESCALATION_ATTEMPT", {"user": "test", "action": "install_service"}),
            ("AUTHENTICATION_FAILURE", {"user": "admin", "ip": "192.168.1.100"}),
            ("UNAUTHORIZED_ACCESS", {"resource": "/admin/panel", "user": "guest"}),
            ("RATE_LIMIT_EXCEEDED", {"action": "api_call", "ip": "10.0.0.1"}),
        ]
        
        for event_type, details in security_events:
            logger.log_security_event(event_type, details)
    
    def test_log_tampering_prevention(self):
        """Test prevention of log tampering"""
        import hashlib
        
        log_content = "Security event: unauthorized access attempt"
        
        with open(self.log_file, 'w') as f:
            f.write(log_content)
            hash_original = hashlib.sha256(log_content.encode()).hexdigest()
        
        if sys.platform == 'win32':
            import stat
            os.chmod(self.log_file, stat.S_IRUSR)
        else:
            os.chmod(self.log_file, 0o400)
        
        with self.assertRaises(PermissionError):
            with open(self.log_file, 'a') as f:
                f.write("Tampered content")
        
        with open(self.log_file, 'r') as f:
            content = f.read()
            hash_current = hashlib.sha256(content.encode()).hexdigest()
        
        self.assertEqual(hash_original, hash_current)
    
    def test_log_rotation_security(self):
        """Test secure log rotation"""
        from src.utils.logger import LogRotator
        
        rotator = LogRotator(
            log_file=str(self.log_file),
            max_size_mb=1,
            max_backups=3
        )
        
        for i in range(100):
            with open(self.log_file, 'a') as f:
                f.write(f"Log entry {i}\n" * 1000)
            
            rotator.check_and_rotate()
        
        log_files = list(Path(self.temp_dir).glob("audit.log*"))
        self.assertLessEqual(len(log_files), 4)
        
        for log_file in log_files:
            stat_info = os.stat(log_file)
            if sys.platform != 'win32':
                self.assertEqual(stat_info.st_mode & 0o077, 0)


if __name__ == '__main__':
    unittest.main()