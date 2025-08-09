"""Performance optimization and resource management"""
import psutil
import gc
import threading
import time
import numpy as np
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
import queue
import weakref
from pathlib import Path
import json
import logging

class PowerMode(Enum):
    """Power consumption modes"""
    HIGH_PERFORMANCE = "high"
    BALANCED = "balanced"
    POWER_SAVER = "saver"
    ADAPTIVE = "adaptive"

class Priority(Enum):
    """Processing priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    IDLE = 5

@dataclass
class ResourceProfile:
    """System resource profile"""
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    battery_percent: Optional[float]
    power_plugged: bool
    process_count: int
    thread_count: int
    
    @property
    def is_low_resource(self) -> bool:
        """Check if system is low on resources"""
        return (self.cpu_percent > 80 or 
                self.memory_percent > 85 or
                (self.battery_percent and self.battery_percent < 20))
    
    @property
    def is_high_load(self) -> bool:
        """Check if system is under high load"""
        return self.cpu_percent > 60 or self.memory_percent > 70

class ResourceManager:
    """Manages application resource usage"""
    
    def __init__(self):
        self.logger = logging.getLogger("ResourceManager")
        self.power_mode = PowerMode.BALANCED
        self.process = psutil.Process()
        
        # Resource limits
        self.limits = {
            PowerMode.HIGH_PERFORMANCE: {
                'cpu_percent': 50,
                'memory_mb': 500,
                'threads': 20,
                'screenshot_interval': 2
            },
            PowerMode.BALANCED: {
                'cpu_percent': 30,
                'memory_mb': 300,
                'threads': 10,
                'screenshot_interval': 5
            },
            PowerMode.POWER_SAVER: {
                'cpu_percent': 15,
                'memory_mb': 150,
                'threads': 5,
                'screenshot_interval': 10
            }
        }
        
        # Monitoring
        self.monitoring = False
        self.monitor_thread = None
        self.resource_profile = None
        
        # Callbacks for mode changes
        self.mode_change_callbacks = []
    
    def start_monitoring(self):
        """Start resource monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Get current resource usage
                self.resource_profile = self._get_resource_profile()
                
                # Adaptive mode adjustments
                if self.power_mode == PowerMode.ADAPTIVE:
                    self._adjust_adaptive_mode()
                
                # Check limits
                self._enforce_limits()
                
                time.sleep(5)
            
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
    
    def _get_resource_profile(self) -> ResourceProfile:
        """Get current system resource profile"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        battery = psutil.sensors_battery()
        battery_percent = battery.percent if battery else None
        power_plugged = battery.power_plugged if battery else True
        
        process_count = len(psutil.pids())
        thread_count = threading.active_count()
        
        return ResourceProfile(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_mb=memory.used / (1024 * 1024),
            battery_percent=battery_percent,
            power_plugged=power_plugged,
            process_count=process_count,
            thread_count=thread_count
        )
    
    def _adjust_adaptive_mode(self):
        """Automatically adjust power mode based on conditions"""
        if not self.resource_profile:
            return
        
        profile = self.resource_profile
        
        # Determine best mode
        if profile.battery_percent and profile.battery_percent < 30 and not profile.power_plugged:
            new_mode = PowerMode.POWER_SAVER
        elif profile.is_high_load:
            new_mode = PowerMode.POWER_SAVER
        elif profile.is_low_resource:
            new_mode = PowerMode.BALANCED
        else:
            new_mode = PowerMode.HIGH_PERFORMANCE
        
        # Change mode if needed
        if new_mode != self.power_mode:
            self.set_power_mode(new_mode)
    
    def _enforce_limits(self):
        """Enforce resource limits based on current mode"""
        limits = self.get_current_limits()
        
        # CPU limiting
        cpu_percent = self.process.cpu_percent()
        if cpu_percent > limits['cpu_percent']:
            self._throttle_cpu()
        
        # Memory limiting
        memory_mb = self.process.memory_info().rss / (1024 * 1024)
        if memory_mb > limits['memory_mb']:
            self._reduce_memory()
    
    def _throttle_cpu(self):
        """Reduce CPU usage"""
        # Lower process priority on Windows
        try:
            import win32process
            import win32api
            
            handle = win32api.GetCurrentProcess()
            win32process.SetPriorityClass(handle, win32process.BELOW_NORMAL_PRIORITY_CLASS)
        except:
            pass
        
        # Add small delays to processing loops
        time.sleep(0.01)
    
    def _reduce_memory(self):
        """Reduce memory usage"""
        # Force garbage collection
        gc.collect()
        gc.collect(2)  # Full collection
        
        # Clear caches
        self._clear_caches()
        
        # Log memory reduction
        before = self.process.memory_info().rss / (1024 * 1024)
        gc.collect()
        after = self.process.memory_info().rss / (1024 * 1024)
        
        if before - after > 10:
            self.logger.info(f"Memory reduced by {before - after:.1f} MB")
    
    def _clear_caches(self):
        """Clear application caches"""
        # This would clear various caches in the application
        pass
    
    def set_power_mode(self, mode: PowerMode):
        """Set power consumption mode"""
        old_mode = self.power_mode
        self.power_mode = mode
        
        self.logger.info(f"Power mode changed: {old_mode.value} -> {mode.value}")
        
        # Notify callbacks
        for callback in self.mode_change_callbacks:
            try:
                callback(mode)
            except:
                pass
    
    def get_current_limits(self) -> Dict[str, Any]:
        """Get current resource limits"""
        if self.power_mode == PowerMode.ADAPTIVE:
            # Use balanced as base for adaptive
            return self.limits[PowerMode.BALANCED].copy()
        return self.limits.get(self.power_mode, self.limits[PowerMode.BALANCED])
    
    def register_mode_change_callback(self, callback: Callable):
        """Register callback for mode changes"""
        self.mode_change_callbacks.append(callback)

class MemoryPool:
    """Memory pool for efficient allocation"""
    
    def __init__(self, object_type, pool_size: int = 10):
        self.object_type = object_type
        self.pool_size = pool_size
        self.pool = []
        self.in_use = weakref.WeakSet()
        
        # Pre-allocate objects
        self._expand_pool()
    
    def _expand_pool(self):
        """Expand the object pool"""
        for _ in range(self.pool_size):
            obj = self.object_type()
            self.pool.append(obj)
    
    def acquire(self):
        """Get object from pool"""
        if not self.pool:
            self._expand_pool()
        
        if self.pool:
            obj = self.pool.pop()
            self.in_use.add(obj)
            return obj
        
        # Fallback to new allocation
        return self.object_type()
    
    def release(self, obj):
        """Return object to pool"""
        if obj in self.in_use:
            self.in_use.discard(obj)
            
            # Reset object if it has a reset method
            if hasattr(obj, 'reset'):
                obj.reset()
            
            if len(self.pool) < self.pool_size * 2:
                self.pool.append(obj)

class LazyLoader:
    """Lazy loading for expensive modules"""
    
    def __init__(self):
        self._modules = {}
        self._loaders = {}
    
    def register(self, name: str, loader: Callable):
        """Register a module loader"""
        self._loaders[name] = loader
    
    def get(self, name: str):
        """Get or load a module"""
        if name not in self._modules:
            if name in self._loaders:
                self._modules[name] = self._loaders[name]()
                logging.info(f"Lazy loaded module: {name}")
        
        return self._modules.get(name)
    
    def unload(self, name: str):
        """Unload a module to free memory"""
        if name in self._modules:
            del self._modules[name]
            gc.collect()

class ProcessingQueue:
    """Priority-based processing queue"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.queue = queue.PriorityQueue()
        self.workers = []
        self.running = False
    
    def start(self):
        """Start processing workers"""
        self.running = True
        
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self.workers.append(worker)
    
    def stop(self):
        """Stop processing workers"""
        self.running = False
        
        # Add stop signals
        for _ in range(self.max_workers):
            self.queue.put((Priority.CRITICAL.value, None, None))
        
        # Wait for workers
        for worker in self.workers:
            worker.join(timeout=2)
    
    def _worker(self):
        """Worker thread for processing"""
        while self.running:
            try:
                priority, func, args = self.queue.get(timeout=1)
                
                if func is None:  # Stop signal
                    break
                
                # Process task
                func(*args) if args else func()
                
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Processing error: {e}")
    
    def add_task(self, func: Callable, args: tuple = None, priority: Priority = Priority.NORMAL):
        """Add task to processing queue"""
        self.queue.put((priority.value, func, args))
    
    def adjust_workers(self, num_workers: int):
        """Dynamically adjust number of workers"""
        if num_workers > self.max_workers:
            # Add workers
            for _ in range(num_workers - self.max_workers):
                worker = threading.Thread(target=self._worker, daemon=True)
                worker.start()
                self.workers.append(worker)
        
        elif num_workers < self.max_workers:
            # Remove workers
            for _ in range(self.max_workers - num_workers):
                self.queue.put((Priority.CRITICAL.value, None, None))
        
        self.max_workers = num_workers

class ImageOptimizer:
    """Optimize image processing for performance"""
    
    @staticmethod
    def downsample(image: np.ndarray, factor: float = 0.5) -> np.ndarray:
        """Downsample image for faster processing"""
        import cv2
        
        if factor >= 1.0:
            return image
        
        height, width = image.shape[:2]
        new_size = (int(width * factor), int(height * factor))
        
        return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
    
    @staticmethod
    def to_grayscale(image: np.ndarray) -> np.ndarray:
        """Convert to grayscale to reduce data"""
        import cv2
        
        if len(image.shape) == 2:
            return image
        
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    @staticmethod
    def compress(image: np.ndarray, quality: int = 85) -> bytes:
        """Compress image for storage/transmission"""
        import cv2
        
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        _, encoded = cv2.imencode('.jpg', image, encode_params)
        
        return encoded.tobytes()
    
    @staticmethod
    def roi_extraction(image: np.ndarray, regions: List[tuple]) -> List[np.ndarray]:
        """Extract regions of interest instead of full image"""
        rois = []
        
        for x, y, w, h in regions:
            roi = image[y:y+h, x:x+w]
            rois.append(roi)
        
        return rois

class CacheManager:
    """Intelligent caching system"""
    
    def __init__(self, max_size_mb: int = 100):
        self.max_size = max_size_mb * 1024 * 1024  # Convert to bytes
        self.cache = {}
        self.access_times = {}
        self.sizes = {}
        self.total_size = 0
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self.lock:
            if key in self.cache:
                self.access_times[key] = time.time()
                return self.cache[key]
        return None
    
    def put(self, key: str, value: Any, size_bytes: int = None):
        """Add item to cache"""
        if size_bytes is None:
            size_bytes = len(str(value).encode())
        
        with self.lock:
            # Remove old item if exists
            if key in self.cache:
                self.total_size -= self.sizes.get(key, 0)
            
            # Check if we need to evict items
            while self.total_size + size_bytes > self.max_size and self.cache:
                self._evict_lru()
            
            # Add new item
            self.cache[key] = value
            self.sizes[key] = size_bytes
            self.access_times[key] = time.time()
            self.total_size += size_bytes
    
    def _evict_lru(self):
        """Evict least recently used item"""
        if not self.cache:
            return
        
        # Find LRU item
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        
        # Remove it
        self.total_size -= self.sizes.get(lru_key, 0)
        del self.cache[lru_key]
        del self.access_times[lru_key]
        del self.sizes[lru_key]
    
    def clear(self):
        """Clear entire cache"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.sizes.clear()
            self.total_size = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'items': len(self.cache),
            'size_mb': self.total_size / (1024 * 1024),
            'max_size_mb': self.max_size / (1024 * 1024),
            'hit_rate': self._calculate_hit_rate()
        }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        # This would track hits and misses
        return 0.0

# Global instances
resource_manager = ResourceManager()
lazy_loader = LazyLoader()
cache_manager = CacheManager(max_size_mb=50)
processing_queue = ProcessingQueue()

# Start resource monitoring
resource_manager.start_monitoring()
processing_queue.start()