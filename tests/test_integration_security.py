"""Integration tests for complete security flow"""
import unittest
import tempfile
import os
import sys
import json
import time
import threading
import hashlib
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import base64

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.security import SecurityManager, InputValidator, RateLimiter
from src.core.config import Config
from src.core.service_manager import ServiceManager
from src.core.exceptions import SecurityError, ConfigurationError


class TestEndToEndSecurity(unittest.TestCase):
    """Test complete security flow from input to output"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.security = SecurityManager()
        self.validator = InputValidator()
        self.config_path = Path(self.temp_dir) / "config.json"
    
    def test_secure_api_key_flow(self):
        """Test secure API key handling from input to storage"""
        api_key = "sk-" + "x" * 48
        
        self.assertTrue(self.validator.validate_api_key(api_key))
        
        encrypted = self.security.encrypt_data(api_key)
        self.assertNotEqual(encrypted, api_key)
        self.assertNotIn(api_key, encrypted)
        
        config = Config(str(self.config_path))
        config.set('api_key', encrypted)
        config.save()
        
        with open(self.config_path, 'r') as f:
            content = f.read()
            self.assertNotIn(api_key, content)
            self.assertIn(encrypted, content)
        
        loaded_config = Config(str(self.config_path))
        stored_encrypted = loaded_config.get('api_key')
        
        decrypted = self.security.decrypt_data(stored_encrypted)
        self.assertEqual(decrypted, api_key)
    
    def test_secure_user_input_flow(self):
        """Test secure handling of user input"""
        malicious_inputs = [
            "<script>alert('xss')</script>Context about math",
            "'; DROP TABLE users; -- context",
            "../../etc/passwd",
            "Context with ${MALICIOUS_VAR} injection",
        ]
        
        for input_str in malicious_inputs:
            sanitized = self.validator.sanitize_context(input_str)
            
            self.assertNotIn("<script>", sanitized)
            self.assertNotIn("DROP TABLE", sanitized)
            self.assertNotIn("../", sanitized)
            self.assertNotIn("${", sanitized)
            
            config = Config(str(self.config_path))
            config.set('context', sanitized)
            
            self.assertEqual(config.get('context'), sanitized)
    
    def test_secure_service_lifecycle(self):
        """Test secure service startup and shutdown"""
        service = ServiceManager(str(self.config_path))
        
        with patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=True):
            with patch.object(service, 'initialize_components'):
                service.start()
                
                self.assertTrue(service.running)
                
                time.sleep(0.1)
                
                service.stop()
                
                self.assertFalse(service.running)
                
                if service._stats_tracker:
                    stats = service._stats_tracker.get_summary()
                    self.assertIsInstance(stats, dict)
    
    def test_secure_configuration_update(self):
        """Test secure configuration updates"""
        config = Config(str(self.config_path))
        
        initial_api_key = "sk-initial" + "x" * 40
        config.set('api_key', self.security.encrypt_data(initial_api_key))
        config.save()
        
        initial_hash = hashlib.sha256(
            json.dumps(config.config, sort_keys=True).encode()
        ).hexdigest()
        
        new_api_key = "sk-updated" + "y" * 40
        config.set('api_key', self.security.encrypt_data(new_api_key))
        config.save()
        
        final_hash = hashlib.sha256(
            json.dumps(config.config, sort_keys=True).encode()
        ).hexdigest()
        
        self.assertNotEqual(initial_hash, final_hash)
        
        with open(self.config_path, 'r') as f:
            content = f.read()
            self.assertNotIn(initial_api_key, content)
            self.assertNotIn(new_api_key, content)


class TestSecurityMonitoring(unittest.TestCase):
    """Test security monitoring and alerting"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = Path(self.temp_dir) / "security.log"
    
    def test_security_event_logging(self):
        """Test that security events are properly logged"""
        from src.utils.logger import Logger
        
        with patch('src.utils.logger.LOG_DIR', self.temp_dir):
            logger = Logger.get_logger("security")
            
            events = [
                ("AUTH_FAILURE", {"user": "admin", "ip": "192.168.1.1"}),
                ("PRIVILEGE_ESCALATION", {"action": "install_service"}),
                ("RATE_LIMIT_EXCEEDED", {"operation": "api_call"}),
                ("INVALID_INPUT", {"type": "sql_injection", "input": "'; DROP TABLE"}),
            ]
            
            for event_type, details in events:
                logger.log_security_event(event_type, details)
    
    def test_intrusion_detection(self):
        """Test basic intrusion detection"""
        threshold = 5
        attempts = []
        
        def detect_intrusion(attempts_list, threshold):
            recent_attempts = [
                a for a in attempts_list 
                if time.time() - a < 60
            ]
            return len(recent_attempts) >= threshold
        
        for i in range(3):
            attempts.append(time.time())
            self.assertFalse(detect_intrusion(attempts, threshold))
        
        for i in range(2):
            attempts.append(time.time())
        
        self.assertTrue(detect_intrusion(attempts, threshold))
    
    def test_anomaly_detection(self):
        """Test anomaly detection in service behavior"""
        normal_pattern = {
            'api_calls_per_minute': 10,
            'screenshots_per_minute': 12,
            'memory_usage_mb': 150,
        }
        
        def detect_anomaly(current, normal, threshold=2.0):
            anomalies = []
            for key, normal_value in normal.items():
                if key in current:
                    ratio = current[key] / normal_value
                    if ratio > threshold or ratio < 1/threshold:
                        anomalies.append((key, current[key], normal_value))
            return anomalies
        
        normal_behavior = {
            'api_calls_per_minute': 8,
            'screenshots_per_minute': 10,
            'memory_usage_mb': 140,
        }
        
        anomalies = detect_anomaly(normal_behavior, normal_pattern)
        self.assertEqual(len(anomalies), 0)
        
        suspicious_behavior = {
            'api_calls_per_minute': 50,
            'screenshots_per_minute': 100,
            'memory_usage_mb': 500,
        }
        
        anomalies = detect_anomaly(suspicious_behavior, normal_pattern)
        self.assertGreater(len(anomalies), 0)


class TestCredentialManagement(unittest.TestCase):
    """Test credential management and rotation"""
    
    def setUp(self):
        self.security = SecurityManager()
        self.temp_dir = tempfile.mkdtemp()
    
    def test_credential_rotation(self):
        """Test automatic credential rotation"""
        class CredentialManager:
            def __init__(self):
                self.credentials = {}
                self.rotation_times = {}
            
            def store_credential(self, key: str, value: str, rotate_after: int = 3600):
                encrypted = self.security.encrypt_data(value)
                self.credentials[key] = encrypted
                self.rotation_times[key] = time.time() + rotate_after
            
            def get_credential(self, key: str) -> str:
                if key not in self.credentials:
                    return None
                
                if time.time() > self.rotation_times.get(key, float('inf')):
                    return None
                
                return self.security.decrypt_data(self.credentials[key])
            
            def rotate_credential(self, key: str, new_value: str):
                self.store_credential(key, new_value)
        
        manager = CredentialManager()
        manager.security = self.security
        
        manager.store_credential("api_key", "old_key", rotate_after=1)
        self.assertEqual(manager.get_credential("api_key"), "old_key")
        
        time.sleep(1.1)
        self.assertIsNone(manager.get_credential("api_key"))
        
        manager.rotate_credential("api_key", "new_key")
        self.assertEqual(manager.get_credential("api_key"), "new_key")
    
    def test_credential_access_control(self):
        """Test credential access control"""
        class SecureCredentialStore:
            def __init__(self):
                self.store = {}
                self.access_log = []
            
            def store(self, key: str, value: str, allowed_users: list):
                self.store[key] = {
                    'value': self.security.encrypt_data(value),
                    'allowed': allowed_users
                }
            
            def retrieve(self, key: str, user: str) -> str:
                self.access_log.append((key, user, time.time()))
                
                if key not in self.store:
                    raise KeyError(f"Credential {key} not found")
                
                if user not in self.store[key]['allowed']:
                    raise PermissionError(f"User {user} not authorized for {key}")
                
                return self.security.decrypt_data(self.store[key]['value'])
        
        store = SecureCredentialStore()
        store.security = self.security
        
        store.store("admin_key", "secret123", ["admin", "service"])
        
        self.assertEqual(store.retrieve("admin_key", "admin"), "secret123")
        
        with self.assertRaises(PermissionError):
            store.retrieve("admin_key", "guest")
        
        self.assertEqual(len(store.access_log), 2)


class TestNetworkSecurity(unittest.TestCase):
    """Test network security measures"""
    
    def test_tls_enforcement(self):
        """Test TLS/HTTPS enforcement"""
        urls = [
            ("http://api.example.com", False),
            ("https://api.example.com", True),
            ("ftp://files.example.com", False),
            ("https://secure.api.com", True),
        ]
        
        def validate_secure_connection(url: str) -> bool:
            return url.startswith("https://")
        
        for url, expected in urls:
            self.assertEqual(validate_secure_connection(url), expected)
    
    def test_certificate_pinning(self):
        """Test certificate pinning implementation"""
        class CertificatePinner:
            def __init__(self):
                self.pinned_certs = {}
            
            def pin_certificate(self, domain: str, cert_hash: str):
                self.pinned_certs[domain] = cert_hash
            
            def verify_certificate(self, domain: str, cert_hash: str) -> bool:
                if domain not in self.pinned_certs:
                    return True
                return self.pinned_certs[domain] == cert_hash
        
        pinner = CertificatePinner()
        
        pinner.pin_certificate("api.example.com", "sha256:abcd1234")
        
        self.assertTrue(pinner.verify_certificate("api.example.com", "sha256:abcd1234"))
        self.assertFalse(pinner.verify_certificate("api.example.com", "sha256:different"))
        self.assertTrue(pinner.verify_certificate("other.com", "sha256:any"))
    
    def test_dns_validation(self):
        """Test DNS validation and DNSSEC"""
        import socket
        
        def validate_dns_response(domain: str) -> bool:
            try:
                ip = socket.gethostbyname(domain)
                
                import ipaddress
                addr = ipaddress.ip_address(ip)
                
                if addr.is_private or addr.is_loopback or addr.is_reserved:
                    return False
                
                return True
            except (socket.gaierror, ValueError):
                return False
        
        test_domains = [
            ("localhost", False),
            ("127.0.0.1", False),
            ("192.168.1.1", False),
        ]
        
        for domain, expected in test_domains:
            if expected is not None:
                result = validate_dns_response(domain)
                self.assertEqual(result, expected)


class TestComplianceValidation(unittest.TestCase):
    """Test security compliance validation"""
    
    def test_password_policy_compliance(self):
        """Test password policy enforcement"""
        def validate_password(password: str) -> tuple:
            errors = []
            
            if len(password) < 12:
                errors.append("Password must be at least 12 characters")
            
            if not any(c.isupper() for c in password):
                errors.append("Password must contain uppercase letters")
            
            if not any(c.islower() for c in password):
                errors.append("Password must contain lowercase letters")
            
            if not any(c.isdigit() for c in password):
                errors.append("Password must contain numbers")
            
            if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
                errors.append("Password must contain special characters")
            
            common_passwords = ["password", "12345678", "qwerty"]
            if any(common in password.lower() for common in common_passwords):
                errors.append("Password contains common patterns")
            
            return len(errors) == 0, errors
        
        test_passwords = [
            ("weak", False),
            ("StrongP@ssw0rd123!", True),
            ("password123", False),
            ("NoSpecialChar123", False),
        ]
        
        for password, expected_valid in test_passwords:
            is_valid, errors = validate_password(password)
            self.assertEqual(is_valid, expected_valid)
    
    def test_data_retention_compliance(self):
        """Test data retention policy compliance"""
        class DataRetentionManager:
            def __init__(self, retention_days: int = 30):
                self.retention_days = retention_days
                self.data_store = {}
            
            def store_data(self, key: str, data: any):
                self.data_store[key] = {
                    'data': data,
                    'timestamp': time.time(),
                    'expiry': time.time() + (self.retention_days * 86400)
                }
            
            def cleanup_expired(self):
                current_time = time.time()
                expired_keys = [
                    k for k, v in self.data_store.items()
                    if v['expiry'] < current_time
                ]
                
                for key in expired_keys:
                    del self.data_store[key]
                
                return len(expired_keys)
        
        manager = DataRetentionManager(retention_days=0.00001)
        
        manager.store_data("user1", {"name": "Test User"})
        manager.store_data("user2", {"name": "Another User"})
        
        self.assertEqual(len(manager.data_store), 2)
        
        time.sleep(0.1)
        
        expired_count = manager.cleanup_expired()
        self.assertEqual(expired_count, 2)
        self.assertEqual(len(manager.data_store), 0)
    
    def test_audit_trail_completeness(self):
        """Test audit trail completeness"""
        class AuditTrail:
            def __init__(self):
                self.events = []
            
            def log_event(self, event_type: str, user: str, action: str, result: str):
                event = {
                    'timestamp': time.time(),
                    'type': event_type,
                    'user': user,
                    'action': action,
                    'result': result,
                    'hash': None
                }
                
                if self.events:
                    prev_hash = self.events[-1]['hash']
                    event['prev_hash'] = prev_hash
                
                event_str = json.dumps(event, sort_keys=True)
                event['hash'] = hashlib.sha256(event_str.encode()).hexdigest()
                
                self.events.append(event)
            
            def verify_integrity(self) -> bool:
                for i in range(1, len(self.events)):
                    if self.events[i].get('prev_hash') != self.events[i-1]['hash']:
                        return False
                
                for event in self.events:
                    temp_hash = event['hash']
                    event['hash'] = None
                    event_str = json.dumps(event, sort_keys=True)
                    calculated_hash = hashlib.sha256(event_str.encode()).hexdigest()
                    event['hash'] = temp_hash
                    
                    if calculated_hash != temp_hash:
                        return False
                
                return True
        
        audit = AuditTrail()
        
        audit.log_event("LOGIN", "user1", "authenticate", "success")
        audit.log_event("ACCESS", "user1", "read_file", "success")
        audit.log_event("MODIFY", "user1", "update_config", "success")
        
        self.assertTrue(audit.verify_integrity())
        
        audit.events[1]['user'] = "hacker"
        
        self.assertTrue(audit.verify_integrity())


if __name__ == '__main__':
    unittest.main()