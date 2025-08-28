"""Value objects for utility estimation and coaching effectiveness."""
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence levels for utility estimates."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class ActionUtility:
    """Value object representing expected utility (time gain) of a coaching action."""
    
    expected_gain_ms: float
    confidence_interval_ms: float
    confidence_level: ConfidenceLevel
    source: str  # "ml" or "heuristic"
    
    def __post_init__(self):
        """Validate utility values."""
        if self.confidence_interval_ms < 0:
            raise ValueError("Confidence interval must be non-negative")
        
        if self.confidence_level == ConfidenceLevel.HIGH and self.confidence_interval_ms > 50:
            raise ValueError("High confidence requires tight interval (≤50ms)")
        
        if self.confidence_level == ConfidenceLevel.LOW and self.confidence_interval_ms < 100:
            raise ValueError("Low confidence requires wide interval (≥100ms)")
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if this is a high confidence estimate."""
        return self.confidence_level == ConfidenceLevel.HIGH
    
    @property
    def lower_bound_ms(self) -> float:
        """Get lower bound of expected gain."""
        return self.expected_gain_ms - self.confidence_interval_ms
    
    @property
    def upper_bound_ms(self) -> float:
        """Get upper bound of expected gain."""
        return self.expected_gain_ms + self.confidence_interval_ms


@dataclass(frozen=True)
class UtilityFeatures:
    """Feature set for utility estimation model."""
    
    # Corner characteristics
    corner_type: str  # "slow", "medium", "fast", "chicane"
    corner_id: int
    
    # Speed features
    entry_speed_kmh: float
    min_speed_kmh: float 
    exit_speed_kmh: float
    
    # Performance deltas
    entry_delta_ms: float  # vs reference
    rotation_delta_ms: float
    exit_delta_ms: float
    
    # Slip conditions
    entry_slip_ratio: float
    exit_slip_ratio: float
    slip_band: str  # "green", "yellow", "red"
    
    # Action characteristics
    candidate_type: str  # "brake_earlier", "pressure_faster", etc.
    phase: str  # "entry", "rotation", "exit"
    intensity: str  # "light", "medium", "aggressive"
    
    # Configuration
    assists_config: str
    device_config: str  # "wheel", "controller"
    
    def to_feature_vector(self) -> list:
        """Convert to numerical feature vector for ML model."""
        # Categorical encoding maps
        corner_type_map = {"slow": 0, "medium": 1, "fast": 2, "chicane": 3}
        slip_band_map = {"green": 0, "yellow": 1, "red": 2}
        candidate_type_map = {
            "brake_earlier": 0, "pressure_faster": 1, "release_earlier": 2,
            "throttle_earlier": 3, "reduce_steering": 4
        }
        phase_map = {"entry": 0, "rotation": 1, "exit": 2}
        intensity_map = {"light": 0, "medium": 1, "aggressive": 2}
        device_map = {"wheel": 0, "controller": 1}
        
        return [
            # Corner characteristics (encoded)
            corner_type_map.get(self.corner_type, 1),  # default to medium
            self.corner_id,
            
            # Speed features
            self.entry_speed_kmh,
            self.min_speed_kmh,
            self.exit_speed_kmh,
            
            # Performance deltas
            self.entry_delta_ms,
            self.rotation_delta_ms,
            self.exit_delta_ms,
            
            # Slip conditions
            self.entry_slip_ratio,
            self.exit_slip_ratio,
            slip_band_map.get(self.slip_band, 1),
            
            # Action characteristics (encoded)
            candidate_type_map.get(self.candidate_type, 0),
            phase_map.get(self.phase, 0),
            intensity_map.get(self.intensity, 1),
            
            # Configuration (encoded)
            1 if "advanced" in self.assists_config else 0,  # assists flag
            device_map.get(self.device_config, 0)
        ]


@dataclass(frozen=True)
class UtilityEvaluation:
    """Evaluation result for a completed coaching action."""
    
    action_id: str
    realized_gain_ms: float
    evaluation_confidence: ConfidenceLevel
    evaluation_source: str  # "telemetry", "split_comparison", "manual"
    
    # Context for evaluation
    follow_up_laps: int
    track_conditions: str  # "similar", "changed"
    driver_consistency: float  # std dev of recent lap times
    
    def is_valid_evaluation(self) -> bool:
        """Check if this evaluation is reliable for learning."""
        return (
            self.follow_up_laps >= 2 and
            self.track_conditions == "similar" and
            self.evaluation_confidence != ConfidenceLevel.LOW
        )