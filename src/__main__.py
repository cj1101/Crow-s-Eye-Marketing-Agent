#!/usr/bin/env python3
"""
Main entry point for the Breadsmith Marketing Tool application.
"""

import sys
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def main():
    """
    Run the application.
    """
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Social Media Caption Generator")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Breadsmith Marketing")
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 