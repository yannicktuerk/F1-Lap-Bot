"""Safety gate resolver for enforcing slip/traction constraints."""
from typing import List, Dict
from ...domain.entities.corner_analysis import CoachingCandidate, ActionType
from ...domain.value_objects.slip_indicators import TurnPhase, AmpelColor, SafetyAmpel


class SafetyGateResolver:
    """Service for applying safety gates and filtering candidates based on slip/traction."""
    
    def apply_safety_constraints(
        self,
        candidates: List[CoachingCandidate],
        safety_ampels: Dict[TurnPhase, SafetyAmpel]
    ) -> List[CoachingCandidate]:
        """
        Apply safety constraints to filter candidates based on ampel colors.
        
        Args:
            candidates: List of coaching candidates to filter
            safety_ampels: Safety ampel status for each turn phase
            
        Returns:
            Filtered list of safe candidates
        """
        safe_candidates = []
        
        for candidate in candidates:
            ampel = safety_ampels.get(candidate.phase)
            if not ampel:
                # No ampel data available - allow candidate but mark as unverified
                candidate.safety_constraints.append("no_ampel_data_available")
                safe_candidates.append(candidate)
                continue
            
            # Apply specific safety rules
            if self._is_candidate_safe(candidate, ampel):
                safe_candidates.append(candidate)
            else:
                # Log why candidate was blocked
                print(f"🚫 Candidate blocked: {candidate.action_type.value} "
                      f"in {candidate.phase.value} due to {ampel.color.value} ampel")
        
        return safe_candidates
    
    def _is_candidate_safe(self, candidate: CoachingCandidate, ampel: SafetyAmpel) -> bool:
        """Check if a specific candidate is safe given the ampel color."""
        
        # RED ampel constraints
        if ampel.color == AmpelColor.RED:
            if candidate.phase == TurnPhase.ENTRY:
                # Entry red blocks "pressure faster"; only "brake earlier" allowed
                if candidate.action_type == ActionType.BUILD_PRESSURE_FASTER:
                    return False
            
            elif candidate.phase == TurnPhase.EXIT:
                # Exit red blocks early throttle; only steering reduction allowed
                if candidate.action_type == ActionType.THROTTLE_EARLIER_PROGRESSIVE:
                    return False
        
        # YELLOW ampel constraints  
        elif ampel.color == AmpelColor.YELLOW:
            # Yellow only allows soft/progressive variants
            from ...domain.entities.corner_analysis import ActionIntensity
            if candidate.intensity not in [
                ActionIntensity.SOFT, 
                ActionIntensity.PROGRESSIVE, 
                ActionIntensity.VERY_SOFT
            ]:
                return False
        
        # GREEN allows all (no additional constraints)
        return True
    
    def resolve_conflicts(
        self,
        candidates: List[CoachingCandidate],
        max_actions_per_corner: int = 1
    ) -> List[CoachingCandidate]:
        """
        Resolve conflicts to ensure max one action per corner with phase priority.
        
        Args:
            candidates: List of safe candidates to resolve conflicts for
            max_actions_per_corner: Maximum actions allowed per corner
            
        Returns:
            Conflict-resolved list of candidates
        """
        # Group candidates by corner
        corner_candidates = {}
        for candidate in candidates:
            if candidate.corner_id not in corner_candidates:
                corner_candidates[candidate.corner_id] = []
            corner_candidates[candidate.corner_id].append(candidate)
        
        resolved_candidates = []
        
        for corner_id, corner_candidate_list in corner_candidates.items():
            # Apply phase priority: Entry → Rotation → Exit
            selected = self._select_by_phase_priority(
                corner_candidate_list, max_actions_per_corner
            )
            resolved_candidates.extend(selected)
        
        return resolved_candidates
    
    def _select_by_phase_priority(
        self,
        candidates: List[CoachingCandidate],
        max_actions: int
    ) -> List[CoachingCandidate]:
        """Select candidates using phase priority rule."""
        
        # Define phase priority order
        phase_priority = [TurnPhase.ENTRY, TurnPhase.ROTATION, TurnPhase.EXIT]
        
        selected = []
        candidates_by_phase = {phase: [] for phase in phase_priority}
        
        # Group by phase
        for candidate in candidates:
            candidates_by_phase[candidate.phase].append(candidate)
        
        # Select best candidate from each phase in priority order
        for phase in phase_priority:
            if len(selected) >= max_actions:
                break
            
            phase_candidates = candidates_by_phase[phase]
            if phase_candidates:
                # Sort by priority score and take the best
                best_candidate = max(phase_candidates, key=lambda x: x.priority_score)
                selected.append(best_candidate)
        
        return selected
    
    def enforce_global_limits(
        self,
        candidates: List[CoachingCandidate],
        max_corners_per_lap: int = 3
    ) -> List[CoachingCandidate]:
        """
        Enforce global limits: max 3 corners per lap, max 1 action per corner.
        
        Args:
            candidates: List of candidates after conflict resolution
            max_corners_per_lap: Maximum corners to coach per lap
            
        Returns:
            Final list respecting all global limits
        """
        # Ensure no more than one action per corner (should already be resolved)
        corner_actions = {}
        for candidate in candidates:
            if candidate.corner_id not in corner_actions:
                corner_actions[candidate.corner_id] = candidate
            else:
                # Keep the higher priority candidate
                if candidate.priority_score > corner_actions[candidate.corner_id].priority_score:
                    corner_actions[candidate.corner_id] = candidate
        
        # Sort by priority and limit to max corners
        final_candidates = sorted(
            corner_actions.values(),
            key=lambda x: x.priority_score,
            reverse=True
        )
        
        return final_candidates[:max_corners_per_lap]
    
    def generate_safety_report(
        self,
        original_candidates: List[CoachingCandidate],
        safe_candidates: List[CoachingCandidate],
        safety_ampels: Dict[TurnPhase, SafetyAmpel]
    ) -> Dict[str, any]:
        """
        Generate a report on safety filtering results.
        
        Args:
            original_candidates: Original candidate list before safety filtering
            safe_candidates: Candidates after safety filtering
            safety_ampels: Safety ampel status used for filtering
            
        Returns:
            Dictionary containing safety filtering statistics
        """
        blocked_candidates = len(original_candidates) - len(safe_candidates)
        
        # Count candidates by ampel color
        ampel_distribution = {color.value: 0 for color in AmpelColor}
        for ampel in safety_ampels.values():
            ampel_distribution[ampel.color.value] += 1
        
        # Count blocked actions by type
        blocked_by_type = {}
        safe_action_types = {c.action_type for c in safe_candidates}
        original_action_types = {c.action_type for c in original_candidates}
        
        for action_type in original_action_types:
            if action_type not in safe_action_types:
                blocked_by_type[action_type.value] = blocked_by_type.get(action_type.value, 0) + 1
        
        return {
            'total_candidates_generated': len(original_candidates),
            'candidates_after_safety_filter': len(safe_candidates),
            'candidates_blocked': blocked_candidates,
            'block_rate': blocked_candidates / len(original_candidates) if original_candidates else 0,
            'ampel_distribution': ampel_distribution,
            'blocked_actions_by_type': blocked_by_type,
            'safety_ampel_summary': {
                phase.value: ampel.color.value 
                for phase, ampel in safety_ampels.items()
            }
        }
    
    def validate_final_selection(
        self,
        selected_candidates: List[CoachingCandidate]
    ) -> Dict[str, bool]:
        """
        Validate that final selection meets all requirements.
        
        Args:
            selected_candidates: Final selected candidates
            
        Returns:
            Dictionary of validation results
        """
        # Check max one action per corner
        corner_ids = [c.corner_id for c in selected_candidates]
        unique_corners = set(corner_ids)
        one_per_corner = len(corner_ids) == len(unique_corners)
        
        # Check max 3 corners total
        max_three_corners = len(selected_candidates) <= 3
        
        # Check phase priority is respected (no duplicates within corner)
        phase_conflicts = False
        corner_phases = {}
        for candidate in selected_candidates:
            if candidate.corner_id in corner_phases:
                phase_conflicts = True
                break
            corner_phases[candidate.corner_id] = candidate.phase
        
        return {
            'one_action_per_corner': one_per_corner,
            'max_three_corners': max_three_corners,
            'no_phase_conflicts': not phase_conflicts,
            'total_candidates': len(selected_candidates),
            'all_validations_passed': one_per_corner and max_three_corners and not phase_conflicts
        }