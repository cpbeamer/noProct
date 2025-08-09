import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging
from .exceptions import ConfigurationError

class Config:
    """Enhanced configuration manager with validation and defaults"""
    
    DEFAULT_CONFIG = {
        "monitoring_interval": 5,
        "abort_key": "esc",
        "duration_minutes": 60,
        "num_questions": 10,
        "question_type": "Multiple Choice",
        "context": "",
        "api_key": "",
        "tesseract_path": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        "confidence_threshold": 0.5,
        "ocr_preprocessing": True,
        "human_simulation": {
            "typing_speed_min": 0.05,
            "typing_speed_max": 0.15,
            "mouse_speed_min": 0.3,
            "mouse_speed_max": 0.8,
            "action_delay_min": 0.5,
            "action_delay_max": 2.0
        },
        "detection": {
            "template_matching_threshold": 0.8,
            "text_similarity_threshold": 0.8,
            "min_question_length": 10,
            "max_question_length": 500
        },
        "logging": {
            "level": "INFO",
            "file": "logs/service.log",
            "max_size": 10485760,
            "backup_count": 5
        },
        "performance": {
            "enable_caching": True,
            "cache_ttl": 300,
            "parallel_processing": True,
            "max_workers": 4
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path or "config/settings.json")
        self.config = self.DEFAULT_CONFIG.copy()
        self._ensure_directories()
        self.load()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        dirs = [
            self.config_path.parent,
            Path("logs"),
            Path("templates"),
            Path("cache")
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from file with validation"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    self.config = self._merge_configs(self.DEFAULT_CONFIG, user_config)
                    self._validate_config()
            else:
                logging.info("No config file found, using defaults")
                self.save()
            return self.config
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load config: {e}")
    
    def save(self) -> bool:
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
            return False
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Recursively merge user config with defaults"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _validate_config(self):
        """Validate configuration values"""
        if self.config["monitoring_interval"] < 1:
            raise ConfigurationError("Monitoring interval must be at least 1 second")
        
        if self.config["duration_minutes"] < 1 or self.config["duration_minutes"] > 600:
            raise ConfigurationError("Duration must be between 1 and 600 minutes")
        
        if self.config["num_questions"] < 1 or self.config["num_questions"] > 1000:
            raise ConfigurationError("Number of questions must be between 1 and 1000")
        
        if self.config["confidence_threshold"] < 0 or self.config["confidence_threshold"] > 1:
            raise ConfigurationError("Confidence threshold must be between 0 and 1")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation support"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value with dot notation support"""
        keys = key.split('.')
        target = self.config
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        return self.save()
    
    def update(self, updates: Dict[str, Any]) -> bool:
        """Update multiple configuration values"""
        self.config = self._merge_configs(self.config, updates)
        self._validate_config()
        return self.save()