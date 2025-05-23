import logging
from PySide6.QtWidgets import QDialog, QApplication
from PySide6.QtCore import QEvent

class BaseDialog(QDialog):
    """
    Base class for all dialogs in the application, providing common functionality.
    Overrides the tr method to use JSON-based translations when available.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def tr(self, text):
        """
        Translate text using JSON-based translations if available.
        Falls back to Qt's tr method if not.
        
        Args:
            text: The text to translate
            
        Returns:
            str: The translated text
        """
        # Try to get translations from app properties
        app = QApplication.instance()
        if app:
            translations = app.property("json_translations")
            if translations and isinstance(translations, dict) and text in translations:
                return translations[text]
        
        # Fall back to Qt's tr method
        return super().tr(text)
        
    def changeEvent(self, event):
        """Handle change events, particularly language changes."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)
        
    def retranslateUi(self):
        """
        Update all UI text elements to the current language.
        This should be implemented by subclasses.
        """
        self.logger.debug("Base retranslateUi called. Subclasses should override this method.") 