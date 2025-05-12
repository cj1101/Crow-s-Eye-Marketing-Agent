"""
Status bar widget for the main application window.
"""
import logging
from PySide6.QtWidgets import QStatusBar, QLabel, QProgressBar
from PySide6.QtCore import Qt

class StatusBarWidget(QStatusBar):
    """Custom status bar with additional features."""
    
    def __init__(self, parent=None):
        """Initialize the status bar widget."""
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Setup UI elements
        self._setup_ui()
        
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
        
        # Version label
        self.version_label = QLabel("v1.0.0")
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
            
    def set_version(self, version):
        """
        Set the version text.
        
        Args:
            version: Version string to display
        """
        self.version_label.setText(f"v{version}") 