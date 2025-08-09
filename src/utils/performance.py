"""Performance monitoring and optimization utilities"""
import time
import psutil
import threading
import cProfile
import pstats
import io
import functools
import gc
from typing import Dict, List, Any, Callable, Optional
from collections import deque
from datetime import datetime
import json
from pathlib import Path

class PerformanceMonitor:
    """Monitor application performance metrics"""
    
    def __init__(self):
        self.metrics = {
            'cpu_usage': deque(maxlen=100),
            'memory_usage': deque(maxlen=100),
            'response_times': deque(maxlen=100),
            'operation_counts': {},
            'error_counts': {},
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        self.process = psutil.Process()
        self.monitoring = False
        self.monitor_thread = None
        
        # Performance thresholds
        self.thresholds = {
            'cpu_warning': 50,
            'cpu_critical': 80,
            'memory_warning': 500,  # MB
            'memory_critical': 1000,  # MB
            'response_time_warning': 2.0,  # seconds
            'response_time_critical': 5.0  # seconds
        }
    
    def start_monitoring(self, interval: int = 5):
        """Start performance monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        
        def monitor():
            while self.monitoring:
                self._collect_metrics()
                time.sleep(interval)
        
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def _collect_metrics(self):
        """Collect current performance metrics"""
        try:
            # CPU usage
            cpu_percent = self.process.cpu_percent()
            self.metrics['cpu_usage'].append({
                'time': datetime.now(),
                'value': cpu_percent
            })
            
            # Memory usage
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            self.metrics['memory_usage'].append({
                'time': datetime.now(),
                'value': memory_mb
            })
            
            # Check thresholds
            self._check_thresholds(cpu_percent, memory_mb)
            
        except Exception as e:
            print(f"Error collecting metrics: {e}")
    
    def _check_thresholds(self, cpu: float, memory: float):
        """Check if metrics exceed thresholds"""
        alerts = []
        
        if cpu > self.thresholds['cpu_critical']:
            alerts.append(('critical', f'CPU usage critical: {cpu:.1f}%'))
        elif cpu > self.thresholds['cpu_warning']:
            alerts.append(('warning', f'CPU usage high: {cpu:.1f}%'))
        
        if memory > self.thresholds['memory_critical']:
            alerts.append(('critical', f'Memory usage critical: {memory:.1f} MB'))
        elif memory > self.thresholds['memory_warning']:
            alerts.append(('warning', f'Memory usage high: {memory:.1f} MB'))
        
        # Log alerts
        for level, message in alerts:
            self._log_alert(level, message)
    
    def _log_alert(self, level: str, message: str):
        """Log performance alert"""
        from src.utils.logger import get_logger
        logger = get_logger("Performance")
        
        if level == 'critical':
            logger.error(f"PERFORMANCE CRITICAL: {message}")
        else:
            logger.warning(f"PERFORMANCE WARNING: {message}")
    
    def record_operation(self, operation: str, duration: float):
        """Record operation timing"""
        if operation not in self.metrics['operation_counts']:
            self.metrics['operation_counts'][operation] = {
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
                'min_time': float('inf'),
                'max_time': 0
            }
        
        stats = self.metrics['operation_counts'][operation]
        stats['count'] += 1
        stats['total_time'] += duration
        stats['avg_time'] = stats['total_time'] / stats['count']
        stats['min_time'] = min(stats['min_time'], duration)
        stats['max_time'] = max(stats['max_time'], duration)
        
        # Check response time threshold
        if duration > self.thresholds['response_time_critical']:
            self._log_alert('critical', f'{operation} took {duration:.2f}s')
        elif duration > self.thresholds['response_time_warning']:
            self._log_alert('warning', f'{operation} took {duration:.2f}s')
    
    def record_error(self, operation: str, error: Exception):
        """Record operation error"""
        if operation not in self.metrics['error_counts']:
            self.metrics['error_counts'][operation] = 0
        
        self.metrics['error_counts'][operation] += 1
    
    def record_cache_hit(self):
        """Record cache hit"""
        self.metrics['cache_hits'] += 1
    
    def record_cache_miss(self):
        """Record cache miss"""
        self.metrics['cache_misses'] += 1
    
    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate"""
        total = self.metrics['cache_hits'] + self.metrics['cache_misses']
        if total == 0:
            return 0.0
        return self.metrics['cache_hits'] / total
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        summary = {
            'current_cpu': self.process.cpu_percent(),
            'current_memory_mb': self.process.memory_info().rss / 1024 / 1024,
            'cache_hit_rate': self.get_cache_hit_rate(),
            'operation_stats': self.metrics['operation_counts'],
            'error_counts': self.metrics['error_counts']
        }
        
        # Add averages
        if self.metrics['cpu_usage']:
            summary['avg_cpu'] = sum(m['value'] for m in self.metrics['cpu_usage']) / len(self.metrics['cpu_usage'])
        
        if self.metrics['memory_usage']:
            summary['avg_memory_mb'] = sum(m['value'] for m in self.metrics['memory_usage']) / len(self.metrics['memory_usage'])
        
        return summary
    
    def save_report(self, filepath: Path):
        """Save performance report to file"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': self.get_summary(),
            'metrics': {
                'cpu_history': [{'time': m['time'].isoformat(), 'value': m['value']} 
                               for m in self.metrics['cpu_usage']],
                'memory_history': [{'time': m['time'].isoformat(), 'value': m['value']} 
                                  for m in self.metrics['memory_usage']]
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)

class Profiler:
    """Code profiling utilities"""
    
    def __init__(self):
        self.profiler = None
        self.results = {}
    
    def start(self):
        """Start profiling"""
        self.profiler = cProfile.Profile()
        self.profiler.enable()
    
    def stop(self) -> str:
        """Stop profiling and return results"""
        if not self.profiler:
            return ""
        
        self.profiler.disable()
        
        # Get statistics
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 functions
        
        result = s.getvalue()
        self.profiler = None
        
        return result
    
    @staticmethod
    def profile_function(func: Callable) -> Callable:
        """Decorator to profile a function"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            profiler = cProfile.Profile()
            profiler.enable()
            
            try:
                result = func(*args, **kwargs)
            finally:
                profiler.disable()
                
                # Print stats
                s = io.StringIO()
                ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
                ps.print_stats(10)
                
                print(f"\nProfile for {func.__name__}:")
                print(s.getvalue())
            
            return result
        
        return wrapper

class MemoryOptimizer:
    """Memory optimization utilities"""
    
    @staticmethod
    def optimize():
        """Run memory optimization"""
        # Force garbage collection
        gc.collect()
        
        # Get memory stats before
        process = psutil.Process()
        mem_before = process.memory_info().rss / 1024 / 1024
        
        # Clear caches
        MemoryOptimizer.clear_caches()
        
        # Compact memory
        gc.collect(2)  # Full collection
        
        # Get memory stats after
        mem_after = process.memory_info().rss / 1024 / 1024
        
        freed = mem_before - mem_after
        
        from src.utils.logger import get_logger
        logger = get_logger("Memory")
        logger.info(f"Memory optimization freed {freed:.1f} MB")
        
        return freed
    
    @staticmethod
    def clear_caches():
        """Clear application caches"""
        # This would clear various caches in the application
        # For now, just a placeholder
        pass
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get detailed memory usage"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        }

def measure_time(operation_name: str = None):
    """Decorator to measure function execution time"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = operation_name or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record in performance monitor
                if hasattr(wrapper, '_monitor'):
                    wrapper._monitor.record_operation(name, duration)
                
                return result
            
            except Exception as e:
                duration = time.time() - start_time
                
                # Record error
                if hasattr(wrapper, '_monitor'):
                    wrapper._monitor.record_error(name, e)
                
                raise
        
        # Attach monitor
        wrapper._monitor = performance_monitor
        
        return wrapper
    
    return decorator

def optimize_for_memory(func: Callable) -> Callable:
    """Decorator to optimize function for memory usage"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Run garbage collection before
        gc.collect()
        
        # Disable GC during execution for performance
        gc_enabled = gc.isenabled()
        if gc_enabled:
            gc.disable()
        
        try:
            result = func(*args, **kwargs)
        finally:
            # Re-enable GC
            if gc_enabled:
                gc.enable()
            
            # Run collection after
            gc.collect()
        
        return result
    
    return wrapper

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Start monitoring by default
performance_monitor.start_monitoring()