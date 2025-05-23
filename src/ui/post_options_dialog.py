"""
Dialog for post scheduling options
"""
import logging
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, # QPushButton, # Removed
    QRadioButton, QButtonGroup, QGroupBox, QCheckBox, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QEvent # Added QEvent

from .components.adjustable_button import AdjustableButton # Corrected import path

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
        
        # Store references to buttons that need text updates
        self.post_now_btn: Optional[AdjustableButton] = None
        self.queue_btn: Optional[AdjustableButton] = None
        self.edit_btn: Optional[AdjustableButton] = None
        self.delete_btn: Optional[AdjustableButton] = None
        self.cancel_btn: Optional[AdjustableButton] = None

        self.setWindowTitle(self.tr("Post Options"))
        self.setMinimumWidth(500)
        self.setMaximumHeight(600) # Adjusted for more content potentially
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
                margin-top: 15px; /* Provides space for the title */
                font-weight: bold;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            AdjustableButton { /* Changed from QPushButton */
                background-color: #444444;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 14px;
            }
            AdjustableButton:hover { /* Changed from QPushButton */
                background-color: #555555;
            }
            AdjustableButton#postNowButton { /* Changed from QPushButton */
                background-color: #4CAF50; /* Green */
            }
            AdjustableButton#postNowButton:hover { /* Changed from QPushButton */
                background-color: #45a049;
            }
            AdjustableButton#queueButton { /* Changed from QPushButton */
                background-color: #3949AB; /* Indigo */
            }
            AdjustableButton#queueButton:hover { /* Changed from QPushButton */
                background-color: #303F9F;
            }
            AdjustableButton#editButton { /* Changed from QPushButton */
                background-color: #FF9800; /* Orange */
            }
            AdjustableButton#editButton:hover { /* Changed from QPushButton */
                background-color: #F57C00;
            }
            AdjustableButton#deleteButton { /* Changed from QPushButton */
                background-color: #e74c3c; /* Red */
            }
            AdjustableButton#deleteButton:hover { /* Changed from QPushButton */
                background-color: #c0392b;
            }
        """)
        
        self._init_ui()
        self.retranslateUi() # Initial translation
        
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15) # Increased spacing
        
        # Header with item info
        header = QLabel() # Text set in retranslateUi
        header.setObjectName("dialogHeader")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Display post info (e.g., filename)
        info_frame = QFrame()
        info_frame.setObjectName("infoFrame")
        info_frame.setStyleSheet("background-color: #333333; border-radius: 8px; padding: 10px;")
        info_layout = QVBoxLayout(info_frame)
        
        item_name = self.post_data.get("media_path", "").split("/")[-1] if self.post_data.get("media_path") else self.tr("Unknown Item")
        self.info_label = QLabel(f"<b>{self.tr('Item')}:</b> {item_name}")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #EEEEEE;")
        info_layout.addWidget(self.info_label)
        
        layout.addWidget(info_frame)
        
        # Post Now Section
        self.post_now_group = QGroupBox() # Title set in retranslateUi
        post_now_layout = QVBoxLayout(self.post_now_group)
        
        # Social media platforms checkboxes
        self.fb_checkbox = QCheckBox() # Text set in retranslateUi
        self.fb_checkbox.setChecked(True)
        post_now_layout.addWidget(self.fb_checkbox)
        
        self.ig_checkbox = QCheckBox() # Text set in retranslateUi
        self.ig_checkbox.setChecked(True)
        post_now_layout.addWidget(self.ig_checkbox)
        
        self.post_now_btn = AdjustableButton() # Changed from QPushButton, text set in retranslateUi
        self.post_now_btn.setObjectName("postNowButton")
        self.post_now_btn.clicked.connect(self._on_post_now)
        post_now_layout.addWidget(self.post_now_btn)
        
        layout.addWidget(self.post_now_group)
        
        # Queue Section
        self.queue_group = QGroupBox() # Title set in retranslateUi
        queue_layout = QVBoxLayout(self.queue_group)
        
        self.queue_info_label = QLabel() # Text set in retranslateUi
        self.queue_info_label.setWordWrap(True)
        queue_layout.addWidget(self.queue_info_label)
        
        self.queue_btn = AdjustableButton() # Changed from QPushButton, text set in retranslateUi
        self.queue_btn.setObjectName("queueButton")
        self.queue_btn.clicked.connect(self._on_add_to_queue)
        queue_layout.addWidget(self.queue_btn)
        
        layout.addWidget(self.queue_group)
        
        # Edit/Delete section (conditionally shown)
        self.action_group = QGroupBox() # Title set in retranslateUi
        action_layout = QHBoxLayout(self.action_group)
        
        self.edit_btn = AdjustableButton() # Changed from QPushButton, text set in retranslateUi
        self.edit_btn.setObjectName("editButton")
        self.edit_btn.clicked.connect(self._on_edit_post)
        action_layout.addWidget(self.edit_btn)
        
        self.delete_btn = AdjustableButton() # Changed from QPushButton, text set in retranslateUi
        self.delete_btn.setObjectName("deleteButton")
        self.delete_btn.clicked.connect(self._on_delete_post)
        action_layout.addWidget(self.delete_btn)
        
        layout.addWidget(self.action_group)
        
        if not (self.post_data.get("is_draft") or self.post_data.get("is_scheduled")):
            self.action_group.setVisible(False)

        # Cancel button
        self.cancel_btn = AdjustableButton() # Changed from QPushButton, text set in retranslateUi
        self.cancel_btn.setObjectName("cancelButtonDialog") # Unique name if needed
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn, 0, Qt.AlignmentFlag.AlignRight) # Align right
        
    def _on_post_now(self):
        """Handle post now button click."""
        if not self.fb_checkbox.isChecked() and not self.ig_checkbox.isChecked():
            QMessageBox.warning(self, self.tr("Post Error"), self.tr("Please select at least one platform to post to."))
            return
            
        platforms = []
        if self.fb_checkbox.isChecked():
            platforms.append("facebook")
        if self.ig_checkbox.isChecked():
            platforms.append("instagram")
            
        # Add platforms to post data
        post_data = self.post_data.copy() # Ensure we don't modify original dict directly if passed around
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
            self.tr("Confirm Delete"),
            self.tr("Are you sure you want to delete this post? This action cannot be undone."),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No # Default to No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            # Emit signal
            self.delete_post.emit(self.post_data)
            self.accept()

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.setWindowTitle(self.tr("Post Options"))
        if hasattr(self, 'dialogHeader') and self.dialogHeader: # Check if dialogHeader exists
             self.dialogHeader.setText(self.tr("Post Options"))
        
        item_name = self.post_data.get("media_path", "").split("/")[-1] if self.post_data.get("media_path") else self.tr("Unknown Item")
        if hasattr(self, 'info_label') and self.info_label: # Check if info_label exists
            self.info_label.setText(f"<b>{self.tr('Item')}:</b> {item_name}")

        if hasattr(self, 'post_now_group') and self.post_now_group: # Check if post_now_group exists
            self.post_now_group.setTitle(self.tr("Post Now"))
        if hasattr(self, 'fb_checkbox') and self.fb_checkbox: # Check if fb_checkbox exists
            self.fb_checkbox.setText(self.tr("Post to Facebook"))
        if hasattr(self, 'ig_checkbox') and self.ig_checkbox: # Check if ig_checkbox exists
            self.ig_checkbox.setText(self.tr("Post to Instagram"))
        if self.post_now_btn: # Check if post_now_btn exists
            self.post_now_btn.setText(self.tr("Post Now"))

        if hasattr(self, 'queue_group') and self.queue_group: # Check if queue_group exists
            self.queue_group.setTitle(self.tr("Add to Queue"))
        if hasattr(self, 'queue_info_label') and self.queue_info_label: # Check if queue_info_label exists
            self.queue_info_label.setText(self.tr("Add this post to the next available slot in the queue."))
        if self.queue_btn: # Check if queue_btn exists
            self.queue_btn.setText(self.tr("Add to Queue"))
        
        if hasattr(self, 'action_group') and self.action_group: # Check if action_group exists
            self.action_group.setTitle(self.tr("Other Actions"))
        if self.edit_btn: # Check if edit_btn exists
            self.edit_btn.setText(self.tr("Edit Post"))
        if self.delete_btn: # Check if delete_btn exists
            self.delete_btn.setText(self.tr("Delete Post"))

        if self.cancel_btn: # Check if cancel_btn exists
            self.cancel_btn.setText(self.tr("Cancel"))

# Removed </rewritten_file> 