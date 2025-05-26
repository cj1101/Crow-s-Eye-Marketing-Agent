#!/usr/bin/env python3
"""
Simple test script to verify the unified connection dialog works properly.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt

from src.ui.dialogs.unified_connection_dialog import UnifiedConnectionDialog

class TestWindow(QWidget):
    """Simple test window to launch the connection dialog."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Connection Dialog Test")
        self.setGeometry(100, 100, 400, 200)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Connection Dialog Test")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("Click the button below to test the unified connection dialog.")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Test button
        test_button = QPushButton("Open Connection Dialog")
        test_button.setStyleSheet("""
            QPushButton {
                background-color: #8B5A9F;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
                margin: 20px;
            }
            QPushButton:hover {
                background-color: #7A4F8E;
            }
        """)
        test_button.clicked.connect(self.open_connection_dialog)
        layout.addWidget(test_button)
        
        # Status label
        self.status_label = QLabel("Ready to test")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666; margin: 10px;")
        layout.addWidget(self.status_label)
        
    def open_connection_dialog(self):
        """Open the unified connection dialog."""
        try:
            self.status_label.setText("Opening connection dialog...")
            
            dialog = UnifiedConnectionDialog(self)
            dialog.connection_successful.connect(self.on_connection_result)
            
            result = dialog.exec()
            
            if result:
                self.status_label.setText("Dialog completed successfully")
            else:
                self.status_label.setText("Dialog was cancelled")
                
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            print(f"Error opening dialog: {e}")
    
    def on_connection_result(self, platform_status):
        """Handle connection results."""
        connected_platforms = []
        for platform, status in platform_status.items():
            if status.get('connected', False):
                connected_platforms.append(platform.upper())
        
        if connected_platforms:
            platforms_text = ", ".join(connected_platforms)
            self.status_label.setText(f"Connected to: {platforms_text}")
        else:
            self.status_label.setText("No platforms connected")

def main():
    """Main function to run the test."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Connection Dialog Test")
    app.setApplicationVersion("1.0")
    
    # Create and show test window
    window = TestWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 