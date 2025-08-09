import cv2
import numpy as np
import logging
from src.ocr_engine import OCREngine

class QuestionDetector:
    def __init__(self, config):
        self.config = config
        self.ocr_engine = OCREngine()
        self.last_detected_question = None
        self.context_keywords = self.extract_context_keywords()
    
    def extract_context_keywords(self):
        context = self.config.get('context', '')
        keywords = []
        
        if context:
            words = context.lower().split()
            keywords = [word for word in words if len(word) > 3 and word not in ['the', 'and', 'for', 'with']]
        
        return keywords
    
    def detect_question(self, screenshot):
        try:
            has_ui_elements = self.detect_quiz_ui_elements(screenshot)
            
            components = self.ocr_engine.extract_question_components(screenshot)
            
            if not components['question_text']:
                return None
            
            is_new_question = self.is_new_question(components['question_text'])
            if not is_new_question:
                return None
            
            confidence_score = self.calculate_confidence(components, has_ui_elements)
            
            if confidence_score > 0.5:
                self.last_detected_question = components['question_text']
                
                return {
                    'question_text': components['question_text'],
                    'options': components['options'],
                    'region': components['regions'].get('question'),
                    'confidence': confidence_score,
                    'timestamp': self.get_timestamp()
                }
            
            return None
        
        except Exception as e:
            logging.error(f"Question detection error: {e}")
            return None
    
    def detect_quiz_ui_elements(self, screenshot):
        gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)
        
        edges = cv2.Canny(gray, 50, 150)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        button_like_shapes = 0
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            if 50 < w < 300 and 20 < h < 100:
                aspect_ratio = w / h
                if 1.5 < aspect_ratio < 6:
                    button_like_shapes += 1
        
        has_timer = self.detect_timer_element(screenshot)
        
        has_progress = self.detect_progress_indicator(screenshot)
        
        return button_like_shapes > 2 or has_timer or has_progress
    
    def detect_timer_element(self, screenshot):
        text = self.ocr_engine.extract_text(screenshot, preprocess=False)
        
        timer_patterns = ['time:', 'timer:', 'remaining:', ':', 'seconds', 'minutes']
        
        return any(pattern in text.lower() for pattern in timer_patterns)
    
    def detect_progress_indicator(self, screenshot):
        text = self.ocr_engine.extract_text(screenshot, preprocess=False)
        
        progress_patterns = ['question', 'of', '/', 'progress', 'score']
        
        matches = sum(1 for pattern in progress_patterns if pattern in text.lower())
        
        return matches >= 2
    
    def is_new_question(self, question_text):
        if not self.last_detected_question:
            return True
        
        similarity = self.calculate_text_similarity(self.last_detected_question, question_text)
        
        return similarity < 0.8
    
    def calculate_text_similarity(self, text1, text2):
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def calculate_confidence(self, components, has_ui_elements):
        score = 0.0
        
        if '?' in components['question_text']:
            score += 0.3
        
        if len(components['options']) >= 2:
            score += 0.3
        
        if has_ui_elements:
            score += 0.2
        
        question_lower = components['question_text'].lower()
        for keyword in self.context_keywords:
            if keyword in question_lower:
                score += 0.1
                break
        
        question_indicators = ['what', 'when', 'where', 'who', 'which', 'how', 'why']
        if any(indicator in question_lower for indicator in question_indicators):
            score += 0.1
        
        return min(score, 1.0)
    
    def get_timestamp(self):
        import datetime
        return datetime.datetime.now().isoformat()