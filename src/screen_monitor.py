import mss
import numpy as np
from PIL import Image
import cv2
import logging

class ScreenMonitor:
    def __init__(self):
        self.sct = mss.mss()
        self.last_screenshot = None
    
    def capture_screen(self, monitor_index=0):
        try:
            if monitor_index == 0:
                monitor = self.sct.monitors[0]
            else:
                monitor = self.sct.monitors[monitor_index]
            
            screenshot = self.sct.grab(monitor)
            
            img = Image.frombytes('RGB', (screenshot.width, screenshot.height), 
                                screenshot.rgb, 'raw', 'BGRX')
            
            img_array = np.array(img)
            
            self.last_screenshot = img_array
            
            return img_array
        
        except Exception as e:
            logging.error(f"Error capturing screen: {e}")
            return None
    
    def capture_region(self, x, y, width, height):
        try:
            region = {'left': x, 'top': y, 'width': width, 'height': height}
            
            screenshot = self.sct.grab(region)
            
            img = Image.frombytes('RGB', (screenshot.width, screenshot.height), 
                                screenshot.rgb, 'raw', 'BGRX')
            
            return np.array(img)
        
        except Exception as e:
            logging.error(f"Error capturing region: {e}")
            return None
    
    def find_image_on_screen(self, template_path, threshold=0.8):
        try:
            screen = self.capture_screen()
            if screen is None:
                return None
            
            template = cv2.imread(template_path)
            if template is None:
                logging.error(f"Could not load template: {template_path}")
                return None
            
            screen_gray = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                h, w = template_gray.shape
                return {
                    'x': max_loc[0],
                    'y': max_loc[1],
                    'width': w,
                    'height': h,
                    'confidence': max_val
                }
            
            return None
        
        except Exception as e:
            logging.error(f"Error finding image on screen: {e}")
            return None
    
    def detect_changes(self, threshold=10000):
        try:
            current = self.capture_screen()
            if current is None or self.last_screenshot is None:
                return False
            
            diff = cv2.absdiff(self.last_screenshot, current)
            
            change_amount = np.sum(diff)
            
            return change_amount > threshold
        
        except Exception as e:
            logging.error(f"Error detecting changes: {e}")
            return False