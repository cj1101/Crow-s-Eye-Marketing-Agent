import logging
from PySide6.QtWidgets import QDialog, QApplication
from PySide6.QtCore import QEvent

class BaseDialog(QDialog):
    """
    Base class for all dialogs in the application, providing common functionality.
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