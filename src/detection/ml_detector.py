"""ML-enhanced detection integration"""
import numpy as np
from typing import Optional, Dict, Any
from src.ml.models import ml_detector, active_learner, QuestionFeatures
from src.detection.detector import Detection, OptimizedQuestionDetector
from src.utils.logger import get_logger
from src.utils.performance import measure_time
from src.localization.i18n import _
import time

class MLEnhancedDetector(OptimizedQuestionDetector):
    """Question detector enhanced with machine learning"""
    
    def __init__(self, config: Dict, ocr_engine):
        super().__init__(config, ocr_engine)
        self.ml_enabled = config.get('ml_detection', True)
        self.ml_confidence_weight = 0.4
        self.traditional_weight = 0.6
        self.logger = get_logger("MLDetector")
        
        # User feedback tracking
        self.feedback_enabled = config.get('active_learning', True)
        self.pending_feedback = []
    
    @measure_time("ml_detection")
    def detect(self, screenshot: np.ndarray) -> Optional[Detection]:
        """Enhanced detection with ML"""
        start_time = time.time()
        
        try:
            # First, use traditional detection
            traditional_detection = super().detect(screenshot)
            
            if not self.ml_enabled or traditional_detection is None:
                return traditional_detection
            
            # Extract text and region for ML
            components = self.ocr_engine.extract_question_components(screenshot)
            question_text = components.get('question_text', '')
            region = components.get('regions', {}).get('question')
            
            if not question_text or not region:
                return traditional_detection
            
            # Get ML prediction
            ml_result = ml_detector.predict(
                text=question_text,
                region=region,
                image=screenshot
            )
            
            # Combine confidences
            traditional_confidence = traditional_detection.confidence
            ml_confidence = ml_result['confidence']
            
            combined_confidence = (
                traditional_confidence * self.traditional_weight +
                ml_confidence * self.ml_confidence_weight
            )
            
            # Update detection with combined confidence
            traditional_detection.confidence = combined_confidence
            traditional_detection.detection_method = f"{traditional_detection.detection_method}+ML"
            
            # Log ML contribution
            self.logger.debug(
                f"Detection confidence - Traditional: {traditional_confidence:.3f}, "
                f"ML: {ml_confidence:.3f}, Combined: {combined_confidence:.3f}"
            )
            
            # Active learning - check if we should request feedback
            if self.feedback_enabled and active_learner.should_request_label(combined_confidence):
                self._queue_for_feedback(
                    screenshot=screenshot,
                    detection=traditional_detection,
                    ml_result=ml_result
                )
            
            # Record performance
            duration = time.time() - start_time
            self._record_ml_metrics(ml_result, duration)
            
            return traditional_detection
            
        except Exception as e:
            self.logger.error(f"ML detection error: {e}")
            # Fallback to traditional detection
            return traditional_detection
    
    def _queue_for_feedback(self, screenshot: np.ndarray, 
                           detection: Detection, ml_result: Dict):
        """Queue detection for user feedback"""
        self.pending_feedback.append({
            'timestamp': detection.timestamp,
            'screenshot': screenshot,
            'detection': detection,
            'ml_result': ml_result,
            'question_text': detection.question_text
        })
        
        # Limit queue size
        if len(self.pending_feedback) > 10:
            self.pending_feedback.pop(0)
    
    def _record_ml_metrics(self, ml_result: Dict, duration: float):
        """Record ML performance metrics"""
        if hasattr(self, '_stats_tracker'):
            self._stats_tracker.track_performance('ml_inference', duration)
            
            # Track individual model performances
            for model_name, score in ml_result.get('model_scores', {}).items():
                self._stats_tracker.track_performance(f'ml_{model_name}', score)
    
    def provide_feedback(self, feedback_id: int, is_correct: bool):
        """Provide feedback for active learning"""
        if not self.feedback_enabled or feedback_id >= len(self.pending_feedback):
            return
        
        feedback_item = self.pending_feedback[feedback_id]
        
        # Extract features for training
        features = ml_detector.extract_features(
            text=feedback_item['question_text'],
            region=feedback_item['detection'].region,
            image=feedback_item['screenshot']
        )
        
        # Add to training data
        active_learner.add_training_sample(
            features=features,
            is_question=is_correct,
            confidence=feedback_item['detection'].confidence
        )
        
        # Remove from pending
        self.pending_feedback.pop(feedback_id)
        
        self.logger.info(f"Feedback recorded: {'Correct' if is_correct else 'Incorrect'}")
    
    def get_pending_feedback(self) -> list:
        """Get list of detections pending feedback"""
        return [
            {
                'id': i,
                'question': item['question_text'][:100],
                'confidence': item['detection'].confidence,
                'timestamp': item['timestamp']
            }
            for i, item in enumerate(self.pending_feedback)
        ]
    
    def retrain_models(self):
        """Manually trigger model retraining"""
        self.logger.info(_("status.retraining_models"))
        active_learner.retrain_models()
        self.logger.info(_("status.retraining_complete"))