"""
Dialog for post scheduling options
"""
import logging
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QGroupBox, QCheckBox, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal

class PostOptionsDialog(QDialog):
    """Dialog for post scheduling and publishing options."""
    
    # Signals
    post_now = Signal(dict)  # Post immediately
    add_to_queue = Signal(dict)  # Add to schedule queue
    edit_post = Signal(dict)  # Edit post
    delete_post = Signal(dict)  # Delete post
    
    def __init__(self, parent=None, post_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.post_data = post_data or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.setWindowTitle("Post Options")
        self.setMinimumWidth(500)
        self.setMaximumHeight(600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2A2A2A;
                color: white;
            }
            QLabel {
                color: white;
            }
            QRadioButton, QCheckBox {
                color: white;
            }
            QGroupBox {
                border: 1px solid #555555;
                border-radius: 8px;
                margin-top: 15px;
                font-weight: bold;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #444444;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            #postNowButton {
                background-color: #4CAF50;
            }
            #postNowButton:hover {
                background-color: #45a049;
            }
            #queueButton {
                background-color: #3949AB;
            }
            #queueButton:hover {
                background-color: #303F9F;
            }
            #editButton {
                background-color: #FF9800;
            }
            #editButton:hover {
                background-color: #F57C00;
            }
            #deleteButton {
                background-color: #e74c3c;
            }
            #deleteButton:hover {
                background-color: #c0392b;
            }
        """)
        
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header with item info
        header = QLabel("Post Options")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Display post info
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #333333; border-radius: 8px; padding: 10px;")
        info_layout = QVBoxLayout(info_frame)
        
        item_name = self.post_data.get("media_path", "").split("/")[-1] if self.post_data.get("media_path") else "Unknown"
        self.info_label = QLabel(f"<b>Item:</b> {item_name}")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #EEEEEE;")
        info_layout.addWidget(self.info_label)
        
        layout.addWidget(info_frame)
        
        # Post Now Section
        post_now_group = QGroupBox("Post Now")
        post_now_layout = QVBoxLayout(post_now_group)
        
        # Social media platforms checkboxes
        self.fb_checkbox = QCheckBox("Post to Facebook")
        self.fb_checkbox.setChecked(True)
        post_now_layout.addWidget(self.fb_checkbox)
        
        self.ig_checkbox = QCheckBox("Post to Instagram")
        self.ig_checkbox.setChecked(True)
        post_now_layout.addWidget(self.ig_checkbox)
        
        post_now_button = QPushButton("Post Now")
        post_now_button.setObjectName("postNowButton")
        post_now_button.clicked.connect(self._on_post_now)
        post_now_layout.addWidget(post_now_button)
        
        layout.addWidget(post_now_group)
        
        # Queue Section
        queue_group = QGroupBox("Add to Queue")
        queue_layout = QVBoxLayout(queue_group)
        
        queue_info = QLabel("Add this post to the next available slot in the queue")
        queue_info.setWordWrap(True)
        queue_layout.addWidget(queue_info)
        
        queue_button = QPushButton("Add to Queue")
        queue_button.setObjectName("queueButton")
        queue_button.clicked.connect(self._on_add_to_queue)
        queue_layout.addWidget(queue_button)
        
        layout.addWidget(queue_group)
        
        # Edit/Delete section
        action_group = QGroupBox("Other Actions")
        action_layout = QHBoxLayout(action_group)
        
        edit_button = QPushButton("Edit Post")
        edit_button.setObjectName("editButton")
        edit_button.clicked.connect(self._on_edit_post)
        action_layout.addWidget(edit_button)
        
        delete_button = QPushButton("Delete Post")
        delete_button.setObjectName("deleteButton")
        delete_button.clicked.connect(self._on_delete_post)
        action_layout.addWidget(delete_button)
        
        layout.addWidget(action_group)
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)
        
    def _on_post_now(self):
        """Handle post now button click."""
        if not self.fb_checkbox.isChecked() and not self.ig_checkbox.isChecked():
            QMessageBox.warning(self, "Post Error", "Please select at least one platform to post to.")
            return
            
        platforms = []
        if self.fb_checkbox.isChecked():
            platforms.append("facebook")
        if self.ig_checkbox.isChecked():
            platforms.append("instagram")
            
        # Add platforms to post data
        post_data = self.post_data.copy()
        post_data["platforms"] = platforms
        
        # Emit signal
        self.post_now.emit(post_data)
        self.accept()
        
    def _on_add_to_queue(self):
        """Handle add to queue button click."""
        # Emit signal
        self.add_to_queue.emit(self.post_data)
        self.accept()
        
    def _on_edit_post(self):
        """Handle edit post button click."""
        # Emit signal
        self.edit_post.emit(self.post_data)
        self.accept()
        
    def _on_delete_post(self):
        """Handle delete post button click."""
        result = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this post?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            # Emit signal
            self.delete_post.emit(self.post_data)
            self.accept() 