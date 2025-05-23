"""
Pending Messages Tab for Knowledge Management
Shows pending/unanswered comments and DMs with suggested responses.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QScrollArea, QFrame, QTextEdit, QCheckBox, QSplitter,
    QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon

try:
    # Try to import the messages handler
    from src.handlers.messages_handler import messages_handler
    HAS_MESSAGES_HANDLER = True
except ImportError:
    # For development, allow running without the messages handler
    HAS_MESSAGES_HANDLER = False

class PendingMessageWidget(QWidget):
    """Widget for displaying a single pending message with response options."""
    
    approved = Signal(dict)  # Signal emitted when message is approved
    edited = Signal(dict, str)  # Signal emitted when message is edited
    deleted = Signal(dict)  # Signal emitted when message is deleted
    
    def __init__(self, message_data: Dict[str, Any], parent=None):
        """
        Initialize the pending message widget.
        
        Args:
            message_data: Dictionary containing message data
            parent: Parent widget
        """
        super().__init__(parent)
        self.message_data = message_data
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Set up UI
        self._create_ui()
        
    def _create_ui(self):
        """Create the widget UI."""
        main_layout = QVBoxLayout(self)
        
        # Message frame
        message_frame = QFrame()
        message_frame.setFrameShape(QFrame.Shape.StyledPanel)
        message_frame.setLineWidth(1)
        message_layout = QVBoxLayout(message_frame)
        
        # Message info
        info_layout = QHBoxLayout()
        
        # Source (Comment/DM)
        source_label = QLabel(f"<b>{self.message_data['type']}:</b>")
        info_layout.addWidget(source_label)
        
        # From
        from_label = QLabel(f"From: <b>{self.message_data['sender']}</b>")
        info_layout.addWidget(from_label)
        
        # Time
        time_label = QLabel(f"Time: {self.message_data['time']}")
        info_layout.addWidget(time_label)
        
        # Add spacer
        info_layout.addStretch()
        
        message_layout.addLayout(info_layout)
        
        # Original message
        message_label = QLabel("<b>Message:</b>")
        message_layout.addWidget(message_label)
        
        message_text = QTextEdit()
        message_text.setReadOnly(True)
        message_text.setPlainText(self.message_data['content'])
        message_text.setMaximumHeight(80)
        message_layout.addWidget(message_text)
        
        # Suggested response
        response_label = QLabel("<b>Suggested Response:</b>")
        message_layout.addWidget(response_label)
        
        self.response_text = QTextEdit()
        self.response_text.setPlainText(self.message_data['suggested_response'])
        self.response_text.setMaximumHeight(100)
        message_layout.addWidget(self.response_text)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        approve_button = QPushButton("Approve")
        approve_button.clicked.connect(self._on_approve)
        buttons_layout.addWidget(approve_button)
        
        edit_button = QPushButton("Edit & Approve")
        edit_button.clicked.connect(self._on_edit)
        buttons_layout.addWidget(edit_button)
        
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self._on_delete)
        buttons_layout.addWidget(delete_button)
        
        message_layout.addLayout(buttons_layout)
        
        main_layout.addWidget(message_frame)
        
    def _on_approve(self):
        """Approve the response without editing."""
        try:
            # Clone the message data and add the final response
            message = dict(self.message_data)
            message['final_response'] = message['suggested_response']
            self.approved.emit(message)
        except Exception as e:
            self.logger.exception(f"Error approving message: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Could not approve message: {str(e)}"
            )
    
    def _on_edit(self):
        """Edit and approve the response."""
        try:
            # Get the edited response text
            edited_response = self.response_text.toPlainText().strip()
            
            if not edited_response:
                QMessageBox.warning(
                    self,
                    "Empty Response",
                    "Please provide a response before approving."
                )
                return
            
            # Clone the message data
            message = dict(self.message_data)
            self.edited.emit(message, edited_response)
        except Exception as e:
            self.logger.exception(f"Error editing message: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Could not edit message: {str(e)}"
            )
    
    def _on_delete(self):
        """Delete the message."""
        try:
            # Confirm deletion
            result = QMessageBox.question(
                self,
                "Confirm Deletion",
                "Are you sure you want to delete this message?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if result == QMessageBox.StandardButton.Yes:
                self.deleted.emit(self.message_data)
        except Exception as e:
            self.logger.exception(f"Error deleting message: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Could not delete message: {str(e)}"
            )

class PendingMessagesTab(QWidget):
    """Tab for displaying and managing pending messages."""
    
    def __init__(self, parent=None):
        """Initialize the pending messages tab."""
        super().__init__(parent)
        
        # Set up logger
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # List of pending messages
        self.pending_messages = []
        
        # Auto-approve setting
        self.auto_approve = False
        
        # Create UI
        self._create_ui()
        
        # Load messages data
        self._load_messages_data()
        
    def _create_ui(self):
        """Create the tab UI."""
        main_layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        header_label = QLabel("Pending Messages")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        # Status label
        self.status_label = QLabel("No pending messages")
        header_layout.addWidget(self.status_label)
        
        # Spacer
        header_layout.addStretch()
        
        # Auto-approve checkbox
        self.auto_approve_checkbox = QCheckBox("Auto-approve responses")
        self.auto_approve_checkbox.setToolTip("Automatically approve and post suggested responses without manual review")
        self.auto_approve_checkbox.toggled.connect(self._on_auto_approve_toggled)
        header_layout.addWidget(self.auto_approve_checkbox)
        
        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self._on_refresh)
        header_layout.addWidget(refresh_button)
        
        main_layout.addLayout(header_layout)
        
        # Scroll area for messages
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Container widget for messages
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.addStretch()  # Push everything to the top
        
        scroll_area.setWidget(self.messages_container)
        main_layout.addWidget(scroll_area)
        
        # Search filter
        filter_layout = QHBoxLayout()
        
        filter_label = QLabel("Filter:")
        filter_layout.addWidget(filter_label)
        
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter messages...")
        self.filter_input.textChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_input)
        
        main_layout.addLayout(filter_layout)
        
        # API status
        if HAS_MESSAGES_HANDLER:
            api_keys_set = all([
                os.environ.get("BREADSMITH_META_APP_ID"),
                os.environ.get("BREADSMITH_META_APP_SECRET"),
                os.environ.get("BREADSMITH_META_ACCESS_TOKEN")
            ])
            
            if api_keys_set:
                self.api_status_label = QLabel("Meta API connected (using environment variables)")
                self.api_status_label.setStyleSheet("color: green;")
            else:
                self.api_status_label = QLabel("Meta API credentials missing - set environment variables to connect")
                self.api_status_label.setStyleSheet("color: orange;")
        else:
            self.api_status_label = QLabel("Meta API not available (using test data)")
            self.api_status_label.setStyleSheet("color: orange;")
        main_layout.addWidget(self.api_status_label)
    
    def _on_auto_approve_toggled(self, checked: bool):
        """Handle auto-approve checkbox toggled."""
        self.auto_approve = checked
        self.logger.info(f"Auto-approve set to: {checked}")
        
        # Update status with warning if enabled
        if checked:
            QMessageBox.warning(
                self,
                "Auto-Approve Enabled",
                "Responses will be automatically approved and posted without review. Use with caution."
            )
    
    def _on_refresh(self):
        """Refresh the pending messages list."""
        try:
            # Update status
            self.status_label.setText("Refreshing messages...")
            self._load_messages_data()
            
        except Exception as e:
            self.logger.exception(f"Error refreshing messages: {e}")
            self.status_label.setText(f"Error: {str(e)}")
    
    def _on_filter_changed(self, text: str):
        """Filter messages based on text input."""
        filter_text = text.lower()
        
        # Show/hide messages based on filter
        for i in range(self.messages_layout.count() - 1):  # -1 to skip the stretch at the end
            widget = self.messages_layout.itemAt(i).widget()
            if widget:
                # Check if widget is a PendingMessageWidget
                if isinstance(widget, PendingMessageWidget):
                    message_data = widget.message_data
                    content = message_data['content'].lower()
                    sender = message_data['sender'].lower()
                    
                    # Show if filter matches content or sender
                    if filter_text in content or filter_text in sender:
                        widget.show()
                    else:
                        widget.hide()
    
    def _load_messages(self, messages: List[Dict[str, Any]]):
        """
        Load messages into the UI.
        
        Args:
            messages: List of message dictionaries
        """
        # Clear current messages
        self._clear_messages()
        
        # Store messages
        self.pending_messages = messages
        
        # Create widgets for each message
        for message in messages:
            message_widget = PendingMessageWidget(message)
            
            # Connect signals
            message_widget.approved.connect(self._on_message_approved)
            message_widget.edited.connect(self._on_message_edited)
            message_widget.deleted.connect(self._on_message_deleted)
            
            # Add to layout before the stretch
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, message_widget)
        
        # Update status
        if messages:
            self.status_label.setText(f"{len(messages)} pending messages")
        else:
            self.status_label.setText("No pending messages")
            
        # Process auto-approvals if enabled
        if self.auto_approve and messages:
            self._process_auto_approvals()
    
    def _load_messages_data(self):
        """Load messages data from API or test data."""
        try:
            if HAS_MESSAGES_HANDLER:
                # Get messages from the Meta API via the handler
                messages = messages_handler.get_all_pending_messages()
                
                # Check if we got any messages - if not, likely missing credentials
                if not messages and not os.environ.get("BREADSMITH_META_ACCESS_TOKEN"):
                    self.api_status_label.setText("Meta API credentials missing - set environment variables to connect")
                    self.api_status_label.setStyleSheet("color: orange;")
                    # Fall back to test data
                    self._load_test_data()
                else:
                    self._load_messages(messages)
                    # Update API status
                    self.api_status_label.setText("Meta API connected (using environment variables)")
                    self.api_status_label.setStyleSheet("color: green;")
            else:
                # Use test data
                self._load_test_data()
                
                # Update API status
                self.api_status_label.setText("Meta API not available (using test data)")
                self.api_status_label.setStyleSheet("color: orange;")
                
        except Exception as e:
            self.logger.exception(f"Error loading messages data: {e}")
            self.status_label.setText(f"Error loading messages: {str(e)}")
            
            # Update API status
            self.api_status_label.setText(f"Meta API error: {str(e)}")
            self.api_status_label.setStyleSheet("color: red;")
    
    def _process_auto_approvals(self):
        """Process auto-approvals if enabled."""
        if not self.auto_approve:
            return
            
        approved_count = 0
        
        # Make a copy since we'll be modifying the list
        messages_to_process = list(self.pending_messages)
        
        for message in messages_to_process:
            # Clone the message and add final response
            msg_copy = dict(message)
            msg_copy['final_response'] = msg_copy['suggested_response']
            
            # Process the approval
            if self._process_message_approval(msg_copy):
                approved_count += 1
        
        if approved_count > 0:
            self.logger.info(f"Auto-approved {approved_count} messages")
            QMessageBox.information(
                self,
                "Auto-Approval Complete",
                f"Auto-approved and posted {approved_count} messages."
            )
    
    def _clear_messages(self):
        """Clear all message widgets."""
        # Remove all items except the stretch at the end
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Clear pending messages list
        self.pending_messages = []
    
    def _on_message_approved(self, message: Dict[str, Any]):
        """
        Handle message approved.
        
        Args:
            message: Message dictionary with final_response
        """
        try:
            self.logger.info(f"Message approved: {message['id']}")
            
            # Process the approval
            if self._process_message_approval(message):
                # Show confirmation
                QMessageBox.information(
                    self,
                    "Response Approved",
                    f"Response to {message['sender']} has been approved and will be posted."
                )
            
        except Exception as e:
            self.logger.exception(f"Error approving message: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Could not approve message: {str(e)}"
            )
    
    def _process_message_approval(self, message: Dict[str, Any]) -> bool:
        """
        Process message approval with Meta API.
        
        Args:
            message: Message dictionary with final response
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            success = False
            
            if HAS_MESSAGES_HANDLER:
                # Use the messages handler to post the response
                if message['type'] == 'Comment':
                    # Comment response
                    success = messages_handler.respond_to_comment(
                        message['id'], 
                        message['final_response']
                    )
                else:
                    # Direct message response
                    success = messages_handler.send_direct_message(
                        message['conversation_id'], 
                        message['final_response']
                    )
            else:
                # Simulation mode - always succeeds
                success = True
                self.logger.info(f"Simulation: Message {message['id']} approved")
            
            if success:
                # Remove from UI and list
                self._remove_message_widget(message['id'])
                self.pending_messages = [m for m in self.pending_messages if m['id'] != message['id']]
                
                # Update status
                self.status_label.setText(f"{len(self.pending_messages)} pending messages")
                
                return True
            else:
                QMessageBox.warning(
                    self,
                    "API Error",
                    f"Failed to post response to {message['sender']}. Please try again."
                )
                return False
                
        except Exception as e:
            self.logger.exception(f"Error processing message approval: {e}")
            return False
    
    def _on_message_edited(self, message: Dict[str, Any], edited_response: str):
        """
        Handle message edited and approved.
        
        Args:
            message: Original message dictionary
            edited_response: Edited response text
        """
        try:
            self.logger.info(f"Message edited and approved: {message['id']}")
            
            # Add the edited response to the message
            message['final_response'] = edited_response
            
            # Process the approval
            if self._process_message_approval(message):
                # Show confirmation
                QMessageBox.information(
                    self,
                    "Response Edited & Approved",
                    f"Edited response to {message['sender']} has been approved and will be posted."
                )
            
        except Exception as e:
            self.logger.exception(f"Error editing message: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Could not edit message: {str(e)}"
            )
    
    def _on_message_deleted(self, message: Dict[str, Any]):
        """
        Handle message deleted.
        
        Args:
            message: Message dictionary
        """
        try:
            self.logger.info(f"Message deleted: {message['id']}")
            
            # Remove the message from the UI
            self._remove_message_widget(message['id'])
            
            # Remove from pending messages list
            self.pending_messages = [m for m in self.pending_messages if m['id'] != message['id']]
            
            # Update status
            self.status_label.setText(f"{len(self.pending_messages)} pending messages")
            
        except Exception as e:
            self.logger.exception(f"Error deleting message: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Could not delete message: {str(e)}"
            )
    
    def _remove_message_widget(self, message_id: str):
        """
        Remove a message widget from the UI.
        
        Args:
            message_id: ID of the message to remove
        """
        # Find and remove the widget
        for i in range(self.messages_layout.count() - 1):  # -1 to skip the stretch at the end
            widget = self.messages_layout.itemAt(i).widget()
            if widget and isinstance(widget, PendingMessageWidget) and widget.message_data['id'] == message_id:
                self.messages_layout.removeWidget(widget)
                widget.deleteLater()
                break
    
    def _load_test_data(self):
        """Load test data for development."""
        # Sample test data
        test_messages = [
            {
                'id': '1',
                'type': 'Comment',
                'sender': 'John Doe',
                'time': '2023-07-15 10:30 AM',
                'content': 'Do you have any gluten-free options available?',
                'suggested_response': 'Yes, we offer several gluten-free bread options including our popular rice flour loaf and almond flour sandwich bread. Please visit our store or check our weekly menu online for current availability.',
                'post_id': '123456789',
                'source': 'instagram'
            },
            {
                'id': '2',
                'type': 'Direct Message',
                'sender': 'Jane Smith',
                'time': '2023-07-14 3:45 PM',
                'content': 'What are your store hours on Sundays?',
                'suggested_response': 'Our store is open from 8:00 AM to 2:00 PM on Sundays. We often sell out of popular items by noon, so we recommend coming early for the best selection!',
                'conversation_id': '987654321',
                'source': 'instagram'
            },
            {
                'id': '3',
                'type': 'Comment',
                'sender': 'Mike Johnson',
                'time': '2023-07-13 11:20 AM',
                'content': 'Love your sourdough! Do you ship nationwide?',
                'suggested_response': 'Thank you for the kind words about our sourdough! Currently, we don\'t ship nationwide, but we do offer local delivery within a 25-mile radius of our store. We\'re exploring shipping options for the future!',
                'post_id': '567891234',
                'source': 'instagram'
            }
        ]
        
        # Load the messages
        self._load_messages(test_messages) 