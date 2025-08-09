"""Analytics and crash reporting utilities"""
import sys
import traceback
import platform
import json
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import threading
import queue
import requests

class CrashReporter:
    """Handles crash reporting and error tracking"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.crash_dir = Path("data/crashes")
        self.crash_dir.mkdir(parents=True, exist_ok=True)
        
        # Anonymous user ID for tracking
        self.user_id = self._get_or_create_user_id()
        
        # Crash queue for async reporting
        self.crash_queue = queue.Queue()
        self.reporting_thread = None
        
        if enabled:
            self._install_exception_hook()
            self._start_reporting_thread()
    
    def _get_or_create_user_id(self) -> str:
        """Get or create anonymous user ID"""
        id_file = Path("data/.user_id")
        
        if id_file.exists():
            return id_file.read_text().strip()
        
        # Generate new ID
        user_id = str(uuid.uuid4())
        id_file.parent.mkdir(exist_ok=True)
        id_file.write_text(user_id)
        
        return user_id
    
    def _install_exception_hook(self):
        """Install global exception hook"""
        original_hook = sys.excepthook
        
        def exception_hook(exc_type, exc_value, exc_traceback):
            # Call original hook
            original_hook(exc_type, exc_value, exc_traceback)
            
            # Report crash
            self.report_crash(exc_type, exc_value, exc_traceback)
        
        sys.excepthook = exception_hook
    
    def _start_reporting_thread(self):
        """Start background thread for crash reporting"""
        def report_worker():
            while self.enabled:
                try:
                    crash_data = self.crash_queue.get(timeout=1)
                    if crash_data:
                        self._send_crash_report(crash_data)
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"Error in crash reporter: {e}")
        
        self.reporting_thread = threading.Thread(target=report_worker, daemon=True)
        self.reporting_thread.start()
    
    def report_crash(self, exc_type, exc_value, exc_traceback):
        """Report a crash"""
        if not self.enabled:
            return
        
        crash_data = self._collect_crash_data(exc_type, exc_value, exc_traceback)
        
        # Save locally
        self._save_crash_locally(crash_data)
        
        # Queue for remote reporting
        self.crash_queue.put(crash_data)
    
    def _collect_crash_data(self, exc_type, exc_value, exc_traceback) -> Dict[str, Any]:
        """Collect crash data"""
        # Format traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_str = ''.join(tb_lines)
        
        # Collect system info
        system_info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'processor': platform.processor(),
            'machine': platform.machine(),
            'node': hashlib.sha256(platform.node().encode()).hexdigest()[:8]  # Anonymized
        }
        
        # Create crash report
        crash_data = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'user_id': self.user_id,
            'exception': {
                'type': exc_type.__name__ if exc_type else 'Unknown',
                'message': str(exc_value),
                'traceback': tb_str
            },
            'system': system_info,
            'app_version': self._get_app_version()
        }
        
        return crash_data
    
    def _get_app_version(self) -> str:
        """Get application version"""
        try:
            # Try to read from version file
            version_file = Path("version.txt")
            if version_file.exists():
                return version_file.read_text().strip()
        except:
            pass
        
        return "3.0.0"  # Default version
    
    def _save_crash_locally(self, crash_data: Dict[str, Any]):
        """Save crash report locally"""
        try:
            filename = f"crash_{crash_data['id']}.json"
            filepath = self.crash_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(crash_data, f, indent=2)
        
        except Exception as e:
            print(f"Failed to save crash report: {e}")
    
    def _send_crash_report(self, crash_data: Dict[str, Any]):
        """Send crash report to remote server"""
        # Note: In production, this would send to your crash reporting service
        # For now, just log that we would send it
        print(f"Would send crash report: {crash_data['id']}")
        
        # Example implementation:
        # try:
        #     response = requests.post(
        #         "https://your-crash-server.com/api/crashes",
        #         json=crash_data,
        #         timeout=10
        #     )
        #     response.raise_for_status()
        # except Exception as e:
        #     print(f"Failed to send crash report: {e}")
    
    def get_crash_history(self) -> List[Dict[str, Any]]:
        """Get local crash history"""
        crashes = []
        
        for crash_file in self.crash_dir.glob("crash_*.json"):
            try:
                with open(crash_file, 'r') as f:
                    crashes.append(json.load(f))
            except:
                continue
        
        # Sort by timestamp
        crashes.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return crashes

class Analytics:
    """Application analytics and telemetry"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.session_id = str(uuid.uuid4())
        self.events = []
        self.analytics_dir = Path("data/analytics")
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        
        # Event queue for async processing
        self.event_queue = queue.Queue()
        
        if enabled:
            self._start_analytics_thread()
    
    def _start_analytics_thread(self):
        """Start analytics processing thread"""
        def analytics_worker():
            batch = []
            
            while self.enabled:
                try:
                    event = self.event_queue.get(timeout=5)
                    batch.append(event)
                    
                    # Send batch when it reaches certain size
                    if len(batch) >= 10:
                        self._process_event_batch(batch)
                        batch = []
                
                except queue.Empty:
                    # Send remaining events
                    if batch:
                        self._process_event_batch(batch)
                        batch = []
                
                except Exception as e:
                    print(f"Analytics error: {e}")
        
        thread = threading.Thread(target=analytics_worker, daemon=True)
        thread.start()
    
    def track_event(self, category: str, action: str, 
                   label: Optional[str] = None, value: Optional[Any] = None):
        """Track an analytics event"""
        if not self.enabled:
            return
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'category': category,
            'action': action,
            'label': label,
            'value': value
        }
        
        self.events.append(event)
        self.event_queue.put(event)
    
    def track_timing(self, category: str, variable: str, time_ms: int):
        """Track timing information"""
        self.track_event('timing', variable, category, time_ms)
    
    def track_exception(self, description: str, fatal: bool = False):
        """Track exception"""
        self.track_event('exception', description, 'fatal' if fatal else 'non-fatal')
    
    def track_screen_view(self, screen_name: str):
        """Track screen/page view"""
        self.track_event('screen_view', screen_name)
    
    def _process_event_batch(self, batch: List[Dict[str, Any]]):
        """Process a batch of events"""
        # Save locally
        self._save_events_locally(batch)
        
        # In production, send to analytics service
        # self._send_to_analytics_service(batch)
    
    def _save_events_locally(self, events: List[Dict[str, Any]]):
        """Save events to local file"""
        try:
            filename = f"events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.analytics_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(events, f, indent=2)
        
        except Exception as e:
            print(f"Failed to save analytics: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        event_counts = {}
        
        for event in self.events:
            category = event['category']
            if category not in event_counts:
                event_counts[category] = 0
            event_counts[category] += 1
        
        return {
            'session_id': self.session_id,
            'total_events': len(self.events),
            'event_counts': event_counts,
            'duration': self._get_session_duration()
        }
    
    def _get_session_duration(self) -> float:
        """Get session duration in seconds"""
        if not self.events:
            return 0
        
        first = datetime.fromisoformat(self.events[0]['timestamp'])
        last = datetime.fromisoformat(self.events[-1]['timestamp'])
        
        return (last - first).total_seconds()

class FeatureFlags:
    """Manage feature flags for A/B testing"""
    
    def __init__(self):
        self.flags = {}
        self.load_flags()
    
    def load_flags(self):
        """Load feature flags from config"""
        flags_file = Path("config/feature_flags.json")
        
        if flags_file.exists():
            try:
                with open(flags_file, 'r') as f:
                    self.flags = json.load(f)
            except:
                pass
        
        # Default flags
        defaults = {
            'new_detection_algorithm': False,
            'parallel_processing': True,
            'advanced_ocr': True,
            'ml_detection': False,
            'cloud_sync': False,
            'voice_control': False
        }
        
        # Merge with defaults
        for key, value in defaults.items():
            if key not in self.flags:
                self.flags[key] = value
    
    def is_enabled(self, flag: str) -> bool:
        """Check if feature flag is enabled"""
        return self.flags.get(flag, False)
    
    def set_flag(self, flag: str, enabled: bool):
        """Set feature flag"""
        self.flags[flag] = enabled
        self.save_flags()
    
    def save_flags(self):
        """Save feature flags"""
        flags_file = Path("config/feature_flags.json")
        flags_file.parent.mkdir(exist_ok=True)
        
        with open(flags_file, 'w') as f:
            json.dump(self.flags, f, indent=2)
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags"""
        return self.flags.copy()

# Global instances
crash_reporter = CrashReporter(enabled=True)
analytics = Analytics(enabled=True)
feature_flags = FeatureFlags()