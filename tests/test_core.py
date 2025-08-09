"""Unit tests for core functionality"""
import unittest
import tempfile
import json
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import Config
from src.core.exceptions import ConfigurationError
from src.utils.security import SecurityManager, InputValidator, RateLimiter
from src.utils.logger import Logger

class TestConfig(unittest.TestCase):
    """Test configuration management"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"
    
    def test_default_config(self):
        """Test default configuration values"""
        config = Config(str(self.config_path))
        
        self.assertEqual(config.get('monitoring_interval'), 5)
        self.assertEqual(config.get('duration_minutes'), 60)
        self.assertEqual(config.get('question_type'), 'Multiple Choice')
    
    def test_config_validation(self):
        """Test configuration validation"""
        config = Config(str(self.config_path))
        
        # Test invalid values
        with self.assertRaises(ConfigurationError):
            config.set('monitoring_interval', 0)
            config._validate_config()
        
        with self.assertRaises(ConfigurationError):
            config.set('duration_minutes', 1000)
            config._validate_config()
    
    def test_config_persistence(self):
        """Test configuration save and load"""
        config = Config(str(self.config_path))
        
        # Set values
        config.set('api_key', 'test_key')
        config.set('context', 'test context')
        config.save()
        
        # Load in new instance
        config2 = Config(str(self.config_path))
        
        self.assertEqual(config2.get('api_key'), 'test_key')
        self.assertEqual(config2.get('context'), 'test context')
    
    def test_dot_notation(self):
        """Test dot notation for nested values"""
        config = Config(str(self.config_path))
        
        # Test getting nested values
        self.assertEqual(config.get('human_simulation.typing_speed_min'), 0.05)
        
        # Test setting nested values
        config.set('human_simulation.typing_speed_min', 0.1)
        self.assertEqual(config.get('human_simulation.typing_speed_min'), 0.1)

class TestSecurity(unittest.TestCase):
    """Test security features"""
    
    def setUp(self):
        self.security = SecurityManager()
        self.validator = InputValidator()
        self.rate_limiter = RateLimiter()
    
    def test_encryption(self):
        """Test data encryption and decryption"""
        original = "sensitive_api_key_12345"
        
        # Encrypt
        encrypted = self.security.encrypt_data(original)
        self.assertNotEqual(encrypted, original)
        
        # Decrypt
        decrypted = self.security.decrypt_data(encrypted)
        self.assertEqual(decrypted, original)
    
    def test_password_hashing(self):
        """Test password hashing"""
        password = "SecurePassword123!"
        
        # Hash password
        hashed = self.security.hash_password(password)
        self.assertNotEqual(hashed, password)
        
        # Verify correct password
        self.assertTrue(self.security.verify_password(password, hashed))
        
        # Verify incorrect password
        self.assertFalse(self.security.verify_password("wrong", hashed))
    
    def test_input_validation(self):
        """Test input validation"""
        # API key validation
        self.assertTrue(self.validator.validate_api_key("sk-" + "a" * 48))
        self.assertFalse(self.validator.validate_api_key("short"))
        
        # Duration validation
        self.assertTrue(self.validator.validate_duration(60))
        self.assertFalse(self.validator.validate_duration(0))
        self.assertFalse(self.validator.validate_duration(1000))
        
        # Path sanitization
        dangerous_path = "../../../etc/passwd"
        sanitized = self.validator.sanitize_path(dangerous_path)
        self.assertNotIn("..", sanitized)
        
        # Context sanitization
        context = "<script>alert('xss')</script>Test context"
        sanitized = self.validator.sanitize_context(context)
        self.assertNotIn("<script>", sanitized)
    
    def test_rate_limiting(self):
        """Test rate limiting"""
        import time
        
        # Set limit: 2 attempts per second
        self.rate_limiter.set_limit("test_op", max_attempts=2, window_seconds=1)
        
        # First two attempts should pass
        self.assertTrue(self.rate_limiter.check_limit("test_op"))
        self.assertTrue(self.rate_limiter.check_limit("test_op"))
        
        # Third attempt should fail
        self.assertFalse(self.rate_limiter.check_limit("test_op"))
        
        # Check wait time
        wait_time = self.rate_limiter.get_wait_time("test_op")
        self.assertGreater(wait_time, 0)

class TestLogger(unittest.TestCase):
    """Test logging functionality"""
    
    def test_logger_singleton(self):
        """Test logger singleton pattern"""
        logger1 = Logger()
        logger2 = Logger()
        
        self.assertIs(logger1, logger2)
    
    def test_logger_methods(self):
        """Test logger methods"""
        logger = Logger.get_logger("test")
        
        # Should not raise exceptions
        logger.info("Test info")
        logger.debug("Test debug")
        logger.error("Test error")
        
        Logger.log_exception(Exception("Test"), "test context")
        Logger.log_performance("test operation", 1.5)
        Logger.log_detection("Test question?", 0.85, "Test answer")

class TestDetection(unittest.TestCase):
    """Test question detection"""
    
    def test_confidence_calculation(self):
        """Test confidence score calculation"""
        # This would test the detection confidence algorithm
        pass
    
    def test_duplicate_detection(self):
        """Test duplicate question detection"""
        # This would test duplicate detection logic
        pass

class TestAutomation(unittest.TestCase):
    """Test automation features"""
    
    def test_human_simulation(self):
        """Test human-like behavior simulation"""
        # This would test mouse/keyboard simulation
        pass
    
    def test_answer_strategies(self):
        """Test different answer strategies"""
        # This would test multiple choice, true/false, etc.
        pass

if __name__ == '__main__':
    unittest.main()