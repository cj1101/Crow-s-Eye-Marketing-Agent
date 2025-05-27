"""
Tools Container - Combines all tool components into a tabbed interface.
"""
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QScrollArea
)
from PySide6.QtCore import Qt, Signal

from .video_tools import VideoTools
from .analytics_tools import AnalyticsTools
from .social_tools import SocialTools

class ToolsContainer(QWidget):
    """Container for all tools organized in tabs."""
    
    # Video tool signals
    highlight_reel_requested = Signal()
    story_assistant_requested = Signal()
    thumbnail_selector_requested = Signal()
    veo_generator_requested = Signal()
    audio_overlay_requested = Signal()
    
    # Analytics tool signals
    performance_dashboard_requested = Signal()
    export_data_requested = Signal()
    compliance_requested = Signal()
    
    # Social tool signals
    connect_accounts_requested = Signal()
    custom_upload_requested = Signal()
    post_current_media_requested = Signal()
    knowledge_base_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Set up the tools container UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                color: #000000;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #cccccc;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #000000;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
        """)
        
        # Create tool components
        self._create_video_tools_tab()
        self._create_social_tools_tab()
        self._create_analytics_tools_tab()
        
        layout.addWidget(self.tab_widget)
        
    def _create_video_tools_tab(self):
        """Create the video tools tab."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        self.video_tools = VideoTools()
        scroll_area.setWidget(self.video_tools)
        
        self.tab_widget.addTab(scroll_area, "🎬 Video")
        
    def _create_social_tools_tab(self):
        """Create the social media tools tab."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        self.social_tools = SocialTools()
        scroll_area.setWidget(self.social_tools)
        
        self.tab_widget.addTab(scroll_area, "📱 Social")
        
    def _create_analytics_tools_tab(self):
        """Create the analytics tools tab."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        self.analytics_tools = AnalyticsTools()
        scroll_area.setWidget(self.analytics_tools)
        
        self.tab_widget.addTab(scroll_area, "📊 Analytics")
        
    def _connect_signals(self):
        """Connect signals from tool components."""
        # Video tools
        self.video_tools.highlight_reel_requested.connect(self.highlight_reel_requested.emit)
        self.video_tools.story_assistant_requested.connect(self.story_assistant_requested.emit)
        self.video_tools.thumbnail_selector_requested.connect(self.thumbnail_selector_requested.emit)
        self.video_tools.veo_generator_requested.connect(self.veo_generator_requested.emit)
        self.video_tools.audio_overlay_requested.connect(self.audio_overlay_requested.emit)
        
        # Social tools
        self.social_tools.connect_accounts_requested.connect(self.connect_accounts_requested.emit)
        self.social_tools.custom_upload_requested.connect(self.custom_upload_requested.emit)
        self.social_tools.post_current_media_requested.connect(self.post_current_media_requested.emit)
        self.social_tools.knowledge_base_requested.connect(self.knowledge_base_requested.emit)
        
        # Analytics tools
        self.analytics_tools.performance_dashboard_requested.connect(self.performance_dashboard_requested.emit)
        self.analytics_tools.export_data_requested.connect(self.export_data_requested.emit)
        self.analytics_tools.compliance_requested.connect(self.compliance_requested.emit) 