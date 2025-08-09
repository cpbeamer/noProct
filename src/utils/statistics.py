import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

@dataclass
class SessionStats:
    """Statistics for a single session"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    questions_detected: int
    questions_answered: int
    successful_answers: int
    failed_answers: int
    avg_detection_confidence: float
    avg_answer_time: float
    total_runtime: float
    
    @property
    def success_rate(self) -> float:
        if self.questions_answered == 0:
            return 0.0
        return self.successful_answers / self.questions_answered
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        data['end_time'] = self.end_time.isoformat() if self.end_time else None
        data['success_rate'] = self.success_rate
        return data

class StatisticsTracker:
    """Track and analyze service statistics"""
    
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = datetime.now()
        
        # Current session stats
        self.questions_detected = 0
        self.questions_answered = 0
        self.successful_answers = 0
        self.failed_answers = 0
        self.detection_confidences = []
        self.answer_times = []
        
        # Detailed tracking
        self.detections = []
        self.answers = []
        self.errors = []
        
        # Performance metrics
        self.performance_data = {
            'detection_times': [],
            'ocr_times': [],
            'ai_query_times': [],
            'automation_times': []
        }
        
        # Load historical data
        self.historical_data = self._load_historical_data()
    
    def track_detection(self, detection):
        """Track a question detection"""
        self.questions_detected += 1
        self.detection_confidences.append(detection.confidence)
        
        self.detections.append({
            'timestamp': detection.timestamp.isoformat(),
            'question': detection.question_text[:100],
            'confidence': detection.confidence,
            'method': detection.detection_method
        })
    
    def track_answer(self, answer: str, success: bool):
        """Track an answer attempt"""
        self.questions_answered += 1
        
        if success:
            self.successful_answers += 1
        else:
            self.failed_answers += 1
        
        self.answers.append({
            'timestamp': datetime.now().isoformat(),
            'answer': answer[:50],
            'success': success
        })
    
    def track_error(self, error: Exception, context: str):
        """Track an error"""
        self.errors.append({
            'timestamp': datetime.now().isoformat(),
            'error': str(error),
            'context': context
        })
    
    def track_performance(self, operation: str, duration: float):
        """Track performance metrics"""
        if operation in self.performance_data:
            self.performance_data[operation].append(duration)
    
    def get_current_stats(self) -> Dict:
        """Get current session statistics"""
        runtime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'session_id': self.session_id,
            'runtime': runtime,
            'questions_detected': self.questions_detected,
            'questions_answered': self.questions_answered,
            'successful_answers': self.successful_answers,
            'failed_answers': self.failed_answers,
            'success_rate': self.successful_answers / max(self.questions_answered, 1),
            'avg_confidence': sum(self.detection_confidences) / max(len(self.detection_confidences), 1),
            'errors': len(self.errors),
            'total_runtime': runtime
        }
    
    def get_summary(self) -> SessionStats:
        """Get session summary"""
        runtime = (datetime.now() - self.start_time).total_seconds()
        
        return SessionStats(
            session_id=self.session_id,
            start_time=self.start_time,
            end_time=datetime.now(),
            questions_detected=self.questions_detected,
            questions_answered=self.questions_answered,
            successful_answers=self.successful_answers,
            failed_answers=self.failed_answers,
            avg_detection_confidence=sum(self.detection_confidences) / max(len(self.detection_confidences), 1),
            avg_answer_time=sum(self.answer_times) / max(len(self.answer_times), 1),
            total_runtime=runtime
        )
    
    def get_performance_report(self) -> Dict:
        """Get detailed performance report"""
        report = {}
        
        for operation, times in self.performance_data.items():
            if times:
                report[operation] = {
                    'count': len(times),
                    'total': sum(times),
                    'average': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times)
                }
        
        return report
    
    def save_session(self):
        """Save current session data"""
        session_data = {
            'summary': self.get_summary().to_dict(),
            'detections': self.detections,
            'answers': self.answers,
            'errors': self.errors,
            'performance': self.get_performance_report()
        }
        
        # Save to file
        stats_dir = Path('data/statistics')
        stats_dir.mkdir(parents=True, exist_ok=True)
        
        filename = stats_dir / f"session_{self.session_id}.json"
        with open(filename, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        # Update historical data
        self._update_historical_data(session_data['summary'])
    
    def _load_historical_data(self) -> Dict:
        """Load historical statistics"""
        history_file = Path('data/statistics/history.json')
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'total_sessions': 0,
            'total_questions_answered': 0,
            'total_successful_answers': 0,
            'all_time_success_rate': 0.0,
            'sessions': []
        }
    
    def _update_historical_data(self, session_summary: Dict):
        """Update historical data with session results"""
        self.historical_data['total_sessions'] += 1
        self.historical_data['total_questions_answered'] += session_summary['questions_answered']
        self.historical_data['total_successful_answers'] += session_summary['successful_answers']
        
        # Update all-time success rate
        if self.historical_data['total_questions_answered'] > 0:
            self.historical_data['all_time_success_rate'] = (
                self.historical_data['total_successful_answers'] / 
                self.historical_data['total_questions_answered']
            )
        
        # Add session summary
        self.historical_data['sessions'].append(session_summary)
        
        # Keep only last 100 sessions
        if len(self.historical_data['sessions']) > 100:
            self.historical_data['sessions'] = self.historical_data['sessions'][-100:]
        
        # Save updated history
        history_file = Path('data/statistics/history.json')
        with open(history_file, 'w') as f:
            json.dump(self.historical_data, f, indent=2)
    
    def get_historical_summary(self) -> Dict:
        """Get historical statistics summary"""
        return self.historical_data.copy()
    
    def generate_report(self) -> str:
        """Generate a text report of statistics"""
        current = self.get_current_stats()
        historical = self.get_historical_summary()
        performance = self.get_performance_report()
        
        report = f"""
Question Assistant Statistics Report
=====================================
Session ID: {current['session_id']}
Runtime: {current['runtime']:.1f} seconds

Current Session:
- Questions Detected: {current['questions_detected']}
- Questions Answered: {current['questions_answered']}
- Successful Answers: {current['successful_answers']}
- Failed Answers: {current['failed_answers']}
- Success Rate: {current['success_rate']:.1%}
- Average Confidence: {current['avg_confidence']:.2f}
- Errors: {current['errors']}

Historical Data:
- Total Sessions: {historical['total_sessions']}
- Total Questions Answered: {historical['total_questions_answered']}
- All-Time Success Rate: {historical['all_time_success_rate']:.1%}

Performance Metrics:
"""
        
        for operation, metrics in performance.items():
            report += f"\n{operation}:"
            report += f"\n  - Count: {metrics['count']}"
            report += f"\n  - Average: {metrics['average']:.3f}s"
            report += f"\n  - Min: {metrics['min']:.3f}s"
            report += f"\n  - Max: {metrics['max']:.3f}s"
        
        return report