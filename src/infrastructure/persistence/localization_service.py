"""Localization service for multi-language support."""
import logging
import os
import json
from typing import Dict, Optional, Any, List
from enum import Enum


class Language(Enum):
    """Supported languages."""
    GERMAN = "de"
    ENGLISH = "en"


class LocalizationService:
    """
    Service for managing localized strings and formatting.
    
    Provides translation and localization support for the coaching system,
    ensuring proper formatting and cultural considerations for different languages.
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize localization service.
        
        Args:
            base_path: Base path for localization files (auto-detected if None)
        """
        self.logger = logging.getLogger(__name__)
        
        if base_path is None:
            # Auto-detect localization directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(script_dir, "..", "..", "..")
            self.base_path = os.path.join(project_root, "localization")
        else:
            self.base_path = base_path
        
        # Ensure localization directory exists
        os.makedirs(self.base_path, exist_ok=True)
        
        # Load translations
        self.translations = self._load_translations()
        
        # Default language
        self.default_language = Language.GERMAN
    
    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """Load translation files for all supported languages."""
        translations = {}
        
        for language in Language:
            lang_code = language.value
            file_path = os.path.join(self.base_path, f"{lang_code}.json")
            
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        translations[lang_code] = json.load(f)
                    self.logger.info(f"✅ Loaded translations for {lang_code}")
                else:
                    # Create default translation file
                    translations[lang_code] = self._create_default_translations(language)
                    self._save_translation_file(lang_code, translations[lang_code])
                    self.logger.info(f"📁 Created default translations for {lang_code}")
                    
            except Exception as e:
                self.logger.error(f"❌ Error loading translations for {lang_code}: {e}")
                translations[lang_code] = self._create_default_translations(language)
        
        return translations
    
    def _create_default_translations(self, language: Language) -> Dict[str, str]:
        """Create default translations for a language."""
        if language == Language.GERMAN:
            return {
                # System messages
                "system.coaching_started": "Coaching-System gestartet",
                "system.coaching_stopped": "Coaching-System gestoppt",
                "system.error": "Fehler im System",
                
                # Coaching actions
                "action.brake_earlier": "früher bremsen",
                "action.pressure_faster": "Druck schneller aufbauen",
                "action.release_earlier": "früher lösen",
                "action.throttle_earlier": "früher ans Gas",
                "action.reduce_steering": "Lenkwinkel reduzieren",
                
                # Intensities
                "intensity.light": "sanft",
                "intensity.medium": "mittel",
                "intensity.aggressive": "aggressiv",
                
                # Corner types
                "corner.slow": "langsame Kurve",
                "corner.medium": "mittlere Kurve",
                "corner.fast": "schnelle Kurve",
                "corner.chicane": "Schikane",
                "corner.hairpin": "Haarnadelkurve",
                
                # Review outcomes
                "review.success": "erfolgreich",
                "review.overshoot": "übertrieben",
                "review.no_attempt": "nicht versucht",
                "review.inconclusive": "unklar",
                
                # Safety messages
                "safety.green": "Optimale Grip-Bedingungen",
                "safety.yellow": "Vorsichtige Fahrweise empfohlen",
                "safety.red": "Gefährliche Grip-Verhältnisse - Vorsicht!",
                
                # General coaching
                "coaching.stability_first": "Stabilität vor Geschwindigkeit",
                "coaching.consistency": "Konstanz ist wichtiger als Einzelzeiten",
                "coaching.patience": "Geduld - Verbesserung braucht Zeit",
                "coaching.focus": "Einen Punkt nach dem anderen",
                
                # Feedback
                "feedback.good_progress": "Gute Fortschritte",
                "feedback.keep_practicing": "Weiter üben",
                "feedback.excellent": "Ausgezeichnet",
                "feedback.try_again": "Nochmal versuchen"
            }
        
        else:  # English
            return {
                # System messages
                "system.coaching_started": "Coaching system started",
                "system.coaching_stopped": "Coaching system stopped",
                "system.error": "System error",
                
                # Coaching actions
                "action.brake_earlier": "brake earlier",
                "action.pressure_faster": "build pressure faster",
                "action.release_earlier": "release earlier",
                "action.throttle_earlier": "throttle earlier",
                "action.reduce_steering": "reduce steering angle",
                
                # Intensities
                "intensity.light": "gentle",
                "intensity.medium": "medium",
                "intensity.aggressive": "aggressive",
                
                # Corner types
                "corner.slow": "slow corner",
                "corner.medium": "medium corner",
                "corner.fast": "fast corner",
                "corner.chicane": "chicane",
                "corner.hairpin": "hairpin",
                
                # Review outcomes
                "review.success": "successful",
                "review.overshoot": "overdone",
                "review.no_attempt": "not attempted",
                "review.inconclusive": "inconclusive",
                
                # Safety messages
                "safety.green": "Optimal grip conditions",
                "safety.yellow": "Cautious driving recommended",
                "safety.red": "Dangerous grip conditions - be careful!",
                
                # General coaching
                "coaching.stability_first": "Stability before speed",
                "coaching.consistency": "Consistency is more important than single times",
                "coaching.patience": "Patience - improvement takes time",
                "coaching.focus": "One point at a time",
                
                # Feedback
                "feedback.good_progress": "Good progress",
                "feedback.keep_practicing": "Keep practicing",
                "feedback.excellent": "Excellent",
                "feedback.try_again": "Try again"
            }
    
    def _save_translation_file(self, lang_code: str, translations: Dict[str, str]) -> None:
        """Save translations to file."""
        try:
            file_path = os.path.join(self.base_path, f"{lang_code}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"❌ Error saving translations for {lang_code}: {e}")
    
    def get_text(self, key: str, language: Optional[Language] = None, **kwargs) -> str:
        """
        Get localized text for a key.
        
        Args:
            key: Translation key (dot-separated)
            language: Target language (uses default if None)
            **kwargs: Format parameters for the text
            
        Returns:
            Localized text string
        """
        try:
            lang = language or self.default_language
            lang_code = lang.value
            
            # Get translation
            if lang_code not in self.translations:
                self.logger.warning(f"Language {lang_code} not available")
                lang_code = self.default_language.value
            
            translation = self.translations[lang_code].get(key)
            
            if translation is None:
                # Fallback to default language
                if lang_code != self.default_language.value:
                    default_lang_code = self.default_language.value
                    translation = self.translations[default_lang_code].get(key)
                
                # Ultimate fallback
                if translation is None:
                    self.logger.warning(f"Translation not found for key: {key}")
                    return key.split('.')[-1]  # Return last part of key
            
            # Apply formatting
            if kwargs:
                try:
                    translation = translation.format(**kwargs)
                except Exception as e:
                    self.logger.warning(f"Error formatting translation '{key}': {e}")
            
            return translation
            
        except Exception as e:
            self.logger.error(f"❌ Error getting text for key '{key}': {e}")
            return key.split('.')[-1]
    
    def format_time(self, time_ms: float, language: Optional[Language] = None) -> str:
        """
        Format time value according to language conventions.
        Note: For coaching messages, this should NOT be used as per specification.
        This is for internal/system use only.
        
        Args:
            time_ms: Time in milliseconds
            language: Target language
            
        Returns:
            Formatted time string
        """
        lang = language or self.default_language
        
        if time_ms < 1000:
            # Milliseconds
            if lang == Language.GERMAN:
                return f"{time_ms:.0f} ms"
            else:
                return f"{time_ms:.0f} ms"
        else:
            # Seconds
            seconds = time_ms / 1000
            if lang == Language.GERMAN:
                return f"{seconds:.2f} s"
            else:
                return f"{seconds:.2f} s"
    
    def format_percentage(self, value: float, language: Optional[Language] = None) -> str:
        """
        Format percentage value according to language conventions.
        
        Args:
            value: Percentage value (0.0-1.0)
            language: Target language
            
        Returns:
            Formatted percentage string
        """
        lang = language or self.default_language
        percentage = value * 100
        
        if lang == Language.GERMAN:
            return f"{percentage:.1f}%"
        else:
            return f"{percentage:.1f}%"
    
    def get_language_name(self, language: Language, in_language: Optional[Language] = None) -> str:
        """
        Get the name of a language in the specified language.
        
        Args:
            language: Language to get name for
            in_language: Language to show name in
            
        Returns:
            Language name string
        """
        target_lang = in_language or self.default_language
        
        names = {
            (Language.GERMAN, Language.GERMAN): "Deutsch",
            (Language.GERMAN, Language.ENGLISH): "German",
            (Language.ENGLISH, Language.GERMAN): "Englisch",
            (Language.ENGLISH, Language.ENGLISH): "English"
        }
        
        return names.get((language, target_lang), language.value)
    
    async def reload_translations(self) -> bool:
        """
        Reload translations from files.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.translations = self._load_translations()
            self.logger.info("✅ Translations reloaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error reloading translations: {e}")
            return False
    
    def get_available_languages(self) -> List[Language]:
        """Get list of available languages."""
        return list(Language)
    
    def get_translation_coverage(self) -> Dict[str, Dict[str, Any]]:
        """Get translation coverage statistics."""
        coverage = {}
        
        # Get all unique keys across all languages
        all_keys = set()
        for lang_translations in self.translations.values():
            all_keys.update(lang_translations.keys())
        
        # Calculate coverage for each language
        for lang_code, translations in self.translations.items():
            coverage[lang_code] = {
                "total_keys": len(all_keys),
                "translated_keys": len(translations),
                "coverage_percentage": len(translations) / len(all_keys) * 100 if all_keys else 0,
                "missing_keys": list(all_keys - set(translations.keys()))
            }
        
        return coverage
    
    def add_translation(self, key: str, text: str, language: Language) -> bool:
        """
        Add or update a translation.
        
        Args:
            key: Translation key
            text: Translation text
            language: Target language
            
        Returns:
            True if successful, False otherwise
        """
        try:
            lang_code = language.value
            
            if lang_code not in self.translations:
                self.translations[lang_code] = {}
            
            self.translations[lang_code][key] = text
            self._save_translation_file(lang_code, self.translations[lang_code])
            
            self.logger.info(f"✅ Added translation for '{key}' in {lang_code}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error adding translation: {e}")
            return False
    
    def get_localization_status(self) -> Dict[str, Any]:
        """Get status of localization service."""
        coverage = self.get_translation_coverage()
        
        return {
            "default_language": self.default_language.value,
            "available_languages": [lang.value for lang in self.get_available_languages()],
            "base_path": self.base_path,
            "translation_coverage": coverage,
            "total_translation_files": len(self.translations)
        }