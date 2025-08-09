import sys
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

# Windows service imports
try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    WINDOWS_SERVICE_AVAILABLE = True
except ImportError:
    WINDOWS_SERVICE_AVAILABLE = False

from src.utils.logger import get_logger, log_exception
from src.core.config import Config
from src.core.exceptions import ServiceError
from src.detection.detector import OptimizedQuestionDetector
from src.automation.controller import AdvancedAutomationController
from src.ai.researcher import EnhancedAIResearcher
from src.utils.statistics import StatisticsTracker

class ServiceManager:
    """Main service manager with error recovery and monitoring"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = Config(config_path)
        self.logger = get_logger("ServiceManager")
        
        # Service state
        self.running = False
        self.paused = False
        self.start_time = None
        self.end_time = None
        
        # Components (lazy initialization)
        self._screen_monitor = None
        self._ocr_engine = None
        self._detector = None
        self._controller = None
        self._researcher = None
        self._stats_tracker = None
        
        # Threading
        self.main_thread = None
        self.abort_thread = None
        self.monitor_thread = None
        
        # Error handling
        self.error_count = 0
        self.max_errors = 10
        self.last_error_time = None
        
    def initialize_components(self):
        """Initialize all service components"""
        try:
            self.logger.info("Initializing service components...")
            
            # Import components
            from src.screen_monitor import ScreenMonitor
            from src.ocr_engine import OCREngine
            
            # Initialize components
            self._screen_monitor = ScreenMonitor()
            self._ocr_engine = OCREngine(self.config.get('tesseract_path'))
            self._detector = OptimizedQuestionDetector(self.config.config, self._ocr_engine)
            self._controller = AdvancedAutomationController(self.config.config)
            self._researcher = EnhancedAIResearcher(self.config.config)
            self._stats_tracker = StatisticsTracker()
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            log_exception(e, "Component initialization")
            raise ServiceError(f"Failed to initialize components: {e}")
    
    def start(self):
        """Start the service"""
        if self.running:
            self.logger.warning("Service already running")
            return
        
        try:
            self.logger.info("Starting Question Assistant Service...")
            
            # Initialize components
            self.initialize_components()
            
            # Set service state
            self.running = True
            self.start_time = datetime.now()
            self.end_time = self.start_time + timedelta(
                minutes=self.config.get('duration_minutes', 60)
            )
            
            # Start threads
            self._start_abort_listener()
            self._start_health_monitor()
            
            # Start main loop
            self.main_thread = threading.Thread(target=self._main_loop)
            self.main_thread.daemon = False
            self.main_thread.start()
            
            self.logger.info("Service started successfully")
            
        except Exception as e:
            self.running = False
            log_exception(e, "Service start")
            raise ServiceError(f"Failed to start service: {e}")
    
    def stop(self):
        """Stop the service"""
        self.logger.info("Stopping service...")
        self.running = False
        
        # Wait for threads to finish
        if self.main_thread and self.main_thread.is_alive():
            self.main_thread.join(timeout=5)
        
        # Log final statistics
        if self._stats_tracker:
            stats = self._stats_tracker.get_summary()
            self.logger.info(f"Service statistics: {stats}")
        
        self.logger.info("Service stopped")
    
    def pause(self):
        """Pause the service"""
        self.paused = True
        self.logger.info("Service paused")
    
    def resume(self):
        """Resume the service"""
        self.paused = False
        self.logger.info("Service resumed")
    
    def _main_loop(self):
        """Main service loop with error recovery"""
        monitoring_interval = self.config.get('monitoring_interval', 5)
        max_questions = self.config.get('num_questions', 10)
        questions_answered = 0
        
        while self.running:
            try:
                # Check if paused
                if self.paused:
                    time.sleep(1)
                    continue
                
                # Check time limit
                if datetime.now() >= self.end_time:
                    self.logger.info("Session time limit reached")
                    break
                
                # Check question limit
                if questions_answered >= max_questions:
                    self.logger.info(f"Maximum questions answered ({max_questions})")
                    break
                
                # Capture screen
                screenshot = self._screen_monitor.capture_screen()
                if screenshot is None:
                    self.logger.warning("Failed to capture screen")
                    time.sleep(monitoring_interval)
                    continue
                
                # Detect question
                detection = self._detector.detect(screenshot)
                
                if detection and not self._detector.is_duplicate(detection):
                    self.logger.info(f"Question detected: {detection.question_text[:50]}...")
                    
                    # Track detection
                    self._stats_tracker.track_detection(detection)
                    
                    # Research answer
                    answer = self._researcher.research_answer(
                        detection.question_text,
                        detection.options,
                        self.config.get('context')
                    )
                    
                    if answer:
                        # Answer question
                        success = self._controller.answer_question(
                            answer,
                            self.config.get('question_type'),
                            detection.options,
                            detection.region
                        )
                        
                        if success:
                            questions_answered += 1
                            self._stats_tracker.track_answer(answer, success)
                            
                            # Pace actions
                            self._pace_actions(questions_answered, max_questions)
                    else:
                        self.logger.warning("Could not determine answer")
                
                # Sleep before next check
                time.sleep(monitoring_interval)
                
                # Reset error count on successful iteration
                self.error_count = 0
                
            except Exception as e:
                self._handle_error(e)
                if self.error_count >= self.max_errors:
                    self.logger.error("Maximum errors reached, stopping service")
                    break
    
    def _pace_actions(self, current_questions: int, max_questions: int):
        """Intelligent pacing based on progress"""
        duration_minutes = self.config.get('duration_minutes', 60)
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60
        remaining_minutes = duration_minutes - elapsed
        remaining_questions = max_questions - current_questions
        
        if remaining_questions > 0 and remaining_minutes > 0:
            # Calculate optimal pace
            minutes_per_question = remaining_minutes / remaining_questions
            wait_time = max(5, min(minutes_per_question * 60 - 10, 120))
            
            self.logger.debug(f"Pacing: waiting {wait_time:.1f} seconds")
            time.sleep(wait_time)
    
    def _handle_error(self, error: Exception):
        """Handle errors with recovery logic"""
        self.error_count += 1
        current_time = datetime.now()
        
        # Log error
        log_exception(error, "Main loop")
        
        # Check error frequency
        if self.last_error_time:
            time_since_last = (current_time - self.last_error_time).total_seconds()
            if time_since_last < 5:
                # Rapid errors, increase wait time
                wait_time = min(self.error_count * 2, 30)
                self.logger.warning(f"Rapid errors detected, waiting {wait_time} seconds")
                time.sleep(wait_time)
        
        self.last_error_time = current_time
        
        # Try to recover based on error type
        if "OCR" in str(error):
            self.logger.info("Attempting to reinitialize OCR engine...")
            try:
                from src.ocr_engine import OCREngine
                self._ocr_engine = OCREngine(self.config.get('tesseract_path'))
            except:
                pass
        
        # General recovery wait
        time.sleep(2)
    
    def _start_abort_listener(self):
        """Start keyboard listener for abort key"""
        def listen_for_abort():
            try:
                from pynput import keyboard
                
                def on_press(key):
                    try:
                        if key == keyboard.Key.esc:
                            self.logger.info("Abort key pressed")
                            self.stop()
                            return False
                    except:
                        pass
                
                listener = keyboard.Listener(on_press=on_press)
                listener.start()
                listener.join()
                
            except Exception as e:
                self.logger.error(f"Abort listener error: {e}")
        
        self.abort_thread = threading.Thread(target=listen_for_abort)
        self.abort_thread.daemon = True
        self.abort_thread.start()
    
    def _start_health_monitor(self):
        """Start health monitoring thread"""
        def monitor_health():
            while self.running:
                try:
                    # Check component health
                    if self._stats_tracker:
                        stats = self._stats_tracker.get_current_stats()
                        
                        # Log periodic stats
                        if stats['total_runtime'] % 300 == 0:  # Every 5 minutes
                            self.logger.info(f"Health check - Questions: {stats['questions_answered']}, "
                                          f"Success rate: {stats['success_rate']:.1%}")
                    
                    # Check memory usage
                    import psutil
                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    
                    if memory_mb > 500:
                        self.logger.warning(f"High memory usage: {memory_mb:.1f} MB")
                    
                    time.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    self.logger.debug(f"Health monitor error: {e}")
        
        self.monitor_thread = threading.Thread(target=monitor_health)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

class WindowsService(win32serviceutil.ServiceFramework if WINDOWS_SERVICE_AVAILABLE else object):
    """Windows Service wrapper"""
    
    _svc_name_ = "QuestionAssistantService"
    _svc_display_name_ = "Question Assistant Service"
    _svc_description_ = "Automated question detection and answering service"
    
    def __init__(self, args):
        if WINDOWS_SERVICE_AVAILABLE:
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.service_manager = None
    
    def SvcStop(self):
        """Stop the Windows service"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.service_manager:
            self.service_manager.stop()
        win32event.SetEvent(self.hWaitStop)
    
    def SvcDoRun(self):
        """Run the Windows service"""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        try:
            self.service_manager = ServiceManager()
            self.service_manager.start()
            
            # Wait for stop signal
            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
            
        except Exception as e:
            servicemanager.LogErrorMsg(f"Service error: {e}")

def install_service():
    """Install Windows service"""
    if not WINDOWS_SERVICE_AVAILABLE:
        print("Windows service support not available")
        return
    
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(WindowsService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(WindowsService)