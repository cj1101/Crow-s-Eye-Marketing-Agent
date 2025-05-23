"""
Status bar widget for the main application window.
"""
import logging
from PySide6.QtWidgets import QStatusBar, QLabel, QProgressBar, QApplication
from PySide6.QtCore import Qt, QEvent

class StatusBarWidget(QStatusBar):
    """Custom status bar with additional features."""
    
    def __init__(self, parent=None):
        """Initialize the status bar widget."""
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Setup UI elements
        self._setup_ui()
        self.retranslateUi() # Initial translation
        
    def _setup_ui(self):
        """Set up the status bar UI components."""
        # Status label
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.addWidget(self.status_label, 1)  # Stretch factor 1
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFixedWidth(150)
        self.progress_bar.setVisible(False)
        self.addPermanentWidget(self.progress_bar)
        
        # Version label - text is set in retranslateUi or by set_version
        self.version_label = QLabel()
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.addPermanentWidget(self.version_label)
        
    def showMessage(self, message, timeout=0):
        """
        Show a message in the status bar.
        
        Args:
            message: Message to display
            timeout: Timeout in milliseconds (0 = no timeout)
        """
        super().showMessage(message, timeout)
        self.status_label.setText(message)
        self.logger.debug(f"Status message: {message}")
        
    def set_progress(self, value):
        """
        Set the progress bar value.
        
        Args:
            value: Progress value (0-100)
        """
        if not self.progress_bar.isVisible():
            self.progress_bar.setVisible(True)
            
        self.progress_bar.setValue(value)
        
        # Hide progress bar when complete
        if value >= 100:
            self.progress_bar.setVisible(False)
            
    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        # If status_label has a default text that should be translated, set it here.
        # For example, if it was initialized with "Ready":
        # current_text = self.status_label.text()
        # if current_text == "Ready" or not current_text: # Assuming "Ready" is an English key
        #    self.status_label.setText(self.tr("Ready"))
        # Most messages are set via showMessage, which should receive pre-translated strings.

        # For version label, if it has a stored version number, re-apply with tr().
        # Let's assume we have a way to get the raw version number if needed for retranslation.
        # For simplicity, if _current_version is stored: 
        if hasattr(self, '_current_raw_version') and self._current_raw_version:
            self.version_label.setText(self.tr("v{version}").format(version=self._current_raw_version))
        else: # Default initial state
             self.version_label.setText(self.tr("v1.0.0")) # Default version text

    # Override set_version to store the raw version for retranslation
    def set_version(self, version_str):
        """
        Set the version text and store raw version for retranslation.
        
        Args:
            version_str: Version string to display (e.g., "1.0.0")
        """
        self._current_raw_version = version_str # Store raw version
        self.version_label.setText(self.tr("v{version}").format(version=version_str))

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