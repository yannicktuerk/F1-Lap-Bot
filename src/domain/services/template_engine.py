"""Language templates and qualitative coaching message generation."""
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class Language(Enum):
    """Supported languages for coaching messages."""
    GERMAN = "de"
    ENGLISH = "en"


class IntensityLevel(Enum):
    """Intensity levels for coaching messages."""
    LIGHT = "light"
    MEDIUM = "medium"
    AGGRESSIVE = "aggressive"


class MessageType(Enum):
    """Types of coaching messages."""
    BRAKE_EARLIER = "brake_earlier"
    PRESSURE_FASTER = "pressure_faster"
    RELEASE_EARLIER = "release_earlier"
    THROTTLE_EARLIER = "throttle_earlier"
    REDUCE_STEERING = "reduce_steering"
    STABILITY_FOCUS = "stability_focus"
    CONSISTENCY_DRILL = "consistency_drill"


@dataclass(frozen=True)
class MessageTemplate:
    """Template for coaching message generation."""
    
    message_type: MessageType
    language: Language
    intensity: IntensityLevel
    
    # Template components (Cause → Action → Focus structure)
    cause_phrase: str
    action_phrase: str
    focus_phrase: str
    
    # Optional additional context
    context_phrase: Optional[str] = None
    
    def generate_message(self, corner_context: Optional[str] = None) -> str:
        """
        Generate complete coaching message using template.
        
        Args:
            corner_context: Optional corner-specific context
            
        Returns:
            Complete coaching message string
        """
        # Build message: Cause → Action → Focus
        message_parts = [
            self.cause_phrase,
            self.action_phrase,
            self.focus_phrase
        ]
        
        # Add context if provided
        if self.context_phrase:
            message_parts.append(self.context_phrase)
        
        if corner_context:
            message_parts.append(corner_context)
        
        # Join with appropriate punctuation
        if self.language == Language.GERMAN:
            return ". ".join(message_parts) + "."
        else:
            return ". ".join(message_parts) + "."
    
    def validate_no_numbers(self) -> bool:
        """Validate that template contains no numbers, meters, or times."""
        all_text = " ".join([
            self.cause_phrase, self.action_phrase, self.focus_phrase,
            self.context_phrase or ""
        ])
        
        # Check for forbidden content
        forbidden_patterns = [
            "meter", "m ", " m", "km/h", "mph", "second", "ms", "lap time",
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "Meter", "Zeit", "Sekunde", "Runde"
        ]
        
        for pattern in forbidden_patterns:
            if pattern in all_text:
                return False
        
        return True


# German Template Library
GERMAN_TEMPLATES = {
    # Brake Earlier Templates
    (MessageType.BRAKE_EARLIER, IntensityLevel.LIGHT): MessageTemplate(
        message_type=MessageType.BRAKE_EARLIER,
        language=Language.GERMAN,
        intensity=IntensityLevel.LIGHT,
        cause_phrase="Der Bremspunkt könnte optimiert werden",
        action_phrase="etwas früher bremsen",
        focus_phrase="dann entspannt in die Kurve rollen"
    ),
    
    (MessageType.BRAKE_EARLIER, IntensityLevel.MEDIUM): MessageTemplate(
        message_type=MessageType.BRAKE_EARLIER,
        language=Language.GERMAN,
        intensity=IntensityLevel.MEDIUM,
        cause_phrase="Die Bremsphase ist zu spät",
        action_phrase="früher bremsen",
        focus_phrase="mehr Zeit für die Kurveneinfahrt gewinnen"
    ),
    
    (MessageType.BRAKE_EARLIER, IntensityLevel.AGGRESSIVE): MessageTemplate(
        message_type=MessageType.BRAKE_EARLIER,
        language=Language.GERMAN,
        intensity=IntensityLevel.AGGRESSIVE,
        cause_phrase="Zu späte Bremsung kostet Zeit",
        action_phrase="deutlich früher bremsen",
        focus_phrase="aggressive aber kontrollierte Einfahrt"
    ),
    
    # Pressure Faster Templates
    (MessageType.PRESSURE_FASTER, IntensityLevel.LIGHT): MessageTemplate(
        message_type=MessageType.PRESSURE_FASTER,
        language=Language.GERMAN,
        intensity=IntensityLevel.LIGHT,
        cause_phrase="Der Bremsdruckaufbau ist zu zögerlich",
        action_phrase="Druck zügig aufbauen",
        focus_phrase="dann gleichmäßig halten"
    ),
    
    (MessageType.PRESSURE_FASTER, IntensityLevel.MEDIUM): MessageTemplate(
        message_type=MessageType.PRESSURE_FASTER,
        language=Language.GERMAN,
        intensity=IntensityLevel.MEDIUM,
        cause_phrase="Zu langsamer Druckaufbau verschenkt Potential",
        action_phrase="Druck schneller aufbauen",
        focus_phrase="maximale Verzögerung ohne Blockieren"
    ),
    
    (MessageType.PRESSURE_FASTER, IntensityLevel.AGGRESSIVE): MessageTemplate(
        message_type=MessageType.PRESSURE_FASTER,
        language=Language.GERMAN,
        intensity=IntensityLevel.AGGRESSIVE,
        cause_phrase="Ineffiziente Bremsphase",
        action_phrase="Druck sehr schnell aufbauen",
        focus_phrase="an der Blockiergrenze arbeiten"
    ),
    
    # Release Earlier Templates
    (MessageType.RELEASE_EARLIER, IntensityLevel.LIGHT): MessageTemplate(
        message_type=MessageType.RELEASE_EARLIER,
        language=Language.GERMAN,
        intensity=IntensityLevel.LIGHT,
        cause_phrase="Das Bremslösen kommt zu spät",
        action_phrase="früher lösen",
        focus_phrase="sanft in die Rotation überleiten"
    ),
    
    (MessageType.RELEASE_EARLIER, IntensityLevel.MEDIUM): MessageTemplate(
        message_type=MessageType.RELEASE_EARLIER,
        language=Language.GERMAN,
        intensity=IntensityLevel.MEDIUM,
        cause_phrase="Zu spätes Lösen blockiert den Kurvenfluss",
        action_phrase="klar früher lösen",
        focus_phrase="ruhige Hände für bessere Balance"
    ),
    
    # Throttle Earlier Templates  
    (MessageType.THROTTLE_EARLIER, IntensityLevel.LIGHT): MessageTemplate(
        message_type=MessageType.THROTTLE_EARLIER,
        language=Language.GERMAN,
        intensity=IntensityLevel.LIGHT,
        cause_phrase="Der Gaspunkt ist konservativ",
        action_phrase="etwas früher ans Gas, sanft öffnen",
        focus_phrase="progressive Beschleunigung aufbauen"
    ),
    
    (MessageType.THROTTLE_EARLIER, IntensityLevel.MEDIUM): MessageTemplate(
        message_type=MessageType.THROTTLE_EARLIER,
        language=Language.GERMAN,
        intensity=IntensityLevel.MEDIUM,
        cause_phrase="Verschenktes Potential beim Kurvenausgang",
        action_phrase="früher ans Gas, progressiv öffnen",
        focus_phrase="maximale Traktion ausnutzen"
    ),
    
    # Reduce Steering Templates
    (MessageType.REDUCE_STEERING, IntensityLevel.LIGHT): MessageTemplate(
        message_type=MessageType.REDUCE_STEERING,
        language=Language.GERMAN,
        intensity=IntensityLevel.LIGHT,
        cause_phrase="Der Lenkwinkel ist zu groß",
        action_phrase="Lenkwinkel etwas reduzieren, dann Gas",
        focus_phrase="sanftere Kurvenlinie finden"
    ),
    
    (MessageType.REDUCE_STEERING, IntensityLevel.MEDIUM): MessageTemplate(
        message_type=MessageType.REDUCE_STEERING,
        language=Language.GERMAN,
        intensity=IntensityLevel.MEDIUM,
        cause_phrase="Übersteuern kostet Geschwindigkeit",
        action_phrase="Lenkwinkel reduzieren, dann Gas",
        focus_phrase="effizientere Linie durch weniger Lenkarbeit"
    ),
    
    # Stability Focus Templates
    (MessageType.STABILITY_FOCUS, IntensityLevel.LIGHT): MessageTemplate(
        message_type=MessageType.STABILITY_FOCUS,
        language=Language.GERMAN,
        intensity=IntensityLevel.LIGHT,
        cause_phrase="Stabilität vor Geschwindigkeit",
        action_phrase="ruhige, gleichmäßige Eingaben",
        focus_phrase="Vertrauen in die Fahrzeugbalance aufbauen"
    ),
    
    (MessageType.STABILITY_FOCUS, IntensityLevel.MEDIUM): MessageTemplate(
        message_type=MessageType.STABILITY_FOCUS,
        language=Language.GERMAN,
        intensity=IntensityLevel.MEDIUM,
        cause_phrase="Fahrzeug arbeitet gegen dich",
        action_phrase="sanftere Übergänge zwischen Bremse und Gas",
        focus_phrase="Grip bewusst spüren und respektieren"
    ),
    
    # Consistency Drill Templates
    (MessageType.CONSISTENCY_DRILL, IntensityLevel.LIGHT): MessageTemplate(
        message_type=MessageType.CONSISTENCY_DRILL,
        language=Language.GERMAN,
        intensity=IntensityLevel.LIGHT,
        cause_phrase="Konstanz ist wichtiger als Einzelzeiten",
        action_phrase="wiederholbare Referenzpunkte setzen",
        focus_phrase="gleiche Linie mehrfach fahren"
    ),
    
    (MessageType.CONSISTENCY_DRILL, IntensityLevel.MEDIUM): MessageTemplate(
        message_type=MessageType.CONSISTENCY_DRILL,
        language=Language.GERMAN,
        intensity=IntensityLevel.MEDIUM,
        cause_phrase="Schwankende Performance kostet Gesamtzeit",
        action_phrase="präzise Wiederholung der besten Linie",
        focus_phrase="Muskelerinnerung für optimale Eingaben entwickeln"
    )
}

# English Template Library
ENGLISH_TEMPLATES = {
    # Brake Earlier Templates
    (MessageType.BRAKE_EARLIER, IntensityLevel.LIGHT): MessageTemplate(
        message_type=MessageType.BRAKE_EARLIER,
        language=Language.ENGLISH,
        intensity=IntensityLevel.LIGHT,
        cause_phrase="Brake point could be optimized",
        action_phrase="brake slightly earlier",
        focus_phrase="roll smoothly into the corner"
    ),
    
    (MessageType.BRAKE_EARLIER, IntensityLevel.MEDIUM): MessageTemplate(
        message_type=MessageType.BRAKE_EARLIER,
        language=Language.ENGLISH,
        intensity=IntensityLevel.MEDIUM,
        cause_phrase="Braking phase is too late",
        action_phrase="brake earlier",
        focus_phrase="gain more time for corner entry"
    ),
    
    (MessageType.BRAKE_EARLIER, IntensityLevel.AGGRESSIVE): MessageTemplate(
        message_type=MessageType.BRAKE_EARLIER,
        language=Language.ENGLISH,
        intensity=IntensityLevel.AGGRESSIVE,
        cause_phrase="Late braking is costing time",
        action_phrase="brake much earlier",
        focus_phrase="aggressive but controlled entry"
    ),
    
    # Pressure Faster Templates
    (MessageType.PRESSURE_FASTER, IntensityLevel.LIGHT): MessageTemplate(
        message_type=MessageType.PRESSURE_FASTER,
        language=Language.ENGLISH,
        intensity=IntensityLevel.LIGHT,
        cause_phrase="Brake pressure buildup is hesitant",
        action_phrase="build pressure smoothly",
        focus_phrase="then hold consistently"
    ),
    
    (MessageType.PRESSURE_FASTER, IntensityLevel.MEDIUM): MessageTemplate(
        message_type=MessageType.PRESSURE_FASTER,
        language=Language.ENGLISH,
        intensity=IntensityLevel.MEDIUM,
        cause_phrase="Slow pressure buildup wastes potential",
        action_phrase="build pressure faster",
        focus_phrase="maximum deceleration without locking"
    ),
    
    # Add more English templates...
}


class TemplateEngine:
    """Engine for managing and selecting coaching message templates."""
    
    def __init__(self, primary_language: Language = Language.GERMAN):
        """
        Initialize template engine.
        
        Args:
            primary_language: Primary language for coaching messages
        """
        self.primary_language = primary_language
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """Load all templates for all languages."""
        templates = {}
        templates.update(GERMAN_TEMPLATES)
        templates.update(ENGLISH_TEMPLATES)
        return templates
    
    def get_template(self, 
                    message_type: MessageType,
                    intensity: IntensityLevel,
                    language: Optional[Language] = None) -> Optional[MessageTemplate]:
        """
        Get template for specific message type and intensity.
        
        Args:
            message_type: Type of coaching message
            intensity: Intensity level
            language: Language (uses primary if None)
            
        Returns:
            Template or None if not found
        """
        lang = language or self.primary_language
        key = (message_type, intensity)
        
        # Try primary language first
        template_key = (*key, lang) if len(key) == 2 else key
        if template_key in self.templates:
            return self.templates[template_key]
        
        # Try with just message type and intensity (for dict lookup)
        if key in self.templates:
            return self.templates[key]
        
        # Fallback to medium intensity if specific not found
        fallback_key = (message_type, IntensityLevel.MEDIUM)
        if fallback_key in self.templates:
            return self.templates[fallback_key]
        
        return None
    
    def generate_message(self,
                        message_type: MessageType,
                        intensity: IntensityLevel,
                        corner_context: Optional[str] = None,
                        language: Optional[Language] = None) -> str:
        """
        Generate coaching message using templates.
        
        Args:
            message_type: Type of coaching message
            intensity: Intensity level
            corner_context: Optional corner-specific context
            language: Language (uses primary if None)
            
        Returns:
            Generated coaching message
        """
        template = self.get_template(message_type, intensity, language)
        
        if template is None:
            # Fallback message
            lang = language or self.primary_language
            if lang == Language.GERMAN:
                return "Konzentriere dich auf saubere Fahrweise."
            else:
                return "Focus on clean driving technique."
        
        return template.generate_message(corner_context)
    
    def validate_all_templates(self) -> Dict[str, List[str]]:
        """
        Validate all templates for forbidden content.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            "valid": [],
            "invalid": [],
            "errors": []
        }
        
        for key, template in self.templates.items():
            try:
                if template.validate_no_numbers():
                    results["valid"].append(str(key))
                else:
                    results["invalid"].append(str(key))
            except Exception as e:
                results["errors"].append(f"{key}: {e}")
        
        return results
    
    def get_available_message_types(self, language: Optional[Language] = None) -> List[MessageType]:
        """Get list of available message types for a language."""
        lang = language or self.primary_language
        available_types = set()
        
        for (msg_type, intensity) in self.templates.keys():
            if isinstance(msg_type, MessageType):
                available_types.add(msg_type)
        
        return list(available_types)
    
    def get_template_statistics(self) -> Dict[str, int]:
        """Get statistics about loaded templates."""
        stats = {
            "total_templates": len(self.templates),
            "german_templates": 0,
            "english_templates": 0,
            "message_types": set(),
            "intensity_levels": set()
        }
        
        for template in self.templates.values():
            if isinstance(template, MessageTemplate):
                if template.language == Language.GERMAN:
                    stats["german_templates"] += 1
                elif template.language == Language.ENGLISH:
                    stats["english_templates"] += 1
                
                stats["message_types"].add(template.message_type)
                stats["intensity_levels"].add(template.intensity)
        
        stats["message_types"] = len(stats["message_types"])
        stats["intensity_levels"] = len(stats["intensity_levels"])
        
        return stats