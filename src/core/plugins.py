"""Plugin system for extending functionality"""
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Any, Optional, Type
from abc import ABC, abstractmethod
import json
import logging

class Plugin(ABC):
    """Base class for all plugins"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.version = "1.0.0"
        self.description = "No description provided"
        self.author = "Unknown"
        self.enabled = True
        self.config = {}
    
    @abstractmethod
    def initialize(self, app_context: Dict[str, Any]) -> bool:
        """Initialize the plugin with application context"""
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute plugin functionality"""
        pass
    
    def configure(self, config: Dict[str, Any]):
        """Configure the plugin"""
        self.config = config
    
    def cleanup(self):
        """Cleanup plugin resources"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'enabled': self.enabled
        }

class DetectionPlugin(Plugin):
    """Base class for detection plugins"""
    
    @abstractmethod
    def detect(self, screenshot: Any) -> Optional[Dict]:
        """Perform detection on screenshot"""
        pass

class AIProviderPlugin(Plugin):
    """Base class for AI provider plugins"""
    
    @abstractmethod
    def query(self, question: str, context: str, options: List[str]) -> Optional[str]:
        """Query AI for answer"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass

class AutomationPlugin(Plugin):
    """Base class for automation plugins"""
    
    @abstractmethod
    def automate(self, action: str, parameters: Dict) -> bool:
        """Perform automation action"""
        pass

class PluginManager:
    """Manages plugin loading and execution"""
    
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_types: Dict[Type, List[str]] = {
            DetectionPlugin: [],
            AIProviderPlugin: [],
            AutomationPlugin: [],
            Plugin: []
        }
        
        self.logger = logging.getLogger("PluginManager")
        
        # Create plugin directory if it doesn't exist
        self.plugin_dir.mkdir(exist_ok=True)
        
        # Load plugin manifest
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> Dict:
        """Load plugin manifest"""
        manifest_file = self.plugin_dir / "manifest.json"
        
        if manifest_file.exists():
            try:
                with open(manifest_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load manifest: {e}")
        
        return {'plugins': [], 'disabled': []}
    
    def _save_manifest(self):
        """Save plugin manifest"""
        manifest_file = self.plugin_dir / "manifest.json"
        
        try:
            with open(manifest_file, 'w') as f:
                json.dump(self.manifest, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save manifest: {e}")
    
    def discover_plugins(self):
        """Discover plugins in plugin directory"""
        discovered = []
        
        # Look for Python files in plugin directory
        for file_path in self.plugin_dir.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            
            module_name = file_path.stem
            
            try:
                # Import module
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{module_name}", 
                    file_path
                )
                
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find plugin classes
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, Plugin) and 
                            obj != Plugin and
                            not name.startswith("_")):
                            
                            plugin_info = {
                                'module': module_name,
                                'class': name,
                                'file': str(file_path)
                            }
                            
                            discovered.append(plugin_info)
                            self.logger.info(f"Discovered plugin: {name} in {module_name}")
            
            except Exception as e:
                self.logger.error(f"Failed to load module {module_name}: {e}")
        
        # Update manifest
        self.manifest['plugins'] = discovered
        self._save_manifest()
        
        return discovered
    
    def load_plugin(self, plugin_info: Dict, app_context: Dict[str, Any] = None) -> bool:
        """Load a specific plugin"""
        try:
            # Import module
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_info['module']}", 
                plugin_info['file']
            )
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Get plugin class
                plugin_class = getattr(module, plugin_info['class'])
                
                # Instantiate plugin
                plugin = plugin_class()
                
                # Check if disabled
                if plugin.name in self.manifest.get('disabled', []):
                    plugin.enabled = False
                
                # Initialize plugin
                if plugin.enabled and app_context:
                    if not plugin.initialize(app_context):
                        self.logger.warning(f"Plugin {plugin.name} initialization failed")
                        return False
                
                # Register plugin
                self.plugins[plugin.name] = plugin
                
                # Categorize by type
                for plugin_type in self.plugin_types:
                    if isinstance(plugin, plugin_type):
                        self.plugin_types[plugin_type].append(plugin.name)
                        break
                
                self.logger.info(f"Loaded plugin: {plugin.name}")
                return True
        
        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_info}: {e}")
            return False
    
    def load_all_plugins(self, app_context: Dict[str, Any] = None):
        """Load all discovered plugins"""
        for plugin_info in self.manifest.get('plugins', []):
            self.load_plugin(plugin_info, app_context)
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a specific plugin"""
        return self.plugins.get(name)
    
    def get_plugins_by_type(self, plugin_type: Type) -> List[Plugin]:
        """Get all plugins of a specific type"""
        plugin_names = self.plugin_types.get(plugin_type, [])
        return [self.plugins[name] for name in plugin_names if name in self.plugins]
    
    def execute_plugin(self, name: str, *args, **kwargs) -> Any:
        """Execute a specific plugin"""
        plugin = self.get_plugin(name)
        
        if not plugin:
            raise ValueError(f"Plugin {name} not found")
        
        if not plugin.enabled:
            raise ValueError(f"Plugin {name} is disabled")
        
        return plugin.execute(*args, **kwargs)
    
    def enable_plugin(self, name: str):
        """Enable a plugin"""
        if name in self.plugins:
            self.plugins[name].enabled = True
            
            # Update manifest
            if name in self.manifest.get('disabled', []):
                self.manifest['disabled'].remove(name)
                self._save_manifest()
    
    def disable_plugin(self, name: str):
        """Disable a plugin"""
        if name in self.plugins:
            self.plugins[name].enabled = False
            
            # Update manifest
            if 'disabled' not in self.manifest:
                self.manifest['disabled'] = []
            
            if name not in self.manifest['disabled']:
                self.manifest['disabled'].append(name)
                self._save_manifest()
    
    def unload_plugin(self, name: str):
        """Unload a plugin"""
        if name in self.plugins:
            # Cleanup
            self.plugins[name].cleanup()
            
            # Remove from registry
            del self.plugins[name]
            
            # Remove from type registry
            for plugin_type in self.plugin_types:
                if name in self.plugin_types[plugin_type]:
                    self.plugin_types[plugin_type].remove(name)
            
            self.logger.info(f"Unloaded plugin: {name}")
    
    def reload_plugin(self, name: str, app_context: Dict[str, Any] = None):
        """Reload a plugin"""
        # Find plugin info
        plugin_info = None
        for info in self.manifest.get('plugins', []):
            if info['class'] == name:
                plugin_info = info
                break
        
        if not plugin_info:
            raise ValueError(f"Plugin {name} not in manifest")
        
        # Unload if loaded
        if name in self.plugins:
            self.unload_plugin(name)
        
        # Reload
        return self.load_plugin(plugin_info, app_context)
    
    def get_plugin_list(self) -> List[Dict[str, Any]]:
        """Get list of all plugins with their info"""
        plugin_list = []
        
        for name, plugin in self.plugins.items():
            info = plugin.get_info()
            info['loaded'] = True
            info['type'] = plugin.__class__.__bases__[0].__name__
            plugin_list.append(info)
        
        return plugin_list

# Example plugin implementation
class ExampleDetectionPlugin(DetectionPlugin):
    """Example detection plugin"""
    
    def __init__(self):
        super().__init__()
        self.name = "ExampleDetection"
        self.version = "1.0.0"
        self.description = "Example detection plugin for demonstration"
        self.author = "QuestionAssistant Team"
    
    def initialize(self, app_context: Dict[str, Any]) -> bool:
        """Initialize the plugin"""
        self.logger = app_context.get('logger')
        self.config_manager = app_context.get('config_manager')
        return True
    
    def detect(self, screenshot: Any) -> Optional[Dict]:
        """Perform detection"""
        # Example detection logic
        return {
            'detected': False,
            'confidence': 0.0,
            'message': 'Example detection result'
        }
    
    def execute(self, *args, **kwargs) -> Any:
        """Execute plugin"""
        if 'screenshot' in kwargs:
            return self.detect(kwargs['screenshot'])
        return None

# Global plugin manager instance
plugin_manager = PluginManager()