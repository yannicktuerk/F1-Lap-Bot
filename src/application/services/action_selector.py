"""Action selector service for choosing final coaching actions."""
from typing import List, Dict, Optional
from datetime import datetime
from ...domain.entities.corner_analysis import (
    CoachingCandidate, SelectedAction, ActionType, ActionIntensity
)
from ...domain.value_objects.slip_indicators import TurnPhase, AmpelColor, SafetyAmpel


class ActionSelector:
    """Service for selecting final coaching actions from candidates with language generation."""
    
    def __init__(self):
        self.language_templates = self._initialize_language_templates()
    
    def select_final_actions(
        self,
        candidates: List[CoachingCandidate],
        safety_ampels: Dict[TurnPhase, SafetyAmpel]
    ) -> List[SelectedAction]:
        """
        Select final coaching actions from candidates and generate user text.
        
        Args:
            candidates: List of safe, conflict-resolved candidates
            safety_ampels: Safety ampel status for language generation
            
        Returns:
            List of selected actions with user-friendly text
        """
        selected_actions = []
        
        for candidate in candidates:
            # Get ampel color for this phase
            ampel = safety_ampels.get(candidate.phase)
            ampel_color = ampel.color if ampel else AmpelColor.GREEN
            
            # Generate user text
            user_text = self._generate_user_text(candidate)
            focus_hint = self._generate_focus_hint(candidate, ampel_color)
            
            selected_action = SelectedAction(
                corner_id=candidate.corner_id,
                phase=candidate.phase,
                action_type=candidate.action_type,
                intensity=candidate.intensity,
                expected_gain_ms=candidate.expected_gain_ms,
                confidence=candidate.confidence,
                safety_ampel_color=ampel_color,
                generated_at=datetime.now(),
                user_text=user_text,
                focus_hint=focus_hint
            )
            
            selected_actions.append(selected_action)
        
        return selected_actions
    
    def _generate_user_text(self, candidate: CoachingCandidate) -> str:
        """Generate user-friendly coaching text for a candidate."""
        
        action_key = candidate.action_type.value
        intensity_key = candidate.intensity.value
        
        # Get base template
        if action_key not in self.language_templates:
            return f"Work on {candidate.phase.value} technique"
        
        templates = self.language_templates[action_key]
        
        # Select intensity-appropriate template
        if intensity_key in templates:
            return templates[intensity_key]
        else:
            # Fallback to default template
            return templates.get("default", f"Improve {action_key.replace('_', ' ')}")
    
    def _generate_focus_hint(
        self, 
        candidate: CoachingCandidate, 
        ampel_color: AmpelColor
    ) -> Optional[str]:
        """Generate optional focus hint based on action and safety context."""
        
        focus_hints = {
            ActionType.BRAKE_EARLIER: {
                AmpelColor.GREEN: "Hands ruhig halten",
                AmpelColor.YELLOW: "Sanft und kontrolliert",
                AmpelColor.RED: "Sicherheit vor Tempo"
            },
            ActionType.BUILD_PRESSURE_FASTER: {
                AmpelColor.GREEN: "Druckaufbau zügig",
                AmpelColor.YELLOW: "Progressiv steigern",
                AmpelColor.RED: None  # Not allowed in red
            },
            ActionType.RELEASE_EARLIER: {
                AmpelColor.GREEN: "Fließend lösen",
                AmpelColor.YELLOW: "Sanft reduzieren",
                AmpelColor.RED: "Sehr behutsam"
            },
            ActionType.THROTTLE_EARLIER_PROGRESSIVE: {
                AmpelColor.GREEN: "Progressiv öffnen",
                AmpelColor.YELLOW: "Sehr sanft öffnen",
                AmpelColor.RED: None  # Not allowed in red
            },
            ActionType.REDUCE_STEERING_THEN_GAS: {
                AmpelColor.GREEN: "Lenkwinkel reduzieren, dann Gas",
                AmpelColor.YELLOW: "Sanft reduzieren, dann Gas",
                AmpelColor.RED: "Traktion vor Tempo"
            }
        }
        
        action_hints = focus_hints.get(candidate.action_type, {})
        return action_hints.get(ampel_color)
    
    def _initialize_language_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize language templates for coaching actions."""
        return {
            "brake_earlier": {
                "soft": "Etwas früher bremsen",
                "progressive": "Früher bremsen",
                "fast": "Deutlich früher bremsen",
                "very_soft": "Etwas früher an die Bremse",
                "default": "Früher bremsen"
            },
            "build_pressure_faster": {
                "soft": "Druck sanft aufbauen",
                "progressive": "Druck zügig aufbauen",
                "fast": "Druck schnell aufbauen",
                "very_fast": "Druck sehr schnell aufbauen",
                "default": "Druck schneller aufbauen"
            },
            "release_earlier": {
                "soft": "Sanft früher lösen",
                "progressive": "Früher lösen",
                "fast": "Klar früher lösen",
                "very_soft": "Behutsam früher lösen",
                "default": "Früher lösen"
            },
            "throttle_earlier_progressive": {
                "soft": "Früher ans Gas, sehr sanft öffnen",
                "progressive": "Früher ans Gas, progressiv öffnen",
                "fast": "Früher ans Gas, zügig öffnen",
                "very_soft": "Früher ans Gas, behutsam öffnen",
                "default": "Früher ans Gas, progressiv öffnen"
            },
            "reduce_steering_then_gas": {
                "soft": "Lenkwinkel sanft reduzieren, dann Gas",
                "progressive": "Lenkwinkel reduzieren, dann Gas",
                "fast": "Lenkwinkel deutlich reduzieren, dann Gas",
                "very_soft": "Lenkwinkel behutsam reduzieren, dann Gas",
                "default": "Lenkwinkel reduzieren, dann Gas"
            }
        }
    
    def format_coaching_session_output(
        self,
        selected_actions: List[SelectedAction],
        corner_names: Optional[Dict[int, str]] = None
    ) -> str:
        """
        Format the complete coaching session output for the user.
        
        Args:
            selected_actions: List of selected actions
            corner_names: Optional mapping of corner IDs to names
            
        Returns:
            Formatted coaching message string
        """
        if not selected_actions:
            return "Keine Verbesserungsvorschläge für diese Runde. Gut gefahren!"
        
        message_lines = []
        message_lines.append("🏎️ **Coaching Empfehlungen:**")
        message_lines.append("")
        
        for i, action in enumerate(selected_actions, 1):
            corner_name = self._get_corner_name(action.corner_id, corner_names)
            
            # Format individual action
            action_line = f"**{i}. {corner_name}** ({action.phase.value.title()}): {action.coaching_message}"
            message_lines.append(action_line)
            
            # Add confidence indicator if low
            if action.confidence < 0.7:
                message_lines.append("   ↳ *Vorsichtig versuchen*")
            
            message_lines.append("")
        
        # Add global reminder
        if len(selected_actions) > 1:
            message_lines.append("💡 **Fokus:** Ein Punkt nach dem anderen umsetzen.")
        
        return "\n".join(message_lines)
    
    def _get_corner_name(self, corner_id: int, corner_names: Optional[Dict[int, str]]) -> str:
        """Get user-friendly corner name."""
        if corner_names and corner_id in corner_names:
            return corner_names[corner_id]
        else:
            return f"Kurve {corner_id}"
    
    def generate_session_summary(
        self,
        selected_actions: List[SelectedAction],
        total_expected_gain_ms: float,
        safety_summary: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Generate summary statistics for the coaching session.
        
        Args:
            selected_actions: List of selected actions
            total_expected_gain_ms: Total expected time improvement
            safety_summary: Safety filtering summary from resolver
            
        Returns:
            Dictionary containing session summary
        """
        if not selected_actions:
            return {
                'actions_count': 0,
                'expected_gain_ms': 0.0,
                'corners_coached': [],
                'phases_distribution': {},
                'average_confidence': 0.0,
                'safety_summary': safety_summary
            }
        
        # Calculate statistics
        corners_coached = [action.corner_id for action in selected_actions]
        phases_distribution = {}
        total_confidence = 0.0
        
        for action in selected_actions:
            phase = action.phase.value
            phases_distribution[phase] = phases_distribution.get(phase, 0) + 1
            total_confidence += action.confidence
        
        average_confidence = total_confidence / len(selected_actions)
        
        return {
            'actions_count': len(selected_actions),
            'expected_gain_ms': total_expected_gain_ms,
            'corners_coached': corners_coached,
            'phases_distribution': phases_distribution,
            'average_confidence': average_confidence,
            'safety_summary': safety_summary,
            'action_types': [action.action_type.value for action in selected_actions],
            'intensities': [action.intensity.value for action in selected_actions]
        }
    
    def validate_language_output(self, user_text: str) -> bool:
        """
        Validate that generated language follows the rules (no numbers/meters).
        
        Args:
            user_text: Generated user text to validate
            
        Returns:
            True if text follows language rules, False otherwise
        """
        # Check for forbidden patterns
        forbidden_patterns = [
            r'\d+\s*m[^\w]',      # Numbers followed by meters
            r'\d+\s*meter',       # Numbers followed by meter/meters
            r'\d+\s*ms',          # Milliseconds
            r'\d+\s*sek',         # Sekunden
            r'\d+\s*km/h',        # Speed units
            r'\d+\s*%'            # Percentages
        ]
        
        import re
        for pattern in forbidden_patterns:
            if re.search(pattern, user_text.lower()):
                return False
        
        return True