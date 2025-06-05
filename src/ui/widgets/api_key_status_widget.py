"""
API Key Status Widget - Shows users whether they're using shared or personal API keys.
"""
import logging
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ...config.shared_api_keys import is_using_shared_key


class APIKeyStatusWidget(QWidget):
    """Widget to display API key status and allow users to understand their usage."""
    
    # Signal emitted when user wants to learn about API keys
    learn_more_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_ui()
        self._update_status()
    
    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Status icon and text
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Learn more button
        self.learn_more_btn = QPushButton("Learn More")
        self.learn_more_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #007bff;
                border: 1px solid #007bff;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #007bff;
                color: white;
            }
        """)
        self.learn_more_btn.clicked.connect(self.learn_more_requested.emit)
        layout.addWidget(self.learn_more_btn)
        
        # Style the widget
        self.setStyleSheet("""
            APIKeyStatusWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin: 5px;
            }
        """)
        
        self.setMaximumHeight(40)
    
    def _update_status(self):
        """Update the status display based on current API key usage."""
        using_shared_gemini = is_using_shared_key("gemini")
        using_shared_google = is_using_shared_key("google")
        
        if using_shared_gemini and using_shared_google:
            # Using all shared keys
            self.status_label.setText("🔑 Using shared API keys - Ready to use with no setup required!")
            self.setStyleSheet("""
                APIKeyStatusWidget {
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 6px;
                    margin: 5px;
                }
            """)
        elif not using_shared_gemini and not using_shared_google:
            # Using all personal keys
            self.status_label.setText("🔐 Using your personal API keys - Full control and billing")
            self.setStyleSheet("""
                APIKeyStatusWidget {
                    background-color: #cce5ff;
                    border: 1px solid #99d6ff;
                    border-radius: 6px;
                    margin: 5px;
                }
            """)
        else:
            # Mixed usage
            shared_services = []
            personal_services = []
            
            if using_shared_gemini:
                shared_services.append("Gemini AI")
            else:
                personal_services.append("Gemini AI")
                
            if using_shared_google:
                shared_services.append("Veo Video")
            else:
                personal_services.append("Veo Video")
            
            shared_text = ", ".join(shared_services)
            personal_text = ", ".join(personal_services)
            
            self.status_label.setText(f"🔑 Mixed: Shared ({shared_text}) | Personal ({personal_text})")
            self.setStyleSheet("""
                APIKeyStatusWidget {
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 6px;
                    margin: 5px;
                }
            """)
    
    def refresh_status(self):
        """Refresh the status display (call this if API keys change)."""
        self._update_status() 