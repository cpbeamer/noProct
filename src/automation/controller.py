import pyautogui
import time
import random
import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from src.utils.logger import get_logger
from src.core.exceptions import AutomationError

@dataclass
class MousePath:
    """Represents a mouse movement path"""
    points: List[Tuple[int, int]]
    duration: float
    
class HumanSimulator:
    """Advanced human behavior simulation"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = get_logger("HumanSimulator")
        
        # Movement parameters
        self.typing_speed = config.get('human_simulation.typing_speed_min', 0.05)
        self.typing_variance = config.get('human_simulation.typing_speed_max', 0.15)
        self.mouse_speed = config.get('human_simulation.mouse_speed_min', 0.3)
        self.mouse_variance = config.get('human_simulation.mouse_speed_max', 0.8)
        
        # Behavior patterns
        self.typo_probability = 0.02
        self.pause_probability = 0.1
        self.overshoot_probability = 0.15
        
        # Initialize pyautogui settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
    
    def move_mouse(self, x: int, y: int, duration: Optional[float] = None):
        """Move mouse with human-like behavior"""
        current_x, current_y = pyautogui.position()
        
        if duration is None:
            distance = np.sqrt((x - current_x)**2 + (y - current_y)**2)
            duration = self._calculate_duration(distance)
        
        # Generate path
        path = self._generate_bezier_path(current_x, current_y, x, y)
        
        # Add overshoot if applicable
        if random.random() < self.overshoot_probability:
            path = self._add_overshoot(path, x, y)
        
        # Execute movement
        for point in path:
            pyautogui.moveTo(point[0], point[1], duration=duration/len(path))
            
            # Random micro-pauses
            if random.random() < 0.05:
                time.sleep(random.uniform(0.01, 0.03))
    
    def click(self, x: Optional[int] = None, y: Optional[int] = None, 
             button: str = 'left', clicks: int = 1):
        """Click with human-like behavior"""
        if x is not None and y is not None:
            self.move_mouse(x, y)
        
        # Add small random offset
        offset_x = random.randint(-3, 3)
        offset_y = random.randint(-3, 3)
        current_x, current_y = pyautogui.position()
        
        pyautogui.moveTo(current_x + offset_x, current_y + offset_y, 
                         duration=random.uniform(0.05, 0.15))
        
        for _ in range(clicks):
            # Variable click duration
            pyautogui.mouseDown(button=button)
            time.sleep(random.uniform(0.05, 0.15))
            pyautogui.mouseUp(button=button)
            
            if clicks > 1:
                time.sleep(random.uniform(0.1, 0.3))
    
    def type_text(self, text: str, correct_typos: bool = True):
        """Type text with human-like behavior"""
        for i, char in enumerate(text):
            # Occasionally make typos
            if correct_typos and random.random() < self.typo_probability:
                # Type wrong character
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                pyautogui.typewrite(wrong_char)
                time.sleep(random.uniform(0.1, 0.3))
                
                # Correct it
                pyautogui.press('backspace')
                time.sleep(random.uniform(0.1, 0.2))
            
            # Type the character
            pyautogui.typewrite(char)
            
            # Variable typing speed
            base_delay = random.uniform(self.typing_speed, self.typing_variance)
            
            # Longer pauses for spaces and punctuation
            if char == ' ':
                base_delay *= random.uniform(1.2, 1.8)
            elif char in '.,!?;:':
                base_delay *= random.uniform(2, 3)
            
            # Occasional longer pauses (thinking)
            if random.random() < self.pause_probability:
                base_delay += random.uniform(0.5, 1.5)
            
            time.sleep(base_delay)
    
    def scroll(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None):
        """Scroll with human-like behavior"""
        if x is not None and y is not None:
            self.move_mouse(x, y)
        
        # Break into smaller scrolls
        remaining = abs(clicks)
        direction = 1 if clicks > 0 else -1
        
        while remaining > 0:
            scroll_amount = min(random.randint(1, 3), remaining)
            pyautogui.scroll(scroll_amount * direction)
            remaining -= scroll_amount
            
            if remaining > 0:
                time.sleep(random.uniform(0.1, 0.3))
    
    def _generate_bezier_path(self, x1: float, y1: float, 
                              x2: float, y2: float, 
                              num_points: int = 50) -> List[Tuple[int, int]]:
        """Generate a bezier curve path for mouse movement"""
        # Generate control points
        ctrl_points = self._generate_control_points(x1, y1, x2, y2)
        
        # Generate path
        points = []
        for t in np.linspace(0, 1, num_points):
            point = self._bezier_point(t, (x1, y1), ctrl_points[0], 
                                      ctrl_points[1], (x2, y2))
            points.append((int(point[0]), int(point[1])))
        
        return points
    
    def _generate_control_points(self, x1: float, y1: float, 
                                x2: float, y2: float) -> List[Tuple[float, float]]:
        """Generate control points for bezier curve"""
        distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        # More variation for longer distances
        variation = min(distance * 0.3, 100)
        
        # Generate two control points
        ctrl1_x = x1 + (x2 - x1) * 0.3 + random.uniform(-variation, variation)
        ctrl1_y = y1 + (y2 - y1) * 0.3 + random.uniform(-variation, variation)
        
        ctrl2_x = x1 + (x2 - x1) * 0.7 + random.uniform(-variation, variation)
        ctrl2_y = y1 + (y2 - y1) * 0.7 + random.uniform(-variation, variation)
        
        return [(ctrl1_x, ctrl1_y), (ctrl2_x, ctrl2_y)]
    
    def _bezier_point(self, t: float, p0: Tuple, p1: Tuple, 
                     p2: Tuple, p3: Tuple) -> Tuple[float, float]:
        """Calculate point on cubic bezier curve"""
        u = 1 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        return (x, y)
    
    def _add_overshoot(self, path: List[Tuple[int, int]], 
                      target_x: int, target_y: int) -> List[Tuple[int, int]]:
        """Add overshoot to mouse path"""
        overshoot_distance = random.uniform(10, 30)
        angle = random.uniform(0, 2 * np.pi)
        
        overshoot_x = target_x + int(overshoot_distance * np.cos(angle))
        overshoot_y = target_y + int(overshoot_distance * np.sin(angle))
        
        # Add overshoot points
        overshoot_path = []
        for t in np.linspace(0, 1, 10):
            x = target_x + (overshoot_x - target_x) * t
            y = target_y + (overshoot_y - target_y) * t
            overshoot_path.append((int(x), int(y)))
        
        # Return to target
        return_path = []
        for t in np.linspace(0, 1, 5):
            x = overshoot_x + (target_x - overshoot_x) * t
            y = overshoot_y + (target_y - overshoot_y) * t
            return_path.append((int(x), int(y)))
        
        return path[:-1] + overshoot_path + return_path
    
    def _calculate_duration(self, distance: float) -> float:
        """Calculate movement duration based on distance"""
        # Fitts's law approximation
        base_time = 0.2
        distance_factor = np.log2(distance / 50 + 1) * 0.15
        
        duration = base_time + distance_factor
        
        # Add randomness
        duration *= random.uniform(0.8, 1.2)
        
        return max(duration, 0.1)

class AdvancedAutomationController:
    """Enhanced automation controller with multiple answer strategies"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = get_logger("AutomationController")
        self.human_sim = HumanSimulator(config)
        
        # Statistics
        self.stats = {
            'total_answers': 0,
            'successful_answers': 0,
            'answer_times': []
        }
    
    def answer_question(self, answer: str, question_type: str, 
                       options: Optional[List[Dict]] = None,
                       region: Optional[Dict] = None) -> bool:
        """Answer a question with appropriate strategy"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Answering {question_type} question")
            
            # Choose strategy based on question type
            if question_type == "Multiple Choice":
                success = self._answer_multiple_choice(answer, options)
            elif question_type == "True/False":
                success = self._answer_true_false(answer)
            elif question_type == "Short Answer":
                success = self._answer_short_answer(answer, region)
            else:
                success = self._answer_mixed(answer, options, region)
            
            # Update statistics
            self.stats['total_answers'] += 1
            if success:
                self.stats['successful_answers'] += 1
            
            answer_time = time.time() - start_time
            self.stats['answer_times'].append(answer_time)
            
            self.logger.info(f"Question answered in {answer_time:.2f} seconds")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to answer question: {e}")
            raise AutomationError(f"Automation failed: {e}")
    
    def _answer_multiple_choice(self, answer: str, 
                               options: Optional[List[Dict]]) -> bool:
        """Answer multiple choice question"""
        if not options:
            self.logger.warning("No options provided for multiple choice")
            return False
        
        # Find matching option
        target_option = None
        answer_lower = answer.lower().strip()
        
        for option in options:
            option_text = option['text'].lower().strip()
            
            # Check for exact match
            if answer_lower in option_text:
                target_option = option
                break
            
            # Check for letter match (A, B, C, etc.)
            if len(answer_lower) == 1 and option_text.startswith(answer_lower):
                target_option = option
                break
        
        if not target_option:
            # Fallback to best guess
            self.logger.warning("Could not match answer, using best guess")
            target_option = self._guess_best_option(options, answer)
        
        if target_option:
            # Click the option
            click_x = target_option['x'] + target_option['width'] // 2
            click_y = target_option['y'] + target_option['height'] // 2
            
            # Add some randomness to click position
            click_x += random.randint(-10, 10)
            click_y += random.randint(-5, 5)
            
            self.human_sim.click(click_x, click_y)
            return True
        
        return False
    
    def _answer_true_false(self, answer: str) -> bool:
        """Answer true/false question"""
        answer_lower = answer.lower().strip()
        
        # Determine answer
        is_true = answer_lower in ['true', 't', 'yes', 'y', '1']
        
        # Try to find buttons on screen
        screen_width, screen_height = pyautogui.size()
        
        # Search for True/False buttons
        true_button = pyautogui.locateOnScreen('templates/buttons/true.png', 
                                              confidence=0.7)
        false_button = pyautogui.locateOnScreen('templates/buttons/false.png', 
                                               confidence=0.7)
        
        if is_true and true_button:
            center = pyautogui.center(true_button)
            self.human_sim.click(center.x, center.y)
            return True
        elif not is_true and false_button:
            center = pyautogui.center(false_button)
            self.human_sim.click(center.x, center.y)
            return True
        else:
            # Fallback positions
            if is_true:
                self.human_sim.click(screen_width // 2 - 100, screen_height // 2)
            else:
                self.human_sim.click(screen_width // 2 + 100, screen_height // 2)
            return True
    
    def _answer_short_answer(self, answer: str, 
                           region: Optional[Dict]) -> bool:
        """Answer short answer question"""
        # Find input field
        if region:
            click_x = region['x'] + region['width'] // 2
            click_y = region['y'] + region['height'] + 30
        else:
            # Search for input field
            input_field = pyautogui.locateOnScreen('templates/patterns/input_field.png',
                                                  confidence=0.6)
            if input_field:
                center = pyautogui.center(input_field)
                click_x, click_y = center.x, center.y
            else:
                # Default to center of screen
                screen_width, screen_height = pyautogui.size()
                click_x = screen_width // 2
                click_y = screen_height // 2 + 50
        
        # Click input field
        self.human_sim.click(click_x, click_y)
        time.sleep(0.3)
        
        # Clear existing text
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        
        # Type answer
        self.human_sim.type_text(answer)
        
        return True
    
    def _answer_mixed(self, answer: str, options: Optional[List[Dict]], 
                     region: Optional[Dict]) -> bool:
        """Handle mixed or unknown question types"""
        if options and len(options) >= 2:
            return self._answer_multiple_choice(answer, options)
        else:
            return self._answer_short_answer(answer, region)
    
    def _guess_best_option(self, options: List[Dict], answer: str) -> Optional[Dict]:
        """Make educated guess for best option"""
        # Strategy 1: Look for "all of the above"
        for option in options:
            if 'all of the above' in option['text'].lower():
                return option
        
        # Strategy 2: Choose longest option (often correct)
        longest = max(options, key=lambda x: len(x['text']))
        if len(longest['text']) > len(options[0]['text']) * 1.5:
            return longest
        
        # Strategy 3: Middle option (C in A-E)
        if len(options) >= 3:
            return options[len(options) // 2]
        
        # Strategy 4: Random
        return random.choice(options)
    
    def submit_answer(self):
        """Submit the current answer"""
        # Look for submit button
        submit_button = pyautogui.locateOnScreen('templates/buttons/submit.png',
                                                confidence=0.7)
        if submit_button:
            center = pyautogui.center(submit_button)
            self.human_sim.click(center.x, center.y)
        else:
            # Try Enter key
            pyautogui.press('enter')
    
    def navigate_next(self):
        """Navigate to next question"""
        # Look for next button
        next_button = pyautogui.locateOnScreen('templates/buttons/next.png',
                                              confidence=0.7)
        if next_button:
            center = pyautogui.center(next_button)
            self.human_sim.click(center.x, center.y)
        else:
            # Try arrow key
            pyautogui.press('right')
    
    def get_statistics(self) -> Dict:
        """Get automation statistics"""
        stats = self.stats.copy()
        if stats['answer_times']:
            stats['avg_answer_time'] = sum(stats['answer_times']) / len(stats['answer_times'])
        return stats