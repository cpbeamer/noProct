import json
import os
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_path: str = "config/settings.json"):
        self.config_path = config_path
        self.config = {}
        self.ensure_config_dir()
    
    def ensure_config_dir(self):
        config_dir = os.path.dirname(self.config_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
    
    def save_config(self, config_data: Dict[str, Any]) -> bool:
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=4)
            self.config = config_data
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def load_config(self) -> Dict[str, Any]:
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            return self.config
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def get(self, key: str, default=None):
        return self.config.get(key, default)