import cv2
import numpy as np
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib
from src.utils.logger import get_logger, log_performance
from src.core.exceptions import DetectionError
import time

@dataclass
class Detection:
    """Data class for detection results"""
    question_text: str
    options: List[Dict]
    confidence: float
    region: Optional[Dict]
    timestamp: datetime
    detection_method: str
    screenshot_hash: str
    
    def to_dict(self) -> Dict:
        return {
            'question_text': self.question_text,
            'options': self.options,
            'confidence': self.confidence,
            'region': self.region,
            'timestamp': self.timestamp.isoformat(),
            'detection_method': self.detection_method,
            'screenshot_hash': self.screenshot_hash
        }

class OptimizedQuestionDetector:
    """Optimized question detection with multiple strategies"""
    
    def __init__(self, config: Dict, ocr_engine):
        self.config = config
        self.ocr_engine = ocr_engine
        self.logger = get_logger("Detector")
        
        # Detection cache
        self.detection_cache = {}
        self.cache_ttl = config.get('performance.cache_ttl', 300)
        
        # Detection history
        self.detection_history = []
        self.max_history = 100
        
        # Performance metrics
        self.metrics = {
            'total_detections': 0,
            'successful_detections': 0,
            'avg_detection_time': 0,
            'detection_methods': {}
        }
        
        # Pre-compiled patterns for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for performance"""
        import re
        self.question_patterns = [
            re.compile(r'\b(what|when|where|who|which|how|why)\b', re.IGNORECASE),
            re.compile(r'\?$'),
            re.compile(r'^Q\d+[:\.]', re.IGNORECASE),
            re.compile(r'^Question \d+', re.IGNORECASE)
        ]
        
        self.option_patterns = [
            re.compile(r'^[A-E][\.\)]\s'),
            re.compile(r'^\d+[\.\)]\s'),
            re.compile(r'^(True|False)$', re.IGNORECASE)
        ]
    
    def detect(self, screenshot: np.ndarray) -> Optional[Detection]:
        """Main detection method with multiple strategies"""
        start_time = time.time()
        
        try:
            # Generate screenshot hash for caching
            screenshot_hash = self._hash_screenshot(screenshot)
            
            # Check cache
            cached = self._check_cache(screenshot_hash)
            if cached:
                self.logger.debug("Detection retrieved from cache")
                return cached
            
            # Try detection strategies in order of speed
            detection = None
            strategies = [
                ('template', self._detect_by_template),
                ('text_patterns', self._detect_by_text_patterns),
                ('ui_analysis', self._detect_by_ui_analysis),
                ('ml_classification', self._detect_by_ml_classification)
            ]
            
            for method_name, method in strategies:
                try:
                    detection = method(screenshot)
                    if detection:
                        detection.detection_method = method_name
                        detection.screenshot_hash = screenshot_hash
                        break
                except Exception as e:
                    self.logger.debug(f"{method_name} detection failed: {e}")
            
            if detection:
                # Update cache and metrics
                self._update_cache(screenshot_hash, detection)
                self._update_metrics(detection, time.time() - start_time)
                
                # Add to history
                self._add_to_history(detection)
                
                log_performance("Question detection", time.time() - start_time)
                
            return detection
            
        except Exception as e:
            self.logger.error(f"Detection error: {e}")
            raise DetectionError(f"Failed to detect question: {e}")
    
    def _detect_by_template(self, screenshot: np.ndarray) -> Optional[Detection]:
        """Fast template matching for known UI patterns"""
        # This would load and match against saved templates
        # Implementation depends on specific quiz platforms
        return None
    
    def _detect_by_text_patterns(self, screenshot: np.ndarray) -> Optional[Detection]:
        """Detect questions by text patterns and keywords"""
        # Extract text with OCR
        components = self.ocr_engine.extract_question_components(screenshot)
        
        if not components.get('question_text'):
            return None
        
        question_text = components['question_text']
        
        # Check patterns
        confidence = 0.0
        
        # Question indicators
        for pattern in self.question_patterns:
            if pattern.search(question_text):
                confidence += 0.25
        
        # Check for options
        options = components.get('options', [])
        if len(options) >= 2:
            confidence += 0.3
        
        # Check text length
        if 10 < len(question_text) < 500:
            confidence += 0.2
        
        # Context matching
        if self._matches_context(question_text):
            confidence += 0.25
        
        confidence = min(confidence, 1.0)
        
        if confidence >= self.config.get('confidence_threshold', 0.5):
            return Detection(
                question_text=question_text,
                options=options,
                confidence=confidence,
                region=components.get('regions', {}).get('question'),
                timestamp=datetime.now(),
                detection_method='text_patterns',
                screenshot_hash=''
            )
        
        return None
    
    def _detect_by_ui_analysis(self, screenshot: np.ndarray) -> Optional[Detection]:
        """Analyze UI structure for question elements"""
        gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Analyze contours for UI patterns
        ui_score = self._analyze_ui_structure(contours, screenshot.shape)
        
        if ui_score > 0.7:
            # High UI score, extract text
            components = self.ocr_engine.extract_question_components(screenshot)
            if components.get('question_text'):
                return Detection(
                    question_text=components['question_text'],
                    options=components.get('options', []),
                    confidence=ui_score,
                    region=components.get('regions', {}).get('question'),
                    timestamp=datetime.now(),
                    detection_method='ui_analysis',
                    screenshot_hash=''
                )
        
        return None
    
    def _detect_by_ml_classification(self, screenshot: np.ndarray) -> Optional[Detection]:
        """Use ML model for question detection (placeholder)"""
        # This would use a trained model for classification
        # For now, return None
        return None
    
    def _analyze_ui_structure(self, contours: List, shape: Tuple) -> float:
        """Analyze UI structure for question-like patterns"""
        height, width = shape[:2]
        score = 0.0
        
        # Count button-like shapes
        button_count = 0
        text_regions = 0
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Button detection
            if 50 < w < width * 0.4 and 20 < h < 100:
                aspect_ratio = w / h
                if 1.5 < aspect_ratio < 6:
                    button_count += 1
            
            # Text region detection
            if w > width * 0.3 and 30 < h < 200:
                text_regions += 1
        
        # Calculate score
        if button_count >= 2:
            score += 0.4
        if text_regions >= 1:
            score += 0.3
        if button_count >= 4:
            score += 0.3
        
        return min(score, 1.0)
    
    def _matches_context(self, text: str) -> bool:
        """Check if text matches user-defined context"""
        context = self.config.get('context', '').lower()
        if not context:
            return False
        
        text_lower = text.lower()
        context_words = context.split()
        
        matches = sum(1 for word in context_words if word in text_lower)
        return matches >= len(context_words) * 0.3
    
    def _hash_screenshot(self, screenshot: np.ndarray) -> str:
        """Generate hash for screenshot caching"""
        # Downsample for faster hashing
        small = cv2.resize(screenshot, (128, 128))
        return hashlib.md5(small.tobytes()).hexdigest()
    
    def _check_cache(self, screenshot_hash: str) -> Optional[Detection]:
        """Check detection cache"""
        if screenshot_hash in self.detection_cache:
            cached_time, detection = self.detection_cache[screenshot_hash]
            if time.time() - cached_time < self.cache_ttl:
                return detection
            else:
                del self.detection_cache[screenshot_hash]
        return None
    
    def _update_cache(self, screenshot_hash: str, detection: Detection):
        """Update detection cache"""
        self.detection_cache[screenshot_hash] = (time.time(), detection)
        
        # Clean old cache entries
        current_time = time.time()
        expired = [k for k, (t, _) in self.detection_cache.items() 
                  if current_time - t > self.cache_ttl]
        for k in expired:
            del self.detection_cache[k]
    
    def _add_to_history(self, detection: Detection):
        """Add detection to history"""
        self.detection_history.append(detection)
        if len(self.detection_history) > self.max_history:
            self.detection_history.pop(0)
    
    def _update_metrics(self, detection: Detection, duration: float):
        """Update performance metrics"""
        self.metrics['total_detections'] += 1
        if detection:
            self.metrics['successful_detections'] += 1
            method = detection.detection_method
            self.metrics['detection_methods'][method] = \
                self.metrics['detection_methods'].get(method, 0) + 1
        
        # Update average detection time
        n = self.metrics['total_detections']
        old_avg = self.metrics['avg_detection_time']
        self.metrics['avg_detection_time'] = (old_avg * (n-1) + duration) / n
    
    def get_metrics(self) -> Dict:
        """Get detection metrics"""
        return self.metrics.copy()
    
    def is_duplicate(self, detection: Detection) -> bool:
        """Check if detection is duplicate of recent detection"""
        if not self.detection_history:
            return False
        
        last_detection = self.detection_history[-1]
        
        # Check time difference
        time_diff = (detection.timestamp - last_detection.timestamp).total_seconds()
        if time_diff < 2:  # Less than 2 seconds
            # Check text similarity
            from difflib import SequenceMatcher
            similarity = SequenceMatcher(None, 
                                        detection.question_text, 
                                        last_detection.question_text).ratio()
            return similarity > 0.9
        
        return False