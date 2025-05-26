"""
Button section component for the main application window.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, # QPushButton, removed
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QEvent

from .adjustable_button import AdjustableButton # Added import
from ..base_widget import BaseWidget

class ButtonSection(BaseWidget):
    """Button section for the application."""
    
    # Signals for button actions
    generate_clicked = Signal()
    post_clicked = Signal()
    cancel_clicked = Signal()
    library_clicked = Signal()
    knowledge_clicked = Signal()
    add_to_library_clicked = Signal()
    
    def __init__(self, parent=None):
        """Initialize the button section component."""
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Setup UI
        self._setup_ui()
        self.retranslateUi() # Initial translation
        
    def _setup_ui(self):
        """Set up the button section UI components."""
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Generate button
        self.generate_button = AdjustableButton() # Changed to AdjustableButton
        self.generate_button.setObjectName("generate_button")
        self.generate_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Preferred
        )
        self.generate_button.clicked.connect(self.generate_clicked)
        layout.addWidget(self.generate_button)
        
        # Finish Post button (renamed from Add to Library)
        self.add_to_library_button = AdjustableButton() # Changed to AdjustableButton
        self.add_to_library_button.setObjectName("finish_post_button")
        self.add_to_library_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Preferred
        )
        self.add_to_library_button.clicked.connect(self.add_to_library_clicked)
        layout.addWidget(self.add_to_library_button)
        
        # Post button
        self.post_button = AdjustableButton() # Changed to AdjustableButton
        self.post_button.setObjectName("post_button")
        self.post_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Preferred
        )
        self.post_button.clicked.connect(self.post_clicked)
        layout.addWidget(self.post_button)
        
        # Cancel button
        self.cancel_button = AdjustableButton() # Changed to AdjustableButton
        self.cancel_button.setObjectName("cancel_button")
        self.cancel_button.setSizePolicy(
            QSizePolicy.Policy.Minimum, 
            QSizePolicy.Policy.Preferred
        )
        self.cancel_button.clicked.connect(self.cancel_clicked)
        layout.addWidget(self.cancel_button)
        
        # Library button
        self.library_button = AdjustableButton() # Changed to AdjustableButton
        self.library_button.setObjectName("library_button")
        self.library_button.setSizePolicy(
            QSizePolicy.Policy.Minimum, 
            QSizePolicy.Policy.Preferred
        )
        self.library_button.clicked.connect(self.library_clicked)
        layout.addWidget(self.library_button)
        
        # Knowledge button
        self.knowledge_button = AdjustableButton() # Changed to AdjustableButton
        self.knowledge_button.setObjectName("knowledge_button")
        self.knowledge_button.setSizePolicy(
            QSizePolicy.Policy.Minimum, 
            QSizePolicy.Policy.Preferred
        )
        self.knowledge_button.clicked.connect(self.knowledge_clicked)
        layout.addWidget(self.knowledge_button)
        
        # Set initial button states
        self.cancel_button.setEnabled(False)
        self.add_to_library_button.setEnabled(True)
        
    def set_generating(self, is_generating: bool):
        """
        Set the buttons to generating state.
        
        Args:
            is_generating: Whether the system is currently generating content
        """
        self.generate_button.setEnabled(not is_generating)
        self.add_to_library_button.setEnabled(not is_generating)
        self.post_button.setEnabled(not is_generating)
        self.cancel_button.setEnabled(is_generating)
        self.library_button.setEnabled(not is_generating)
        self.knowledge_button.setEnabled(not is_generating)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.generate_button.setText(self.tr("Generate"))
        self.add_to_library_button.setText(self.tr("Finish Post"))
        self.post_button.setText(self.tr("Post to Social Media"))
        self.cancel_button.setText(self.tr("Cancel"))
        self.library_button.setText(self.tr("Library"))
        self.knowledge_button.setText(self.tr("Knowledge Base")) 