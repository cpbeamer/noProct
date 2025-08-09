class QuestionAssistantError(Exception):
    """Base exception for Question Assistant"""
    pass

class ConfigurationError(QuestionAssistantError):
    """Raised when configuration is invalid or missing"""
    pass

class DetectionError(QuestionAssistantError):
    """Raised when detection fails"""
    pass

class AutomationError(QuestionAssistantError):
    """Raised when automation fails"""
    pass

class ServiceError(QuestionAssistantError):
    """Raised when service operations fail"""
    pass

class OCRError(QuestionAssistantError):
    """Raised when OCR operations fail"""
    pass

class APIError(QuestionAssistantError):
    """Raised when API calls fail"""
    pass

class TemplateError(QuestionAssistantError):
    """Raised when template matching fails"""
    pass