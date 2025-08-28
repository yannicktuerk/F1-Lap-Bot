"""Value objects for coaching review and evaluation."""
from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime


class ReviewOutcome(Enum):
    """Classification of coaching attempt outcome."""
    SUCCESS = "success"
    OVERSHOOT = "overshoot"
    NO_ATTEMPT = "no_attempt"
    INCONCLUSIVE = "inconclusive"


class AttemptPattern(Enum):
    """Specific patterns to detect in telemetry."""
    BRAKE_EARLIER = "brake_earlier"
    PRESSURE_FASTER = "pressure_faster"
    RELEASE_EARLIER = "release_earlier"
    THROTTLE_EARLIER = "throttle_earlier"
    REDUCE_STEERING = "reduce_steering"


@dataclass(frozen=True)
class PatternDetection:
    """Result of pattern detection in telemetry data."""
    
    pattern: AttemptPattern
    detected: bool
    confidence: float  # 0.0 to 1.0
    evidence: Dict[str, float]  # Specific measurements that support detection
    
    def __post_init__(self):
        """Validate pattern detection values."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class PerformanceMetrics:
    """Performance metrics extracted from telemetry for evaluation."""
    
    # Speed metrics
    apex_speed_kmh: float
    exit_speed_kmh: float
    sector_time_ms: float
    
    # Slip indicators
    max_front_slip: float
    max_rear_slip: float
    slip_red_duration_ms: float
    
    # Stability metrics
    steering_smoothness: float  # Lower = smoother
    throttle_progression: float  # 0-1, higher = more progressive
    brake_consistency: float    # Lower = more consistent
    
    # Time deltas
    sector_delta_ms: float  # vs reference/personal best
    corner_delta_ms: float
    
    def __post_init__(self):
        """Validate performance metrics."""
        if self.apex_speed_kmh < 0 or self.exit_speed_kmh < 0:
            raise ValueError("Speeds must be non-negative")
        
        if not 0.0 <= self.throttle_progression <= 1.0:
            raise ValueError("Throttle progression must be between 0.0 and 1.0")


@dataclass(frozen=True)
class ReviewClassification:
    """Complete classification of a coaching review."""
    
    outcome: ReviewOutcome
    confidence: float
    
    # Pattern detection results
    pattern_detections: List[PatternDetection]
    primary_pattern: Optional[AttemptPattern]
    
    # Performance analysis
    performance_metrics: PerformanceMetrics
    performance_improvement: bool
    
    # Reasoning
    classification_reason: str
    recommendations: List[str]
    
    def __post_init__(self):
        """Validate classification values."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")


@dataclass
class PendingReview:
    """Tracking for a coaching action awaiting evaluation."""
    
    action_id: str
    corner_id: str
    action_pattern: AttemptPattern
    intensity_level: str
    
    # Timing
    coaching_timestamp: datetime
    target_lap_count: int = 3  # Number of laps to evaluate
    
    # Evaluation progress
    laps_evaluated: int = 0
    baseline_metrics: Optional[PerformanceMetrics] = None
    evaluation_metrics: List[PerformanceMetrics] = None
    
    # Status
    is_complete: bool = False
    final_classification: Optional[ReviewClassification] = None
    
    def __post_init__(self):
        """Initialize evaluation metrics list."""
        if self.evaluation_metrics is None:
            self.evaluation_metrics = []
    
    @property
    def needs_more_evaluation(self) -> bool:
        """Check if more evaluation laps are needed."""
        return not self.is_complete and self.laps_evaluated < self.target_lap_count
    
    @property
    def has_sufficient_data(self) -> bool:
        """Check if we have enough data for classification."""
        return (
            self.baseline_metrics is not None and
            len(self.evaluation_metrics) >= 2
        )
    
    def add_evaluation_lap(self, metrics: PerformanceMetrics) -> None:
        """Add metrics from an evaluation lap."""
        if not self.is_complete:
            self.evaluation_metrics.append(metrics)
            self.laps_evaluated += 1
    
    def complete_review(self, classification: ReviewClassification) -> None:
        """Mark review as complete with final classification."""
        self.final_classification = classification
        self.is_complete = True


@dataclass(frozen=True)
class IntensityAdjustment:
    """Recommended intensity adjustment based on review outcome."""
    
    current_intensity: str
    recommended_intensity: str
    adjustment_reason: str
    alternative_action: Optional[str] = None  # For theme switching
    
    @property
    def is_intensity_change(self) -> bool:
        """Check if this represents an intensity change."""
        return self.current_intensity != self.recommended_intensity
    
    @property
    def is_theme_switch(self) -> bool:
        """Check if this represents switching to a different action type."""
        return self.alternative_action is not None


@dataclass(frozen=True)
class ReviewerReaction:
    """Complete reaction to a review outcome."""
    
    outcome: ReviewOutcome
    intensity_adjustment: Optional[IntensityAdjustment]
    next_coaching_strategy: str
    
    # Timing
    apply_cooldown: bool
    cooldown_duration_minutes: int
    
    # Learning
    update_bandit: bool
    bandit_reward_ms: float
    
    reasoning: str