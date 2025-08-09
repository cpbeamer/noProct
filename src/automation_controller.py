import pyautogui
import time
import random
import logging

class AutomationController:
    def __init__(self):
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        
        self.typing_speed_range = (0.05, 0.15)
        self.mouse_speed_range = (0.3, 0.8)
    
    def answer_question(self, answer, question_type, region=None, options=None):
        try:
            if question_type == "Multiple Choice":
                self.answer_multiple_choice(answer, options)
            elif question_type == "True/False":
                self.answer_true_false(answer)
            elif question_type == "Short Answer":
                self.answer_short_answer(answer, region)
            else:
                self.answer_mixed(answer, options, region)
        
        except Exception as e:
            logging.error(f"Automation error: {e}")
    
    def answer_multiple_choice(self, answer, options):
        if not options:
            logging.warning("No options provided for multiple choice")
            return
        
        target_option = None
        for option in options:
            option_text = option['text'].lower()
            if answer.lower() in option_text or option_text.startswith(answer[0].lower()):
                target_option = option
                break
        
        if not target_option:
            if options:
                target_option = random.choice(options)
                logging.info("Could not match answer, selecting random option")
        
        if target_option:
            self.human_like_click(
                target_option['x'] + target_option['width'] // 2,
                target_option['y'] + target_option['height'] // 2
            )
    
    def answer_true_false(self, answer):
        screen_width, screen_height = pyautogui.size()
        
        true_region = pyautogui.locateOnScreen('templates/true_button.png', confidence=0.7)
        false_region = pyautogui.locateOnScreen('templates/false_button.png', confidence=0.7)
        
        if answer.lower() in ['true', 't', 'yes', 'y']:
            if true_region:
                center = pyautogui.center(true_region)
                self.human_like_click(center.x, center.y)
            else:
                self.human_like_click(screen_width // 2 - 100, screen_height // 2)
        else:
            if false_region:
                center = pyautogui.center(false_region)
                self.human_like_click(center.x, center.y)
            else:
                self.human_like_click(screen_width // 2 + 100, screen_height // 2)
    
    def answer_short_answer(self, answer, region):
        if region:
            click_x = region['x'] + region['width'] // 2
            click_y = region['y'] + region['height'] + 50
        else:
            screen_width, screen_height = pyautogui.size()
            click_x = screen_width // 2
            click_y = screen_height // 2
        
        self.human_like_click(click_x, click_y)
        
        time.sleep(0.5)
        
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        
        self.human_like_type(answer)
    
    def answer_mixed(self, answer, options, region):
        if options and len(options) >= 2:
            self.answer_multiple_choice(answer, options)
        else:
            self.answer_short_answer(answer, region)
    
    def human_like_click(self, x, y):
        offset_x = random.randint(-5, 5)
        offset_y = random.randint(-5, 5)
        
        target_x = x + offset_x
        target_y = y + offset_y
        
        current_x, current_y = pyautogui.position()
        
        duration = random.uniform(*self.mouse_speed_range)
        
        control_points = self.generate_bezier_curve(
            current_x, current_y, target_x, target_y, num_points=10
        )
        
        for point in control_points:
            pyautogui.moveTo(point[0], point[1], duration=duration/10)
        
        time.sleep(random.uniform(0.05, 0.15))
        
        pyautogui.click()
    
    def human_like_type(self, text):
        for char in text:
            pyautogui.typewrite(char)
            
            delay = random.uniform(*self.typing_speed_range)
            
            if char == ' ':
                delay *= 1.5
            elif char in '.,!?':
                delay *= 2
            
            time.sleep(delay)
    
    def generate_bezier_curve(self, x1, y1, x2, y2, num_points=10):
        points = []
        
        control_x = (x1 + x2) / 2 + random.randint(-50, 50)
        control_y = (y1 + y2) / 2 + random.randint(-50, 50)
        
        for i in range(num_points + 1):
            t = i / num_points
            
            x = (1-t)**2 * x1 + 2*(1-t)*t * control_x + t**2 * x2
            y = (1-t)**2 * y1 + 2*(1-t)*t * control_y + t**2 * y2
            
            points.append((int(x), int(y)))
        
        return points
    
    def scroll_down(self, amount=3):
        pyautogui.scroll(-amount)
        time.sleep(0.5)
    
    def scroll_up(self, amount=3):
        pyautogui.scroll(amount)
        time.sleep(0.5)
    
    def press_key(self, key):
        pyautogui.press(key)
        time.sleep(0.2)