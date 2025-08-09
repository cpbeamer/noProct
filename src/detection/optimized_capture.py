"""Optimized screenshot capture and processing"""
import numpy as np
import time
import threading
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
import cv2
import mss
from queue import Queue
import hashlib

from src.core.optimizer import (
    resource_manager, cache_manager, ImageOptimizer,
    Priority, PowerMode, MemoryPool
)
from src.utils.logger import get_logger

@dataclass
class ScreenRegion:
    """Represents a screen region for targeted capture"""
    x: int
    y: int
    width: int
    height: int
    name: str
    priority: Priority = Priority.NORMAL
    
    def to_dict(self) -> Dict:
        return {'left': self.x, 'top': self.y, 'width': self.width, 'height': self.height}

class OptimizedScreenCapture:
    """Optimized screen capture with adaptive quality"""
    
    def __init__(self):
        self.logger = get_logger("ScreenCapture")
        self.sct = mss.mss()
        
        # Capture settings
        self.quality_levels = {
            PowerMode.HIGH_PERFORMANCE: {
                'scale': 1.0,
                'grayscale': False,
                'compression': 95,
                'interval': 2
            },
            PowerMode.BALANCED: {
                'scale': 0.75,
                'grayscale': False,
                'compression': 85,
                'interval': 5
            },
            PowerMode.POWER_SAVER: {
                'scale': 0.5,
                'grayscale': True,
                'compression': 70,
                'interval': 10
            }
        }
        
        # Intelligent region detection
        self.active_regions: List[ScreenRegion] = []
        self.last_capture_time = 0
        self.last_capture_hash = None
        
        # Frame differencing for change detection
        self.previous_frame = None
        self.change_threshold = 5000  # Pixels changed
        
        # Memory pool for image arrays
        self.image_pool = MemoryPool(lambda: np.zeros((1080, 1920, 3), dtype=np.uint8))
        
        # Register for power mode changes
        resource_manager.register_mode_change_callback(self._on_power_mode_change)
    
    def capture_screen(self, region: Optional[ScreenRegion] = None) -> Optional[np.ndarray]:
        """Capture screen with optimization"""
        # Check capture interval
        current_time = time.time()
        settings = self._get_current_settings()
        
        if current_time - self.last_capture_time < settings['interval']:
            # Return cached if available
            cached = cache_manager.get('last_screenshot')
            if cached is not None:
                return cached
        
        try:
            # Capture region or full screen
            if region:
                monitor = region.to_dict()
            else:
                monitor = self.sct.monitors[0]
            
            # Capture
            screenshot = self.sct.grab(monitor)
            
            # Convert to numpy array efficiently
            img = np.frombuffer(screenshot.rgb, dtype=np.uint8)
            img = img.reshape(screenshot.height, screenshot.width, 3)
            
            # Apply optimizations
            img = self._optimize_image(img, settings)
            
            # Check for significant changes
            if self._should_process(img):
                # Cache the result
                cache_manager.put('last_screenshot', img, img.nbytes)
                self.last_capture_time = current_time
                
                return img
            else:
                # No significant change, return previous
                return self.previous_frame
        
        except Exception as e:
            self.logger.error(f"Capture error: {e}")
            return None
    
    def capture_regions(self, regions: List[ScreenRegion]) -> List[Optional[np.ndarray]]:
        """Capture multiple regions efficiently"""
        results = []
        
        # Sort by priority
        sorted_regions = sorted(regions, key=lambda r: r.priority.value)
        
        for region in sorted_regions:
            # Check if we should skip low priority regions
            if resource_manager.resource_profile and resource_manager.resource_profile.is_high_load:
                if region.priority.value > Priority.HIGH.value:
                    results.append(None)
                    continue
            
            img = self.capture_screen(region)
            results.append(img)
        
        return results
    
    def _optimize_image(self, image: np.ndarray, settings: Dict) -> np.ndarray:
        """Apply optimization to image based on settings"""
        # Downscale if needed
        if settings['scale'] < 1.0:
            image = ImageOptimizer.downsample(image, settings['scale'])
        
        # Convert to grayscale if needed
        if settings['grayscale']:
            image = ImageOptimizer.to_grayscale(image)
        
        # Apply compression for memory efficiency
        if settings['compression'] < 95:
            compressed = ImageOptimizer.compress(image, settings['compression'])
            # Decompress back to numpy array
            image = cv2.imdecode(np.frombuffer(compressed, np.uint8), 
                               cv2.IMREAD_GRAYSCALE if settings['grayscale'] else cv2.IMREAD_COLOR)
        
        return image
    
    def _should_process(self, image: np.ndarray) -> bool:
        """Determine if image has significant changes"""
        # Calculate hash for duplicate detection
        image_hash = self._calculate_hash(image)
        
        if image_hash == self.last_capture_hash:
            return False
        
        self.last_capture_hash = image_hash
        
        # Frame differencing
        if self.previous_frame is not None:
            # Ensure same shape
            if self.previous_frame.shape == image.shape:
                diff = cv2.absdiff(self.previous_frame, image)
                change_pixels = np.sum(diff > 30)  # Threshold for pixel change
                
                if change_pixels < self.change_threshold:
                    return False
        
        self.previous_frame = image.copy()
        return True
    
    def _calculate_hash(self, image: np.ndarray) -> str:
        """Calculate perceptual hash of image"""
        # Resize to 8x8 for hash
        small = cv2.resize(image, (8, 8))
        
        # Convert to grayscale if needed
        if len(small.shape) == 3:
            small = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
        
        # Calculate hash
        avg = small.mean()
        hash_bits = (small > avg).flatten()
        
        # Convert to hex string
        hash_str = ''.join(['1' if b else '0' for b in hash_bits])
        return hex(int(hash_str, 2))[2:]
    
    def _get_current_settings(self) -> Dict:
        """Get capture settings based on power mode"""
        mode = resource_manager.power_mode
        return self.quality_levels.get(mode, self.quality_levels[PowerMode.BALANCED])
    
    def _on_power_mode_change(self, new_mode: PowerMode):
        """Handle power mode changes"""
        self.logger.info(f"Adjusting capture settings for {new_mode.value} mode")
        
        # Clear cache when switching modes
        cache_manager.clear()
    
    def detect_active_regions(self, screenshot: np.ndarray) -> List[ScreenRegion]:
        """Intelligently detect active regions on screen"""
        regions = []
        
        # Convert to grayscale for processing
        gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY) if len(screenshot.shape) == 3 else screenshot
        
        # Detect text regions using morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(gray, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter and create regions
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter small regions
            if w > 100 and h > 50:
                region = ScreenRegion(
                    x=x, y=y, width=w, height=h,
                    name=f"region_{len(regions)}",
                    priority=self._calculate_region_priority(w, h, y)
                )
                regions.append(region)
        
        # Limit number of regions based on power mode
        max_regions = {
            PowerMode.HIGH_PERFORMANCE: 10,
            PowerMode.BALANCED: 5,
            PowerMode.POWER_SAVER: 3
        }
        
        limit = max_regions.get(resource_manager.power_mode, 5)
        regions = regions[:limit]
        
        self.active_regions = regions
        return regions
    
    def _calculate_region_priority(self, width: int, height: int, y_pos: int) -> Priority:
        """Calculate priority based on region characteristics"""
        # Larger regions get higher priority
        area = width * height
        
        # Regions at top of screen get higher priority
        if y_pos < 200:
            return Priority.HIGH
        elif area > 50000:
            return Priority.HIGH
        elif area > 20000:
            return Priority.NORMAL
        else:
            return Priority.LOW

class OptimizedOCR:
    """Optimized OCR processing"""
    
    def __init__(self):
        self.logger = get_logger("OptimizedOCR")
        
        # OCR cache
        self.ocr_cache = {}
        self.cache_ttl = 60  # seconds
        
        # Batch processing queue
        self.ocr_queue = Queue()
        self.batch_size = 5
        self.processing_thread = None
        self.running = False
        
        # Preprocessing options based on power mode
        self.preprocessing_levels = {
            PowerMode.HIGH_PERFORMANCE: {
                'denoise': True,
                'sharpen': True,
                'threshold': True,
                'scale': 2.0
            },
            PowerMode.BALANCED: {
                'denoise': True,
                'sharpen': False,
                'threshold': True,
                'scale': 1.5
            },
            PowerMode.POWER_SAVER: {
                'denoise': False,
                'sharpen': False,
                'threshold': True,
                'scale': 1.0
            }
        }
    
    def start_batch_processing(self):
        """Start batch OCR processing"""
        if self.running:
            return
        
        self.running = True
        self.processing_thread = threading.Thread(target=self._batch_processor, daemon=True)
        self.processing_thread.start()
    
    def stop_batch_processing(self):
        """Stop batch OCR processing"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=2)
    
    def _batch_processor(self):
        """Process OCR requests in batches"""
        import pytesseract
        
        batch = []
        
        while self.running:
            try:
                # Collect batch
                timeout = 0.5 if batch else 2.0
                item = self.ocr_queue.get(timeout=timeout)
                batch.append(item)
                
                # Process when batch is full or timeout
                if len(batch) >= self.batch_size or (batch and time.time() - batch[0]['time'] > 2):
                    self._process_batch(batch)
                    batch = []
            
            except:
                if batch:
                    self._process_batch(batch)
                    batch = []
    
    def _process_batch(self, batch: List[Dict]):
        """Process a batch of OCR requests"""
        import pytesseract
        
        for item in batch:
            try:
                # Check cache first
                cache_key = item['hash']
                cached = self._get_cached(cache_key)
                
                if cached:
                    item['callback'](cached)
                    continue
                
                # Preprocess image
                processed = self._preprocess_image(item['image'])
                
                # Perform OCR
                text = pytesseract.image_to_string(processed)
                
                # Cache result
                self._cache_result(cache_key, text)
                
                # Callback with result
                item['callback'](text)
            
            except Exception as e:
                self.logger.error(f"OCR batch processing error: {e}")
                item['callback']("")
    
    def extract_text_async(self, image: np.ndarray, callback: callable):
        """Extract text asynchronously"""
        # Calculate image hash for caching
        image_hash = hashlib.md5(image.tobytes()).hexdigest()
        
        # Check cache
        cached = self._get_cached(image_hash)
        if cached:
            callback(cached)
            return
        
        # Add to queue
        self.ocr_queue.put({
            'image': image,
            'hash': image_hash,
            'callback': callback,
            'time': time.time()
        })
    
    def extract_text_sync(self, image: np.ndarray) -> str:
        """Extract text synchronously with optimization"""
        import pytesseract
        
        # Calculate hash
        image_hash = hashlib.md5(image.tobytes()).hexdigest()
        
        # Check cache
        cached = self._get_cached(image_hash)
        if cached:
            return cached
        
        # Preprocess
        processed = self._preprocess_image(image)
        
        # OCR
        text = pytesseract.image_to_string(processed)
        
        # Cache
        self._cache_result(image_hash, text)
        
        return text
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR"""
        settings = self.preprocessing_levels.get(
            resource_manager.power_mode,
            self.preprocessing_levels[PowerMode.BALANCED]
        )
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Scale if needed
        if settings['scale'] > 1.0:
            height, width = image.shape
            new_size = (int(width * settings['scale']), int(height * settings['scale']))
            image = cv2.resize(image, new_size, interpolation=cv2.INTER_CUBIC)
        
        # Denoise
        if settings['denoise']:
            image = cv2.fastNlMeansDenoising(image, h=10)
        
        # Sharpen
        if settings['sharpen']:
            kernel = np.array([[-1,-1,-1],
                              [-1, 9,-1],
                              [-1,-1,-1]])
            image = cv2.filter2D(image, -1, kernel)
        
        # Threshold
        if settings['threshold']:
            _, image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return image
    
    def _get_cached(self, key: str) -> Optional[str]:
        """Get cached OCR result"""
        if key in self.ocr_cache:
            result, timestamp = self.ocr_cache[key]
            
            if time.time() - timestamp < self.cache_ttl:
                return result
            else:
                del self.ocr_cache[key]
        
        return None
    
    def _cache_result(self, key: str, text: str):
        """Cache OCR result"""
        self.ocr_cache[key] = (text, time.time())
        
        # Limit cache size
        if len(self.ocr_cache) > 100:
            # Remove oldest entries
            oldest = sorted(self.ocr_cache.items(), key=lambda x: x[1][1])[:20]
            for k, _ in oldest:
                del self.ocr_cache[k]

# Global instances
screen_capture = OptimizedScreenCapture()
ocr_processor = OptimizedOCR()

# Start OCR batch processing
ocr_processor.start_batch_processing()