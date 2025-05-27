"""
Video Tools Component - Simple interface for video-related tools.
"""
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

class VideoToolCard(QFrame):
    """Individual video tool card."""
    
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
            VideoToolCard {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
            VideoToolCard:hover {
                border-color: #007bff;
                background-color: #e9ecef;
            }
        """)
        
        self.setFixedHeight(100)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.tool_name)
        super().mousePressEvent(event)

class VideoTools(QWidget):
    """Video tools component."""
    
    # Signals for different tools
    highlight_reel_requested = Signal()
    story_assistant_requested = Signal()
    thumbnail_selector_requested = Signal()
    veo_generator_requested = Signal()
    audio_overlay_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tool_cards = []
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the video tools UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Title
        self.title_label = QLabel(self.tr("Video Tools"))
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #000000; margin-bottom: 10px;")
        layout.addWidget(self.title_label)
        
        # Tools
        tools_data = [
            {
                'title': self.tr('Highlight Reel Generator'),
                'description': self.tr('Create highlight reels from longer videos'),
                'icon': '🎬',
                'tool_name': 'highlight_reel'
            },
            {
                'title': self.tr('Story Assistant'),
                'description': self.tr('AI-powered story creation and editing'),
                'icon': '📖',
                'tool_name': 'story_assistant'
            },
            {
                'title': self.tr('Thumbnail Selector'),
                'description': self.tr('Choose the best thumbnail for your reels'),
                'icon': '🖼️',
                'tool_name': 'thumbnail_selector'
            },
            {
                'title': self.tr('Veo Video Generator'),
                'description': self.tr('Generate videos using Veo AI'),
                'icon': '✨',
                'tool_name': 'veo_generator'
            },
            {
                'title': self.tr('Audio Overlay'),
                'description': self.tr('Add audio tracks to your videos'),
                'icon': '🎵',
                'tool_name': 'audio_overlay'
            }
        ]
        
        for tool_data in tools_data:
            card = VideoToolCard(
                title=tool_data['title'],
                description=tool_data['description'],
                icon=tool_data['icon'],
                tool_name=tool_data['tool_name']
            )
            card.clicked.connect(self._on_tool_clicked)
            layout.addWidget(card)
            self.tool_cards.append(card)
            
        layout.addStretch()
        
    def _on_tool_clicked(self, tool_name: str):
        """Handle tool click."""
        self.logger.info(f"Video tool clicked: {tool_name}")
        
        if tool_name == 'highlight_reel':
            self.highlight_reel_requested.emit()
        elif tool_name == 'story_assistant':
            self.story_assistant_requested.emit()
        elif tool_name == 'thumbnail_selector':
            self.thumbnail_selector_requested.emit()
        elif tool_name == 'veo_generator':
            self.veo_generator_requested.emit()
        elif tool_name == 'audio_overlay':
            self.audio_overlay_requested.emit()
            
    def retranslateUi(self):
        """Update UI text for internationalization."""
        if hasattr(self, 'title_label'):
            self.title_label.setText(self.tr("Video Tools"))
        
        # Recreate the tools with updated translations
        self._setup_ui() 