"""
Internationalization (i18n) module for the application.
Provides translation support with signal-based language switching.
"""

import json
import logging
import os
from typing import Dict, Any
from PySide6.QtCore import QObject, Signal

class I18N(QObject):
    """
    Internationalization class implementing signal-based singleton pattern.
    Handles loading and managing translations from JSON files.
    """
    
    # Signal emitted when language changes
    language_changed = Signal(str)  # Emits the new language code
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the I18N system."""
        if hasattr(self, '_initialized'):
            return
        
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Current language and translations
        self.current_language = "en"
        self.translations: Dict[str, Any] = {}
        self.available_languages = [
            "en", "es", "zh", "hi", "fr", 
            "ar", "pt", "ru", "ja", "de"
        ]
        
        # Get project root directory (go up from src/ to project root)
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.translations_dir = os.path.join(self.project_root, "translations")
        
        # Load default language
        self._load_language("en")
        self._initialized = True
        
        self.logger.info("I18N system initialized with default language: en")
    
    def t(self, key: str, **kwargs) -> str:
        """
        Translate a key to the current language.
        
        Args:
            key: The translation key
            **kwargs: Format arguments for string formatting
            
        Returns:
            str: The translated string, or the key if translation not found
        """
        if not key:
            return ""
        
        # Get translation from current translations
        translated = self.translations.get(key, key)
        
        # Apply string formatting if kwargs provided
        if kwargs:
            try:
                translated = translated.format(**kwargs)
            except (KeyError, ValueError) as e:
                self.logger.warning(f"String formatting failed for key '{key}': {e}")
                # Return unformatted string if formatting fails
        
        return translated
    
    def switch(self, language_code: str) -> bool:
        """
        Switch to a different language.
        
        Args:
            language_code: The language code to switch to (e.g., 'en', 'es')
            
        Returns:
            bool: True if language was switched successfully, False otherwise
        """
        if language_code not in self.available_languages:
            self.logger.warning(f"Language '{language_code}' is not available")
            return False
        
        if language_code == self.current_language:
            self.logger.debug(f"Already using language: {language_code}")
            return True
        
        if self._load_language(language_code):
            old_language = self.current_language
            self.current_language = language_code
            self.logger.info(f"Language switched from '{old_language}' to '{language_code}'")
            
            # Emit signal for UI updates
            self.language_changed.emit(language_code)
            return True
        
        return False
    
    def _load_language(self, language_code: str) -> bool:
        """
        Load translations for a specific language.
        
        Args:
            language_code: The language code to load
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        translations_file = os.path.join(self.translations_dir, f"{language_code}.json")
        
        if not os.path.exists(translations_file):
            self.logger.error(f"Translation file not found: {translations_file}")
            return False
        
        try:
            with open(translations_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            
            self.logger.debug(f"Loaded {len(self.translations)} translations for '{language_code}'")
            return True
            
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Failed to load translations for '{language_code}': {e}")
            return False
    
    def get_current_language(self) -> str:
        """
        Get the current language code.
        
        Returns:
            str: The current language code
        """
        return self.current_language
    
    def get_available_languages(self) -> list:
        """
        Get list of available language codes.
        
        Returns:
            list: List of available language codes
        """
        return self.available_languages.copy()
    
    def reload_translations(self) -> bool:
        """
        Reload translations for the current language.
        Useful for development or if translation files are updated.
        
        Returns:
            bool: True if reloaded successfully, False otherwise
        """
        return self._load_language(self.current_language)


# Global instance - can be imported directly
i18n = I18N() 