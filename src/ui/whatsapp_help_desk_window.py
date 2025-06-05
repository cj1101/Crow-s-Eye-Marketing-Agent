"""
WhatsApp Help Desk Window - Main interface for managing WhatsApp virtual assistant.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit, QPushButton,
    QLabel, QGroupBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QProgressBar, QFrame, QScrollArea,
    QFormLayout, QComboBox, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, pyqtSignal
from PySide6.QtGui import QFont, QPixmap, QIcon, QTextCharFormat, QBrush, QColor

from .base_window import BaseMainWindow
from .whatsapp_settings_dialog import WhatsAppSettingsDialog
from ..api.whatsapp.whatsapp_api_handler import WhatsAppAPIHandler
from ..api.whatsapp.whatsapp_virtual_assistant import WhatsAppVirtualAssistant
from ..api.whatsapp.whatsapp_webhook_handler import WhatsAppWebhookHandler

class ConversationItem(QListWidgetItem):
    """Custom list item for conversations."""
    
    def __init__(self, user_id: str, user_info: Dict[str, Any], last_message: str = ""):
        super().__init__()
        self.user_id = user_id
        self.user_info = user_info
        self.last_message = last_message
        self.unread_count = 0
        self.escalated = user_info.get('escalated', False)
        
        self.update_display()
    
    def update_display(self):
        """Update the display text for this conversation."""
        name = self.user_info.get('name', 'Unknown')
        phone = self.user_id
        
        # Format display text
        display_text = f"{name}\n{phone}"
        if self.last_message:
            # Truncate long messages
            message_preview = self.last_message[:50] + "..." if len(self.last_message) > 50 else self.last_message
            display_text += f"\n{message_preview}"
        
        if self.unread_count > 0:
            display_text += f" ({self.unread_count})"
        
        if self.escalated:
            display_text = "🚨 " + display_text
        
        self.setText(display_text)
        
        # Set styling based on status
        if self.escalated:
            self.setBackground(QBrush(QColor(255, 248, 220)))  # Light orange for escalated
        elif self.unread_count > 0:
            self.setBackground(QBrush(QColor(240, 248, 255)))  # Light blue for unread
        else:
            self.setBackground(QBrush(QColor(255, 255, 255)))  # White for normal

class WhatsAppHelpDeskWindow(BaseMainWindow):
    """Main window for WhatsApp Help Desk functionality."""
    
    # Signals
    conversation_selected = Signal(str)  # user_id
    message_sent = Signal(str, str)  # user_id, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize WhatsApp components
        self.api_handler = WhatsAppAPIHandler()
        self.virtual_assistant = WhatsAppVirtualAssistant(self.api_handler)
        self.webhook_handler = WhatsAppWebhookHandler(self.api_handler, self.virtual_assistant)
        
        # State
        self.current_conversation = None
        self.conversations = {}
        self.is_webhook_running = False
        
        # UI Components
        self.conversations_list = None
        self.chat_display = None
        self.message_input = None
        self.send_button = None
        self.stats_labels = {}
        
        self.setWindowTitle("WhatsApp Virtual Help Desk")
        self.setMinimumSize(1200, 800)
        
        self.setup_ui()
        self.setup_connections()
        self.setup_timers()
        
        # Load initial data
        self.refresh_conversations()
        self.check_webhook_status()
        
        self.logger.info("WhatsApp Help Desk window initialized")
    
    def setup_ui(self):
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Header with title and controls
        self.create_header(main_layout)
        
        # Status bar
        self.create_status_bar(main_layout)
        
        # Main content area
        self.create_main_content(main_layout)
        
        # Apply styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
    
    def create_header(self, main_layout: QVBoxLayout):
        """Create header with title and action buttons."""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_layout = QHBoxLayout(header_frame)
        
        # Title
        title_label = QLabel("📱 WhatsApp Virtual Help Desk")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; padding: 10px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Action buttons
        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        self.webhook_toggle_btn = QPushButton("🔗 Start Webhook")
        self.webhook_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        
        header_layout.addWidget(self.settings_btn)
        header_layout.addWidget(self.webhook_toggle_btn)
        header_layout.addWidget(self.refresh_btn)
        
        main_layout.addWidget(header_frame)
    
    def create_status_bar(self, main_layout: QVBoxLayout):
        """Create status bar with connection and activity info."""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        status_frame.setMaximumHeight(80)
        status_layout = QHBoxLayout(status_frame)
        
        # Connection status
        self.connection_status_label = QLabel("❌ Not Connected")
        self.connection_status_label.setStyleSheet("font-weight: bold; color: #e74c3c; padding: 5px;")
        status_layout.addWidget(QLabel("Status:"))
        status_layout.addWidget(self.connection_status_label)
        
        status_layout.addWidget(QFrame())  # Separator
        
        # Statistics
        self.stats_labels['conversations'] = QLabel("0")
        self.stats_labels['messages_today'] = QLabel("0")
        self.stats_labels['escalated'] = QLabel("0")
        
        status_layout.addWidget(QLabel("Conversations:"))
        status_layout.addWidget(self.stats_labels['conversations'])
        status_layout.addWidget(QLabel("Messages Today:"))
        status_layout.addWidget(self.stats_labels['messages_today'])
        status_layout.addWidget(QLabel("Escalated:"))
        status_layout.addWidget(self.stats_labels['escalated'])
        
        status_layout.addStretch()
        
        main_layout.addWidget(status_frame)
    
    def create_main_content(self, main_layout: QVBoxLayout):
        """Create main content area with conversations and chat."""
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Conversations tab
        self.create_conversations_tab()
        
        # Analytics tab
        self.create_analytics_tab()
        
        # Logs tab
        self.create_logs_tab()
    
    def create_conversations_tab(self):
        """Create the conversations management tab."""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Conversations list
        self.create_conversations_panel(splitter)
        
        # Right panel - Chat interface
        self.create_chat_panel(splitter)
        
        # Set initial splitter sizes (30% for conversations, 70% for chat)
        splitter.setSizes([300, 700])
        
        self.tab_widget.addTab(tab, "💬 Conversations")
    
    def create_conversations_panel(self, parent):
        """Create conversations list panel."""
        conversations_widget = QWidget()
        conversations_layout = QVBoxLayout(conversations_widget)
        
        # Header
        conversations_header = QLabel("Active Conversations")
        conversations_header.setFont(QFont("Arial", 12, QFont.Bold))
        conversations_header.setStyleSheet("color: #2c3e50; padding: 5px;")
        conversations_layout.addWidget(conversations_header)
        
        # Search/filter
        self.conversations_search = QLineEdit()
        self.conversations_search.setPlaceholderText("Search conversations...")
        self.conversations_search.setStyleSheet("padding: 5px; border: 1px solid #bdc3c7; border-radius: 3px;")
        conversations_layout.addWidget(self.conversations_search)
        
        # Conversations list
        self.conversations_list = QListWidget()
        self.conversations_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #ecf0f1;
            }
        """)
        conversations_layout.addWidget(self.conversations_list)
        
        # Conversation actions
        actions_layout = QHBoxLayout()
        
        self.escalate_btn = QPushButton("🚨 Escalate")
        self.escalate_btn.setEnabled(False)
        self.escalate_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        
        self.resolve_btn = QPushButton("✅ Resolve")
        self.resolve_btn.setEnabled(False)
        self.resolve_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        
        actions_layout.addWidget(self.escalate_btn)
        actions_layout.addWidget(self.resolve_btn)
        actions_layout.addStretch()
        
        conversations_layout.addLayout(actions_layout)
        
        parent.addWidget(conversations_widget)
    
    def create_chat_panel(self, parent):
        """Create chat interface panel."""
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        
        # Chat header
        self.chat_header_label = QLabel("Select a conversation to start chatting")
        self.chat_header_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.chat_header_label.setStyleSheet("color: #2c3e50; padding: 10px; background-color: #ecf0f1; border-radius: 3px;")
        chat_layout.addWidget(self.chat_header_label)
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
            }
        """)
        chat_layout.addWidget(self.chat_display)
        
        # Message input area
        input_frame = QFrame()
        input_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        input_layout = QHBoxLayout(input_frame)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setEnabled(False)
        self.message_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                font-size: 12px;
            }
        """)
        
        self.send_button = QPushButton("Send")
        self.send_button.setEnabled(False)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        
        # Quick reply buttons
        self.quick_reply_layout = QHBoxLayout()
        self.create_quick_reply_buttons()
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        
        chat_layout.addWidget(input_frame)
        chat_layout.addLayout(self.quick_reply_layout)
        
        parent.addWidget(chat_widget)
    
    def create_quick_reply_buttons(self):
        """Create quick reply buttons for common responses."""
        quick_replies = [
            ("👋 Greeting", "Hello! How can I help you today?"),
            ("⏰ Hours", f"Our business hours are {self.virtual_assistant.business_info['contact']['hours']}"),
            ("📞 Contact", f"You can reach us at {self.virtual_assistant.business_info['contact']['phone']} or {self.virtual_assistant.business_info['contact']['email']}"),
            ("🔄 Transfer", "Let me connect you with one of our team members who can better assist you."),
        ]
        
        for text, message in quick_replies:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #95a5a6;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                    margin: 2px;
                }
                QPushButton:hover {
                    background-color: #7f8c8d;
                }
            """)
            btn.clicked.connect(lambda checked, msg=message: self.insert_quick_reply(msg))
            self.quick_reply_layout.addWidget(btn)
        
        self.quick_reply_layout.addStretch()
    
    def create_analytics_tab(self):
        """Create analytics and performance tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Performance metrics
        metrics_group = QGroupBox("Performance Metrics")
        metrics_layout = QFormLayout(metrics_group)
        
        self.metrics_labels = {
            'total_conversations': QLabel("0"),
            'avg_response_time': QLabel("0s"),
            'resolution_rate': QLabel("0%"),
            'satisfaction_score': QLabel("N/A"),
            'escalation_rate': QLabel("0%")
        }
        
        metrics_layout.addRow("Total Conversations:", self.metrics_labels['total_conversations'])
        metrics_layout.addRow("Avg Response Time:", self.metrics_labels['avg_response_time'])
        metrics_layout.addRow("Resolution Rate:", self.metrics_labels['resolution_rate'])
        metrics_layout.addRow("Customer Satisfaction:", self.metrics_labels['satisfaction_score'])
        metrics_layout.addRow("Escalation Rate:", self.metrics_labels['escalation_rate'])
        
        layout.addWidget(metrics_group)
        
        # Recent activity
        activity_group = QGroupBox("Recent Activity")
        activity_layout = QVBoxLayout(activity_group)
        
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(4)
        self.activity_table.setHorizontalHeaderLabels(["Time", "User", "Action", "Details"])
        self.activity_table.horizontalHeader().setStretchLastSection(True)
        self.activity_table.setAlternatingRowColors(True)
        
        activity_layout.addWidget(self.activity_table)
        layout.addWidget(activity_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "📊 Analytics")
    
    def create_logs_tab(self):
        """Create logs and debugging tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Log controls
        controls_layout = QHBoxLayout()
        
        log_level_combo = QComboBox()
        log_level_combo.addItems(["All", "Info", "Warning", "Error"])
        controls_layout.addWidget(QLabel("Filter:"))
        controls_layout.addWidget(log_level_combo)
        
        clear_logs_btn = QPushButton("Clear Logs")
        clear_logs_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        controls_layout.addWidget(clear_logs_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Logs display
        self.logs_display = QTextEdit()
        self.logs_display.setReadOnly(True)
        self.logs_display.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(self.logs_display)
        
        self.tab_widget.addTab(tab, "📋 Logs")
    
    def setup_connections(self):
        """Setup signal connections."""
        # UI connections
        self.settings_btn.clicked.connect(self.show_settings)
        self.webhook_toggle_btn.clicked.connect(self.toggle_webhook)
        self.refresh_btn.clicked.connect(self.refresh_conversations)
        
        self.conversations_list.currentItemChanged.connect(self.on_conversation_selected)
        self.conversations_search.textChanged.connect(self.filter_conversations)
        
        self.send_button.clicked.connect(self.send_message)
        self.message_input.returnPressed.connect(self.send_message)
        
        self.escalate_btn.clicked.connect(self.escalate_conversation)
        self.resolve_btn.clicked.connect(self.resolve_conversation)
        
        # WhatsApp API connections
        self.api_handler.signals.message_sent.connect(self.on_message_sent)
        self.api_handler.signals.error_occurred.connect(self.on_api_error)
        
        self.virtual_assistant.signals.response_generated.connect(self.on_ai_response)
        self.virtual_assistant.signals.escalation_requested.connect(self.on_escalation_requested)
        self.virtual_assistant.signals.conversation_started.connect(self.on_conversation_started)
        
        self.webhook_handler.signals.message_received.connect(self.on_webhook_message)
        self.webhook_handler.signals.webhook_error.connect(self.on_webhook_error)
    
    def setup_timers(self):
        """Setup periodic update timers."""
        # Refresh timer for updating UI every 30 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_ui_stats)
        self.refresh_timer.start(30000)  # 30 seconds
        
        # Connection check timer every 5 minutes
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.check_connection_status)
        self.connection_timer.start(300000)  # 5 minutes
    
    def show_settings(self):
        """Show WhatsApp settings dialog."""
        dialog = WhatsAppSettingsDialog(self)
        dialog.settings_saved.connect(self.on_settings_saved)
        dialog.exec()
    
    def toggle_webhook(self):
        """Toggle webhook server on/off."""
        try:
            if self.is_webhook_running:
                self.webhook_handler.stop_server()
                self.webhook_toggle_btn.setText("🔗 Start Webhook")
                self.webhook_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #27ae60;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #229954;
                    }
                """)
                self.is_webhook_running = False
                self.add_log("Webhook server stopped")
            else:
                self.webhook_handler.start_server(port=5000)
                self.webhook_toggle_btn.setText("🔗 Stop Webhook")
                self.webhook_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #e74c3c;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #c0392b;
                    }
                """)
                self.is_webhook_running = True
                self.add_log("Webhook server started on port 5000")
                
        except Exception as e:
            QMessageBox.critical(self, "Webhook Error", f"Error toggling webhook: {str(e)}")
            self.add_log(f"Webhook error: {str(e)}")
    
    def refresh_conversations(self):
        """Refresh conversations list."""
        try:
            # Get active conversations from virtual assistant
            active_conversations = self.virtual_assistant.get_active_conversations()
            
            self.conversations_list.clear()
            self.conversations = {}
            
            for conv_summary in active_conversations:
                if conv_summary:
                    user_id = conv_summary['user_id']
                    self.conversations[user_id] = conv_summary
                    
                    item = ConversationItem(
                        user_id=user_id,
                        user_info=conv_summary['user_info'],
                        last_message=f"Messages: {conv_summary['message_count']}"
                    )
                    item.escalated = conv_summary.get('escalated', False)
                    
                    self.conversations_list.addItem(item)
            
            self.update_ui_stats()
            self.add_log(f"Refreshed {len(active_conversations)} conversations")
            
        except Exception as e:
            self.add_log(f"Error refreshing conversations: {str(e)}")
    
    def filter_conversations(self, text: str):
        """Filter conversations list based on search text."""
        for i in range(self.conversations_list.count()):
            item = self.conversations_list.item(i)
            if text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def on_conversation_selected(self, current: ConversationItem, previous):
        """Handle conversation selection."""
        if current:
            self.current_conversation = current.user_id
            self.chat_header_label.setText(f"Chat with {current.user_info.get('name', 'Unknown')} ({current.user_id})")
            
            # Enable chat controls
            self.message_input.setEnabled(True)
            self.send_button.setEnabled(True)
            self.escalate_btn.setEnabled(True)
            self.resolve_btn.setEnabled(True)
            
            # Load conversation history
            self.load_conversation_history(current.user_id)
            
            self.add_log(f"Selected conversation with {current.user_id}")
    
    def load_conversation_history(self, user_id: str):
        """Load and display conversation history."""
        try:
            conversation = self.virtual_assistant.conversations.get(user_id)
            if not conversation:
                self.chat_display.clear()
                return
            
            self.chat_display.clear()
            
            for message in conversation.get('messages', []):
                role = message.get('role', 'unknown')
                content = message.get('content', '')
                timestamp = message.get('timestamp', '')
                
                # Format message for display
                if role == 'user':
                    formatted_msg = f"<div style='margin: 5px 0; padding: 8px; background-color: #e3f2fd; border-radius: 8px;'>"
                    formatted_msg += f"<b>Customer ({timestamp}):</b><br>{content}</div>"
                else:
                    formatted_msg = f"<div style='margin: 5px 0; padding: 8px; background-color: #f1f8e9; border-radius: 8px;'>"
                    formatted_msg += f"<b>Assistant ({timestamp}):</b><br>{content}</div>"
                
                self.chat_display.append(formatted_msg)
            
            # Scroll to bottom
            self.chat_display.verticalScrollBar().setValue(
                self.chat_display.verticalScrollBar().maximum()
            )
            
        except Exception as e:
            self.add_log(f"Error loading conversation history: {str(e)}")
    
    def send_message(self):
        """Send message to current conversation."""
        if not self.current_conversation or not self.message_input.text().strip():
            return
        
        try:
            message = self.message_input.text().strip()
            user_id = self.current_conversation
            
            # Send message via API
            success, result = self.api_handler.send_text_message(user_id, message)
            
            if success:
                # Add to conversation history
                self.virtual_assistant._add_to_conversation(user_id, 'assistant', message)
                
                # Update UI
                formatted_msg = f"<div style='margin: 5px 0; padding: 8px; background-color: #f1f8e9; border-radius: 8px;'>"
                formatted_msg += f"<b>You ({datetime.now().strftime('%H:%M')}):</b><br>{message}</div>"
                self.chat_display.append(formatted_msg)
                
                # Clear input
                self.message_input.clear()
                
                self.add_log(f"Sent message to {user_id}: {message[:50]}...")
            else:
                QMessageBox.warning(self, "Send Error", f"Failed to send message: {result}")
                self.add_log(f"Failed to send message: {result}")
                
        except Exception as e:
            QMessageBox.critical(self, "Send Error", f"Error sending message: {str(e)}")
            self.add_log(f"Error sending message: {str(e)}")
    
    def insert_quick_reply(self, message: str):
        """Insert quick reply into message input."""
        self.message_input.setText(message)
        self.message_input.setFocus()
    
    def escalate_conversation(self):
        """Escalate current conversation to human agent."""
        if not self.current_conversation:
            return
        
        try:
            # Mark as escalated in virtual assistant
            user_id = self.current_conversation
            if user_id in self.virtual_assistant.conversations:
                self.virtual_assistant.conversations[user_id]['escalated'] = True
            
            # Update UI
            current_item = self.conversations_list.currentItem()
            if isinstance(current_item, ConversationItem):
                current_item.escalated = True
                current_item.update_display()
            
            # Send escalation message
            escalation_msg = "This conversation has been escalated to our human support team. Someone will be with you shortly."
            self.api_handler.send_text_message(user_id, escalation_msg)
            
            self.add_log(f"Escalated conversation with {user_id}")
            QMessageBox.information(self, "Escalated", "Conversation has been escalated to human support.")
            
        except Exception as e:
            QMessageBox.critical(self, "Escalation Error", f"Error escalating conversation: {str(e)}")
    
    def resolve_conversation(self):
        """Mark current conversation as resolved."""
        if not self.current_conversation:
            return
        
        try:
            user_id = self.current_conversation
            
            # Mark as resolved
            if user_id in self.virtual_assistant.conversations:
                self.virtual_assistant.conversations[user_id]['ended'] = True
                self.virtual_assistant.conversations[user_id]['resolved_at'] = datetime.now().isoformat()
            
            # Remove from active conversations list
            current_item = self.conversations_list.currentItem()
            if current_item:
                row = self.conversations_list.row(current_item)
                self.conversations_list.takeItem(row)
            
            # Clear chat display
            self.chat_display.clear()
            self.chat_header_label.setText("Select a conversation to start chatting")
            self.current_conversation = None
            
            # Disable controls
            self.message_input.setEnabled(False)
            self.send_button.setEnabled(False)
            self.escalate_btn.setEnabled(False)
            self.resolve_btn.setEnabled(False)
            
            self.add_log(f"Resolved conversation with {user_id}")
            QMessageBox.information(self, "Resolved", "Conversation has been marked as resolved.")
            
        except Exception as e:
            QMessageBox.critical(self, "Resolution Error", f"Error resolving conversation: {str(e)}")
    
    def update_ui_stats(self):
        """Update UI statistics."""
        try:
            # Count conversations
            total_conversations = len(self.conversations)
            escalated_count = sum(1 for conv in self.conversations.values() if conv.get('escalated', False))
            
            # Update status bar
            self.stats_labels['conversations'].setText(str(total_conversations))
            self.stats_labels['escalated'].setText(str(escalated_count))
            
            # Update connection status
            config_status = self.api_handler.get_configuration_status()
            if config_status.get('configured'):
                self.connection_status_label.setText("✅ Connected")
                self.connection_status_label.setStyleSheet("font-weight: bold; color: #27ae60; padding: 5px;")
            else:
                self.connection_status_label.setText("❌ Not Connected")
                self.connection_status_label.setStyleSheet("font-weight: bold; color: #e74c3c; padding: 5px;")
            
        except Exception as e:
            self.add_log(f"Error updating UI stats: {str(e)}")
    
    def check_connection_status(self):
        """Check and update connection status."""
        try:
            success, message = self.api_handler.test_connection()
            if success:
                self.add_log("Connection check: OK")
            else:
                self.add_log(f"Connection check failed: {message}")
                
        except Exception as e:
            self.add_log(f"Connection check error: {str(e)}")
    
    def check_webhook_status(self):
        """Check webhook server status."""
        try:
            status = self.webhook_handler.get_server_status()
            self.is_webhook_running = status.get('running', False)
            
            if self.is_webhook_running:
                self.webhook_toggle_btn.setText("🔗 Stop Webhook")
                self.webhook_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #e74c3c;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #c0392b;
                    }
                """)
            
        except Exception as e:
            self.add_log(f"Error checking webhook status: {str(e)}")
    
    def add_log(self, message: str):
        """Add message to logs display."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs_display.append(log_entry)
        
        # Scroll to bottom
        self.logs_display.verticalScrollBar().setValue(
            self.logs_display.verticalScrollBar().maximum()
        )
        
        # Also log to console
        self.logger.info(message)
    
    # Signal handlers
    def on_settings_saved(self, settings: Dict[str, Any]):
        """Handle settings saved event."""
        try:
            # Update virtual assistant with new settings
            if 'business_info' in settings:
                self.virtual_assistant.business_info.update(settings['business_info'])
            
            if 'assistant_config' in settings:
                self.virtual_assistant.assistant_config.update(settings['assistant_config'])
            
            self.add_log("Settings saved and applied")
            self.update_ui_stats()
            
        except Exception as e:
            self.add_log(f"Error applying settings: {str(e)}")
    
    def on_message_sent(self, recipient: str, message_data: Dict[str, Any]):
        """Handle message sent confirmation."""
        self.add_log(f"Message sent to {recipient}")
    
    def on_api_error(self, operation: str, error: str):
        """Handle API errors."""
        self.add_log(f"API Error ({operation}): {error}")
    
    def on_ai_response(self, user_id: str, response: str, metadata: Dict[str, Any]):
        """Handle AI response generated."""
        self.add_log(f"AI response generated for {user_id}")
        
        # If this is the current conversation, update the chat display
        if user_id == self.current_conversation:
            self.load_conversation_history(user_id)
    
    def on_escalation_requested(self, user_id: str, reason: str, context: Dict[str, Any]):
        """Handle escalation request from AI."""
        self.add_log(f"Escalation requested for {user_id}: {reason}")
        
        # Update conversation in list if visible
        for i in range(self.conversations_list.count()):
            item = self.conversations_list.item(i)
            if isinstance(item, ConversationItem) and item.user_id == user_id:
                item.escalated = True
                item.update_display()
                break
    
    def on_conversation_started(self, user_id: str, user_info: Dict[str, Any]):
        """Handle new conversation started."""
        self.add_log(f"New conversation started with {user_id}")
        self.refresh_conversations()
    
    def on_webhook_message(self, webhook_data: Dict[str, Any]):
        """Handle incoming webhook message."""
        self.add_log("Webhook message received")
        
        # Refresh conversations to show any new activity
        self.refresh_conversations()
        
        # If current conversation is updated, reload it
        if self.current_conversation:
            self.load_conversation_history(self.current_conversation)
    
    def on_webhook_error(self, operation: str, error: str):
        """Handle webhook errors."""
        self.add_log(f"Webhook Error ({operation}): {error}") 