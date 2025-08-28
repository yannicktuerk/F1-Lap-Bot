"""Structured logging and metrics collection for observability (Issue 13)."""
import json
import time
import logging
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels for structured logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class CoachingRecommendationLog:
    """Structured log entry for coaching recommendations."""
    timestamp: float
    session_uid: str
    lap_number: int
    turn_id: int
    action_type: str
    coaching_message: str
    expected_utility: float
    confidence: float
    safety_ampel: str
    slip_conditions: Dict[str, float]
    bandit_arm: str
    exploration: bool
    context: Dict[str, Any]


@dataclass
class ReviewerResultLog:
    """Structured log entry for reviewer results."""
    timestamp: float
    session_uid: str
    lap_number: int
    turn_id: int
    action_type: str
    outcome: str  # attempt, success, overshoot, no_attempt
    performance_delta: float
    pattern_detected: bool
    intensity_adjustment: str
    context: Dict[str, Any]


@dataclass
class PerformanceMetrics:
    """Performance metrics for the coaching system."""
    total_recommendations: int = 0
    recommendations_per_turn: Dict[int, int] = None
    hit_rate: float = 0.0  # attempt detection rate
    success_rate: float = 0.0  # success without red slip
    pb_improvement_rate: float = 0.0
    sector_pb_improvement_rate: float = 0.0
    avg_coaching_delay_ms: float = 0.0
    avg_utility_confidence: float = 0.0
    
    def __post_init__(self):
        if self.recommendations_per_turn is None:
            self.recommendations_per_turn = {}


class StructuredLogger:
    """Structured logger for coaching system events."""
    
    def __init__(self, logger_name: str = "f1_coaching"):
        """Initialize structured logger."""
        self.logger = logging.getLogger(logger_name)
        self._lock = threading.Lock()
    
    def log_recommendation(self, log_entry: CoachingRecommendationLog) -> None:
        """Log a coaching recommendation with full context."""
        with self._lock:
            log_data = {
                "event_type": "coaching_recommendation",
                "data": asdict(log_entry)
            }
            self.logger.info(json.dumps(log_data, separators=(',', ':')))
    
    def log_reviewer_result(self, log_entry: ReviewerResultLog) -> None:
        """Log a reviewer evaluation result."""
        with self._lock:
            log_data = {
                "event_type": "reviewer_result",
                "data": asdict(log_entry)
            }
            self.logger.info(json.dumps(log_data, separators=(',', ':')))
    
    def log_performance_metrics(self, metrics: PerformanceMetrics) -> None:
        """Log aggregated performance metrics."""
        with self._lock:
            log_data = {
                "event_type": "performance_metrics",
                "data": asdict(metrics)
            }
            self.logger.info(json.dumps(log_data, separators=(',', ':')))
    
    def log_error(self, component: str, error: str, context: Dict[str, Any] = None) -> None:
        """Log an error with context."""
        with self._lock:
            log_data = {
                "event_type": "error",
                "component": component,
                "error": error,
                "context": context or {},
                "timestamp": time.time()
            }
            self.logger.error(json.dumps(log_data, separators=(',', ':')))
    
    def log_system_event(self, event: str, data: Dict[str, Any]) -> None:
        """Log a general system event."""
        with self._lock:
            log_data = {
                "event_type": "system_event",
                "event": event,
                "data": data,
                "timestamp": time.time()
            }
            self.logger.info(json.dumps(log_data, separators=(',', ':')))


class MetricsCollector:
    """Collector for coaching system KPIs and metrics."""
    
    def __init__(self, window_size: int = 1000):
        """Initialize metrics collector."""
        self.window_size = window_size
        self._lock = threading.Lock()
        
        # Time series data
        self.recommendation_history: deque = deque(maxlen=window_size)
        self.reviewer_history: deque = deque(maxlen=window_size)
        self.performance_history: deque = deque(maxlen=window_size)
        self.turn_split_deltas: Dict[int, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Counters
        self.total_recommendations = 0
        self.total_attempts = 0
        self.total_successes = 0
        self.total_pb_improvements = 0
        self.total_sector_pb_improvements = 0
        
        # Performance tracking
        self.coaching_delays_ms: deque = deque(maxlen=100)
        self.utility_confidences: deque = deque(maxlen=100)
    
    def record_recommendation(self, log_entry: CoachingRecommendationLog) -> None:
        """Record a coaching recommendation."""
        with self._lock:
            self.recommendation_history.append(log_entry)
            self.total_recommendations += 1
            
            if log_entry.confidence > 0:
                self.utility_confidences.append(log_entry.confidence)
    
    def record_reviewer_result(self, log_entry: ReviewerResultLog) -> None:
        """Record a reviewer evaluation result."""
        with self._lock:
            self.reviewer_history.append(log_entry)
            
            if log_entry.outcome in ["attempt", "success", "overshoot"]:
                self.total_attempts += 1
            
            if log_entry.outcome == "success":
                self.total_successes += 1
            
            # Record turn split delta
            if log_entry.performance_delta != 0:
                self.turn_split_deltas[log_entry.turn_id].append(log_entry.performance_delta)
    
    def record_performance_improvement(self, pb_improvement: bool, sector_pb_improvement: bool) -> None:
        """Record performance improvements."""
        with self._lock:
            if pb_improvement:
                self.total_pb_improvements += 1
            if sector_pb_improvement:
                self.total_sector_pb_improvements += 1
    
    def record_coaching_delay(self, delay_ms: float) -> None:
        """Record coaching pipeline delay."""
        with self._lock:
            self.coaching_delays_ms.append(delay_ms)
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        with self._lock:
            # Calculate rates
            hit_rate = self.total_attempts / max(1, self.total_recommendations)
            success_rate = self.total_successes / max(1, self.total_attempts)
            
            # Calculate averages
            avg_delay = statistics.mean(self.coaching_delays_ms) if self.coaching_delays_ms else 0.0
            avg_confidence = statistics.mean(self.utility_confidences) if self.utility_confidences else 0.0
            
            # Recommendations per turn
            turn_counts = defaultdict(int)
            for rec in self.recommendation_history:
                turn_counts[rec.turn_id] += 1
            
            return PerformanceMetrics(
                total_recommendations=self.total_recommendations,
                recommendations_per_turn=dict(turn_counts),
                hit_rate=hit_rate,
                success_rate=success_rate,
                pb_improvement_rate=self.total_pb_improvements / max(1, len(self.performance_history)),
                sector_pb_improvement_rate=self.total_sector_pb_improvements / max(1, len(self.performance_history)),
                avg_coaching_delay_ms=avg_delay,
                avg_utility_confidence=avg_confidence
            )
    
    def get_turn_split_distribution(self, turn_id: int) -> Dict[str, float]:
        """Get split delta distribution for a specific turn."""
        with self._lock:
            deltas = list(self.turn_split_deltas.get(turn_id, []))
            if not deltas:
                return {}
            
            return {
                "count": len(deltas),
                "mean": statistics.mean(deltas),
                "median": statistics.median(deltas),
                "std_dev": statistics.stdev(deltas) if len(deltas) > 1 else 0.0,
                "min": min(deltas),
                "max": max(deltas),
                "p25": statistics.quantiles(deltas, n=4)[0] if len(deltas) >= 4 else deltas[0],
                "p75": statistics.quantiles(deltas, n=4)[2] if len(deltas) >= 4 else deltas[-1]
            }


class DashboardService:
    """Service for real-time KPI dashboard and metrics visualization."""
    
    def __init__(self, metrics_collector: MetricsCollector, update_interval: int = 30):
        """Initialize dashboard service."""
        self.metrics_collector = metrics_collector
        self.update_interval = update_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[Dict[str, Any]], None]] = []
    
    def add_update_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Add callback for dashboard updates."""
        self._callbacks.append(callback)
    
    def start(self) -> None:
        """Start dashboard updates."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()
        logger.info("Dashboard service started")
    
    def stop(self) -> None:
        """Stop dashboard updates."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("Dashboard service stopped")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data."""
        metrics = self.metrics_collector.get_current_metrics()
        
        # Get turn split distributions
        turn_distributions = {}
        for turn_id in range(1, 10):  # Common turn IDs
            dist = self.metrics_collector.get_turn_split_distribution(turn_id)
            if dist:
                turn_distributions[turn_id] = dist
        
        return {
            "metrics": asdict(metrics),
            "turn_distributions": turn_distributions,
            "last_updated": time.time()
        }
    
    def _update_loop(self) -> None:
        """Main update loop for dashboard."""
        while self._running:
            try:
                dashboard_data = self.get_dashboard_data()
                
                # Notify all callbacks
                for callback in self._callbacks:
                    try:
                        callback(dashboard_data)
                    except Exception as e:
                        logger.error(f"Error in dashboard callback: {e}")
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in dashboard update loop: {e}")
                time.sleep(5.0)


class ObservabilityFacade:
    """Facade coordinating all observability components."""
    
    def __init__(self, 
                 structured_logger: StructuredLogger,
                 metrics_collector: MetricsCollector,
                 dashboard_service: DashboardService):
        """Initialize observability facade."""
        self.logger = structured_logger
        self.metrics = metrics_collector
        self.dashboard = dashboard_service
    
    def log_and_track_recommendation(self, log_entry: CoachingRecommendationLog) -> None:
        """Log and track a coaching recommendation."""
        self.logger.log_recommendation(log_entry)
        self.metrics.record_recommendation(log_entry)
    
    def log_and_track_reviewer_result(self, log_entry: ReviewerResultLog) -> None:
        """Log and track a reviewer result."""
        self.logger.log_reviewer_result(log_entry)
        self.metrics.record_reviewer_result(log_entry)
    
    def record_performance_timing(self, delay_ms: float) -> None:
        """Record coaching pipeline performance timing."""
        self.metrics.record_coaching_delay(delay_ms)
        
        # Log if delay exceeds threshold
        if delay_ms > 150:  # 150ms threshold from requirements
            self.logger.log_system_event("performance_warning", {
                "delay_ms": delay_ms,
                "threshold_ms": 150
            })
    
    def start(self) -> None:
        """Start all observability services."""
        self.dashboard.start()
        logger.info("Observability services started")
    
    def stop(self) -> None:
        """Stop all observability services."""
        self.dashboard.stop()
        logger.info("Observability services stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get observability system status."""
        return {
            "metrics": asdict(self.metrics.get_current_metrics()),
            "dashboard_running": self.dashboard._running,
            "total_logs": len(self.metrics.recommendation_history) + len(self.metrics.reviewer_history)
        }