"""
Campaign Manager - Manage social media campaigns and post scheduling.
"""
import logging
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTabWidget, QScrollArea, QGroupBox, QListWidget, QListWidgetItem,
    QFrame, QSplitter, QMessageBox, QInputDialog, QComboBox, QSpinBox,
    QDateTimeEdit, QCheckBox, QTextEdit, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QMimeData, QByteArray, QDataStream, QIODevice, QDateTime
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QPainter, QFont

from ...handlers.library_handler import LibraryManager

class DraggablePostWidget(QFrame):
    """A draggable widget representing a post in a campaign."""
    
    def __init__(self, post_data: Dict[str, Any], campaign_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.post_data = post_data
        self.campaign_data = campaign_data
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setFixedHeight(120)
        self.setAcceptDrops(True)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Media thumbnail/icon
        media_label = QLabel()
        media_label.setFixedSize(80, 80)
        media_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
        """)
        
        # Try to load media thumbnail
        media_path = self.post_data.get('path', '')
        if media_path and os.path.exists(media_path):
            try:
                if any(ext in media_path.lower() for ext in ['.mp4', '.mov', '.avi']):
                    media_label.setText("🎬\nVideo")
                    media_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    pixmap = QPixmap(media_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(
                            78, 78, 
                            Qt.AspectRatioMode.KeepAspectRatio, 
                            Qt.TransformationMode.SmoothTransformation
                        )
                        media_label.setPixmap(scaled_pixmap)
                    else:
                        media_label.setText("📷\nImage")
                        media_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            except:
                media_label.setText("📷\nMedia")
                media_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            media_label.setText("📷\nMedia")
            media_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(media_label)
        
        # Post details
        details_layout = QVBoxLayout()
        
        # Caption (truncated)
        caption = self.post_data.get('caption', 'No caption')
        caption_label = QLabel(caption[:100] + "..." if len(caption) > 100 else caption)
        caption_label.setWordWrap(True)
        caption_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        details_layout.addWidget(caption_label)
        
        # Platforms
        platforms = self.post_data.get('platforms', [])
        if platforms:
            platforms_text = "Platforms: " + ", ".join(platforms)
        else:
            platforms_text = "Platforms: Not specified"
        platforms_label = QLabel(platforms_text)
        platforms_label.setStyleSheet("color: #666666; font-size: 12px; margin-bottom: 5px;")
        details_layout.addWidget(platforms_label)
        
        # Scheduled time
        scheduled_time = self.post_data.get('scheduled_time')
        if scheduled_time:
            try:
                dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                time_str = dt.strftime("%b %d, %Y at %I:%M %p")
            except:
                time_str = scheduled_time
            time_label = QLabel(f"Scheduled: {time_str}")
        else:
            # Calculate based on campaign rules and position
            position = self.post_data.get('campaign_position', 0)
            time_label = QLabel(f"Position #{position + 1} - Time will be calculated")
        
        time_label.setStyleSheet("color: #007bff; font-size: 12px; font-weight: bold;")
        details_layout.addWidget(time_label)
        
        layout.addLayout(details_layout)
        
        # Status indicator
        status_layout = QVBoxLayout()
        status_layout.addStretch()
        
        status = self.post_data.get('status', 'draft')
        status_color = {
            'draft': '#6c757d',
            'scheduled': '#007bff',
            'published': '#28a745',
            'failed': '#dc3545'
        }.get(status, '#6c757d')
        
        status_label = QLabel(status.title())
        status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {status_color};
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }}
        """)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(status_label)
        
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # Style the frame
        self.setStyleSheet("""
            DraggablePostWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 2px;
            }
            DraggablePostWidget:hover {
                border-color: #007bff;
                background-color: #f8f9fa;
            }
        """)
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        
        if not hasattr(self, 'drag_start_position'):
            return
        
        # Start drag if moved enough
        if ((event.pos() - self.drag_start_position).manhattanLength() < 
            self.parent().parent().startDragDistance()):
            return
        
        # Create drag
        drag = self.parent().parent().drag()
        mimeData = QMimeData()
        
        # Encode post data
        data = QByteArray()
        stream = QDataStream(data, QIODevice.OpenModeFlag.WriteOnly)
        stream.writeQString(json.dumps(self.post_data))
        mimeData.setData("application/x-post-data", data)
        
        # Create drag pixmap
        pixmap = self.grab()
        
        drag.setMimeData(mimeData)
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        
        # Execute drag
        dropAction = drag.exec(Qt.DropAction.MoveAction)

class CampaignPostsList(QListWidget):
    """A list widget that accepts dropped posts and allows reordering."""
    
    posts_reordered = Signal(str, list)  # campaign_id, new_post_order
    
    def __init__(self, campaign_id: str, parent=None):
        super().__init__(parent)
        self.campaign_id = campaign_id
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter."""
        if event.mimeData().hasFormat("application/x-post-data"):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        if event.mimeData().hasFormat("application/x-post-data"):
            # Get the dropped post data
            data = event.mimeData().data("application/x-post-data")
            stream = QDataStream(data, QIODevice.OpenModeFlag.ReadOnly)
            post_json = stream.readQString()
            post_data = json.loads(post_json)
            
            # Add to this campaign
            self._add_post_to_campaign(post_data, event.pos())
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
    
    def _add_post_to_campaign(self, post_data: Dict[str, Any], position):
        """Add a post to this campaign at the specified position."""
        # Find insertion point
        item_at_pos = self.itemAt(position)
        if item_at_pos:
            row = self.row(item_at_pos)
        else:
            row = self.count()
        
        # Create widget for the post
        post_widget = DraggablePostWidget(post_data, {'id': self.campaign_id})
        
        # Create list item
        item = QListWidgetItem()
        item.setSizeHint(post_widget.sizeHint())
        
        # Insert at position
        self.insertItem(row, item)
        self.setItemWidget(item, post_widget)
        
        # Emit reorder signal
        self._emit_reorder_signal()
    
    def _emit_reorder_signal(self):
        """Emit signal with new post order."""
        post_order = []
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if isinstance(widget, DraggablePostWidget):
                post_order.append(widget.post_data)
        
        self.posts_reordered.emit(self.campaign_id, post_order)

class CampaignTab(QWidget):
    """Tab widget for managing a single campaign."""
    
    def __init__(self, campaign_data: Dict[str, Any], library_manager: LibraryManager, parent=None):
        super().__init__(parent)
        self.campaign_data = campaign_data
        self.library_manager = library_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self._setup_ui()
        self._load_campaign_posts()
    
    def _setup_ui(self):
        """Set up the campaign tab UI."""
        layout = QVBoxLayout(self)
        
        # Campaign header
        header_layout = QHBoxLayout()
        
        # Campaign name and description
        info_layout = QVBoxLayout()
        
        name_label = QLabel(self.campaign_data.get('name', 'Unnamed Campaign'))
        name_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 5px;")
        info_layout.addWidget(name_label)
        
        description = self.campaign_data.get('description', 'No description')
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #666666; margin-bottom: 10px;")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)
        
        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        
        # Campaign settings button
        settings_btn = QPushButton("Campaign Settings")
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        settings_btn.clicked.connect(self._edit_campaign_settings)
        header_layout.addWidget(settings_btn)
        
        layout.addLayout(header_layout)
        
        # Campaign stats
        stats_layout = QHBoxLayout()
        
        total_posts = len(self.campaign_data.get('posts', []))
        scheduled_posts = len([p for p in self.campaign_data.get('posts', []) if p.get('status') == 'scheduled'])
        published_posts = len([p for p in self.campaign_data.get('posts', []) if p.get('status') == 'published'])
        
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Shape.Box)
        stats_frame.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 10px;")
        stats_frame_layout = QHBoxLayout(stats_frame)
        
        stats_frame_layout.addWidget(QLabel(f"Total Posts: {total_posts}"))
        stats_frame_layout.addWidget(QLabel("•"))
        stats_frame_layout.addWidget(QLabel(f"Scheduled: {scheduled_posts}"))
        stats_frame_layout.addWidget(QLabel("•"))
        stats_frame_layout.addWidget(QLabel(f"Published: {published_posts}"))
        stats_frame_layout.addStretch()
        
        layout.addWidget(stats_frame)
        
        # Posts list
        posts_group = QGroupBox("Campaign Posts (Drag to Reorder)")
        posts_layout = QVBoxLayout(posts_group)
        
        # Create the posts list
        self.posts_list = CampaignPostsList(self.campaign_data.get('id', ''))
        self.posts_list.posts_reordered.connect(self._on_posts_reordered)
        posts_layout.addWidget(self.posts_list)
        
        # Add post button
        add_post_layout = QHBoxLayout()
        add_post_btn = QPushButton("Add Post to Campaign")
        add_post_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        add_post_btn.clicked.connect(self._add_post_to_campaign)
        add_post_layout.addWidget(add_post_btn)
        add_post_layout.addStretch()
        
        posts_layout.addLayout(add_post_layout)
        layout.addWidget(posts_group)
    
    def _load_campaign_posts(self):
        """Load and display posts in this campaign."""
        posts = self.campaign_data.get('posts', [])
        
        for post_data in posts:
            post_widget = DraggablePostWidget(post_data, self.campaign_data)
            
            item = QListWidgetItem()
            item.setSizeHint(post_widget.sizeHint())
            
            self.posts_list.addItem(item)
            self.posts_list.setItemWidget(item, post_widget)
    
    def _on_posts_reordered(self, campaign_id: str, new_post_order: List[Dict[str, Any]]):
        """Handle posts being reordered."""
        self.logger.info(f"Posts reordered in campaign {campaign_id}")
        
        # Update campaign data
        self.campaign_data['posts'] = new_post_order
        
        # Recalculate scheduled times based on campaign rules
        self._recalculate_post_times()
        
        # Save campaign data (implement this method)
        self._save_campaign_data()
    
    def _recalculate_post_times(self):
        """Recalculate scheduled times based on campaign rules and post order."""
        campaign_rules = self.campaign_data.get('rules', {})
        start_date = campaign_rules.get('start_date')
        posts_per_day = campaign_rules.get('posts_per_day', 1)
        posting_times = campaign_rules.get('posting_times', ['09:00'])
        
        if not start_date:
            return
        
        try:
            base_date = datetime.fromisoformat(start_date)
        except:
            base_date = datetime.now()
        
        posts = self.campaign_data.get('posts', [])
        current_date = base_date
        posts_today = 0
        time_index = 0
        
        for i, post in enumerate(posts):
            # Check if we need to move to next day
            if posts_today >= posts_per_day:
                current_date += timedelta(days=1)
                posts_today = 0
                time_index = 0
            
            # Set scheduled time
            time_str = posting_times[time_index % len(posting_times)]
            hour, minute = map(int, time_str.split(':'))
            
            scheduled_datetime = current_date.replace(hour=hour, minute=minute)
            post['scheduled_time'] = scheduled_datetime.isoformat()
            post['campaign_position'] = i
            
            posts_today += 1
            time_index += 1
    
    def _save_campaign_data(self):
        """Save campaign data to file."""
        # TODO: Implement campaign data persistence
        self.logger.info("Campaign data would be saved here")
    
    def _edit_campaign_settings(self):
        """Open campaign settings dialog."""
        QMessageBox.information(self, "Campaign Settings", "Campaign settings dialog coming soon!")
    
    def _add_post_to_campaign(self):
        """Add a post to this campaign."""
        QMessageBox.information(self, "Add Post", "Post selection dialog coming soon!")

class CampaignManager(QWidget):
    """Main campaign manager widget."""
    
    def __init__(self, library_manager: LibraryManager, parent=None):
        super().__init__(parent)
        self.library_manager = library_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Sample campaign data (replace with actual data loading)
        self.campaigns = self._load_campaigns()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the campaign manager UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Campaign Manager")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # New campaign button
        new_campaign_btn = QPushButton("New Campaign")
        new_campaign_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        new_campaign_btn.clicked.connect(self._create_new_campaign)
        header_layout.addWidget(new_campaign_btn)
        
        layout.addLayout(header_layout)
        
        # Campaign tabs
        self.campaign_tabs = QTabWidget()
        self.campaign_tabs.setTabsClosable(True)
        self.campaign_tabs.tabCloseRequested.connect(self._close_campaign_tab)
        
        # Load campaign tabs
        self._load_campaign_tabs()
        
        layout.addWidget(self.campaign_tabs)
        
        # If no campaigns, show welcome message
        if not self.campaigns:
            self._show_welcome_message()
    
    def _load_campaigns(self) -> List[Dict[str, Any]]:
        """Load campaigns from storage."""
        # TODO: Implement actual campaign loading
        # For now, return sample data
        return [
            {
                'id': 'campaign_1',
                'name': 'Holiday Promotions',
                'description': 'Seasonal holiday marketing campaign',
                'rules': {
                    'start_date': '2025-12-01T00:00:00',
                    'posts_per_day': 2,
                    'posting_times': ['09:00', '15:00']
                },
                'posts': [
                    {
                        'id': 'post_1',
                        'caption': 'Holiday special offer - 20% off all items!',
                        'platforms': ['instagram', 'facebook'],
                        'status': 'scheduled',
                        'scheduled_time': '2025-12-01T09:00:00',
                        'campaign_position': 0
                    },
                    {
                        'id': 'post_2',
                        'caption': 'Fresh baked goods for the holidays',
                        'platforms': ['instagram', 'twitter'],
                        'status': 'draft',
                        'campaign_position': 1
                    }
                ]
            }
        ]
    
    def _load_campaign_tabs(self):
        """Load tabs for each campaign."""
        for campaign in self.campaigns:
            tab = CampaignTab(campaign, self.library_manager)
            self.campaign_tabs.addTab(tab, campaign.get('name', 'Unnamed'))
    
    def _show_welcome_message(self):
        """Show welcome message when no campaigns exist."""
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.addStretch()
        
        welcome_label = QLabel("Welcome to Campaign Manager")
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #666666;")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(welcome_label)
        
        description_label = QLabel("Create your first campaign to start scheduling posts")
        description_label.setStyleSheet("font-size: 16px; color: #888888; margin-top: 10px;")
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(description_label)
        
        create_btn = QPushButton("Create First Campaign")
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        create_btn.clicked.connect(self._create_new_campaign)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(create_btn)
        button_layout.addStretch()
        welcome_layout.addLayout(button_layout)
        
        welcome_layout.addStretch()
        
        self.campaign_tabs.addTab(welcome_widget, "Welcome")
    
    def _create_new_campaign(self):
        """Create a new campaign."""
        name, ok = QInputDialog.getText(self, "New Campaign", "Enter campaign name:")
        if ok and name:
            # Create new campaign data
            new_campaign = {
                'id': f'campaign_{len(self.campaigns) + 1}',
                'name': name,
                'description': 'New campaign',
                'rules': {
                    'start_date': datetime.now().isoformat(),
                    'posts_per_day': 1,
                    'posting_times': ['09:00']
                },
                'posts': []
            }
            
            self.campaigns.append(new_campaign)
            
            # Create tab for new campaign
            tab = CampaignTab(new_campaign, self.library_manager)
            index = self.campaign_tabs.addTab(tab, name)
            self.campaign_tabs.setCurrentIndex(index)
            
            # Remove welcome tab if it exists
            for i in range(self.campaign_tabs.count()):
                if self.campaign_tabs.tabText(i) == "Welcome":
                    self.campaign_tabs.removeTab(i)
                    break
    
    def _close_campaign_tab(self, index: int):
        """Close a campaign tab."""
        reply = QMessageBox.question(
            self, 
            "Close Campaign", 
            "Are you sure you want to close this campaign tab?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.campaign_tabs.removeTab(index) 