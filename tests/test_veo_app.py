"""
Simple test app for Veo integration
Run this to test Veo functionality before integrating with main app
"""
import sys
import os
import logging
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

from src.components.simple_veo_widget import SimpleVeoWidget

class TestVeoApp(QMainWindow):
    """Simple test application for Veo."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎬 Veo 3 Test App")
        self.setGeometry(100, 100, 500, 400)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
            QWidget {
                background-color: #1a1a1a;
                color: #FFFFFF;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Add Veo widget
        self.veo_widget = SimpleVeoWidget()
        layout.addWidget(self.veo_widget)

def main():
    """Run the test app."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 Starting Veo 3 Test App...")
    print("📋 Make sure you have GOOGLE_API_KEY set in your environment")
    
    # Create app
    app = QApplication(sys.argv)
    
    # Create and show window
    window = TestVeoApp()
    window.show()
    
    # Run app
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 