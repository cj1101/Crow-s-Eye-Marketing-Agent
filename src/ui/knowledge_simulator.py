"""
Knowledge Simulator to test Q&A with knowledge base files.
"""
import os
import logging
import random
from typing import List, Dict, Any, Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QLineEdit, QMessageBox, QWidget, QSplitter
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon

class KnowledgeSimulatorDialog(QDialog):
    """Dialog for testing knowledge-based Q&A"""
    
    def __init__(self, parent=None):
        """Initialize the dialog."""
        super().__init__(parent)
        self.setWindowTitle("Knowledge Base Q&A Simulator")
        self.resize(800, 600)
        
        # Set up knowledge base directory
        self.knowledge_base_dir = Path("knowledge_base")
        
        # Logger
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Create UI
        self._create_ui()
        
        # Load knowledge files
        self._load_knowledge_files()
        
    def _create_ui(self):
        """Create the dialog UI."""
        main_layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Knowledge Base Q&A Simulator")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_label)
        
        # Instructions
        instructions = QLabel(
            "Test how the system would respond to customer inquiries using your knowledge base files. "
            "Enter a question below to see a simulated response."
        )
        instructions.setWordWrap(True)
        main_layout.addWidget(instructions)
        
        # Splitter for history and input
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Chat history
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        
        history_label = QLabel("Conversation:")
        history_layout.addWidget(history_label)
        
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setPlaceholderText("Conversation will appear here...")
        history_layout.addWidget(self.history_text)
        
        splitter.addWidget(history_widget)
        
        # Input section
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        
        # Question input
        question_layout = QHBoxLayout()
        
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Type your question here...")
        self.question_input.returnPressed.connect(self._on_send_clicked)
        question_layout.addWidget(self.question_input)
        
        send_button = QPushButton("Send")
        send_button.clicked.connect(self._on_send_clicked)
        question_layout.addWidget(send_button)
        
        input_layout.addLayout(question_layout)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Add manage button
        manage_button = QPushButton("Manage Knowledge Files")
        manage_button.clicked.connect(self._on_manage_clicked)
        buttons_layout.addWidget(manage_button)
        
        # Add pending messages button
        pending_button = QPushButton("View Pending Messages")
        pending_button.clicked.connect(self._on_pending_clicked)
        buttons_layout.addWidget(pending_button)
        
        input_layout.addLayout(buttons_layout)
        
        splitter.addWidget(input_widget)
        
        # Set initial sizes (70% for history, 30% for input)
        splitter.setSizes([400, 200])
        
        main_layout.addWidget(splitter)
        
        # Status label
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
    def _load_knowledge_files(self):
        """Load knowledge files from the knowledge base directory."""
        try:
            self.knowledge_files = []
            
            if not self.knowledge_base_dir.exists():
                self.status_label.setText("Knowledge base directory not found.")
                return
                
            # Get all text and markdown files
            for file_path in self.knowledge_base_dir.glob("*.txt"):
                self.knowledge_files.append(file_path)
                
            for file_path in self.knowledge_base_dir.glob("*.md"):
                self.knowledge_files.append(file_path)
                
            # Update status
            if self.knowledge_files:
                self.status_label.setText(f"Loaded {len(self.knowledge_files)} knowledge base file(s).")
            else:
                self.status_label.setText("No knowledge base files found.")
                
            self.logger.info(f"Loaded {len(self.knowledge_files)} knowledge base files")
            
        except Exception as e:
            self.logger.exception(f"Error loading knowledge base files: {e}")
            self.status_label.setText(f"Error loading files: {str(e)}")
            
    def _on_send_clicked(self):
        """Handle send button click."""
        question = self.question_input.text().strip()
        
        if not question:
            return
            
        try:
            # Display question in history
            self.history_text.append(f"<b>You:</b> {question}")
            
            # Generate response
            response = self._generate_response(question)
            
            # Display response in history
            self.history_text.append(f"<b>Bot:</b> {response}")
            self.history_text.append("")  # Add blank line
            
            # Clear question input
            self.question_input.clear()
            
        except Exception as e:
            self.logger.exception(f"Error generating response: {e}")
            self.history_text.append(f"<b>Error:</b> {str(e)}")
            
    def _generate_response(self, question: str) -> str:
        """Generate a response to the question using knowledge base files."""
        if not self.knowledge_files:
            return "I don't have any knowledge base files loaded. Please add some files to the knowledge base."
            
        try:
            # Simple keyword matching for demonstration
            question_lower = question.lower()
            
            # Find relevant knowledge files
            relevant_content = []
            
            # Open each knowledge file and search for relevant content
            for file_path in self.knowledge_files:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    content_lower = content.lower()
                    
                    # Check if file contains question keywords
                    words = question_lower.split()
                    relevant_words = [word for word in words if len(word) > 3 and word in content_lower]
                    
                    if relevant_words:
                        relevant_content.append({
                            'file': file_path.name,
                            'content': content,
                            'relevance': len(relevant_words)
                        })
            
            # Sort by relevance
            relevant_content.sort(key=lambda x: x['relevance'], reverse=True)
            
            if relevant_content:
                # Use the most relevant file to generate a response
                best_match = relevant_content[0]
                
                # Get paragraphs from the content
                paragraphs = best_match['content'].split('\n\n')
                
                # Filter relevant paragraphs
                relevant_paragraphs = []
                for para in paragraphs:
                    para_lower = para.lower()
                    if any(word in para_lower for word in question_lower.split() if len(word) > 3):
                        relevant_paragraphs.append(para)
                
                if relevant_paragraphs:
                    # Use the most relevant paragraph
                    response = f"Based on our information: {relevant_paragraphs[0]}"
                    
                    # Add reference
                    response += f"\n\n(Source: {best_match['file']})"
                    
                    return response
                else:
                    # Fall back to a general response from the file
                    return f"I found some information that might help, but I couldn't find a specific answer to your question in our knowledge base. Please try to rephrase or ask a more specific question."
            else:
                return "I don't have specific information about that in my knowledge base. Please try asking something else or contact support for more assistance."
                
        except Exception as e:
            self.logger.exception(f"Error generating response: {e}")
            return f"Sorry, I encountered an error while trying to answer your question: {str(e)}"
            
    def _on_manage_clicked(self):
        """Open the knowledge management dialog."""
        try:
            from .knowledge_management import KnowledgeManagementDialog
            
            knowledge_dialog = KnowledgeManagementDialog(parent=self)
            result = knowledge_dialog.exec()
            
            # Reload knowledge files after management
            self._load_knowledge_files()
            
        except Exception as e:
            self.logger.exception(f"Error opening knowledge management: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Could not open knowledge management: {str(e)}"
            )
            
    def _on_pending_clicked(self):
        """Open the knowledge management dialog with the Pending Messages tab active."""
        try:
            from .knowledge_management import KnowledgeManagementDialog
            
            knowledge_dialog = KnowledgeManagementDialog(parent=self)
            # Switch to the Pending Messages tab (index 1)
            knowledge_dialog.tab_widget.setCurrentIndex(1)
            result = knowledge_dialog.exec()
            
            # Reload knowledge files after management
            self._load_knowledge_files()
            
        except Exception as e:
            self.logger.exception(f"Error opening pending messages: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Could not open pending messages: {str(e)}"
            ) 