import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

class Logger:
    """Enhanced logging system with rotation and formatting"""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self):
        """Initialize the logging system"""
        self._logger = logging.getLogger("QuestionAssistant")
        self._logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self._logger.handlers = []
        
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"service_{datetime.now().strftime('%Y%m%d')}.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Detailed formatter for file
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Simple formatter for console
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)
    
    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        """Get a logger instance"""
        instance = cls()
        if name:
            return logging.getLogger(f"QuestionAssistant.{name}")
        return instance._logger
    
    @classmethod
    def log_exception(cls, e: Exception, context: str = ""):
        """Log an exception with full traceback"""
        logger = cls.get_logger()
        import traceback
        logger.error(f"Exception in {context}: {str(e)}")
        logger.debug(f"Traceback:\n{traceback.format_exc()}")
    
    @classmethod
    def log_performance(cls, operation: str, duration: float):
        """Log performance metrics"""
        logger = cls.get_logger("Performance")
        logger.info(f"{operation} completed in {duration:.3f} seconds")
    
    @classmethod
    def log_detection(cls, question_text: str, confidence: float, answer: Optional[str] = None):
        """Log question detection events"""
        logger = cls.get_logger("Detection")
        logger.info(f"Question detected (confidence: {confidence:.2f}): {question_text[:100]}...")
        if answer:
            logger.info(f"Answer: {answer}")

# Convenience functions
def get_logger(name: Optional[str] = None) -> logging.Logger:
    return Logger.get_logger(name)

def log_exception(e: Exception, context: str = ""):
    Logger.log_exception(e, context)

def log_performance(operation: str, duration: float):
    Logger.log_performance(operation, duration)

def log_detection(question_text: str, confidence: float, answer: Optional[str] = None):
    Logger.log_detection(question_text, confidence, answer)