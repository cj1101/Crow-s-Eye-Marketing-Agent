import logging
from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtCore import QEvent

class BaseMainWindow(QMainWindow):
    """
    Base class for all main windows in the application, providing common functionality.
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
        if app and hasattr(app, 'json_translations') and app.json_translations:
            # If text exists in translations dictionary, return translated version
            if text in app.json_translations:
                return app.json_translations[text]
        
        # Fall back to Qt's translation method
        return super().tr(text)
    
    def changeEvent(self, event):
        """Handle language change event."""
        if event.type() == QEvent.Type.LanguageChange:
            self.logger.info(f"{self.__class__.__name__} received LanguageChange event.")
            self.retranslateUi()
        super().changeEvent(event)
    
    def retranslateUi(self):
        """
        Update UI text when language changes.
        To be overridden by subclasses.
        """
        pass 