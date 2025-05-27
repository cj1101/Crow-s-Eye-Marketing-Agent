"""
Social Media Tools Component - Simple interface for social media tools.
"""
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

class SocialToolCard(QFrame):
    """Individual social media tool card."""
    
    clicked = Signal(str)  # tool_name
    
    def __init__(self, title: str, description: str, icon: str, tool_name: str):
        super().__init__()
        self.tool_name = tool_name
        
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Icon and title
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #000000;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #666666; font-size: 12px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Styling
        self.setStyleSheet("""
            SocialToolCard {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
            SocialToolCard:hover {
                border-color: #17a2b8;
                background-color: #e9ecef;
            }
        """)
        
        self.setFixedHeight(100)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.tool_name)
        super().mousePressEvent(event)

class SocialTools(QWidget):
    """Social media tools component."""
    
    # Signals for different tools
    connect_accounts_requested = Signal()
    custom_upload_requested = Signal()
    post_current_media_requested = Signal()
    knowledge_base_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the social media tools UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Social Media Tools")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #000000; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Tools
        tools_data = [
            {
                'title': 'Connect Accounts',
                'description': 'Connect to Instagram, Facebook, and other social platforms',
                'icon': '🔗',
                'tool_name': 'connect_accounts'
            },
            {
                'title': 'Custom Media Upload',
                'description': 'Upload custom media files to platforms',
                'icon': '📤',
                'tool_name': 'custom_upload'
            },
            {
                'title': 'Post Current Media',
                'description': 'Post the currently loaded media to platforms',
                'icon': '📱',
                'tool_name': 'post_current_media'
            },
            {
                'title': 'Knowledge Base',
                'description': 'Customer support knowledge base system',
                'icon': '💬',
                'tool_name': 'knowledge_base'
            }
        ]
        
        for tool_data in tools_data:
            card = SocialToolCard(
                title=tool_data['title'],
                description=tool_data['description'],
                icon=tool_data['icon'],
                tool_name=tool_data['tool_name']
            )
            card.clicked.connect(self._on_tool_clicked)
            layout.addWidget(card)
            
        layout.addStretch()
        
    def _on_tool_clicked(self, tool_name: str):
        """Handle tool click."""
        self.logger.info(f"Social tool clicked: {tool_name}")
        
        if tool_name == 'connect_accounts':
            self.connect_accounts_requested.emit()
        elif tool_name == 'custom_upload':
            self.custom_upload_requested.emit()
        elif tool_name == 'post_current_media':
            self.post_current_media_requested.emit()
        elif tool_name == 'knowledge_base':
            self.knowledge_base_requested.emit() 