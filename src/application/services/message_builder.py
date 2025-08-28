"""Message builder service for generating coaching messages."""
import logging
from typing import Optional, Dict, Any, List

from ...domain.services.template_engine import (
    TemplateEngine, MessageType, IntensityLevel, Language
)
from ...domain.value_objects.review_outcomes import ReviewOutcome
from ...infrastructure.persistence.localization_service import LocalizationService


class MessageBuilder:
    """
    Service for building coaching messages using templates.
    
    Generates user-facing coaching messages with proper localization,
    intensity matching, and qualitative language (no numbers/meters).
    """
    
    def __init__(self, 
                 template_engine: Optional[TemplateEngine] = None,
                 localization_service: Optional[LocalizationService] = None,
                 primary_language: Language = Language.GERMAN):
        """
        Initialize message builder.
        
        Args:
            template_engine: Template engine (auto-created if None)
            localization_service: Localization service (auto-created if None)
            primary_language: Primary language for messages
        """
        self.logger = logging.getLogger(__name__)
        self.template_engine = template_engine or TemplateEngine(primary_language)
        self.localization_service = localization_service or LocalizationService()
        self.primary_language = primary_language
        
        # Message type mapping from action types
        self.action_to_message_type = {
            "brake_earlier": MessageType.BRAKE_EARLIER,
            "pressure_faster": MessageType.PRESSURE_FASTER,
            "release_earlier": MessageType.RELEASE_EARLIER,
            "throttle_earlier": MessageType.THROTTLE_EARLIER,
            "reduce_steering": MessageType.REDUCE_STEERING
        }
        
        # Intensity mapping
        self.intensity_mapping = {
            "light": IntensityLevel.LIGHT,
            "medium": IntensityLevel.MEDIUM,
            "aggressive": IntensityLevel.AGGRESSIVE
        }
        
        # Corner context phrases (German)
        self.corner_contexts_de = {
            "slow": "in der langsamen Kurve",
            "medium": "in der mittleren Kurve", 
            "fast": "in der schnellen Kurve",
            "chicane": "in der Schikane",
            "hairpin": "in der Haarnadelkurve",
            "s_curve": "in der S-Kurve"
        }
        
        # Corner context phrases (English)
        self.corner_contexts_en = {
            "slow": "in the slow corner",
            "medium": "in the medium corner",
            "fast": "in the fast corner", 
            "chicane": "in the chicane",
            "hairpin": "in the hairpin",
            "s_curve": "in the S-curve"
        }
    
    def build_coaching_message(self,
                             action_type: str,
                             intensity: str,
                             corner_type: Optional[str] = None,
                             corner_name: Optional[str] = None,
                             language: Optional[Language] = None) -> str:
        """
        Build coaching message for a specific action.
        
        Args:
            action_type: Type of coaching action
            intensity: Intensity level of coaching
            corner_type: Type of corner (slow, medium, fast, etc.)
            corner_name: Specific corner name
            language: Target language
            
        Returns:
            Complete coaching message string
        """
        try:
            # Map action type to message type
            message_type = self.action_to_message_type.get(action_type)
            if message_type is None:
                self.logger.warning(f"Unknown action type: {action_type}")
                return self._fallback_message(language)
            
            # Map intensity
            intensity_level = self.intensity_mapping.get(intensity, IntensityLevel.MEDIUM)
            
            # Build corner context
            corner_context = self._build_corner_context(corner_type, corner_name, language)
            
            # Generate message
            message = self.template_engine.generate_message(
                message_type=message_type,
                intensity=intensity_level,
                corner_context=corner_context,
                language=language
            )
            
            # Validate no numbers
            if not self._validate_no_numbers(message):
                self.logger.warning(f"Generated message contains forbidden content: {message}")
                return self._fallback_message(language)
            
            self.logger.debug(f"Generated coaching message: {message}")
            return message
            
        except Exception as e:
            self.logger.error(f"❌ Error building coaching message: {e}")
            return self._fallback_message(language)
    
    def build_success_message(self,
                            action_type: str,
                            improvement_context: Optional[str] = None,
                            language: Optional[Language] = None) -> str:
        """
        Build success/confirmation message after positive outcome.
        
        Args:
            action_type: Type of action that succeeded
            improvement_context: Context about the improvement
            language: Target language
            
        Returns:
            Success message string
        """
        try:
            lang = language or self.primary_language
            
            if lang == Language.GERMAN:
                success_templates = {
                    "brake_earlier": "Sehr gut! Das frühere Bremsen zeigt Wirkung",
                    "pressure_faster": "Perfekt! Der schnellere Druckaufbau funktioniert",
                    "release_earlier": "Ausgezeichnet! Das frühere Lösen verbessert den Fluss",
                    "throttle_earlier": "Hervorragend! Die frühere Gasannahme bringt Zeit",
                    "reduce_steering": "Prima! Der reduzierte Lenkwinkel ist effizienter"
                }
                base_message = success_templates.get(action_type, "Sehr gut! Die Verbesserung ist spürbar")
                
                if improvement_context:
                    return f"{base_message}. {improvement_context}."
                else:
                    return f"{base_message}. Weiter so!"
            
            else:  # English
                success_templates = {
                    "brake_earlier": "Excellent! The earlier braking is working",
                    "pressure_faster": "Perfect! The faster pressure buildup is effective",
                    "release_earlier": "Outstanding! The earlier release improves flow",
                    "throttle_earlier": "Great! The earlier throttle application gains time",
                    "reduce_steering": "Nice! The reduced steering angle is more efficient"
                }
                base_message = success_templates.get(action_type, "Excellent! The improvement is noticeable")
                
                if improvement_context:
                    return f"{base_message}. {improvement_context}."
                else:
                    return f"{base_message}. Keep it up!"
                    
        except Exception as e:
            self.logger.error(f"❌ Error building success message: {e}")
            return self._fallback_success_message(language)
    
    def build_overshoot_message(self,
                              action_type: str,
                              issue_type: str,  # "wheelspin", "front_slip", "time_loss"
                              language: Optional[Language] = None) -> str:
        """
        Build message for overshoot/overdone coaching.
        
        Args:
            action_type: Type of action that was overdone
            issue_type: Specific issue that occurred
            language: Target language
            
        Returns:
            Overshoot correction message
        """
        try:
            lang = language or self.primary_language
            
            if lang == Language.GERMAN:
                overshoot_templates = {
                    ("brake_earlier", "time_loss"): "Etwas zu früh gebremst. Bremspunkt leicht nach hinten verschieben",
                    ("pressure_faster", "front_slip"): "Druckaufbau zu aggressiv. Sanfter an die Blockiergrenze herantasten",
                    ("throttle_earlier", "wheelspin"): "Gas zu früh und zu hart. Später ansetzen, progressiver öffnen",
                    ("reduce_steering", "time_loss"): "Lenkwinkel zu stark reduziert. Mittleren Weg zwischen Effizienz und Geschwindigkeit finden"
                }
                
                message = overshoot_templates.get((action_type, issue_type))
                if message:
                    return f"{message}. Stabilität vor Geschwindigkeit."
                else:
                    return "Etwas übertrieben ausgeführt. Einen Gang zurückschalten und sanfter angehen."
            
            else:  # English
                overshoot_templates = {
                    ("brake_earlier", "time_loss"): "Braked slightly too early. Move brake point slightly later",
                    ("pressure_faster", "front_slip"): "Pressure buildup too aggressive. Approach threshold more gently",
                    ("throttle_earlier", "wheelspin"): "Throttle too early and hard. Apply later, more progressively",
                    ("reduce_steering", "time_loss"): "Steering angle reduced too much. Find middle ground between efficiency and speed"
                }
                
                message = overshoot_templates.get((action_type, issue_type))
                if message:
                    return f"{message}. Stability before speed."
                else:
                    return "Slightly overdone. Dial it back and approach more gently."
                    
        except Exception as e:
            self.logger.error(f"❌ Error building overshoot message: {e}")
            return self._fallback_overshoot_message(language)
    
    def build_no_attempt_message(self,
                               action_type: str,
                               language: Optional[Language] = None) -> str:
        """
        Build message for no attempt (micro-drill encouragement).
        
        Args:
            action_type: Type of action that wasn't attempted
            language: Target language
            
        Returns:
            Encouragement message for micro-drill
        """
        try:
            lang = language or self.primary_language
            
            if lang == Language.GERMAN:
                micro_drill_templates = {
                    "brake_earlier": "Fokus auf einen einzigen Referenzpunkt. Beim nächsten Mal bewusst vor diesem Punkt bremsen",
                    "pressure_faster": "Konzentration auf das Bremspedal. Bewusst schneller zum Maximum durchdrücken",
                    "release_earlier": "Aufmerksamkeit auf das Loslassen. Vor dem gewohnten Punkt das Pedal freigeben",
                    "throttle_earlier": "Fokus auf den Gaspunkt. Einen Hauch früher das Pedal antippen",
                    "reduce_steering": "Bewusstsein für den Lenkwinkel. Weniger Lenkeinschlag vor der Gasannahme"
                }
                
                message = micro_drill_templates.get(action_type, "Einen Aspekt herausgreifen und bewusst ändern")
                return f"{message}. Nur diesen einen Punkt beachten."
            
            else:  # English
                micro_drill_templates = {
                    "brake_earlier": "Focus on a single reference point. Next time, brake consciously before this point",
                    "pressure_faster": "Concentrate on the brake pedal. Consciously push to maximum faster",
                    "release_earlier": "Attention on the release. Let off the pedal before the usual point",
                    "throttle_earlier": "Focus on the throttle point. Touch the pedal slightly earlier",
                    "reduce_steering": "Awareness of steering angle. Less steering input before throttle application"
                }
                
                message = micro_drill_templates.get(action_type, "Pick one aspect and change it consciously")
                return f"{message}. Focus only on this one point."
                
        except Exception as e:
            self.logger.error(f"❌ Error building no attempt message: {e}")
            return self._fallback_no_attempt_message(language)
    
    def build_review_summary(self,
                           action_type: str,
                           outcome: ReviewOutcome,
                           laps_evaluated: int,
                           language: Optional[Language] = None) -> str:
        """
        Build summary message after review completion.
        
        Args:
            action_type: Type of action that was reviewed
            outcome: Review outcome
            laps_evaluated: Number of laps evaluated
            language: Target language
            
        Returns:
            Review summary message
        """
        try:
            lang = language or self.primary_language
            
            if lang == Language.GERMAN:
                outcome_phrases = {
                    ReviewOutcome.SUCCESS: "erfolgreich umgesetzt",
                    ReviewOutcome.OVERSHOOT: "etwas übertrieben ausgeführt",
                    ReviewOutcome.NO_ATTEMPT: "noch nicht probiert",
                    ReviewOutcome.INCONCLUSIVE: "gemischte Signale"
                }
                
                outcome_phrase = outcome_phrases.get(outcome, "bewertet")
                return f"Coaching '{action_type}' wurde {outcome_phrase}. Nächste Strategie wird angepasst."
            
            else:  # English
                outcome_phrases = {
                    ReviewOutcome.SUCCESS: "successfully implemented",
                    ReviewOutcome.OVERSHOOT: "somewhat overdone",
                    ReviewOutcome.NO_ATTEMPT: "not yet attempted",
                    ReviewOutcome.INCONCLUSIVE: "mixed signals"
                }
                
                outcome_phrase = outcome_phrases.get(outcome, "evaluated")
                return f"Coaching '{action_type}' was {outcome_phrase}. Next strategy will be adjusted."
                
        except Exception as e:
            self.logger.error(f"❌ Error building review summary: {e}")
            return "Coaching evaluation completed."
    
    def _build_corner_context(self,
                            corner_type: Optional[str],
                            corner_name: Optional[str],
                            language: Optional[Language]) -> Optional[str]:
        """Build corner context phrase."""
        if not corner_type and not corner_name:
            return None
        
        lang = language or self.primary_language
        
        if corner_name:
            # Use specific corner name if available
            if lang == Language.GERMAN:
                return f"in {corner_name}"
            else:
                return f"in {corner_name}"
        
        elif corner_type:
            # Use corner type context
            if lang == Language.GERMAN:
                return self.corner_contexts_de.get(corner_type)
            else:
                return self.corner_contexts_en.get(corner_type)
        
        return None
    
    def _validate_no_numbers(self, message: str) -> bool:
        """Validate that message contains no numbers, meters, or times."""
        forbidden_patterns = [
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "meter", "m ", " m", "km/h", "mph", "second", "ms", "lap time",
            "Meter", "Zeit", "Sekunde", "Runde", "km/h"
        ]
        
        for pattern in forbidden_patterns:
            if pattern in message:
                return False
        
        return True
    
    def _fallback_message(self, language: Optional[Language]) -> str:
        """Generate safe fallback message."""
        lang = language or self.primary_language
        
        if lang == Language.GERMAN:
            return "Konzentriere dich auf saubere Fahrweise."
        else:
            return "Focus on clean driving technique."
    
    def _fallback_success_message(self, language: Optional[Language]) -> str:
        """Generate safe fallback success message."""
        lang = language or self.primary_language
        
        if lang == Language.GERMAN:
            return "Sehr gut! Die Verbesserung ist spürbar."
        else:
            return "Excellent! The improvement is noticeable."
    
    def _fallback_overshoot_message(self, language: Optional[Language]) -> str:
        """Generate safe fallback overshoot message."""
        lang = language or self.primary_language
        
        if lang == Language.GERMAN:
            return "Etwas sanfter angehen. Stabilität vor Geschwindigkeit."
        else:
            return "Approach more gently. Stability before speed."
    
    def _fallback_no_attempt_message(self, language: Optional[Language]) -> str:
        """Generate safe fallback no attempt message."""
        lang = language or self.primary_language
        
        if lang == Language.GERMAN:
            return "Einen Aspekt bewusst ändern. Schritt für Schritt."
        else:
            return "Change one aspect consciously. Step by step."
    
    def get_message_builder_status(self) -> Dict[str, Any]:
        """Get status of message builder service."""
        template_stats = self.template_engine.get_template_statistics()
        validation_results = self.template_engine.validate_all_templates()
        
        return {
            "primary_language": self.primary_language.value,
            "template_statistics": template_stats,
            "validation_results": {
                "total_templates": len(validation_results["valid"]) + len(validation_results["invalid"]),
                "valid_templates": len(validation_results["valid"]),
                "invalid_templates": len(validation_results["invalid"]),
                "validation_errors": len(validation_results["errors"])
            },
            "supported_action_types": list(self.action_to_message_type.keys()),
            "supported_intensities": list(self.intensity_mapping.keys()),
            "corner_contexts": {
                "german": list(self.corner_contexts_de.keys()),
                "english": list(self.corner_contexts_en.keys())
            }
        }