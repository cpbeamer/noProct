"""Efficient thread management and coordination"""
import threading
import concurrent.futures
import queue
import time
import weakref
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from src.core.optimizer import resource_manager, PowerMode

class ThreadPriority(Enum):
    """Thread priority levels"""
    REALTIME = 0
    HIGH = 1
    NORMAL = 2  
    LOW = 3
    IDLE = 4

@dataclass
class ThreadTask:
    """Represents a task for thread execution"""
    func: Callable
    args: tuple
    kwargs: dict
    priority: ThreadPriority
    callback: Optional[Callable] = None
    timeout: Optional[float] = None

class ThreadPoolManager:
    """Manages thread pools with dynamic sizing"""
    
    def __init__(self):
        self.logger = logging.getLogger("ThreadPool")
        
        # Thread pool configurations per power mode
        self.pool_configs = {
            PowerMode.HIGH_PERFORMANCE: {
                'core_threads': 8,
                'max_threads': 16,
                'queue_size': 100,
                'idle_timeout': 60
            },
            PowerMode.BALANCED: {
                'core_threads': 4,
                'max_threads': 8,
                'queue_size': 50,
                'idle_timeout': 30
            },
            PowerMode.POWER_SAVER: {
                'core_threads': 2,
                'max_threads': 4,
                'queue_size': 20,
                'idle_timeout': 10
            }
        }
        
        # Thread pools
        self.executor = None
        self.io_executor = None
        self.cpu_executor = None
        
        # Task tracking
        self.active_tasks = weakref.WeakSet()
        self.task_queue = queue.PriorityQueue()
        
        # Statistics
        self.stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'avg_execution_time': 0
        }
        
        # Initialize pools
        self._initialize_pools()
        
        # Register for power mode changes
        resource_manager.register_mode_change_callback(self._on_power_mode_change)
    
    def _initialize_pools(self):
        """Initialize thread pools based on current power mode"""
        config = self._get_current_config()
        
        # Main executor for general tasks
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=config['max_threads'],
            thread_name_prefix='QA-Main'
        )
        
        # I/O bound executor
        self.io_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=min(config['max_threads'] * 2, 20),
            thread_name_prefix='QA-IO'
        )
        
        # CPU bound executor
        self.cpu_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=config['core_threads'],
            thread_name_prefix='QA-CPU'
        )
    
    def submit_task(self, task: ThreadTask) -> concurrent.futures.Future:
        """Submit a task for execution"""
        self.stats['tasks_submitted'] += 1
        
        # Choose executor based on task type
        if 'io' in str(task.func.__name__).lower():
            executor = self.io_executor
        elif 'cpu' in str(task.func.__name__).lower():
            executor = self.cpu_executor
        else:
            executor = self.executor
        
        # Wrap task for monitoring
        wrapped_task = self._wrap_task(task)
        
        # Submit to executor
        future = executor.submit(wrapped_task)
        
        # Add callback if specified
        if task.callback:
            future.add_done_callback(task.callback)
        
        # Track active task
        self.active_tasks.add(future)
        
        return future
    
    def _wrap_task(self, task: ThreadTask) -> Callable:
        """Wrap task with monitoring and error handling"""
        def wrapped():
            start_time = time.time()
            
            try:
                # Set thread priority if supported
                self._set_thread_priority(task.priority)
                
                # Execute task
                result = task.func(*task.args, **task.kwargs)
                
                # Update statistics
                execution_time = time.time() - start_time
                self._update_stats(True, execution_time)
                
                return result
            
            except Exception as e:
                self.logger.error(f"Task execution failed: {e}")
                self._update_stats(False, time.time() - start_time)
                raise
        
        return wrapped
    
    def _set_thread_priority(self, priority: ThreadPriority):
        """Set current thread priority"""
        try:
            import win32api
            import win32process
            import win32con
            
            thread_handle = win32api.GetCurrentThread()
            
            priority_map = {
                ThreadPriority.REALTIME: win32process.THREAD_PRIORITY_TIME_CRITICAL,
                ThreadPriority.HIGH: win32process.THREAD_PRIORITY_HIGHEST,
                ThreadPriority.NORMAL: win32process.THREAD_PRIORITY_NORMAL,
                ThreadPriority.LOW: win32process.THREAD_PRIORITY_BELOW_NORMAL,
                ThreadPriority.IDLE: win32process.THREAD_PRIORITY_IDLE
            }
            
            win32process.SetThreadPriority(
                thread_handle,
                priority_map.get(priority, win32process.THREAD_PRIORITY_NORMAL)
            )
        except:
            pass  # Not critical if priority setting fails
    
    def _update_stats(self, success: bool, execution_time: float):
        """Update execution statistics"""
        if success:
            self.stats['tasks_completed'] += 1
        else:
            self.stats['tasks_failed'] += 1
        
        # Update average execution time
        total_tasks = self.stats['tasks_completed'] + self.stats['tasks_failed']
        old_avg = self.stats['avg_execution_time']
        self.stats['avg_execution_time'] = (old_avg * (total_tasks - 1) + execution_time) / total_tasks
    
    def _get_current_config(self) -> Dict:
        """Get configuration for current power mode"""
        mode = resource_manager.power_mode
        return self.pool_configs.get(mode, self.pool_configs[PowerMode.BALANCED])
    
    def _on_power_mode_change(self, new_mode: PowerMode):
        """Handle power mode changes"""
        self.logger.info(f"Adjusting thread pools for {new_mode.value} mode")
        
        # Shutdown old pools gracefully
        self._shutdown_pools(wait=False)
        
        # Initialize new pools
        self._initialize_pools()
    
    def _shutdown_pools(self, wait: bool = True):
        """Shutdown thread pools"""
        for executor in [self.executor, self.io_executor, self.cpu_executor]:
            if executor:
                executor.shutdown(wait=wait)
    
    def get_stats(self) -> Dict:
        """Get thread pool statistics"""
        return {
            **self.stats,
            'active_tasks': len(self.active_tasks),
            'thread_count': threading.active_count()
        }
    
    def shutdown(self):
        """Shutdown thread manager"""
        self._shutdown_pools(wait=True)

class CoordinatedThreadGroup:
    """Coordinates a group of related threads"""
    
    def __init__(self, name: str):
        self.name = name
        self.threads = []
        self.barrier = None
        self.stop_event = threading.Event()
        self.logger = logging.getLogger(f"ThreadGroup-{name}")
    
    def add_thread(self, target: Callable, args: tuple = (), name: str = None):
        """Add a thread to the group"""
        thread = threading.Thread(
            target=self._thread_wrapper(target),
            args=args,
            name=name or f"{self.name}-{len(self.threads)}",
            daemon=True
        )
        self.threads.append(thread)
    
    def _thread_wrapper(self, target: Callable) -> Callable:
        """Wrap thread target with coordination"""
        def wrapped(*args, **kwargs):
            try:
                while not self.stop_event.is_set():
                    # Synchronize at barrier if set
                    if self.barrier:
                        self.barrier.wait()
                    
                    # Execute target
                    result = target(*args, **kwargs)
                    
                    # Check if should continue
                    if result == 'stop':
                        break
            
            except Exception as e:
                self.logger.error(f"Thread error: {e}")
        
        return wrapped
    
    def start_all(self):
        """Start all threads in the group"""
        for thread in self.threads:
            thread.start()
        
        self.logger.info(f"Started {len(self.threads)} threads")
    
    def stop_all(self, timeout: float = 5):
        """Stop all threads in the group"""
        self.stop_event.set()
        
        for thread in self.threads:
            thread.join(timeout=timeout)
        
        self.logger.info(f"Stopped {len(self.threads)} threads")
    
    def synchronize(self):
        """Create synchronization barrier for threads"""
        self.barrier = threading.Barrier(len(self.threads))

class TaskScheduler:
    """Schedules tasks for optimal execution"""
    
    def __init__(self, thread_pool: ThreadPoolManager):
        self.thread_pool = thread_pool
        self.scheduled_tasks = queue.PriorityQueue()
        self.scheduler_thread = None
        self.running = False
        self.logger = logging.getLogger("TaskScheduler")
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True
        )
        self.scheduler_thread.start()
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2)
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Get next scheduled task
                priority, scheduled_time, task = self.scheduled_tasks.get(timeout=1)
                
                # Wait until scheduled time
                wait_time = scheduled_time - time.time()
                if wait_time > 0:
                    time.sleep(min(wait_time, 1))
                    
                    # Re-queue if not ready
                    if scheduled_time > time.time():
                        self.scheduled_tasks.put((priority, scheduled_time, task))
                        continue
                
                # Submit task for execution
                self.thread_pool.submit_task(task)
            
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
    
    def schedule_task(self, task: ThreadTask, delay: float = 0):
        """Schedule a task for future execution"""
        scheduled_time = time.time() + delay
        priority = task.priority.value
        
        self.scheduled_tasks.put((priority, scheduled_time, task))
    
    def schedule_recurring(self, task: ThreadTask, interval: float):
        """Schedule a recurring task"""
        def recurring_wrapper():
            # Execute task
            result = task.func(*task.args, **task.kwargs)
            
            # Reschedule
            if self.running:
                self.schedule_task(task, interval)
            
            return result
        
        # Create modified task
        recurring_task = ThreadTask(
            func=recurring_wrapper,
            args=(),
            kwargs={},
            priority=task.priority
        )
        
        # Schedule initial execution
        self.schedule_task(recurring_task, 0)

class ThreadSafeCache:
    """Thread-safe caching implementation"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.lock = threading.RLock()
        self.access_count = {}
        self.hit_count = 0
        self.miss_count = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self.lock:
            if key in self.cache:
                self.hit_count += 1
                self.access_count[key] = self.access_count.get(key, 0) + 1
                return self.cache[key]
            else:
                self.miss_count += 1
                return None
    
    def put(self, key: str, value: Any):
        """Put item in cache"""
        with self.lock:
            # Evict if at capacity
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict()
            
            self.cache[key] = value
            self.access_count[key] = 0
    
    def _evict(self):
        """Evict least frequently used item"""
        if not self.cache:
            return
        
        # Find LFU item
        lfu_key = min(self.access_count.keys(), key=lambda k: self.access_count[k])
        
        del self.cache[lfu_key]
        del self.access_count[lfu_key]
    
    def get_hit_rate(self) -> float:
        """Get cache hit rate"""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0
    
    def clear(self):
        """Clear cache"""
        with self.lock:
            self.cache.clear()
            self.access_count.clear()
            self.hit_count = 0
            self.miss_count = 0

# Global instances
thread_pool = ThreadPoolManager()
task_scheduler = TaskScheduler(thread_pool)
thread_cache = ThreadSafeCache()

# Start scheduler
task_scheduler.start()