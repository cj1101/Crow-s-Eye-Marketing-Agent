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

from ...features.subscription.access_control import Feature, access_control
from ...utils.subscription_utils import (
    check_feature_access_with_dialog, 
    check_usage_limit_with_dialog,
    create_pro_feature_button_style
)

class VideoToolCard(QFrame):
    """Individual video tool card."""
    
    clicked = Signal(str)  # tool_name
    
    def __init__(self, title: str, description: str, icon: str, tool_name: str, is_pro_feature: bool = False):
        super().__init__()
        self.tool_name = tool_name
        self.is_pro_feature = is_pro_feature
        
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
        
        # Pro badge for pro features
        if is_pro_feature:
            pro_badge = QLabel("PRO")
            pro_badge.setStyleSheet("""
                QLabel {
                    background-color: #FFD700;
                    color: #8B4513;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
            header_layout.addWidget(pro_badge)
        
        layout.addLayout(header_layout)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #666666; font-size: 12px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Update styling based on feature availability
        self._update_styling()
        
        self.setFixedHeight(100)
    
    def _update_styling(self):
        """Update styling based on feature availability."""
        if self.is_pro_feature:
            # Check if user has access to this pro feature
            feature_map = {
                'highlight_reel': Feature.HIGHLIGHT_REEL_GENERATOR,
                'story_assistant': Feature.STORY_ASSISTANT,
                'veo_generator': Feature.VEO_VIDEO_GENERATOR,
                'audio_overlay': Feature.AUDIO_IMPORTER
            }
            
            feature = feature_map.get(self.tool_name)
            has_access = feature and access_control.has_feature_access(feature)
            
            if has_access:
                # User has Pro access
                self.setStyleSheet("""
                    VideoToolCard {
                        background-color: #f8f9fa;
                        border: 1px solid #dee2e6;
                        border-radius: 6px;
                    }
                    VideoToolCard:hover {
                        border-color: #28a745;
                        background-color: #e9ecef;
                    }
                """)
            else:
                # User needs to upgrade
                self.setStyleSheet("""
                    VideoToolCard {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                            stop:0 #FFF8DC, stop:1 #F0E68C);
                        border: 2px solid #DAA520;
                        border-radius: 6px;
                    }
                    VideoToolCard:hover {
                        border-color: #FFD700;
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                            stop:0 #FFFFE0, stop:1 #F5DEB3);
                    }
                """)
        else:
            # Free feature
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
                'description': self.tr('Create highlight reels from longer videos (Pro)'),
                'icon': '🎬',
                'tool_name': 'highlight_reel',
                'is_pro': True
            },
            {
                'title': self.tr('Story Assistant'),
                'description': self.tr('AI-powered story creation and editing (Pro)'),
                'icon': '📖',
                'tool_name': 'story_assistant',
                'is_pro': True
            },
            {
                'title': self.tr('Thumbnail Selector'),
                'description': self.tr('Choose the best thumbnail for your reels'),
                'icon': '🖼️',
                'tool_name': 'thumbnail_selector',
                'is_pro': False
            },
            {
                'title': self.tr('Veo Video Generator'),
                'description': self.tr('Generate videos using Veo AI (Pro)'),
                'icon': '✨',
                'tool_name': 'veo_generator',
                'is_pro': True
            },
            {
                'title': self.tr('Audio Overlay'),
                'description': self.tr('Add audio tracks to your videos (Pro)'),
                'icon': '🎵',
                'tool_name': 'audio_overlay',
                'is_pro': True
            }
        ]
        
        for tool_data in tools_data:
            card = VideoToolCard(
                title=tool_data['title'],
                description=tool_data['description'],
                icon=tool_data['icon'],
                tool_name=tool_data['tool_name'],
                is_pro_feature=tool_data['is_pro']
            )
            card.clicked.connect(self._on_tool_clicked)
            layout.addWidget(card)
            self.tool_cards.append(card)
            
        layout.addStretch()
        
    def _on_tool_clicked(self, tool_name: str):
        """Handle tool click with subscription access control."""
        self.logger.info(f"Video tool clicked: {tool_name}")
        
        # Define feature requirements
        feature_map = {
            'highlight_reel': Feature.HIGHLIGHT_REEL_GENERATOR,
            'story_assistant': Feature.STORY_ASSISTANT,
            'veo_generator': Feature.VEO_VIDEO_GENERATOR,
            'audio_overlay': Feature.AUDIO_IMPORTER
        }
        
        # Check feature access for Pro features
        required_feature = feature_map.get(tool_name)
        if required_feature:
            if not check_feature_access_with_dialog(required_feature, self):
                return  # Access denied, dialog already shown
        
        # Check usage limits for video generation features
        if tool_name in ['highlight_reel', 'veo_generator']:
            if not check_usage_limit_with_dialog('videos', 1, self):
                return  # Usage limit exceeded, dialog already shown
        
        # Emit appropriate signal
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
    
    def refresh_access_status(self):
        """Refresh the access status of all tool cards."""
        for card in self.tool_cards:
            if hasattr(card, '_update_styling'):
                card._update_styling()
            
    def retranslateUi(self):
        """Update UI text for internationalization."""
        if hasattr(self, 'title_label'):
            self.title_label.setText(self.tr("Video Tools"))
        
        # Recreate the tools with updated translations
        self._setup_ui() 