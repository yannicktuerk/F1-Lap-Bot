"""Domain entities for corner analysis and coaching."""
from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum
from ..value_objects.slip_indicators import TurnPhase, AmpelColor


class ActionType(Enum):
    """Types of coaching actions."""
    # Entry actions
    BRAKE_EARLIER = "brake_earlier"
    BUILD_PRESSURE_FASTER = "build_pressure_faster"
    
    # Rotation actions
    RELEASE_EARLIER = "release_earlier"
    
    # Exit actions
    THROTTLE_EARLIER_PROGRESSIVE = "throttle_earlier_progressive"
    REDUCE_STEERING_THEN_GAS = "reduce_steering_then_gas"


class ActionIntensity(Enum):
    """Intensity levels for coaching actions."""
    SOFT = "soft"
    PROGRESSIVE = "progressive"
    FAST = "fast"
    VERY_FAST = "very_fast"
    VERY_SOFT = "very_soft"


@dataclass
class CornerImpact:
    """Impact analysis for a corner."""
    corner_id: int
    delta_ms: float  # Time delta vs reference
    normalized_impact: float  # IQR-normalized impact (0.0-1.0+)
    consistency_score: float  # Consistency vs reference (lower = more consistent)
    sample_count: int
    reference_median_ms: float
    reference_iqr_ms: float
    
    @property
    def needs_consistency_drill(self) -> bool:
        """Check if corner needs consistency work before pace improvement."""
        # If inconsistency is high (consistency_score > 2.0), prioritize consistency
        return self.consistency_score > 2.0
    
    @property
    def improvement_potential(self) -> float:
        """Get improvement potential (higher = more potential)."""
        return self.normalized_impact


@dataclass
class CoachingCandidate:
    """A candidate coaching action for a corner."""
    corner_id: int
    phase: TurnPhase
    action_type: ActionType
    intensity: ActionIntensity
    expected_gain_ms: float  # Expected time improvement
    confidence: float  # Confidence in the recommendation (0.0-1.0)
    safety_constraints: List[str]  # Any safety constraints applied
    priority_score: float  # Priority for selection (higher = more priority)
    
    @property
    def is_safe_for_ampel(self, ampel_color: AmpelColor) -> bool:
        """Check if this candidate is safe for the given ampel color."""
        if ampel_color == AmpelColor.RED:
            # Red blocks aggressive actions
            if self.action_type in [ActionType.BUILD_PRESSURE_FASTER, ActionType.THROTTLE_EARLIER_PROGRESSIVE]:
                return False
            if self.intensity in [ActionIntensity.FAST, ActionIntensity.VERY_FAST]:
                return False
        elif ampel_color == AmpelColor.YELLOW:
            # Yellow only allows soft/progressive variants
            return self.intensity in [ActionIntensity.SOFT, ActionIntensity.PROGRESSIVE, ActionIntensity.VERY_SOFT]
        
        return True  # Green allows all


@dataclass
class SelectedAction:
    """A selected coaching action for execution."""
    corner_id: int
    phase: TurnPhase
    action_type: ActionType
    intensity: ActionIntensity
    expected_gain_ms: float
    confidence: float
    safety_ampel_color: AmpelColor
    generated_at: datetime
    user_text: str  # Human-readable coaching text
    focus_hint: Optional[str] = None  # Optional focus reminder
    
    @property
    def coaching_message(self) -> str:
        """Get the complete coaching message."""
        message = self.user_text
        if self.focus_hint:
            message += f" {self.focus_hint}"
        return message


@dataclass
class ActionResult:
    """Result of an executed coaching action."""
    action_id: str
    corner_id: int
    attempt_detected: bool  # Was an attempt at the action detected?
    success: bool  # Was the action successful?
    overtrained: bool  # Was the action overdone (causing issues)?
    actual_gain_ms: Optional[float]  # Actual time change measured
    slip_violations: List[str]  # Any slip/safety violations detected
    evaluation_laps: int  # Number of laps used for evaluation
    evaluation_completed_at: datetime
    
    @property
    def coaching_feedback(self) -> str:
        """Get feedback message for the result."""
        if not self.attempt_detected:
            return "No attempt detected - focus on the suggested technique."
        elif self.overtrained:
            return "Good attempt, but ease off slightly to maintain control."
        elif self.success:
            return "Excellent improvement! Keep it up."
        else:
            return "Good attempt - let's try a different approach."


@dataclass
class CornerAnalysisSession:
    """Complete analysis session for corner ranking and coaching."""
    session_uid: int
    track_id: int
    corner_impacts: List[CornerImpact]
    selected_corners: List[int]  # Up to 3 corners selected for coaching
    generated_candidates: List[CoachingCandidate]
    selected_actions: List[SelectedAction]  # Up to 3 actions (1 per corner)
    analysis_timestamp: datetime
    assists_config: str
    device_config: str
    
    @property
    def top_improvement_opportunities(self) -> List[CornerImpact]:
        """Get the top corners by improvement potential."""
        return sorted(
            [impact for impact in self.corner_impacts if not impact.needs_consistency_drill],
            key=lambda x: x.improvement_potential,
            reverse=True
        )[:3]
    
    @property
    def consistency_drill_needed(self) -> List[CornerImpact]:
        """Get corners that need consistency work first."""
        return [impact for impact in self.corner_impacts if impact.needs_consistency_drill]