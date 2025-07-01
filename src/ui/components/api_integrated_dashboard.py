"""
API-Integrated Dashboard Component
Comprehensive dashboard that utilizes all the backend API functionality
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QProgressBar, QListWidget, QListWidgetItem,
    QTabWidget, QTextEdit, QLineEdit, QComboBox, QSpinBox, QGroupBox,
    QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QStackedWidget, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtGui import QFont, QPixmap, QIcon

from ...api.crows_eye_api_client import api_client
from ..base_widget import BaseWidget

logger = logging.getLogger(__name__)

class APIWorkerThread(QThread):
    """Worker thread for API calls to avoid blocking the UI."""
    
    finished = Signal(str, dict)  # operation_name, result
    
    def __init__(self, operation: str, method, *args, **kwargs):
        super().__init__()
        self.operation = operation
        self.method = method
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.method(*self.args, **self.kwargs)
            self.finished.emit(self.operation, result)
        except Exception as e:
            logger.error(f"API operation {self.operation} failed: {e}")
            self.finished.emit(self.operation, {"success": False, "error": str(e)})

class StatsCard(QFrame):
    """Individual stats card widget."""
    
    def __init__(self, title: str, value: str = "0", icon: str = "📊"):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
            }
            QFrame:hover {
                border-color: #007bff;
                box-shadow: 0 2px 8px rgba(0,123,255,0.1);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Icon and title
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 20))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 10))
        title_label.setStyleSheet("color: #666;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.value_label.setStyleSheet("color: #333;")
        layout.addWidget(self.value_label)
        
        layout.addStretch()
    
    def update_value(self, value: str):
        """Update the stats value."""
        self.value_label.setText(value)

class MediaGalleryWidget(QWidget):
    """Widget for displaying and managing media from the API."""
    
    media_selected = Signal(str)  # media_id
    
    def __init__(self):
        super().__init__()
        self.media_items = []
        self.setup_ui()
        self.load_media()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Media Library")
        header_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        upload_btn = QPushButton("📁 Upload Media")
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        upload_btn.clicked.connect(self.upload_media)
        header_layout.addWidget(upload_btn)
        
        layout.addLayout(header_layout)
        
        # Media list
        self.media_list = QListWidget()
        self.media_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
        """)
        self.media_list.itemClicked.connect(self.on_media_selected)
        layout.addWidget(self.media_list)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_media)
        controls_layout.addWidget(refresh_btn)
        
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setStyleSheet("QPushButton { color: #dc3545; }")
        delete_btn.clicked.connect(self.delete_selected_media)
        controls_layout.addWidget(delete_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
    
    def load_media(self):
        """Load media items from API."""
        def on_media_loaded(operation, result):
            if result.get("success"):
                self.media_items = result.get("data", [])
                self.populate_media_list()
            else:
                logger.error(f"Failed to load media: {result.get('error')}")
        
        worker = APIWorkerThread("load_media", api_client.get_media_items)
        worker.finished.connect(on_media_loaded)
        worker.start()
    
    def populate_media_list(self):
        """Populate the media list widget."""
        self.media_list.clear()
        
        for item in self.media_items:
            list_item = QListWidgetItem()
            list_item.setText(f"{item.get('original_filename', 'Unknown')} - {item.get('media_type', 'Unknown')}")
            list_item.setData(Qt.ItemDataRole.UserRole, item.get('id'))
            self.media_list.addItem(list_item)
    
    def upload_media(self):
        """Handle media upload."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Media File", "",
            "Media Files (*.jpg *.jpeg *.png *.gif *.mp4 *.mov *.avi);;All Files (*)"
        )
        
        if file_path:
            def on_upload_complete(operation, result):
                if result.get("success"):
                    QMessageBox.information(self, "Success", "Media uploaded successfully!")
                    self.load_media()  # Refresh the list
                else:
                    QMessageBox.critical(self, "Error", f"Upload failed: {result.get('error')}")
            
            worker = APIWorkerThread("upload_media", api_client.upload_media, file_path)
            worker.finished.connect(on_upload_complete)
            worker.start()
    
    def on_media_selected(self, item):
        """Handle media item selection."""
        media_id = item.data(Qt.ItemDataRole.UserRole)
        if media_id:
            self.media_selected.emit(media_id)
    
    def delete_selected_media(self):
        """Delete selected media item."""
        current_item = self.media_list.currentItem()
        if not current_item:
            return
        
        media_id = current_item.data(Qt.ItemDataRole.UserRole)
        if not media_id:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this media item?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            def on_delete_complete(operation, result):
                if result.get("success"):
                    QMessageBox.information(self, "Success", "Media deleted successfully!")
                    self.load_media()  # Refresh the list
                else:
                    QMessageBox.critical(self, "Error", f"Delete failed: {result.get('error')}")
            
            worker = APIWorkerThread("delete_media", api_client.delete_media_item, media_id)
            worker.finished.connect(on_delete_complete)
            worker.start()

class AIContentGenerator(QWidget):
    """Widget for AI content generation."""
    
    content_generated = Signal(str, str)  # content_type, content
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("AI Content Generator")
        header_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        # Content type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Content Type:"))
        
        self.content_type = QComboBox()
        self.content_type.addItems(["caption", "hashtags", "description", "title"])
        type_layout.addWidget(self.content_type)
        
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # Style and tone selection
        style_layout = QHBoxLayout()
        
        style_layout.addWidget(QLabel("Style:"))
        self.style_combo = QComboBox()
        self.style_combo.addItems(["engaging", "professional", "casual", "creative", "formal"])
        style_layout.addWidget(self.style_combo)
        
        style_layout.addWidget(QLabel("Tone:"))
        self.tone_combo = QComboBox()
        self.tone_combo.addItems(["professional", "friendly", "enthusiastic", "informative", "playful"])
        style_layout.addWidget(self.tone_combo)
        
        layout.addLayout(style_layout)
        
        # Prompt input
        layout.addWidget(QLabel("Prompt:"))
        self.prompt_input = QTextEdit()
        self.prompt_input.setMaximumHeight(100)
        self.prompt_input.setPlaceholderText("Enter your content prompt here...")
        layout.addWidget(self.prompt_input)
        
        # Generate button
        generate_btn = QPushButton("🤖 Generate Content")
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #5a36a3; }
        """)
        generate_btn.clicked.connect(self.generate_content)
        layout.addWidget(generate_btn)
        
        # Generated content display
        layout.addWidget(QLabel("Generated Content:"))
        self.content_display = QTextEdit()
        self.content_display.setReadOnly(True)
        layout.addWidget(self.content_display)
        
        # Copy button
        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_content)
        layout.addWidget(copy_btn)
    
    def generate_content(self):
        """Generate AI content."""
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Warning", "Please enter a prompt.")
            return
        
        content_type = self.content_type.currentText()
        
        def on_content_generated(operation, result):
            if result.get("success"):
                content = result.get("content", "No content generated")
                self.content_display.setPlainText(content)
                self.content_generated.emit(content_type, content)
            else:
                QMessageBox.critical(self, "Error", f"Generation failed: {result.get('error')}")
        
        worker = APIWorkerThread("generate_content", api_client.generate_content, prompt, content_type)
        worker.finished.connect(on_content_generated)
        worker.start()
    
    def copy_content(self):
        """Copy content to clipboard."""
        content = self.content_display.toPlainText()
        if content:
            clipboard = QApplication.clipboard()
            clipboard.setText(content)
            QMessageBox.information(self, "Copied", "Content copied to clipboard!")

class PostManager(QWidget):
    """Widget for managing posts."""
    
    def __init__(self):
        super().__init__()
        self.posts = []
        self.setup_ui()
        self.load_posts()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Post Manager")
        header_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        create_btn = QPushButton("✨ Create Post")
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)
        create_btn.clicked.connect(self.create_post)
        header_layout.addWidget(create_btn)
        
        layout.addLayout(header_layout)
        
        # Posts table
        self.posts_table = QTableWidget()
        self.posts_table.setColumnCount(5)
        self.posts_table.setHorizontalHeaderLabels(["Title", "Status", "Platforms", "Created", "Actions"])
        self.posts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.posts_table)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_posts)
        controls_layout.addWidget(refresh_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
    
    def load_posts(self):
        """Load posts from API."""
        def on_posts_loaded(operation, result):
            if result.get("success"):
                self.posts = result.get("data", [])
                self.populate_posts_table()
            else:
                logger.error(f"Failed to load posts: {result.get('error')}")
        
        worker = APIWorkerThread("load_posts", api_client.get_posts)
        worker.finished.connect(on_posts_loaded)
        worker.start()
    
    def populate_posts_table(self):
        """Populate the posts table."""
        self.posts_table.setRowCount(len(self.posts))
        
        for row, post in enumerate(self.posts):
            self.posts_table.setItem(row, 0, QTableWidgetItem(post.get("title", "Untitled")))
            self.posts_table.setItem(row, 1, QTableWidgetItem(post.get("status", "draft")))
            self.posts_table.setItem(row, 2, QTableWidgetItem(", ".join(post.get("platforms", []))))
            
            created_date = post.get("created_at", "")
            if created_date:
                try:
                    dt = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                    formatted_date = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    formatted_date = created_date
            else:
                formatted_date = "Unknown"
            
            self.posts_table.setItem(row, 3, QTableWidgetItem(formatted_date))
            
            # Actions
            action_btn = QPushButton("📤 Publish")
            action_btn.clicked.connect(lambda checked, post_id=post.get("id"): self.publish_post(post_id))
            self.posts_table.setCellWidget(row, 4, action_btn)
    
    def create_post(self):
        """Create a new post."""
        # This would open a post creation dialog
        QMessageBox.information(self, "Info", "Post creation dialog would open here.")
    
    def publish_post(self, post_id: str):
        """Publish a post."""
        if not post_id:
            return
        
        # For now, publish to all connected platforms
        def on_publish_complete(operation, result):
            if result.get("success"):
                QMessageBox.information(self, "Success", "Post published successfully!")
                self.load_posts()  # Refresh the list
            else:
                QMessageBox.critical(self, "Error", f"Publish failed: {result.get('error')}")
        
        # This would need platform selection dialog
        platforms = ["instagram", "twitter", "facebook"]  # Example platforms
        worker = APIWorkerThread("publish_post", api_client.publish_post, post_id, platforms)
        worker.finished.connect(on_publish_complete)
        worker.start()

class AnalyticsDashboard(QWidget):
    """Widget for displaying analytics."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_analytics()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Analytics Dashboard")
        header_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        # Date range selector
        self.date_range = QComboBox()
        self.date_range.addItems(["7d", "30d", "90d", "1y"])
        self.date_range.setCurrentText("30d")
        self.date_range.currentTextChanged.connect(self.load_analytics)
        header_layout.addWidget(QLabel("Range:"))
        header_layout.addWidget(self.date_range)
        
        layout.addLayout(header_layout)
        
        # Stats cards
        stats_layout = QGridLayout()
        
        self.total_posts_card = StatsCard("Total Posts", "0", "📝")
        stats_layout.addWidget(self.total_posts_card, 0, 0)
        
        self.total_views_card = StatsCard("Total Views", "0", "👁️")
        stats_layout.addWidget(self.total_views_card, 0, 1)
        
        self.engagement_card = StatsCard("Avg Engagement", "0%", "💬")
        stats_layout.addWidget(self.engagement_card, 0, 2)
        
        self.reach_card = StatsCard("Total Reach", "0", "📈")
        stats_layout.addWidget(self.reach_card, 0, 3)
        
        layout.addLayout(stats_layout)
        
        # Analytics details
        self.analytics_display = QTextEdit()
        self.analytics_display.setReadOnly(True)
        layout.addWidget(self.analytics_display)
    
    def load_analytics(self):
        """Load analytics data."""
        date_range = self.date_range.currentText()
        
        def on_analytics_loaded(operation, result):
            if result.get("success"):
                self.update_analytics_display(result)
            else:
                logger.error(f"Failed to load analytics: {result.get('error')}")
        
        worker = APIWorkerThread("load_analytics", api_client.get_analytics_overview, date_range)
        worker.finished.connect(on_analytics_loaded)
        worker.start()
    
    def update_analytics_display(self, data):
        """Update analytics display with new data."""
        analytics = data.get("analytics", {})
        
        # Update stats cards
        self.total_posts_card.update_value(str(analytics.get("total_posts", 0)))
        self.total_views_card.update_value(str(analytics.get("total_views", 0)))
        self.engagement_card.update_value(f"{analytics.get('avg_engagement', 0):.1f}%")
        self.reach_card.update_value(str(analytics.get("total_reach", 0)))
        
        # Update detailed analytics
        details = f"""
Analytics Overview
==================
Period: {self.date_range.currentText()}

Posts:
- Total Posts: {analytics.get('total_posts', 0)}
- Published Posts: {analytics.get('published_posts', 0)}
- Draft Posts: {analytics.get('draft_posts', 0)}

Engagement:
- Total Views: {analytics.get('total_views', 0)}
- Total Likes: {analytics.get('total_likes', 0)}
- Total Comments: {analytics.get('total_comments', 0)}
- Total Shares: {analytics.get('total_shares', 0)}
- Average Engagement Rate: {analytics.get('avg_engagement', 0):.1f}%

Reach:
- Total Reach: {analytics.get('total_reach', 0)}
- Unique Viewers: {analytics.get('unique_viewers', 0)}

Platform Breakdown:
{self._format_platform_stats(analytics.get('platform_stats', {}))}
        """
        
        self.analytics_display.setPlainText(details.strip())
    
    def _format_platform_stats(self, platform_stats):
        """Format platform statistics for display."""
        if not platform_stats:
            return "No platform data available"
        
        lines = []
        for platform, stats in platform_stats.items():
            lines.append(f"- {platform.title()}: {stats.get('posts', 0)} posts, {stats.get('engagement', 0):.1f}% engagement")
        
        return "\n".join(lines) if lines else "No platform data available"

class APIIntegratedDashboard(BaseWidget):
    """
    Comprehensive dashboard that integrates with all API functionality.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.start_refresh_timer()
    
    def setup_ui(self):
        """Set up the dashboard UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Crow's Eye Dashboard")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333; margin: 10px 0;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # API Status indicator
        self.api_status = QLabel("🔴 Checking...")
        self.api_status.setStyleSheet("font-size: 14px; padding: 5px;")
        header_layout.addWidget(self.api_status)
        
        layout.addLayout(header_layout)
        
        # Main content area with tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                padding: 10px 20px;
                margin-right: 2px;
                border: 1px solid #ddd;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
        """)
        
        # Overview tab
        overview_tab = self.create_overview_tab()
        self.tab_widget.addTab(overview_tab, "📊 Overview")
        
        # Media tab
        self.media_widget = MediaGalleryWidget()
        self.tab_widget.addTab(self.media_widget, "📁 Media")
        
        # AI Generator tab
        self.ai_widget = AIContentGenerator()
        self.tab_widget.addTab(self.ai_widget, "🤖 AI Generator")
        
        # Posts tab
        self.posts_widget = PostManager()
        self.tab_widget.addTab(self.posts_widget, "📝 Posts")
        
        # Analytics tab
        self.analytics_widget = AnalyticsDashboard()
        self.tab_widget.addTab(self.analytics_widget, "📈 Analytics")
        
        layout.addWidget(self.tab_widget)
        
        # Check API health
        self.check_api_health()
    
    def create_overview_tab(self):
        """Create the overview tab with quick stats and actions."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Quick stats
        stats_group = QGroupBox("Quick Stats")
        stats_layout = QGridLayout(stats_group)
        
        self.media_count_card = StatsCard("Media Files", "Loading...", "📁")
        stats_layout.addWidget(self.media_count_card, 0, 0)
        
        self.posts_count_card = StatsCard("Total Posts", "Loading...", "📝")
        stats_layout.addWidget(self.posts_count_card, 0, 1)
        
        self.scheduled_count_card = StatsCard("Scheduled", "Loading...", "⏰")
        stats_layout.addWidget(self.scheduled_count_card, 0, 2)
        
        layout.addWidget(stats_group)
        
        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QGridLayout(actions_group)
        
        upload_btn = QPushButton("📁 Upload Media")
        upload_btn.setMinimumHeight(50)
        upload_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))
        actions_layout.addWidget(upload_btn, 0, 0)
        
        ai_btn = QPushButton("🤖 Generate Content")
        ai_btn.setMinimumHeight(50)
        ai_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))
        actions_layout.addWidget(ai_btn, 0, 1)
        
        post_btn = QPushButton("📝 Create Post")
        post_btn.setMinimumHeight(50)
        post_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(3))
        actions_layout.addWidget(post_btn, 0, 2)
        
        analytics_btn = QPushButton("📈 View Analytics")
        analytics_btn.setMinimumHeight(50)
        analytics_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(4))
        actions_layout.addWidget(analytics_btn, 1, 0)
        
        connect_btn = QPushButton("🔗 Connect Platforms")
        connect_btn.setMinimumHeight(50)
        connect_btn.clicked.connect(self.connect_platforms)
        actions_layout.addWidget(connect_btn, 1, 1)
        
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setMinimumHeight(50)
        connect_btn.clicked.connect(self.open_settings)
        actions_layout.addWidget(settings_btn, 1, 2)
        
        layout.addWidget(actions_group)
        
        # Recent activity
        activity_group = QGroupBox("Recent Activity")
        activity_layout = QVBoxLayout(activity_group)
        
        self.activity_list = QListWidget()
        self.activity_list.setMaximumHeight(200)
        activity_layout.addWidget(self.activity_list)
        
        layout.addWidget(activity_group)
        
        layout.addStretch()
        return widget
    
    def check_api_health(self):
        """Check API health status."""
        def on_health_checked(operation, result):
            if result.get("success"):
                self.api_status.setText("🟢 API Connected")
                self.api_status.setStyleSheet("color: green; font-size: 14px; padding: 5px;")
                self.load_overview_stats()
            else:
                self.api_status.setText("🔴 API Disconnected")
                self.api_status.setStyleSheet("color: red; font-size: 14px; padding: 5px;")
        
        worker = APIWorkerThread("health_check", api_client.health_check)
        worker.finished.connect(on_health_checked)
        worker.start()
    
    def load_overview_stats(self):
        """Load overview statistics."""
        # Load media count
        def on_media_stats(operation, result):
            if result.get("success"):
                count = len(result.get("data", []))
                self.media_count_card.update_value(str(count))
        
        # Load posts count
        def on_posts_stats(operation, result):
            if result.get("success"):
                count = len(result.get("data", []))
                self.posts_count_card.update_value(str(count))
        
        # Load scheduled count
        def on_scheduled_stats(operation, result):
            if result.get("success"):
                count = len(result.get("data", []))
                self.scheduled_count_card.update_value(str(count))
        
        # Start all requests
        media_worker = APIWorkerThread("media_stats", api_client.get_media_items, 0, 1000)
        media_worker.finished.connect(on_media_stats)
        media_worker.start()
        
        posts_worker = APIWorkerThread("posts_stats", api_client.get_posts, 0, 1000)
        posts_worker.finished.connect(on_posts_stats)
        posts_worker.start()
        
        scheduled_worker = APIWorkerThread("scheduled_stats", api_client.get_scheduled_posts)
        scheduled_worker.finished.connect(on_scheduled_stats)
        scheduled_worker.start()
    
    def connect_platforms(self):
        """Open platform connection dialog."""
        QMessageBox.information(self, "Info", "Platform connection dialog would open here.")
    
    def open_settings(self):
        """Open settings dialog."""
        QMessageBox.information(self, "Info", "Settings dialog would open here.")
    
    def start_refresh_timer(self):
        """Start timer for periodic data refresh."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.check_api_health)
        self.refresh_timer.start(60000)  # Refresh every minute 