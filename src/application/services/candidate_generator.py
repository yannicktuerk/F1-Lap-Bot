"""Candidate generation service for coaching actions."""
from typing import List, Dict, Optional
from ...domain.entities.corner_analysis import (
    CoachingCandidate, ActionType, ActionIntensity, CornerImpact
)
from ...domain.value_objects.slip_indicators import TurnPhase, AmpelColor, SafetyAmpel
from ...domain.services.statistics_service import StatisticsService


class CandidateGenerator:
    """Service for generating coaching action candidates per corner."""
    
    def __init__(self, statistics_service: StatisticsService):
        self.statistics_service = statistics_service
    
    def generate_candidates_for_corner(
        self,
        corner_impact: CornerImpact,
        safety_ampels: Dict[TurnPhase, SafetyAmpel],
        max_candidates_per_phase: int = 1
    ) -> List[CoachingCandidate]:
        """
        Generate up to 3 coaching candidates for a corner (Entry → Rotation → Exit).
        
        Args:
            corner_impact: Impact analysis for the corner
            safety_ampels: Safety ampel status for each turn phase
            max_candidates_per_phase: Maximum candidates per phase
            
        Returns:
            List of coaching candidates (max 3)
        """
        candidates = []
        
        # Check if consistency drill is needed first
        if corner_impact.needs_consistency_drill:
            return self._generate_consistency_candidates(corner_impact, safety_ampels)
        
        # Generate Entry phase candidates
        entry_candidates = self._generate_entry_candidates(
            corner_impact, safety_ampels.get(TurnPhase.ENTRY)
        )
        candidates.extend(entry_candidates[:max_candidates_per_phase])
        
        # Generate Rotation phase candidates
        rotation_candidates = self._generate_rotation_candidates(
            corner_impact, safety_ampels.get(TurnPhase.ROTATION)
        )
        candidates.extend(rotation_candidates[:max_candidates_per_phase])
        
        # Generate Exit phase candidates
        exit_candidates = self._generate_exit_candidates(
            corner_impact, safety_ampels.get(TurnPhase.EXIT)
        )
        candidates.extend(exit_candidates[:max_candidates_per_phase])
        
        # Sort by priority and return max 3
        candidates.sort(key=lambda x: x.priority_score, reverse=True)
        return candidates[:3]
    
    def _generate_entry_candidates(
        self,
        corner_impact: CornerImpact,
        entry_ampel: Optional[SafetyAmpel]
    ) -> List[CoachingCandidate]:
        """Generate entry phase coaching candidates."""
        candidates = []
        ampel_color = entry_ampel.color if entry_ampel else AmpelColor.GREEN
        
        # Base expected gain from entry improvements
        base_gain = self.statistics_service.calculate_expected_improvement(
            corner_impact.delta_ms, 0.0, action_difficulty=0.4
        )
        
        if ampel_color == AmpelColor.RED:
            # Red: Only "brake earlier" allowed, no pressure building
            candidates.append(CoachingCandidate(
                corner_id=corner_impact.corner_id,
                phase=TurnPhase.ENTRY,
                action_type=ActionType.BRAKE_EARLIER,
                intensity=ActionIntensity.PROGRESSIVE,
                expected_gain_ms=base_gain * 0.6,
                confidence=0.8,
                safety_constraints=["entry_slip_red_blocks_pressure_faster"],
                priority_score=self._calculate_priority_score(
                    corner_impact.improvement_potential, 0.8, ampel_color
                )
            ))
        
        elif ampel_color == AmpelColor.YELLOW:
            # Yellow: Soft/progressive variants only
            candidates.extend([
                CoachingCandidate(
                    corner_id=corner_impact.corner_id,
                    phase=TurnPhase.ENTRY,
                    action_type=ActionType.BRAKE_EARLIER,
                    intensity=ActionIntensity.PROGRESSIVE,
                    expected_gain_ms=base_gain * 0.7,
                    confidence=0.85,
                    safety_constraints=["yellow_ampel_progressive_only"],
                    priority_score=self._calculate_priority_score(
                        corner_impact.improvement_potential, 0.85, ampel_color
                    )
                ),
                CoachingCandidate(
                    corner_id=corner_impact.corner_id,
                    phase=TurnPhase.ENTRY,
                    action_type=ActionType.BUILD_PRESSURE_FASTER,
                    intensity=ActionIntensity.SOFT,
                    expected_gain_ms=base_gain * 0.5,
                    confidence=0.7,
                    safety_constraints=["yellow_ampel_soft_only"],
                    priority_score=self._calculate_priority_score(
                        corner_impact.improvement_potential, 0.7, ampel_color
                    )
                )
            ])
        
        else:  # GREEN
            # Green: All entry actions allowed
            candidates.extend([
                CoachingCandidate(
                    corner_id=corner_impact.corner_id,
                    phase=TurnPhase.ENTRY,
                    action_type=ActionType.BRAKE_EARLIER,
                    intensity=ActionIntensity.PROGRESSIVE,
                    expected_gain_ms=base_gain * 0.8,
                    confidence=0.9,
                    safety_constraints=[],
                    priority_score=self._calculate_priority_score(
                        corner_impact.improvement_potential, 0.9, ampel_color
                    )
                ),
                CoachingCandidate(
                    corner_id=corner_impact.corner_id,
                    phase=TurnPhase.ENTRY,
                    action_type=ActionType.BUILD_PRESSURE_FASTER,
                    intensity=ActionIntensity.FAST,
                    expected_gain_ms=base_gain * 0.9,
                    confidence=0.8,
                    safety_constraints=[],
                    priority_score=self._calculate_priority_score(
                        corner_impact.improvement_potential, 0.8, ampel_color
                    )
                )
            ])
        
        return candidates
    
    def _generate_rotation_candidates(
        self,
        corner_impact: CornerImpact,
        rotation_ampel: Optional[SafetyAmpel]
    ) -> List[CoachingCandidate]:
        """Generate rotation phase coaching candidates."""
        candidates = []
        ampel_color = rotation_ampel.color if rotation_ampel else AmpelColor.GREEN
        
        base_gain = self.statistics_service.calculate_expected_improvement(
            corner_impact.delta_ms, 0.0, action_difficulty=0.5
        )
        
        # Rotation phase primarily uses "release earlier"
        intensity = ActionIntensity.PROGRESSIVE
        confidence = 0.85
        constraints = []
        
        if ampel_color == AmpelColor.YELLOW:
            intensity = ActionIntensity.SOFT
            confidence = 0.75
            constraints = ["yellow_ampel_soft_release"]
        elif ampel_color == AmpelColor.RED:
            intensity = ActionIntensity.VERY_SOFT
            confidence = 0.6
            constraints = ["red_ampel_very_soft_release"]
        
        candidates.append(CoachingCandidate(
            corner_id=corner_impact.corner_id,
            phase=TurnPhase.ROTATION,
            action_type=ActionType.RELEASE_EARLIER,
            intensity=intensity,
            expected_gain_ms=base_gain * 0.7,
            confidence=confidence,
            safety_constraints=constraints,
            priority_score=self._calculate_priority_score(
                corner_impact.improvement_potential, confidence, ampel_color
            )
        ))
        
        return candidates
    
    def _generate_exit_candidates(
        self,
        corner_impact: CornerImpact,
        exit_ampel: Optional[SafetyAmpel]
    ) -> List[CoachingCandidate]:
        """Generate exit phase coaching candidates."""
        candidates = []
        ampel_color = exit_ampel.color if exit_ampel else AmpelColor.GREEN
        
        base_gain = self.statistics_service.calculate_expected_improvement(
            corner_impact.delta_ms, 0.0, action_difficulty=0.6
        )
        
        if ampel_color == AmpelColor.RED:
            # Red: Never early throttle; only steering reduction
            candidates.append(CoachingCandidate(
                corner_id=corner_impact.corner_id,
                phase=TurnPhase.EXIT,
                action_type=ActionType.REDUCE_STEERING_THEN_GAS,
                intensity=ActionIntensity.PROGRESSIVE,
                expected_gain_ms=base_gain * 0.5,
                confidence=0.8,
                safety_constraints=["exit_slip_red_blocks_early_throttle"],
                priority_score=self._calculate_priority_score(
                    corner_impact.improvement_potential, 0.8, ampel_color
                )
            ))
        
        elif ampel_color == AmpelColor.YELLOW:
            # Yellow: Only soft/progressive throttle variants
            candidates.extend([
                CoachingCandidate(
                    corner_id=corner_impact.corner_id,
                    phase=TurnPhase.EXIT,
                    action_type=ActionType.THROTTLE_EARLIER_PROGRESSIVE,
                    intensity=ActionIntensity.VERY_SOFT,
                    expected_gain_ms=base_gain * 0.6,
                    confidence=0.7,
                    safety_constraints=["yellow_ampel_very_soft_throttle"],
                    priority_score=self._calculate_priority_score(
                        corner_impact.improvement_potential, 0.7, ampel_color
                    )
                ),
                CoachingCandidate(
                    corner_id=corner_impact.corner_id,
                    phase=TurnPhase.EXIT,
                    action_type=ActionType.REDUCE_STEERING_THEN_GAS,
                    intensity=ActionIntensity.SOFT,
                    expected_gain_ms=base_gain * 0.5,
                    confidence=0.75,
                    safety_constraints=["yellow_ampel_soft_steering"],
                    priority_score=self._calculate_priority_score(
                        corner_impact.improvement_potential, 0.75, ampel_color
                    )
                )
            ])
        
        else:  # GREEN
            # Green: All exit actions allowed
            candidates.extend([
                CoachingCandidate(
                    corner_id=corner_impact.corner_id,
                    phase=TurnPhase.EXIT,
                    action_type=ActionType.THROTTLE_EARLIER_PROGRESSIVE,
                    intensity=ActionIntensity.PROGRESSIVE,
                    expected_gain_ms=base_gain * 0.8,
                    confidence=0.85,
                    safety_constraints=[],
                    priority_score=self._calculate_priority_score(
                        corner_impact.improvement_potential, 0.85, ampel_color
                    )
                ),
                CoachingCandidate(
                    corner_id=corner_impact.corner_id,
                    phase=TurnPhase.EXIT,
                    action_type=ActionType.REDUCE_STEERING_THEN_GAS,
                    intensity=ActionIntensity.PROGRESSIVE,
                    expected_gain_ms=base_gain * 0.6,
                    confidence=0.8,
                    safety_constraints=[],
                    priority_score=self._calculate_priority_score(
                        corner_impact.improvement_potential, 0.8, ampel_color
                    )
                )
            ])
        
        return candidates
    
    def _generate_consistency_candidates(
        self,
        corner_impact: CornerImpact,
        safety_ampels: Dict[TurnPhase, SafetyAmpel]
    ) -> List[CoachingCandidate]:
        """Generate consistency-focused candidates when consistency drill is needed."""
        # For consistency issues, focus on the safest, most fundamental techniques
        candidates = []
        
        # Consistency drill: brake earlier with very soft intensity
        candidates.append(CoachingCandidate(
            corner_id=corner_impact.corner_id,
            phase=TurnPhase.ENTRY,
            action_type=ActionType.BRAKE_EARLIER,
            intensity=ActionIntensity.VERY_SOFT,
            expected_gain_ms=0.0,  # Focus on consistency, not pace
            confidence=0.9,
            safety_constraints=["consistency_drill_prioritized"],
            priority_score=1.0  # High priority for consistency
        ))
        
        return candidates
    
    def _calculate_priority_score(
        self,
        improvement_potential: float,
        confidence: float,
        ampel_color: AmpelColor
    ) -> float:
        """Calculate priority score for candidate selection."""
        base_score = improvement_potential * confidence
        
        # Adjust for safety ampel
        if ampel_color == AmpelColor.GREEN:
            safety_multiplier = 1.0
        elif ampel_color == AmpelColor.YELLOW:
            safety_multiplier = 0.8
        else:  # RED
            safety_multiplier = 0.6
        
        return base_score * safety_multiplier
    
    def validate_candidate_safety(
        self,
        candidate: CoachingCandidate,
        ampel_color: AmpelColor
    ) -> bool:
        """Validate that a candidate is safe for the given ampel color."""
        return candidate.is_safe_for_ampel(ampel_color)