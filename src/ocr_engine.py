import pytesseract
import cv2
import numpy as np
from PIL import Image
import logging
import re

class OCREngine:
    def __init__(self, tesseract_path=None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    def extract_text(self, image, preprocess=True):
        try:
            if isinstance(image, np.ndarray):
                if preprocess:
                    image = self.preprocess_image(image)
                pil_image = Image.fromarray(image)
            else:
                pil_image = image
            
            text = pytesseract.image_to_string(pil_image)
            
            return self.clean_text(text)
        
        except Exception as e:
            logging.error(f"OCR extraction error: {e}")
            return ""
    
    def extract_with_coordinates(self, image):
        try:
            if isinstance(image, np.ndarray):
                image = self.preprocess_image(image)
                pil_image = Image.fromarray(image)
            else:
                pil_image = image
            
            data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)
            
            results = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if text:
                    results.append({
                        'text': text,
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                        'confidence': data['conf'][i]
                    })
            
            return results
        
        except Exception as e:
            logging.error(f"OCR with coordinates error: {e}")
            return []
    
    def preprocess_image(self, image):
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        scaled = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        _, binary = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        denoised = cv2.medianBlur(binary, 3)
        
        return denoised
    
    def clean_text(self, text):
        text = re.sub(r'\s+', ' ', text)
        
        text = text.strip()
        
        return text
    
    def extract_question_components(self, image):
        text_data = self.extract_with_coordinates(image)
        
        components = {
            'question_text': '',
            'options': [],
            'regions': {}
        }
        
        question_keywords = ['question', 'q.', 'q:', '?']
        option_patterns = [r'^[A-E][\.\)]', r'^\d[\.\)]']
        
        question_lines = []
        current_y = -1
        y_threshold = 20
        
        for item in text_data:
            text = item['text']
            y_pos = item['y']
            
            is_question_line = any(keyword in text.lower() for keyword in question_keywords) or '?' in text
            
            if is_question_line or (current_y != -1 and abs(y_pos - current_y) < y_threshold):
                question_lines.append(text)
                current_y = y_pos
                components['regions']['question'] = {
                    'x': item['x'],
                    'y': item['y'],
                    'width': item['width'],
                    'height': item['height']
                }
            
            for pattern in option_patterns:
                if re.match(pattern, text):
                    components['options'].append({
                        'text': text,
                        'x': item['x'],
                        'y': item['y'],
                        'width': item['width'],
                        'height': item['height']
                    })
        
        components['question_text'] = ' '.join(question_lines)
        
        return components