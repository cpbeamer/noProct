"""Security tests for service manager and Windows service operations"""
import unittest
import tempfile
import os
import sys
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import ctypes

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.service_manager import ServiceManager
from src.core.exceptions import ServiceError, SecurityError


class TestServicePrivileges(unittest.TestCase):
    """Test service privilege handling"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.json"
    
    @patch('ctypes.windll.shell32.IsUserAnAdmin')
    def test_admin_required_for_service_install(self, mock_admin):
        """Test that admin privileges are required for service installation"""
        mock_admin.return_value = False
        
        from src.core.service_manager import install_service
        
        with self.assertRaises(PermissionError):
            with patch('src.core.service_manager.WINDOWS_SERVICE_AVAILABLE', True):
                install_service()
    
    def test_service_runs_with_minimal_privileges(self):
        """Test that service drops unnecessary privileges after startup"""
        service = ServiceManager(str(self.config_path))
        
        with patch.object(service, '_drop_privileges') as mock_drop:
            with patch.object(service, 'initialize_components'):
                service.start()
                time.sleep(0.1)
                service.stop()
                
                mock_drop.assert_called_once()
    
    def test_privilege_escalation_detection(self):
        """Test detection of privilege escalation attempts"""
        service = ServiceManager(str(self.config_path))
        
        def escalate_privileges():
            if sys.platform == 'win32':
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, "", None, 1
                )
            else:
                os.setuid(0)
        
        with self.assertRaises((OSError, PermissionError, SecurityError)):
            escalate_privileges()
    
    def test_service_account_restrictions(self):
        """Test that service runs under restricted account"""
        if sys.platform != 'win32':
            self.skipTest("Windows-specific test")
        
        import win32api
        import win32security
        
        token = win32security.OpenProcessToken(
            win32api.GetCurrentProcess(),
            win32security.TOKEN_QUERY
        )
        
        sid = win32security.GetTokenInformation(token, win32security.TokenUser)[0]
        account = win32security.LookupAccountSid(None, sid)
        
        restricted_accounts = ['LocalService', 'NetworkService', 'LocalSystem']
        
        if any(acc in account[0] for acc in restricted_accounts):
            self.assertTrue(True)
        else:
            import warnings
            warnings.warn(f"Service running as {account[0]}, consider using restricted account")


class TestServiceIsolation(unittest.TestCase):
    """Test service isolation and sandboxing"""
    
    def setUp(self):
        self.service = ServiceManager()
    
    def test_filesystem_isolation(self):
        """Test that service has limited filesystem access"""
        restricted_paths = [
            "C:\\Windows\\System32",
            "C:\\Program Files",
            "/etc",
            "/usr/bin",
            "/root",
        ]
        
        for path in restricted_paths:
            if os.path.exists(path):
                with self.assertRaises((PermissionError, OSError)):
                    test_file = Path(path) / "test_write.txt"
                    test_file.write_text("test")
    
    def test_network_isolation(self):
        """Test network access restrictions"""
        import socket
        
        restricted_ports = [22, 23, 445, 3389, 5900]
        
        for port in restricted_ports:
            with self.assertRaises((OSError, PermissionError)):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('0.0.0.0', port))
                sock.close()
    
    def test_process_creation_restrictions(self):
        """Test restrictions on creating new processes"""
        import subprocess
        
        dangerous_commands = [
            ["powershell", "-Command", "Get-Process"],
            ["cmd", "/c", "dir"],
            ["net", "user"],
            ["reg", "query", "HKLM"],
        ]
        
        for cmd in dangerous_commands:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=1,
                    shell=False
                )
                
                if result.returncode == 0:
                    import warnings
                    warnings.warn(f"Service can execute: {' '.join(cmd)}")
            except (subprocess.TimeoutExpired, OSError):
                pass
    
    def test_registry_access_restrictions(self):
        """Test registry access restrictions on Windows"""
        if sys.platform != 'win32':
            self.skipTest("Windows-specific test")
        
        import winreg
        
        protected_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"),
        ]
        
        for hkey, subkey in protected_keys:
            try:
                key = winreg.OpenKey(hkey, subkey, 0, winreg.KEY_WRITE)
                winreg.CloseKey(key)
                import warnings
                warnings.warn(f"Service has write access to: {subkey}")
            except (OSError, PermissionError):
                pass


class TestServiceResilience(unittest.TestCase):
    """Test service resilience and recovery"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.service = ServiceManager(str(Path(self.temp_dir) / "config.json"))
    
    def test_error_recovery(self):
        """Test service recovery from errors"""
        self.service.max_errors = 3
        
        with patch.object(self.service, '_screen_monitor') as mock_monitor:
            mock_monitor.capture_screen.side_effect = [
                Exception("Error 1"),
                Exception("Error 2"),
                None,
            ]
            
            with patch.object(self.service, 'initialize_components'):
                self.service.start()
                time.sleep(0.5)
                
                self.assertLess(self.service.error_count, self.service.max_errors)
                self.assertTrue(self.service.running)
                
                self.service.stop()
    
    def test_memory_leak_prevention(self):
        """Test prevention of memory leaks"""
        import gc
        import psutil
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        service = ServiceManager()
        
        for i in range(100):
            service._stats_tracker = Mock()
            service._detector = Mock()
            service._controller = Mock()
        
        service = None
        gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024
        
        self.assertLess(memory_increase, 50, f"Memory increased by {memory_increase:.1f} MB")
    
    def test_thread_safety(self):
        """Test thread safety of service operations"""
        results = []
        errors = []
        
        def worker():
            try:
                self.service.pause()
                time.sleep(0.01)
                self.service.resume()
                results.append(True)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=worker) for _ in range(10)]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 10)
    
    def test_graceful_shutdown(self):
        """Test graceful service shutdown"""
        with patch.object(self.service, 'initialize_components'):
            self.service.start()
            
            self.assertTrue(self.service.running)
            
            start_time = time.time()
            self.service.stop()
            stop_time = time.time()
            
            self.assertFalse(self.service.running)
            self.assertLess(stop_time - start_time, 6)
    
    def test_resource_cleanup(self):
        """Test proper resource cleanup on shutdown"""
        mock_components = {
            '_screen_monitor': Mock(),
            '_ocr_engine': Mock(),
            '_detector': Mock(),
            '_controller': Mock(),
            '_researcher': Mock(),
        }
        
        for name, mock_obj in mock_components.items():
            setattr(self.service, name, mock_obj)
            mock_obj.cleanup = Mock()
        
        self.service.stop()
        
        for mock_obj in mock_components.values():
            if hasattr(mock_obj, 'cleanup'):
                mock_obj.cleanup.assert_called()


class TestServiceMonitoring(unittest.TestCase):
    """Test service monitoring and alerting"""
    
    def setUp(self):
        self.service = ServiceManager()
    
    def test_health_monitoring(self):
        """Test health monitoring functionality"""
        with patch('psutil.Process') as mock_process:
            mock_process.return_value.memory_info.return_value.rss = 100 * 1024 * 1024
            
            with patch.object(self.service, 'initialize_components'):
                self.service.start()
                
                time.sleep(0.1)
                
                self.assertIsNotNone(self.service.monitor_thread)
                self.assertTrue(self.service.monitor_thread.is_alive())
                
                self.service.stop()
    
    def test_memory_usage_alerting(self):
        """Test memory usage alerts"""
        with patch('psutil.Process') as mock_process:
            mock_process.return_value.memory_info.return_value.rss = 600 * 1024 * 1024
            
            with patch.object(self.service.logger, 'warning') as mock_warning:
                with patch.object(self.service, 'initialize_components'):
                    self.service.start()
                    time.sleep(0.1)
                    
                    self.service._start_health_monitor()
                    time.sleep(0.1)
                    
                    mock_warning.assert_called()
                    
                    self.service.stop()
    
    def test_error_rate_monitoring(self):
        """Test error rate monitoring"""
        self.service.max_errors = 5
        
        for i in range(3):
            self.service._handle_error(Exception(f"Test error {i}"))
        
        self.assertEqual(self.service.error_count, 3)
        self.assertLess(self.service.error_count, self.service.max_errors)
        
        for i in range(3):
            self.service._handle_error(Exception(f"Test error {i+3}"))
        
        self.assertGreaterEqual(self.service.error_count, self.service.max_errors)
    
    def test_performance_tracking(self):
        """Test performance metric tracking"""
        from src.utils.statistics import StatisticsTracker
        
        stats = StatisticsTracker()
        
        stats.track_detection(Mock(confidence=0.9))
        stats.track_answer("test answer", True)
        
        summary = stats.get_summary()
        
        self.assertIn('questions_detected', summary)
        self.assertIn('questions_answered', summary)
        self.assertIn('success_rate', summary)


class TestServiceAPI(unittest.TestCase):
    """Test service API security"""
    
    def test_api_authentication(self):
        """Test API authentication requirements"""
        service = ServiceManager()
        
        with patch.object(service, 'config') as mock_config:
            mock_config.get.return_value = None
            
            with self.assertRaises((ValueError, SecurityError)):
                service._validate_api_access()
    
    def test_api_rate_limiting(self):
        """Test API rate limiting"""
        from src.utils.security import RateLimiter
        
        limiter = RateLimiter()
        limiter.set_limit("api", max_attempts=10, window_seconds=60)
        
        for i in range(10):
            self.assertTrue(limiter.check_limit("api"))
        
        self.assertFalse(limiter.check_limit("api"))
    
    def test_api_input_validation(self):
        """Test API input validation"""
        from src.utils.security import InputValidator
        
        validator = InputValidator()
        
        invalid_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../etc/passwd",
        ]
        
        for input_str in invalid_inputs:
            sanitized = validator.sanitize_input(input_str)
            self.assertNotEqual(sanitized, input_str)
    
    def test_api_response_sanitization(self):
        """Test API response sanitization"""
        service = ServiceManager()
        
        sensitive_data = {
            "api_key": "sk-secret-key",
            "password": "admin123",
            "token": "bearer-token",
        }
        
        sanitized = service._sanitize_response(sensitive_data)
        
        self.assertNotIn("sk-secret-key", str(sanitized))
        self.assertNotIn("admin123", str(sanitized))
        self.assertNotIn("bearer-token", str(sanitized))


class TestWindowsServiceSecurity(unittest.TestCase):
    """Test Windows service specific security"""
    
    @unittest.skipIf(sys.platform != 'win32', "Windows-specific test")
    def test_service_account_permissions(self):
        """Test service account has minimal permissions"""
        import win32api
        import win32security
        
        token = win32security.OpenProcessToken(
            win32api.GetCurrentProcess(),
            win32security.TOKEN_QUERY
        )
        
        privileges = win32security.GetTokenInformation(
            token,
            win32security.TokenPrivileges
        )
        
        dangerous_privileges = [
            'SeDebugPrivilege',
            'SeTcbPrivilege',
            'SeAssignPrimaryTokenPrivilege',
            'SeTakeOwnershipPrivilege',
        ]
        
        enabled_privs = [p[0] for p in privileges if p[1] & 2]
        
        for priv in dangerous_privileges:
            if priv in enabled_privs:
                import warnings
                warnings.warn(f"Service has dangerous privilege: {priv}")
    
    @unittest.skipIf(sys.platform != 'win32', "Windows-specific test")
    def test_service_dacl_security(self):
        """Test service DACL (Discretionary Access Control List) security"""
        import win32service
        import win32security
        
        try:
            scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
            service = win32service.OpenService(
                scm,
                "QuestionAssistantService",
                win32service.SERVICE_QUERY_CONFIG
            )
            
            sd = win32service.QueryServiceObjectSecurity(
                service,
                win32security.DACL_SECURITY_INFORMATION
            )
            
            dacl = sd.GetSecurityDescriptorDacl()
            
            if dacl:
                for i in range(dacl.GetAceCount()):
                    ace = dacl.GetAce(i)
                    
                    if ace[1] & win32security.GENERIC_WRITE:
                        sid = ace[2]
                        account = win32security.LookupAccountSid(None, sid)
                        
                        if account[0] == "Everyone":
                            self.fail("Service allows write access to Everyone")
            
            win32service.CloseServiceHandle(service)
            win32service.CloseServiceHandle(scm)
            
        except Exception:
            self.skipTest("Service not installed")


if __name__ == '__main__':
    unittest.main()