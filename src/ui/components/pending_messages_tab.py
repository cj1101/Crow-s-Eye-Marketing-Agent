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
        
        # Controls section
        controls_layout = QHBoxLayout()
        
        # Filter input
        filter_label = QLabel("Filter:")
        controls_layout.addWidget(filter_label)
        
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter by sender or content...")
        self.filter_input.textChanged.connect(self._on_filter_changed)
        controls_layout.addWidget(self.filter_input)
        
        # Auto-approve checkbox
        self.auto_approve_checkbox = QCheckBox("Auto-approve responses")
        self.auto_approve_checkbox.setToolTip(
            "When enabled, suggested responses will be automatically approved without review."
        )
        self.auto_approve_checkbox.toggled.connect(self._on_auto_approve_toggled)
        controls_layout.addWidget(self.auto_approve_checkbox)
        
        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self._on_refresh)
        controls_layout.addWidget(refresh_button)
        
        main_layout.addLayout(controls_layout)
        
        # Scroll area for messages
        self.messages_scroll_area = QScrollArea()
        self.messages_scroll_area.setWidgetResizable(True)
        
        # Container widget for messages
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setSpacing(10)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.messages_scroll_area.setWidget(self.messages_container)
        main_layout.addWidget(self.messages_scroll_area, 1)  # 1 = stretch factor
        
        # Status label
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)

    def _on_auto_approve_toggled(self, checked: bool):
        """Handle auto-approve checkbox toggled."""
        self.auto_approve = checked
        
        if checked:
            self.status_label.setText("Auto-approve mode enabled.")
            
            # Process any current messages for auto-approval
            self._process_auto_approvals()
        else:
            self.status_label.setText("Auto-approve mode disabled.")
        
        self.logger.info(f"Auto-approve mode {'enabled' if checked else 'disabled'}")
        
    def _on_refresh(self):
        """Refresh the messages list."""
        try:
            self.status_label.setText("Refreshing messages...")
            self._load_messages_data()
        except Exception as e:
            self.logger.exception(f"Error refreshing messages: {e}")
            self.status_label.setText(f"Error refreshing messages: {str(e)}")
            
    def _on_filter_changed(self, text: str):
        """Filter messages based on input text."""
        filter_text = text.lower()
        
        # Show/hide message widgets based on filter
        for i in range(self.messages_layout.count()):
            widget = self.messages_layout.itemAt(i).widget()
            
            if isinstance(widget, PendingMessageWidget):
                message_data = widget.message_data
                
                # Check if message matches filter
                sender_match = filter_text in message_data['sender'].lower()
                content_match = filter_text in message_data['content'].lower()
                
                # Show/hide based on match
                widget.setVisible(sender_match or content_match)
                
        # Update status
        if filter_text:
            visible_count = sum(1 for i in range(self.messages_layout.count()) 
                              if isinstance(self.messages_layout.itemAt(i).widget(), PendingMessageWidget) 
                              and self.messages_layout.itemAt(i).widget().isVisible())
            
            self.status_label.setText(f"Showing {visible_count} of {len(self.pending_messages)} messages matching '{text}'.")
        else:
            self.status_label.setText(f"Showing all {len(self.pending_messages)} messages.")
            
    def _load_messages(self, messages: List[Dict[str, Any]]):
        """Load messages into the UI."""
        # Clear existing messages
        self._clear_messages()
        
        if not messages:
            self.status_label.setText("No pending messages found.")
            return
            
        # Add message widgets
        for message in messages:
            # Check if the message has an ID
            if 'id' not in message:
                message['id'] = f"{message['type']}_{message['sender']}_{message['time']}"
                
            # Create message widget
            message_widget = PendingMessageWidget(message)
            
            # Connect signals
            message_widget.approved.connect(self._on_message_approved)
            message_widget.edited.connect(self._on_message_edited)
            message_widget.deleted.connect(self._on_message_deleted)
            
            # Add to layout
            self.messages_layout.addWidget(message_widget)
            
            # Add to pending messages list
            self.pending_messages.append(message)
            
        # Process auto-approvals if enabled
        if self.auto_approve:
            self._process_auto_approvals()
            
        # Update status
        self.status_label.setText(f"Loaded {len(messages)} pending messages.")
        
    def _load_messages_data(self):
        """Load message data from the messages handler."""
        try:
            if HAS_MESSAGES_HANDLER:
                # Get pending messages from the messages handler
                pending_messages = messages_handler.get_pending_messages()
                self._load_messages(pending_messages)
                
                self.logger.info(f"Loaded {len(pending_messages)} pending messages from handler")
            else:
                # Load test data for development
                self._load_test_data()
                
                self.logger.info("Loaded test message data (messages handler not available)")
                
        except Exception as e:
            self.logger.exception(f"Error loading message data: {e}")
            self.status_label.setText(f"Error loading messages: {str(e)}")
            
            # Load test data as fallback
            self._load_test_data()
            
    def _process_auto_approvals(self):
        """Process auto-approvals for pending messages."""
        if not self.auto_approve:
            return
            
        approved_count = 0
        
        # Process each message
        messages_to_approve = list(self.pending_messages)  # Create a copy
        
        for message in messages_to_approve:
            # Skip messages without a suggested response
            if not message.get('suggested_response'):
                continue
                
            # Attempt to approve the message
            if self._process_message_approval(message):
                approved_count += 1
                
                # Remove from pending messages list
                if message in self.pending_messages:
                    self.pending_messages.remove(message)
                    
                # Remove widget from UI
                self._remove_message_widget(message['id'])
                
        # Update status
        if approved_count > 0:
            self.status_label.setText(f"Auto-approved {approved_count} messages.")
            self.logger.info(f"Auto-approved {approved_count} messages")
            
    def _clear_messages(self):
        """Clear all message widgets."""
        # Remove all message widgets
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Clear pending messages list
        self.pending_messages.clear()
        
    def _on_message_approved(self, message: Dict[str, Any]):
        """Handle message approved signal."""
        try:
            # Process the message approval
            if self._process_message_approval(message):
                # Remove from pending messages list
                if message in self.pending_messages:
                    self.pending_messages.remove(message)
                    
                # Remove widget from UI
                self._remove_message_widget(message['id'])
                
                # Update status
                self.status_label.setText(f"Message approved and sent.")
                self.logger.info(f"Message approved: {message['id']}")
                
                # If messages list is now empty, update status
                if not self.pending_messages:
                    self.status_label.setText("No pending messages remaining.")
            
        except Exception as e:
            self.logger.exception(f"Error approving message: {e}")
            self.status_label.setText(f"Error approving message: {str(e)}")
            
    def _process_message_approval(self, message: Dict[str, Any]) -> bool:
        """
        Process the approval of a message.
        
        Args:
            message: The message data dictionary
            
        Returns:
            bool: True if approval was successful, False otherwise
        """
        try:
            if HAS_MESSAGES_HANDLER:
                # Get the response text
                response_text = message.get('final_response', message.get('suggested_response', ''))
                
                if not response_text:
                    QMessageBox.warning(
                        self,
                        "Empty Response",
                        "Cannot approve a message with an empty response."
                    )
                    return False
                
                # Send the response using the messages handler
                success = messages_handler.send_response(
                    message['id'],
                    response_text,
                    message['type']
                )
                
                if not success:
                    QMessageBox.warning(
                        self,
                        "Response Failed",
                        "Failed to send the response. Please try again later."
                    )
                    return False
                
                return True
            else:
                # Simulate successful approval for development
                self.logger.info(f"Simulated approval: {message['id']}")
                
                # Show confirmation
                QMessageBox.information(
                    self,
                    "Response Simulated",
                    f"Response would be sent: {message.get('final_response', message.get('suggested_response', ''))}"
                )
                
                return True
                
        except Exception as e:
            self.logger.exception(f"Error in message approval process: {e}")
            QMessageBox.critical(
                self,
                "Approval Error",
                f"Error processing message approval: {str(e)}"
            )
            return False
            
    def _on_message_edited(self, message: Dict[str, Any], edited_response: str):
        """Handle message edited signal."""
        try:
            # Create a copy with the edited response
            edited_message = dict(message)
            edited_message['final_response'] = edited_response
            
            # Process the message approval
            if self._process_message_approval(edited_message):
                # Remove from pending messages list
                if message in self.pending_messages:
                    self.pending_messages.remove(message)
                    
                # Remove widget from UI
                self._remove_message_widget(message['id'])
                
                # Update status
                self.status_label.setText(f"Edited message approved and sent.")
                self.logger.info(f"Edited message approved: {message['id']}")
                
                # If messages list is now empty, update status
                if not self.pending_messages:
                    self.status_label.setText("No pending messages remaining.")
            
        except Exception as e:
            self.logger.exception(f"Error processing edited message: {e}")
            self.status_label.setText(f"Error processing edited message: {str(e)}")
            
    def _on_message_deleted(self, message: Dict[str, Any]):
        """Handle message deleted signal."""
        try:
            # Check if we should notify the messages handler
            if HAS_MESSAGES_HANDLER:
                # Mark message as deleted/dismissed
                messages_handler.dismiss_message(message['id'])
                
            # Remove from pending messages list
            if message in self.pending_messages:
                self.pending_messages.remove(message)
                
            # Remove widget from UI
            self._remove_message_widget(message['id'])
            
            # Update status
            remaining = len(self.pending_messages)
            self.status_label.setText(f"Message deleted. {remaining} message(s) remaining.")
            self.logger.info(f"Message deleted: {message['id']}")
            
            # If messages list is now empty, update status
            if not self.pending_messages:
                self.status_label.setText("No pending messages remaining.")
                
        except Exception as e:
            self.logger.exception(f"Error deleting message: {e}")
            self.status_label.setText(f"Error deleting message: {str(e)}")
            
    def _remove_message_widget(self, message_id: str):
        """Remove a message widget from the UI."""
        # Find and remove the widget with the matching message ID
        for i in range(self.messages_layout.count()):
            widget = self.messages_layout.itemAt(i).widget()
            
            if isinstance(widget, PendingMessageWidget) and widget.message_data['id'] == message_id:
                # Remove widget from layout
                self.messages_layout.takeAt(i)
                widget.deleteLater()
                break
                
    def _load_test_data(self):
        """Load test message data for development."""
        # Create sample messages
        test_messages = [
            {
                'id': 'comment_1',
                'type': 'Comment',
                'sender': 'John Smith',
                'content': 'Do you have gluten-free options?',
                'time': '2023-05-25 14:30',
                'suggested_response': 'Yes! We offer several gluten-free bread options. Our buckwheat loaf and rice flour rolls are completely gluten-free and made in a dedicated gluten-free section of our kitchen to prevent cross-contamination.'
            },
            {
                'id': 'dm_1',
                'type': 'Direct Message',
                'sender': 'BreadLover42',
                'content': 'What time do you close on Saturdays?',
                'time': '2023-05-26 09:15',
                'suggested_response': 'We close at 6 PM on Saturdays. Our fresh-baked items are usually available all day, but for the best selection, we recommend visiting before 3 PM when we typically have our full range of products available!'
            },
            {
                'id': 'comment_2',
                'type': 'Comment',
                'sender': 'Sarah Johnson',
                'content': 'Your sourdough looks amazing! What's your secret?',
                'time': '2023-05-26 16:45',
                'suggested_response': 'Thank you for the kind words! Our sourdough is made with a 100-year-old starter that's been carefully maintained. We use organic flour and a 24-hour fermentation process to develop that complex flavor and perfect texture. Come in for a free sample anytime!'
            }
        ]
        
        # Load the test messages
        self._load_messages(test_messages) 