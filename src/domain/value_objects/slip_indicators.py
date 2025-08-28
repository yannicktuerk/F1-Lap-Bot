"""Value objects for slip indicators and safety ampels."""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class AmpelColor(Enum):
    """Safety ampel colors (traffic light system)."""
    GREEN = "green"
    YELLOW = "yellow" 
    RED = "red"


class TurnPhase(Enum):
    """Turn phases for slip analysis."""
    ENTRY = "entry"
    ROTATION = "rotation"
    EXIT = "exit"


@dataclass
class SlipMetrics:
    """Calculated slip metrics for safety analysis."""
    # Longitudinal slip ratio (positive = wheel spinning faster than vehicle)
    front_slip_ratio: float  # Average of front wheels
    rear_slip_ratio: float   # Average of rear wheels
    max_slip_ratio: float    # Maximum across all wheels
    
    # Lateral slip angle (steering vs actual direction)
    front_slip_angle: float  # Average of front wheels (radians)
    rear_slip_angle: float   # Average of rear wheels (radians)
    max_slip_angle: float    # Maximum absolute slip angle
    
    # Combined slip indicator (0.0 = perfect grip, 1.0 = maximum slip)
    combined_slip_factor: float
    
    @property
    def is_understeering(self) -> bool:
        """Check if vehicle is understeering (front slip > rear slip)."""
        return abs(self.front_slip_angle) > abs(self.rear_slip_angle)
    
    @property
    def is_oversteering(self) -> bool:
        """Check if vehicle is oversteering (rear slip > front slip)."""
        return abs(self.rear_slip_angle) > abs(self.front_slip_angle)


@dataclass
class SlipThresholds:
    """Configurable thresholds for ampel color mapping."""
    green_max: float = 0.6      # Green zone: 0.0 to green_max
    yellow_max: float = 0.85    # Yellow zone: green_max to yellow_max
    # Red zone: yellow_max to 1.0


@dataclass
class SafetyAmpel:
    """Safety ampel for a specific turn phase."""
    phase: TurnPhase
    color: AmpelColor
    slip_metrics: SlipMetrics
    confidence: float = 1.0  # Confidence in the assessment (0.0-1.0)
    
    @property
    def allows_aggressive_coaching(self) -> bool:
        """Check if ampel allows aggressive coaching suggestions."""
        return self.color == AmpelColor.GREEN
    
    @property
    def requires_caution(self) -> bool:
        """Check if ampel requires cautious coaching."""
        return self.color == AmpelColor.YELLOW
    
    @property
    def blocks_coaching(self) -> bool:
        """Check if ampel blocks coaching suggestions."""
        return self.color == AmpelColor.RED


@dataclass
class TurnSlipAnalysis:
    """Complete slip analysis for a turn."""
    entry_ampel: SafetyAmpel
    rotation_ampel: SafetyAmpel  
    exit_ampel: SafetyAmpel
    
    @property
    def safest_phase_for_coaching(self) -> TurnPhase:
        """Get the safest phase for coaching interventions."""
        phases = [
            (self.entry_ampel.phase, self.entry_ampel.color),
            (self.rotation_ampel.phase, self.rotation_ampel.color),
            (self.exit_ampel.phase, self.exit_ampel.color)
        ]
        
        # Priority: Green > Yellow > Red
        for phase, color in phases:
            if color == AmpelColor.GREEN:
                return phase
        
        for phase, color in phases:
            if color == AmpelColor.YELLOW:
                return phase
        
        # If all red, return entry as safest fallback
        return TurnPhase.ENTRY