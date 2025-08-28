"""Application service for safety ampel (traffic light) system."""
import logging
from typing import Dict, Optional

from src.domain.value_objects.slip_indicators import (
    SlipMetrics, 
    SlipThresholds,
    SafetyAmpel, 
    AmpelColor, 
    TurnPhase,
    TurnSlipAnalysis
)
from src.domain.entities.telemetry_sample import PlayerTelemetrySample
from src.domain.services.slip_calculator import SlipCalculator


class SafetyAmpelService:
    """
    Application service for mapping slip metrics to safety ampel colors.
    
    This service implements the safety gates described in the coaching spec:
    - Entry-Slip red blocks "pressure faster" coaching
    - Exit-Slip red blocks early throttle coaching  
    - Yellow restricts to safe/progressive formulations
    """
    
    def __init__(
        self,
        slip_calculator: Optional[SlipCalculator] = None,
        entry_thresholds: Optional[SlipThresholds] = None,
        exit_thresholds: Optional[SlipThresholds] = None
    ):
        self.slip_calculator = slip_calculator or SlipCalculator()
        self.logger = logging.getLogger(__name__)
        
        # Configurable thresholds for different turn phases
        self.entry_thresholds = entry_thresholds or SlipThresholds(
            green_max=0.6,
            yellow_max=0.85
        )
        self.exit_thresholds = exit_thresholds or SlipThresholds(
            green_max=0.6, 
            yellow_max=0.85
        )
        
        # Rotation uses same as entry by default
        self.rotation_thresholds = self.entry_thresholds
        
        # Metrics tracking
        self._ampel_counts: Dict[str, int] = {
            "entry_green": 0, "entry_yellow": 0, "entry_red": 0,
            "rotation_green": 0, "rotation_yellow": 0, "rotation_red": 0,
            "exit_green": 0, "exit_yellow": 0, "exit_red": 0
        }
    
    def analyze_safety_ampels(self, telemetry_sample: PlayerTelemetrySample) -> Optional[TurnSlipAnalysis]:
        """
        Analyze telemetry sample and return safety ampels for all turn phases.
        
        Args:
            telemetry_sample: Complete telemetry sample with slip data
            
        Returns:
            TurnSlipAnalysis: Safety ampels for entry, rotation, exit phases
            None if insufficient data for analysis
        """
        try:
            # Require motion ex data for slip analysis
            if not telemetry_sample.has_slip_data:
                self.logger.debug("No slip data available for safety analysis")
                return None
            
            # Calculate slip metrics
            slip_metrics = self.slip_calculator.calculate_slip_metrics(
                telemetry_sample.motion_ex_info,
                telemetry_sample.car_telemetry
            )
            
            # Generate ampels for each turn phase
            entry_ampel = self._generate_phase_ampel(
                TurnPhase.ENTRY, slip_metrics, self.entry_thresholds
            )
            
            rotation_ampel = self._generate_phase_ampel(
                TurnPhase.ROTATION, slip_metrics, self.rotation_thresholds
            )
            
            exit_ampel = self._generate_phase_ampel(
                TurnPhase.EXIT, slip_metrics, self.exit_thresholds
            )
            
            # Update metrics
            self._update_ampel_metrics(entry_ampel, rotation_ampel, exit_ampel)
            
            return TurnSlipAnalysis(
                entry_ampel=entry_ampel,
                rotation_ampel=rotation_ampel,
                exit_ampel=exit_ampel
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing safety ampels: {e}")
            return None
    
    def _generate_phase_ampel(
        self, 
        phase: TurnPhase, 
        slip_metrics: SlipMetrics,
        thresholds: SlipThresholds
    ) -> SafetyAmpel:
        """
        Generate safety ampel for a specific turn phase.
        
        Args:
            phase: Turn phase being analyzed
            slip_metrics: Calculated slip metrics
            thresholds: Threshold configuration for this phase
            
        Returns:
            SafetyAmpel: Generated safety ampel
        """
        # Use combined slip factor as primary indicator
        slip_factor = slip_metrics.combined_slip_factor
        
        # Apply phase-specific logic
        if phase == TurnPhase.ENTRY:
            # Entry phase: focus on front slip for braking/turn-in
            slip_factor = max(slip_factor, abs(slip_metrics.front_slip_angle) / 0.2)
        elif phase == TurnPhase.EXIT:
            # Exit phase: focus on rear slip for traction
            slip_factor = max(slip_factor, abs(slip_metrics.rear_slip_ratio) / 0.3)
        # Rotation uses combined factor as-is
        
        # Map to ampel color
        if slip_factor <= thresholds.green_max:
            color = AmpelColor.GREEN
        elif slip_factor <= thresholds.yellow_max:
            color = AmpelColor.YELLOW
        else:
            color = AmpelColor.RED
        
        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(slip_metrics, phase)
        
        return SafetyAmpel(
            phase=phase,
            color=color,
            slip_metrics=slip_metrics,
            confidence=confidence
        )
    
    def _calculate_confidence(self, slip_metrics: SlipMetrics, phase: TurnPhase) -> float:
        """
        Calculate confidence in the ampel assessment.
        
        Args:
            slip_metrics: Slip metrics used for assessment
            phase: Turn phase being assessed
            
        Returns:
            float: Confidence level (0.0-1.0)
        """
        # Base confidence
        confidence = 1.0
        
        # Reduce confidence for extreme values that might be sensor noise
        if slip_metrics.max_slip_ratio > 1.0:
            confidence *= 0.8
        
        if slip_metrics.max_slip_angle > 0.5:  # ~28 degrees
            confidence *= 0.8
        
        # Reduce confidence for very low speeds where slip calculations are less reliable
        if slip_metrics.combined_slip_factor < 0.05:
            confidence *= 0.9
        
        return max(0.1, confidence)  # Minimum 10% confidence
    
    def _update_ampel_metrics(
        self, 
        entry_ampel: SafetyAmpel,
        rotation_ampel: SafetyAmpel, 
        exit_ampel: SafetyAmpel
    ) -> None:
        """Update internal metrics tracking."""
        # Entry metrics
        if entry_ampel.color == AmpelColor.GREEN:
            self._ampel_counts["entry_green"] += 1
        elif entry_ampel.color == AmpelColor.YELLOW:
            self._ampel_counts["entry_yellow"] += 1
        else:
            self._ampel_counts["entry_red"] += 1
        
        # Rotation metrics
        if rotation_ampel.color == AmpelColor.GREEN:
            self._ampel_counts["rotation_green"] += 1
        elif rotation_ampel.color == AmpelColor.YELLOW:
            self._ampel_counts["rotation_yellow"] += 1
        else:
            self._ampel_counts["rotation_red"] += 1
        
        # Exit metrics
        if exit_ampel.color == AmpelColor.GREEN:
            self._ampel_counts["exit_green"] += 1
        elif exit_ampel.color == AmpelColor.YELLOW:
            self._ampel_counts["exit_yellow"] += 1
        else:
            self._ampel_counts["exit_red"] += 1
    
    def get_coaching_constraints(self, turn_analysis: TurnSlipAnalysis) -> Dict[str, bool]:
        """
        Get coaching constraints based on safety ampel analysis.
        
        Implements the safety rules from the coaching specification:
        - Entry-Slip red blocks "pressure faster" coaching
        - Exit-Slip red blocks early throttle coaching
        - Yellow restricts to progressive formulations
        
        Args:
            turn_analysis: Complete turn slip analysis
            
        Returns:
            Dict[str, bool]: Coaching constraints
        """
        constraints = {
            # Entry coaching constraints
            "can_coach_brake_earlier": True,  # Always allowed
            "can_coach_pressure_faster": turn_analysis.entry_ampel.color != AmpelColor.RED,
            "require_progressive_braking": turn_analysis.entry_ampel.color == AmpelColor.YELLOW,
            
            # Rotation coaching constraints  
            "can_coach_release_earlier": turn_analysis.rotation_ampel.color != AmpelColor.RED,
            "require_smooth_rotation": turn_analysis.rotation_ampel.color == AmpelColor.YELLOW,
            
            # Exit coaching constraints
            "can_coach_early_throttle": turn_analysis.exit_ampel.color != AmpelColor.RED,
            "require_progressive_throttle": turn_analysis.exit_ampel.color == AmpelColor.YELLOW,
            "require_steering_reduction": turn_analysis.exit_ampel.color == AmpelColor.RED
        }
        
        return constraints
    
    def log_metrics(self) -> None:
        """Log safety ampel metrics for observability."""
        total_samples = sum(self._ampel_counts.values())
        
        if total_samples == 0:
            self.logger.info("No safety ampel samples processed")
            return
        
        self.logger.info("=== Safety Ampel Metrics ===")
        
        # Entry phase
        entry_total = sum([
            self._ampel_counts["entry_green"],
            self._ampel_counts["entry_yellow"], 
            self._ampel_counts["entry_red"]
        ])
        if entry_total > 0:
            entry_green_pct = (self._ampel_counts["entry_green"] / entry_total) * 100
            entry_yellow_pct = (self._ampel_counts["entry_yellow"] / entry_total) * 100
            entry_red_pct = (self._ampel_counts["entry_red"] / entry_total) * 100
            self.logger.info(f"Entry Ampels: {entry_green_pct:.1f}% Green, {entry_yellow_pct:.1f}% Yellow, {entry_red_pct:.1f}% Red")
        
        # Exit phase  
        exit_total = sum([
            self._ampel_counts["exit_green"],
            self._ampel_counts["exit_yellow"],
            self._ampel_counts["exit_red"]
        ])
        if exit_total > 0:
            exit_green_pct = (self._ampel_counts["exit_green"] / exit_total) * 100
            exit_yellow_pct = (self._ampel_counts["exit_yellow"] / exit_total) * 100
            exit_red_pct = (self._ampel_counts["exit_red"] / exit_total) * 100
            self.logger.info(f"Exit Ampels: {exit_green_pct:.1f}% Green, {exit_yellow_pct:.1f}% Yellow, {exit_red_pct:.1f}% Red")
        
        self.logger.info(f"Total safety assessments: {total_samples}")
    
    def reset_metrics(self) -> None:
        """Reset all metrics counters."""
        for key in self._ampel_counts:
            self._ampel_counts[key] = 0
        self.logger.info("Safety ampel metrics reset")