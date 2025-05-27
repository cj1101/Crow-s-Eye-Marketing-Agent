import logging
from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtCore import QEvent

class BaseMainWindow(QMainWindow):
    """
    Base class for all main windows in the application, providing common functionality.
    Overrides the tr method to use the I18N system.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Connect to i18n system
        from ..i18n import i18n
        self.i18n = i18n
        self.i18n.language_changed.connect(self.retranslateUi)
        
    def tr(self, text, **kwargs):
        """
        Translate text using the I18N system.
        
        Args:
            text: The text to translate
            **kwargs: Format arguments for string formatting
            
        Returns:
            str: The translated text
        """
        return self.i18n.t(text, **kwargs)
    
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