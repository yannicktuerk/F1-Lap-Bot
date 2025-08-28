"""Use case for complete corner analysis and coaching pipeline (Issues 05-06)."""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from ...domain.entities.corner_analysis import (
    CornerAnalysisSession, CornerImpact, CoachingCandidate, SelectedAction
)
from ...domain.entities.telemetry_sample import PlayerTelemetrySample
from ...domain.interfaces.corner_reference_repository import CornerReferenceRepository, CornerReference
from ...domain.interfaces.coaching_repository import CoachingRepository
from ...domain.services.corner_ranker import CornerRanker
from ...domain.services.statistics_service import StatisticsService
from ...application.services.candidate_generator import CandidateGenerator
from ...application.services.safety_gate_resolver import SafetyGateResolver
from ...application.services.action_selector import ActionSelector
from ...application.services.safety_ampel_service import SafetyAmpelService
from ...domain.value_objects.slip_indicators import TurnPhase, SafetyAmpel


class ProcessCornerAnalysisAndCoaching:
    """
    Use case orchestrating the complete corner analysis and coaching pipeline.
    
    Implements Issues 05 (Turn Ranking) and 06 (Candidates Safety Conflict).
    """
    
    def __init__(
        self,
        corner_reference_repository: CornerReferenceRepository,
        coaching_repository: CoachingRepository,
        corner_ranker: CornerRanker,
        statistics_service: StatisticsService,
        candidate_generator: CandidateGenerator,
        safety_gate_resolver: SafetyGateResolver,
        action_selector: ActionSelector,
        safety_ampel_service: SafetyAmpelService
    ):
        self.corner_reference_repository = corner_reference_repository
        self.coaching_repository = coaching_repository
        self.corner_ranker = corner_ranker
        self.statistics_service = statistics_service
        self.candidate_generator = candidate_generator
        self.safety_gate_resolver = safety_gate_resolver
        self.action_selector = action_selector
        self.safety_ampel_service = safety_ampel_service
    
    async def execute(
        self,
        session_uid: int,
        track_id: int,
        driver_corner_data: Dict[int, List[float]],  # corner_id -> list of times
        current_telemetry: List[PlayerTelemetrySample],
        assists_config: str,
        device_config: str
    ) -> CornerAnalysisSession:
        """
        Execute the complete corner analysis and coaching pipeline.
        
        Args:
            session_uid: Session unique identifier
            track_id: Track identifier
            driver_corner_data: Driver's corner times for analysis
            current_telemetry: Current session telemetry for slip analysis
            assists_config: Assists configuration hash for filtering
            device_config: Input device configuration for filtering
            
        Returns:
            Complete corner analysis session with selected actions
        """
        print(f"🎯 Starting corner analysis and coaching for session {session_uid}")
        
        # Step 1: Load corner references for this track (Issue 05)
        track_name = self._get_track_name_from_id(track_id)
        corner_references = await self.corner_reference_repository.find_all_by_track(
            track_name, assists_config, device_config
        )
        
        if not corner_references:
            print(f"⚠️ No corner references found for track {track_id}")
            return self._create_empty_session(session_uid, track_id, assists_config, device_config)
        
        print(f"📊 Found {len(corner_references)} corner references")
        
        # Step 2: Rank corners by impact (Issue 05)
        corner_impacts = self.corner_ranker.rank_corners_by_impact(
            driver_corner_data, corner_references, max_corners=5
        )
        
        if not corner_impacts:
            print("ℹ️ No corners identified for improvement")
            return self._create_empty_session(session_uid, track_id, assists_config, device_config)
        
        print(f"🏁 Ranked {len(corner_impacts)} corners by impact")
        
        # Step 3: Select corners for coaching (prioritize consistency if needed)
        selected_corner_ids = self.corner_ranker.select_coaching_corners(
            corner_impacts, max_corners=3, prioritize_consistency=True
        )
        
        print(f"🎯 Selected {len(selected_corner_ids)} corners for coaching: {selected_corner_ids}")
        
        # Step 4: Generate safety ampels for selected corners
        safety_ampels = await self._generate_safety_ampels_for_corners(
            selected_corner_ids, current_telemetry
        )
        
        # Step 5: Generate candidates for each selected corner (Issue 06)
        all_candidates = []
        for corner_impact in corner_impacts:
            if corner_impact.corner_id in selected_corner_ids:
                corner_ampels = {
                    phase: ampel for phase, ampel in safety_ampels.items()
                    if self._is_ampel_for_corner(ampel, corner_impact.corner_id)
                }
                
                candidates = self.candidate_generator.generate_candidates_for_corner(
                    corner_impact, corner_ampels
                )
                all_candidates.extend(candidates)
        
        print(f"💡 Generated {len(all_candidates)} coaching candidates")
        
        # Step 6: Apply safety constraints (Issue 06)
        safe_candidates = self.safety_gate_resolver.apply_safety_constraints(
            all_candidates, safety_ampels
        )
        
        print(f"🚦 {len(safe_candidates)} candidates passed safety gates")
        
        # Step 7: Resolve conflicts (max one action per corner)
        conflict_resolved_candidates = self.safety_gate_resolver.resolve_conflicts(
            safe_candidates, max_actions_per_corner=1
        )
        
        print(f"⚖️ {len(conflict_resolved_candidates)} candidates after conflict resolution")
        
        # Step 8: Enforce global limits (max 3 corners per lap)
        final_candidates = self.safety_gate_resolver.enforce_global_limits(
            conflict_resolved_candidates, max_corners_per_lap=3
        )
        
        print(f"🎛️ {len(final_candidates)} final candidates after global limits")
        
        # Step 9: Select final actions and generate language (Issue 06)
        selected_actions = self.action_selector.select_final_actions(
            final_candidates, safety_ampels
        )
        
        print(f"✅ Selected {len(selected_actions)} final coaching actions")
        
        # Step 10: Save coaching actions to repository
        for action in selected_actions:
            await self.coaching_repository.save_action(action)
        
        # Step 11: Create and return analysis session
        analysis_session = CornerAnalysisSession(
            session_uid=session_uid,
            track_id=track_id,
            corner_impacts=corner_impacts,
            selected_corners=selected_corner_ids,
            generated_candidates=all_candidates,
            selected_actions=selected_actions,
            analysis_timestamp=datetime.now(),
            assists_config=assists_config,
            device_config=device_config
        )
        
        print(f"🏎️ Corner analysis complete: {len(selected_actions)} actions selected")
        return analysis_session
    
    async def _generate_safety_ampels_for_corners(
        self,
        corner_ids: List[int],
        telemetry_samples: List[PlayerTelemetrySample]
    ) -> Dict[TurnPhase, SafetyAmpel]:
        """Generate safety ampels for the selected corners from telemetry."""
        
        # For now, we'll generate a simplified ampel analysis
        # In a full implementation, this would analyze slip data for each corner
        safety_ampels = {}
        
        if telemetry_samples:
            # Use the most recent telemetry sample with slip data
            recent_sample = None
            for sample in reversed(telemetry_samples):
                if sample.has_slip_data:
                    recent_sample = sample
                    break
            
            if recent_sample:
                # Generate ampels for each phase
                safety_ampels = await self.safety_ampel_service.calculate_turn_slip_analysis(
                    recent_sample
                )
        
        # If no slip data available, default to GREEN ampels
        if not safety_ampels:
            from ..value_objects.slip_indicators import AmpelColor, SlipMetrics
            default_slip_metrics = SlipMetrics(
                front_slip_ratio=0.1, rear_slip_ratio=0.1, max_slip_ratio=0.1,
                front_slip_angle=0.05, rear_slip_angle=0.05, max_slip_angle=0.05,
                combined_slip_factor=0.1
            )
            
            for phase in TurnPhase:
                safety_ampels[phase] = SafetyAmpel(
                    phase=phase,
                    color=AmpelColor.GREEN,
                    slip_metrics=default_slip_metrics,
                    confidence=0.5
                )
        
        return safety_ampels
    
    def _is_ampel_for_corner(self, ampel: SafetyAmpel, corner_id: int) -> bool:
        """Check if an ampel applies to a specific corner."""
        # In a full implementation, this would check if the ampel data
        # corresponds to the specific corner. For now, assume all ampels apply.
        return True
    
    def _get_track_name_from_id(self, track_id: int):
        """Convert track ID to TrackName. Placeholder implementation."""
        from ..value_objects.track_name import TrackName
        # This would normally be a lookup table or service
        return TrackName(f"track_{track_id}")
    
    def _create_empty_session(
        self, 
        session_uid: int, 
        track_id: int, 
        assists_config: str, 
        device_config: str
    ) -> CornerAnalysisSession:
        """Create an empty analysis session when no analysis is possible."""
        return CornerAnalysisSession(
            session_uid=session_uid,
            track_id=track_id,
            corner_impacts=[],
            selected_corners=[],
            generated_candidates=[],
            selected_actions=[],
            analysis_timestamp=datetime.now(),
            assists_config=assists_config,
            device_config=device_config
        )
    
    async def generate_coaching_report(
        self,
        analysis_session: CornerAnalysisSession,
        corner_names: Optional[Dict[int, str]] = None
    ) -> str:
        """
        Generate a human-readable coaching report from the analysis session.
        
        Args:
            analysis_session: Completed analysis session
            corner_names: Optional mapping of corner IDs to names
            
        Returns:
            Formatted coaching report string
        """
        if not analysis_session.selected_actions:
            return "Keine Verbesserungsvorschläge für diese Session. Gut gefahren! 🏎️"
        
        # Generate session summary
        total_expected_gain = sum(
            action.expected_gain_ms for action in analysis_session.selected_actions
        )
        
        # Use action selector to format the output
        coaching_message = self.action_selector.format_coaching_session_output(
            analysis_session.selected_actions, corner_names
        )
        
        # Add session summary
        summary_lines = [
            "",
            f"📈 **Session Summary:**",
            f"• Analysierte Kurven: {len(analysis_session.corner_impacts)}",
            f"• Coaching-Aktionen: {len(analysis_session.selected_actions)}",
            f"• Erwarteter Zeitgewinn: {total_expected_gain:.0f}ms",
            "",
            "🎯 **Nächste Schritte:** Einen Punkt nach dem anderen umsetzen und 1-3 gültige Runden fahren für Feedback."
        ]
        
        return coaching_message + "\n".join(summary_lines)
    
    async def evaluate_coaching_effectiveness(
        self,
        action_id: str,
        follow_up_telemetry: List[PlayerTelemetrySample],
        evaluation_laps: int = 3
    ) -> bool:
        """
        Evaluate the effectiveness of a coaching action based on follow-up telemetry.
        
        Args:
            action_id: ID of the coaching action to evaluate
            follow_up_telemetry: Telemetry from laps after the coaching
            evaluation_laps: Number of laps used for evaluation
            
        Returns:
            True if evaluation was completed and saved, False otherwise
        """
        # This would implement the "Prüfer" component from the specification
        # For now, this is a placeholder that would need sophisticated
        # telemetry analysis to detect attempts, success, and overtraining
        
        print(f"🔍 Evaluating coaching action {action_id} with {len(follow_up_telemetry)} samples")
        
        # Placeholder evaluation logic
        # In a real implementation, this would analyze:
        # - Whether an attempt was detected in the telemetry pattern
        # - Whether the action was successful (better times without slip violations)
        # - Whether overtraining occurred (slip violations, worse times)
        
        from ..entities.corner_analysis import ActionResult
        
        result = ActionResult(
            action_id=action_id,
            corner_id=1,  # Would be determined from the action
            attempt_detected=True,  # Placeholder
            success=True,  # Placeholder
            overtrained=False,  # Placeholder
            actual_gain_ms=50.0,  # Placeholder - would be calculated from telemetry
            slip_violations=[],  # Placeholder
            evaluation_laps=evaluation_laps,
            evaluation_completed_at=datetime.now()
        )
        
        try:
            await self.coaching_repository.save_action_result(result)
            print(f"✅ Evaluation saved for action {action_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to save evaluation for action {action_id}: {e}")
            return False