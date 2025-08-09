import sys
import os
import time
import logging
import threading
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config_manager import ConfigManager
from src.screen_monitor import ScreenMonitor
from src.question_detector import QuestionDetector
from src.automation_controller import AutomationController
from src.ai_researcher import AIResearcher

logging.basicConfig(
    filename='logs/service.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class BackgroundService:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.running = False
        self.start_time = None
        self.questions_answered = 0
        
        self.screen_monitor = ScreenMonitor()
        self.question_detector = QuestionDetector(self.config)
        self.automation_controller = AutomationController()
        self.ai_researcher = AIResearcher(self.config.get('api_key'))
        
        self.abort_listener_thread = None
    
    def start(self):
        logging.info("Background service starting...")
        self.running = True
        self.start_time = datetime.now()
        
        self.setup_abort_listener()
        
        try:
            self.main_loop()
        except Exception as e:
            logging.error(f"Service error: {e}")
        finally:
            self.stop()
    
    def setup_abort_listener(self):
        from pynput import keyboard
        
        def on_press(key):
            try:
                if key == keyboard.Key.esc:
                    logging.info("Abort key pressed")
                    self.running = False
                    return False
            except:
                pass
        
        listener = keyboard.Listener(on_press=on_press)
        self.abort_listener_thread = threading.Thread(target=listener.start)
        self.abort_listener_thread.daemon = True
        self.abort_listener_thread.start()
    
    def main_loop(self):
        monitoring_interval = self.config.get('monitoring_interval', 5)
        duration_minutes = self.config.get('duration_minutes', 60)
        max_questions = self.config.get('num_questions', 10)
        
        while self.running:
            elapsed_minutes = (datetime.now() - self.start_time).seconds / 60
            
            if elapsed_minutes >= duration_minutes:
                logging.info(f"Session time limit reached ({duration_minutes} minutes)")
                break
            
            if self.questions_answered >= max_questions:
                logging.info(f"Maximum questions answered ({max_questions})")
                break
            
            screenshot = self.screen_monitor.capture_screen()
            
            if screenshot:
                question_data = self.question_detector.detect_question(screenshot)
                
                if question_data:
                    logging.info(f"Question detected: {question_data.get('question_text', 'Unknown')[:50]}...")
                    self.handle_question(question_data)
                    self.questions_answered += 1
            
            time.sleep(monitoring_interval)
    
    def handle_question(self, question_data):
        try:
            question_text = question_data.get('question_text', '')
            options = question_data.get('options', [])
            question_region = question_data.get('region', None)
            
            if not question_text:
                logging.warning("No question text extracted")
                return
            
            answer = self.ai_researcher.research_answer(question_text, options, self.config.get('context'))
            
            if answer:
                logging.info(f"Answer found: {answer}")
                
                self.automation_controller.answer_question(
                    answer=answer,
                    question_type=self.config.get('question_type'),
                    region=question_region,
                    options=options
                )
                
                self.pace_actions()
            else:
                logging.warning("Could not determine answer")
        
        except Exception as e:
            logging.error(f"Error handling question: {e}")
    
    def pace_actions(self):
        duration_minutes = self.config.get('duration_minutes', 60)
        max_questions = self.config.get('num_questions', 10)
        
        seconds_per_question = (duration_minutes * 60) / max_questions
        
        wait_time = max(5, seconds_per_question - 10)
        
        logging.info(f"Waiting {wait_time:.1f} seconds before next action...")
        time.sleep(wait_time)
    
    def stop(self):
        logging.info(f"Service stopping. Questions answered: {self.questions_answered}")
        self.running = False

if __name__ == "__main__":
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    service = BackgroundService()
    service.start()