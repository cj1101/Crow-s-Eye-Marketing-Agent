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
from PySide6.QtCore import Qt, Signal, QSize, QEvent
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
        
        self._init_ui_elements()
        self._create_ui()
        self.retranslateUi() # Initial translation
        
    def _init_ui_elements(self):
        self.source_label = QLabel()
        self.from_label = QLabel()
        self.time_label = QLabel()
        self.message_intro_label = QLabel() # For "Message:"
        self.message_text_edit = QTextEdit()
        self.response_intro_label = QLabel() # For "Suggested Response:"
        self.response_text_edit = QTextEdit()
        self.approve_button = QPushButton()
        self.edit_button = QPushButton()
        self.delete_button = QPushButton()

    def _create_ui(self):
        """Create the widget UI."""
        main_layout = QVBoxLayout(self)
        message_frame = QFrame()
        message_frame.setFrameShape(QFrame.Shape.StyledPanel)
        message_frame.setLineWidth(1)
        message_layout = QVBoxLayout(message_frame)
        info_layout = QHBoxLayout()
        
        # self.source_label = QLabel(f"<b>{self.message_data['type']}:</b>") // Text set in retranslateUi
        info_layout.addWidget(self.source_label)
        # self.from_label = QLabel(f"From: <b>{self.message_data['sender']}</b>") // Text set in retranslateUi
        info_layout.addWidget(self.from_label)
        # self.time_label = QLabel(f"Time: {self.message_data['time']}") // Text set in retranslateUi
        info_layout.addWidget(self.time_label)
        info_layout.addStretch()
        message_layout.addLayout(info_layout)
        
        # self.message_intro_label = QLabel("<b>Message:</b>") // Text set in retranslateUi
        message_layout.addWidget(self.message_intro_label)
        # self.message_text_edit = QTextEdit() // Initialized
        self.message_text_edit.setReadOnly(True)
        self.message_text_edit.setPlainText(self.message_data['content']) # Content is dynamic
        self.message_text_edit.setMaximumHeight(80)
        message_layout.addWidget(self.message_text_edit)
        
        # self.response_intro_label = QLabel("<b>Suggested Response:</b>") // Text set in retranslateUi
        message_layout.addWidget(self.response_intro_label)
        # self.response_text_edit = QTextEdit() // Initialized
        self.response_text_edit.setPlainText(self.message_data['suggested_response']) # Content is dynamic
        self.response_text_edit.setMaximumHeight(100)
        message_layout.addWidget(self.response_text_edit)
        
        buttons_layout = QHBoxLayout()
        # self.approve_button = QPushButton("Approve") // Text set in retranslateUi
        self.approve_button.clicked.connect(self._on_approve)
        buttons_layout.addWidget(self.approve_button)
        # self.edit_button = QPushButton("Edit & Approve") // Text set in retranslateUi
        self.edit_button.clicked.connect(self._on_edit)
        buttons_layout.addWidget(self.edit_button)
        # self.delete_button = QPushButton("Delete") // Text set in retranslateUi
        self.delete_button.clicked.connect(self._on_delete)
        buttons_layout.addWidget(self.delete_button)
        message_layout.addLayout(buttons_layout)
        main_layout.addWidget(message_frame)
        
    def _on_approve(self):
        """Approve the response without editing."""
        try:
            message = dict(self.message_data)
            message['final_response'] = message['suggested_response']
            self.approved.emit(message)
        except Exception as e:
            self.logger.exception(f"Error approving message: {e}")
            QMessageBox.warning(self, self.tr("Error"), self.tr("Could not approve message: {error_message}").format(error_message=str(e)))
    
    def _on_edit(self):
        """Edit and approve the response."""
        try:
            edited_response = self.response_text_edit.toPlainText().strip()
            if not edited_response:
                QMessageBox.warning(self, self.tr("Empty Response"), self.tr("Please provide a response before approving."))
                return
            message = dict(self.message_data)
            self.edited.emit(message, edited_response)
        except Exception as e:
            self.logger.exception(f"Error editing message: {e}")
            QMessageBox.warning(self, self.tr("Error"), self.tr("Could not edit message: {error_message}").format(error_message=str(e)))
    
    def _on_delete(self):
        """Delete the message."""
        try:
            result = QMessageBox.question(
                self,
                self.tr("Confirm Deletion"), 
                self.tr("Are you sure you want to delete this message?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if result == QMessageBox.StandardButton.Yes:
                self.deleted.emit(self.message_data)
        except Exception as e:
            self.logger.exception(f"Error deleting message: {e}")
            QMessageBox.warning(self, self.tr("Error"), self.tr("Could not delete message: {error_message}").format(error_message=str(e)))

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        """Retranslate all UI elements in PendingMessageWidget."""
        # Dynamic parts of labels need to be reconstructed
        self.source_label.setText(self.tr("<b>{message_type}:</b>").format(message_type=self.message_data['type']))
        self.from_label.setText(self.tr("From: <b>{sender}</b>").format(sender=self.message_data['sender']))
        self.time_label.setText(self.tr("Time: {time}").format(time=self.message_data['time']))
        self.message_intro_label.setText(self.tr("<b>Message:</b>"))
        self.response_intro_label.setText(self.tr("<b>Suggested Response:</b>"))
        self.approve_button.setText(self.tr("Approve"))
        self.edit_button.setText(self.tr("Edit & Approve"))
        self.delete_button.setText(self.tr("Delete"))

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
        
        # Initialize UI elements
        self._init_ui_elements()
        
        # Create UI
        self._create_ui()

        # Initial translation
        self.retranslateUi()
        
        # Load messages data
        self._load_messages_data()

    def _init_ui_elements(self):
        """Initialize UI elements for translatability."""
        self.filter_label = QLabel()
        self.filter_input = QLineEdit()
        self.auto_approve_checkbox = QCheckBox()
        self.refresh_button = QPushButton()
        self.messages_scroll_area = QScrollArea()
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container) # Keep as is, layout for dynamic content
        self.status_label = QLabel()
        
    def _create_ui(self):
        """Create the tab UI."""
        main_layout = QVBoxLayout(self)
        
        # Controls section
        controls_layout = QHBoxLayout()
        
        # Filter input
        # self.filter_label = QLabel("Filter:") // Text set in retranslateUi
        controls_layout.addWidget(self.filter_label)
        
        # self.filter_input = QLineEdit() // Initialized
        # self.filter_input.setPlaceholderText("Filter by sender or content...") // Text set in retranslateUi
        self.filter_input.textChanged.connect(self._on_filter_changed)
        controls_layout.addWidget(self.filter_input)
        
        # Auto-approve checkbox
        # self.auto_approve_checkbox = QCheckBox("Auto-approve responses") // Text set in retranslateUi
        # self.auto_approve_checkbox.setToolTip( // Tooltip set in retranslateUi
        # "When enabled, suggested responses will be automatically approved without review."
        # )
        self.auto_approve_checkbox.toggled.connect(self._on_auto_approve_toggled)
        controls_layout.addWidget(self.auto_approve_checkbox)
        
        # Refresh button
        # self.refresh_button = QPushButton("Refresh") // Text set in retranslateUi
        self.refresh_button.clicked.connect(self._on_refresh)
        controls_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(controls_layout)
        
        # Scroll area for messages
        # self.messages_scroll_area = QScrollArea() // Initialized
        self.messages_scroll_area.setWidgetResizable(True)
        
        # Container widget for messages
        # self.messages_container = QWidget() // Initialized
        # self.messages_layout = QVBoxLayout(self.messages_container) // Initialized
        self.messages_layout.setSpacing(10)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.messages_scroll_area.setWidget(self.messages_container)
        main_layout.addWidget(self.messages_scroll_area, 1)  # 1 = stretch factor
        
        # Status label
        # self.status_label = QLabel("Ready") // Text set in retranslateUi
        main_layout.addWidget(self.status_label)

    def changeEvent(self, event: QEvent) -> None:
        """Handle language change event."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        """Retranslate all UI elements in PendingMessagesTab."""
        self.filter_label.setText(self.tr("Filter:"))
        self.filter_input.setPlaceholderText(self.tr("Filter by sender or content..."))
        self.auto_approve_checkbox.setText(self.tr("Auto-approve responses"))
        self.auto_approve_checkbox.setToolTip(
            self.tr("When enabled, suggested responses will be automatically approved without review.")
        )
        self.refresh_button.setText(self.tr("Refresh"))
        self.status_label.setText(self.tr("Ready")) # Initial status

    def _on_auto_approve_toggled(self, checked: bool):
        """Handle auto-approve checkbox toggled."""
        self.auto_approve = checked
        
        if checked:
            self.status_label.setText(self.tr("Auto-approve mode enabled."))
            
            # Process any current messages for auto-approval
            self._process_auto_approvals()
        else:
            self.status_label.setText(self.tr("Auto-approve mode disabled."))
        
        self.logger.info(f"Auto-approve mode {'enabled' if checked else 'disabled'}")
        
    def _on_refresh(self):
        """Refresh the messages list."""
        try:
            self.status_label.setText(self.tr("Refreshing messages..."))
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
        self._clear_messages()
        if not messages:
            self.status_label.setText(self.tr("No pending messages found."))
            return

        if HAS_MESSAGES_HANDLER:
            self.status_label.setText(self.tr("Loading messages..."))
        else:
            self.status_label.setText(self.tr("Displaying test data (messages_handler not found)."))
            
        for msg_data in messages:
            widget = PendingMessageWidget(msg_data)
            
            # Connect signals
            widget.approved.connect(self._on_message_approved)
            widget.edited.connect(self._on_message_edited)
            widget.deleted.connect(self._on_message_deleted)
            
            # Add to layout
            self.messages_layout.addWidget(widget)
            
            # Add to pending messages list
            self.pending_messages.append(msg_data)
            
        # Process auto-approvals if enabled
        if self.auto_approve:
            self._process_auto_approvals()
            
        # Update status
        self.status_label.setText(f"Loaded {len(messages)} pending messages.")
        
    def _load_messages_data(self):
        """Load messages from the handler or test data."""
        if HAS_MESSAGES_HANDLER:
            try:
                self.status_label.setText(self.tr("Fetching messages from handler..."))
                # Ensure messages_handler is available
                if messages_handler is None:
                    self.logger.error("messages_handler is None even though HAS_MESSAGES_HANDLER is True.")
                    QMessageBox.critical(self, self.tr("Error"), self.tr("Messages handler is not available. Cannot load messages."))
                    self.status_label.setText(self.tr("Error: Messages handler not available."))
                    return

                self.pending_messages = messages_handler.get_pending_messages()
                self._load_messages(self.pending_messages)
                if not self.pending_messages: # Check after loading
                     self.status_label.setText(self.tr("No new messages from handler."))
                else:
                    self.status_label.setText(self.tr("Messages loaded from handler."))

            except Exception as e:
                self.logger.exception(f"Error loading messages from handler: {e}")
                QMessageBox.critical(self, self.tr("Error"), self.tr("Could not load messages from handler: {error_message}").format(error_message=str(e)))
                self.status_label.setText(self.tr("Error loading messages from handler."))
        else:
            # Fallback to test data if handler not available
            self.status_label.setText(self.tr("Messages handler not found. Loading test data."))
            self._load_test_data()
            
    def _process_auto_approvals(self):
        """Process auto-approvals for currently loaded messages."""
        if not self.auto_approve:
            return
        
        if not self.pending_messages:
            self.status_label.setText(self.tr("Auto-approve: No messages to process."))
            return

        approved_count = 0
        self.status_label.setText(self.tr("Auto-approving messages..."))
        for message_data in list(self.pending_messages): # Iterate over a copy
            if message_data.get('suggested_response'):
                # Simulate approval process
                if self._process_message_approval(message_data): # Use the existing approval logic
                    approved_count += 1
                    self._remove_message_widget(message_data['id']) # Remove from UI

        if approved_count > 0:
            self.status_label.setText(self.tr("{count} messages auto-approved.").format(count=approved_count))
        else:
            self.status_label.setText(self.tr("Auto-approve: No messages met criteria for auto-approval."))
            
        # Refresh the view if any messages were auto-approved
        if approved_count > 0:
            self._load_messages(self.pending_messages) # Re-load to update UI

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
        """Handle message approval from widget."""
        try:
            if self._process_message_approval(message):
                self.status_label.setText(self.tr("Message approved and sent: {message_id}").format(message_id=message.get('id', 'N/A')))
                self._remove_message_widget(message['id'])
            else:
                # _process_message_approval already shows an error message box
                self.status_label.setText(self.tr("Failed to approve message: {message_id}").format(message_id=message.get('id', 'N/A')))

        except Exception as e:
            self.logger.exception(f"Error during message approval: {e}")
            QMessageBox.warning(self, self.tr("Approval Error"), self.tr("An unexpected error occurred during message approval: {error_message}").format(error_message=str(e)))
            self.status_label.setText(self.tr("Error during approval."))

    def _process_message_approval(self, message: Dict[str, Any]) -> bool:
        """Process the approval of a single message, sending it via the handler."""
        if not HAS_MESSAGES_HANDLER:
            self.logger.warning("Cannot process message approval: messages_handler not available.")
            QMessageBox.warning(self, self.tr("Handler Missing"), self.tr("Cannot send message: Messages handler is not configured."))
            return False

        try:
            # Ensure messages_handler is available
            if messages_handler is None:
                self.logger.error("messages_handler is None even though HAS_MESSAGES_HANDLER is True.")
                QMessageBox.critical(self, self.tr("Error"), self.tr("Messages handler is not available. Cannot process approval."))
                return False

            success = messages_handler.send_response(
                message_id=message['id'], 
                response_text=message['final_response'], 
                message_type=message['type']
            )
            if success:
                self.logger.info(f"Message {message['id']} approved and response sent.")
                # Remove from internal list after successful send
                self.pending_messages = [m for m in self.pending_messages if m['id'] != message['id']]
                return True
            else:
                self.logger.error(f"Failed to send response for message {message['id']}.")
                QMessageBox.warning(self, self.tr("Send Error"), self.tr("Failed to send response for message {message_id}.").format(message_id=message['id']))
                return False
        except Exception as e:
            self.logger.exception(f"Error sending response for message {message['id']}: {e}")
            QMessageBox.critical(self, self.tr("Send Error"), self.tr("An error occurred while sending response for {message_id}: {error_message}").format(message_id=message['id'], error_message=str(e)))
            return False

    def _on_message_edited(self, message: Dict[str, Any], edited_response: str):
        """Handle message editing and approval from widget."""
        try:
            message_copy = dict(message) # Work with a copy
            message_copy['final_response'] = edited_response

            if self._process_message_approval(message_copy): # Use the same approval logic
                self.status_label.setText(self.tr("Message edited, approved, and sent: {message_id}").format(message_id=message_copy.get('id', 'N/A')))
                self._remove_message_widget(message_copy['id'])
            else:
                # _process_message_approval already shows an error message box
                self.status_label.setText(self.tr("Failed to process edited message: {message_id}").format(message_id=message_copy.get('id', 'N/A')))
        
        except Exception as e:
            self.logger.exception(f"Error during message edit and approval: {e}")
            QMessageBox.warning(self, self.tr("Edit Error"), self.tr("An unexpected error occurred during message edit and approval: {error_message}").format(error_message=str(e)))
            self.status_label.setText(self.tr("Error during edit and approval."))


    def _on_message_deleted(self, message: Dict[str, Any]):
        """Handle message deletion from widget."""
        if not HAS_MESSAGES_HANDLER:
            self.logger.warning("Cannot process message deletion: messages_handler not available.")
            # For local deletion even without handler:
            # self.pending_messages = [m for m in self.pending_messages if m['id'] != message['id']]
            # self._remove_message_widget(message['id'])
            # self.status_label.setText(self.tr("Message {message_id} removed locally (handler not available).").format(message_id=message['id']))
            QMessageBox.warning(self, self.tr("Handler Missing"), self.tr("Cannot properly delete message: Messages handler is not configured. Message removed from view only."))
            # Still remove from view
            self.pending_messages = [m for m in self.pending_messages if m['id'] != message['id']]
            self._remove_message_widget(message['id'])
            self.status_label.setText(self.tr("Message {message_id} removed from view (handler not available).").format(message_id=message['id']))

            return

        try:
            # Ensure messages_handler is available
            if messages_handler is None:
                self.logger.error("messages_handler is None even though HAS_MESSAGES_HANDLER is True.")
                QMessageBox.critical(self, self.tr("Error"), self.tr("Messages handler is not available. Cannot process deletion."))
                return

            success = messages_handler.delete_message(message_id=message['id'], message_type=message['type'])
            if success:
                self.logger.info(f"Message {message['id']} deleted successfully via handler.")
                self.status_label.setText(self.tr("Message deleted: {message_id}").format(message_id=message.get('id', 'N/A')))
                # Remove from internal list and UI
                self.pending_messages = [m for m in self.pending_messages if m['id'] != message['id']]
                self._remove_message_widget(message['id'])
            else:
                self.logger.error(f"Failed to delete message {message['id']} via handler.")
                QMessageBox.warning(self, self.tr("Deletion Error"), self.tr("Failed to delete message {message_id} via handler.").format(message_id=message['id']))
                self.status_label.setText(self.tr("Failed to delete message via handler: {message_id}").format(message_id=message.get('id', 'N/A')))

        except Exception as e:
            self.logger.exception(f"Error deleting message {message['id']} via handler: {e}")
            QMessageBox.critical(self, self.tr("Deletion Error"), self.tr("An error occurred while deleting message {message_id} via handler: {error_message}").format(message_id=message['id'], error_message=str(e)))
            self.status_label.setText(self.tr("Error during message deletion via handler."))

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
                'content': 'Your sourdough looks amazing! What\'s your secret?',
                'time': '2023-05-26 16:45',
                'suggested_response': 'Thank you for the kind words! Our sourdough is made with a 100-year-old starter that\'s been carefully maintained. We use organic flour and a 24-hour fermentation process to develop that complex flavor and perfect texture. Come in for a free sample anytime!'
            }
        ]
        
        # Load the test messages
        self._load_messages(test_messages) 