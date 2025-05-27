"""
Campaign Manager component - Simple campaign management interface.
"""
import logging
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

class CampaignCard(QFrame):
    """Individual campaign card widget."""
    
    clicked = Signal(dict)  # campaign_data
    edit_requested = Signal(dict)  # campaign_data
    delete_requested = Signal(dict)  # campaign_data
    
    def __init__(self, campaign_data: Dict[str, Any]):
        super().__init__()
        self.campaign_data = campaign_data
        
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the campaign card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header with name and status
        header_layout = QHBoxLayout()
        
        # Campaign name
        name_label = QLabel(self.campaign_data.get('name', 'Unnamed Campaign'))
        name_font = QFont()
        name_font.setPointSize(14)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: #000000;")
        header_layout.addWidget(name_label)
        
        header_layout.addStretch()
        
        # Status indicator
        is_active = self.campaign_data.get('active', False)
        status_label = QLabel("🟢 Active" if is_active else "⚪ Inactive")
        status_label.setStyleSheet("font-size: 12px; color: #666666;")
        header_layout.addWidget(status_label)
        
        layout.addLayout(header_layout)
        
        # Campaign details
        details_text = f"Posts: {self.campaign_data.get('post_count', 0)}"
        if 'schedule' in self.campaign_data:
            details_text += f" | Schedule: {self.campaign_data['schedule']}"
        
        details_label = QLabel(details_text)
        details_label.setStyleSheet("color: #666666; font-size: 12px;")
        layout.addWidget(details_label)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        edit_btn = QPushButton("Edit")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.campaign_data))
        buttons_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.campaign_data))
        buttons_layout.addWidget(delete_btn)
        
        layout.addLayout(buttons_layout)
        
        # Styling
        active_color = "#e8f5e8" if is_active else "#f8f9fa"
        border_color = "#28a745" if is_active else "#dee2e6"
        
        self.setStyleSheet(f"""
            CampaignCard {{
                background-color: {active_color};
                border: 2px solid {border_color};
                border-radius: 8px;
            }}
            CampaignCard:hover {{
                border-color: #007bff;
            }}
        """)
        
        self.setFixedHeight(120)
        
    def mousePressEvent(self, event):
        """Handle mouse press to emit clicked signal."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.campaign_data)
        super().mousePressEvent(event)

class CampaignManager(QWidget):
    """Simple campaign manager widget."""
    
    # Signals
    campaign_selected = Signal(dict)  # campaign_data
    add_campaign_requested = Signal()
    edit_campaign_requested = Signal(dict)  # campaign_data
    delete_campaign_requested = Signal(dict)  # campaign_data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.campaigns = []  # List of campaign data
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the campaign manager UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        self._create_header(layout)
        
        # Campaigns list
        self._create_campaigns_list(layout)
        
        # Apply styling
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
            QLabel {
                color: #000000;
            }
        """)
        
    def _create_header(self, main_layout: QVBoxLayout):
        """Create the header section."""
        header_layout = QHBoxLayout()
        
        # Title
        self.title_label = QLabel(self.tr("Campaign Manager"))
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #000000;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Add Campaign button
        self.add_btn = QPushButton(self.tr("+ Add Campaign"))
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.add_btn.clicked.connect(self.add_campaign_requested.emit)
        header_layout.addWidget(self.add_btn)
        
        main_layout.addLayout(header_layout)
        
        # Subtitle
        self.subtitle_label = QLabel(self.tr("Manage your posting campaigns and schedules"))
        self.subtitle_label.setStyleSheet("color: #666666; font-size: 14px;")
        main_layout.addWidget(self.subtitle_label)
        
    def _create_campaigns_list(self, main_layout: QVBoxLayout):
        """Create the campaigns list area."""
        # Scroll area for campaigns
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        # Container for campaigns
        self.campaigns_container = QWidget()
        self.campaigns_layout = QVBoxLayout(self.campaigns_container)
        self.campaigns_layout.setSpacing(10)
        self.campaigns_layout.setContentsMargins(0, 0, 0, 0)
        
        # Empty state
        self._show_empty_state()
        
        scroll_area.setWidget(self.campaigns_container)
        main_layout.addWidget(scroll_area, 1)  # Give it stretch factor
        
    def _show_empty_state(self):
        """Show empty state when no campaigns exist."""
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setContentsMargins(40, 40, 40, 40)
        
        # Icon
        icon_label = QLabel("📅")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        empty_layout.addWidget(icon_label)
        
        # Text
        text_label = QLabel(self.tr("No campaigns yet"))
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet("color: #666666; font-size: 16px; margin: 10px;")
        empty_layout.addWidget(text_label)
        
        # Description
        desc_label = QLabel(self.tr("Create your first campaign to start organizing your posts"))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #999999; font-size: 12px;")
        empty_layout.addWidget(desc_label)
        
        self.campaigns_layout.addWidget(empty_widget)
        
    def add_campaign(self, campaign_data: Dict[str, Any]):
        """Add a new campaign to the list."""
        self.campaigns.append(campaign_data)
        self._refresh_campaigns_display()
        
    def remove_campaign(self, campaign_data: Dict[str, Any]):
        """Remove a campaign from the list."""
        if campaign_data in self.campaigns:
            self.campaigns.remove(campaign_data)
            self._refresh_campaigns_display()
            
    def update_campaign(self, old_data: Dict[str, Any], new_data: Dict[str, Any]):
        """Update an existing campaign."""
        try:
            index = self.campaigns.index(old_data)
            self.campaigns[index] = new_data
            self._refresh_campaigns_display()
        except ValueError:
            self.logger.warning("Campaign not found for update")
            
    def _refresh_campaigns_display(self):
        """Refresh the campaigns display."""
        # Clear existing widgets
        while self.campaigns_layout.count():
            child = self.campaigns_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        if not self.campaigns:
            self._show_empty_state()
        else:
            # Add campaign cards
            for campaign_data in self.campaigns:
                card = CampaignCard(campaign_data)
                card.clicked.connect(self.campaign_selected.emit)
                card.edit_requested.connect(self.edit_campaign_requested.emit)
                card.delete_requested.connect(self.delete_campaign_requested.emit)
                self.campaigns_layout.addWidget(card)
                
            # Add stretch at the end
            self.campaigns_layout.addStretch()
            
    def set_campaigns(self, campaigns: List[Dict[str, Any]]):
        """Set the campaigns list."""
        self.campaigns = campaigns
        self._refresh_campaigns_display()
        
    def retranslateUi(self):
        """Update UI text for internationalization."""
        if hasattr(self, 'title_label'):
            self.title_label.setText(self.tr("Campaign Manager"))
        if hasattr(self, 'add_btn'):
            self.add_btn.setText(self.tr("+ Add Campaign"))
        if hasattr(self, 'subtitle_label'):
            self.subtitle_label.setText(self.tr("Manage your posting campaigns and schedules")) 