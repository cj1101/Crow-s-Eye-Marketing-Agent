"""
Video Editing Services Dialog - Shows available video editing services after video upload.
"""
import logging
from typing import List, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QWidget, QCheckBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..base_dialog import BaseDialog

class VideoServiceTile(QFrame):
    """Individual service tile for video editing services."""
    
    toggled = Signal(str, bool)  # service_id, enabled
    
    def __init__(self, service_id: str, title: str, description: str, icon: str):
        super().__init__()
        self.service_id = service_id
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        
        # Set up layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header with checkbox and icon
        header_layout = QHBoxLayout()
        
        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.toggled.connect(lambda checked: self._on_checkbox_toggled(checked))
        header_layout.addWidget(self.checkbox)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 24px; margin-left: 10px;")
        header_layout.addWidget(icon_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Title
        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666666; font-size: 11px;")
        layout.addWidget(desc_label)
        
        # Set fixed size for consistent grid
        self.setFixedSize(280, 120)
        
        # Set cursor to indicate clickability
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Update styling
        self._update_styling()
        
    def _update_styling(self):
        """Update the styling based on selection state."""
        if self.checkbox.isChecked():
            # Selected state
            self.setStyleSheet("""
                VideoServiceTile {
                    background-color: #e3f2fd;
                    border: 2px solid #007bff;
                    border-radius: 8px;
                }
                VideoServiceTile:hover {
                    background-color: #bbdefb;
                    border-color: #0056b3;
                }
                QLabel {
                    color: #000000;
                    background: transparent;
                    border: none;
                }
                QCheckBox {
                    background: transparent;
                }
            """)
        else:
            # Unselected state
            self.setStyleSheet("""
                VideoServiceTile {
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                }
                VideoServiceTile:hover {
                    background-color: #e9ecef;
                    border-color: #007bff;
                }
                QLabel {
                    color: #000000;
                    background: transparent;
                    border: none;
                }
                QCheckBox {
                    background: transparent;
                }
            """)
    
    def mousePressEvent(self, event):
        """Handle mouse press events to toggle selection."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Toggle the checkbox state
            self.checkbox.setChecked(not self.checkbox.isChecked())
        super().mousePressEvent(event)
    
    def _on_checkbox_toggled(self, checked: bool):
        """Handle checkbox toggle and update styling."""
        self._update_styling()
        self.toggled.emit(self.service_id, checked)
        
    def is_checked(self) -> bool:
        """Check if the service is selected."""
        return self.checkbox.isChecked()
        
    def set_checked(self, checked: bool):
        """Set the checkbox state."""
        self.checkbox.setChecked(checked)
        self._update_styling()

class VideoEditingServicesDialog(BaseDialog):
    """Dialog for selecting video editing services."""
    
    def __init__(self, video_path: str, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.video_path = video_path
        self.selected_services = {}
        
        self.setWindowTitle("Video Editing Services")
        self.setModal(True)
        self.setFixedSize(900, 600)
        
        self._setup_ui()
        self._connect_signals()
        
        self.logger.info("Video Editing Services dialog initialized")
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        self._create_header(layout)
        
        # Services
        self._create_services(layout)
        
        # Buttons
        self._create_buttons(layout)
        
        # Apply styling
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #000000;
            }
        """)
    
    def _create_header(self, main_layout: QVBoxLayout):
        """Create the header section."""
        # Title
        title_label = QLabel("Video Editing Services")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #000000; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Select optional video editing services (you can skip all if you prefer)")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #666666; font-size: 14px; margin-bottom: 20px;")
        main_layout.addWidget(subtitle_label)
    
    def _create_services(self, main_layout: QVBoxLayout):
        """Create the video editing services."""
        # Scroll area for services
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        # Container for services
        services_container = QWidget()
        services_layout = QVBoxLayout(services_container)
        services_layout.setSpacing(15)
        services_layout.setContentsMargins(0, 0, 0, 0)
        
        # Define video editing services
        services = [
            {
                'id': 'color_grading',
                'title': 'Color Grading & Enhancement',
                'description': 'Professional color correction, brightness adjustment, and cinematic color grading for marketing appeal',
                'icon': '🎨'
            },
            {
                'id': 'audio_enhancement',
                'title': 'Audio Enhancement',
                'description': 'Noise reduction, audio leveling, and background music addition for professional sound quality',
                'icon': '🔊'
            },
            {
                'id': 'motion_graphics',
                'title': 'Motion Graphics & Text',
                'description': 'Add animated titles, lower thirds, call-to-action overlays, and brand elements',
                'icon': '✨'
            },
            {
                'id': 'transitions',
                'title': 'Smooth Transitions',
                'description': 'Professional transitions between scenes, fade effects, and seamless cuts for polished look',
                'icon': '🔄'
            },
            {
                'id': 'stabilization',
                'title': 'Video Stabilization',
                'description': 'Remove camera shake and smooth out handheld footage for professional appearance',
                'icon': '📹'
            },
            {
                'id': 'highlight_reel',
                'title': 'Highlight Reel Creation',
                'description': 'Create short highlight clips optimized for social media platforms (15-30 seconds)',
                'icon': '⭐'
            },
            {
                'id': 'social_optimization',
                'title': 'Social Media Optimization',
                'description': 'Format for different platforms (Instagram, TikTok, YouTube) with proper aspect ratios',
                'icon': '📱'
            },
            {
                'id': 'captions_subtitles',
                'title': 'Captions & Subtitles',
                'description': 'Auto-generated captions with styling, perfect for silent viewing on social media',
                'icon': '💬'
            }
        ]
        
        # Create service tiles in a grid
        row_layout = None
        for i, service in enumerate(services):
            if i % 3 == 0:  # New row every 3 services
                if row_layout:
                    services_layout.addLayout(row_layout)
                row_layout = QHBoxLayout()
                row_layout.setSpacing(15)
            
            service_tile = VideoServiceTile(
                service['id'],
                service['title'],
                service['description'],
                service['icon']
            )
            service_tile.toggled.connect(self._on_service_toggled)
            row_layout.addWidget(service_tile)
        
        # Add the last row and stretch
        if row_layout:
            # Fill remaining slots in the last row
            while row_layout.count() % 3 != 0:
                row_layout.addStretch()
            services_layout.addLayout(row_layout)
        
        services_layout.addStretch()
        
        scroll_area.setWidget(services_container)
        main_layout.addWidget(scroll_area, 1)
    
    def _create_buttons(self, main_layout: QVBoxLayout):
        """Create the button section."""
        button_layout = QHBoxLayout()
        
        # Skip all button
        skip_button = QPushButton("Skip All Services")
        skip_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        skip_button.clicked.connect(self.reject)
        button_layout.addWidget(skip_button)
        
        button_layout.addStretch()
        
        # Continue button
        continue_button = QPushButton("Continue with Selected Services")
        continue_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        continue_button.clicked.connect(self.accept)
        button_layout.addWidget(continue_button)
        
        main_layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """Connect internal signals."""
        pass
    
    def _on_service_toggled(self, service_id: str, enabled: bool):
        """Handle service toggle."""
        self.selected_services[service_id] = enabled
        self.logger.info(f"Service {service_id} {'enabled' if enabled else 'disabled'}")
    
    def get_selected_services(self) -> Dict[str, bool]:
        """Get the selected services."""
        return self.selected_services.copy()
    
    def retranslateUi(self):
        """Update UI text for internationalization."""
        # TODO: Implement when i18n is needed
        pass 