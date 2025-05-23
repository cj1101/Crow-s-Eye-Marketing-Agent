import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTabWidget, 
                             QFileDialog, QListWidget, QListWidgetItem, QLineEdit)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize

class CrowsEyeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set up the main window
        self.setWindowTitle("Crow's Eye")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header.setStyleSheet("background-color: #6d28d9; color: white;")
        header.setMinimumHeight(80)
        
        # App title
        title_label = QLabel("Crow's Eye")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        # Navigation buttons
        header_layout.addStretch()
        
        pro_button = QPushButton("Pro Features")
        pro_button.setStyleSheet("""
            background-color: #5b21b6; 
            color: white; 
            border: none; 
            padding: 8px 16px;
            border-radius: 4px;
        """)
        header_layout.addWidget(pro_button)
        
        main_layout.addWidget(header)
        
        # Create tab widget for main sections
        self.tabs = QTabWidget()
        
        # Media Library Tab
        self.media_library_tab = QWidget()
        self.setup_media_library_tab()
        self.tabs.addTab(self.media_library_tab, "Media Library")
        
        # Gallery Generator Tab
        self.gallery_generator_tab = QWidget()
        self.setup_gallery_generator_tab()
        self.tabs.addTab(self.gallery_generator_tab, "Gallery Generator")
        
        main_layout.addWidget(self.tabs)
        
        # Status bar setup
        self.statusBar().showMessage("Ready")
    
    def setup_media_library_tab(self):
        layout = QVBoxLayout(self.media_library_tab)
        
        # Upload section
        upload_widget = QWidget()
        upload_layout = QHBoxLayout(upload_widget)
        
        upload_button = QPushButton("Upload Media")
        upload_button.setStyleSheet("""
            background-color: #6d28d9; 
            color: white; 
            padding: 10px 20px;
            border-radius: 4px;
        """)
        upload_button.clicked.connect(self.upload_media)
        upload_layout.addWidget(upload_button)
        
        search_input = QLineEdit()
        search_input.setPlaceholderText("Search media...")
        upload_layout.addWidget(search_input)
        
        layout.addWidget(upload_widget)
        
        # Media display tabs
        media_tabs = QTabWidget()
        
        # Raw Photos Tab
        photos_tab = QWidget()
        photos_layout = QVBoxLayout(photos_tab)
        self.photos_list = QListWidget()
        photos_layout.addWidget(self.photos_list)
        media_tabs.addTab(photos_tab, "Raw Photos")
        
        # Raw Videos Tab
        videos_tab = QWidget()
        videos_layout = QVBoxLayout(videos_tab)
        self.videos_list = QListWidget()
        videos_layout.addWidget(self.videos_list)
        media_tabs.addTab(videos_tab, "Raw Videos")
        
        # Post-Ready Tab
        posts_tab = QWidget()
        posts_layout = QVBoxLayout(posts_tab)
        self.posts_list = QListWidget()
        posts_layout.addWidget(self.posts_list)
        media_tabs.addTab(posts_tab, "Post-Ready Content")
        
        layout.addWidget(media_tabs)
    
    def setup_gallery_generator_tab(self):
        layout = QVBoxLayout(self.gallery_generator_tab)
        
        # Split into two columns
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        
        # Left column - Controls
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        
        prompt_label = QLabel("Natural Language Prompt:")
        controls_layout.addWidget(prompt_label)
        
        prompt_input = QLineEdit()
        prompt_input.setPlaceholderText("e.g., Pick the best 5 for a winter campaign")
        controls_layout.addWidget(prompt_input)
        
        generate_button = QPushButton("Generate Gallery")
        generate_button.setStyleSheet("""
            background-color: #4f46e5; 
            color: white; 
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
        """)
        generate_button.clicked.connect(self.generate_gallery)
        controls_layout.addWidget(generate_button)
        
        # Caption section
        caption_label = QLabel("Caption Generator:")
        controls_layout.addWidget(caption_label)
        controls_layout.addSpacing(10)
        
        tone_input = QLineEdit()
        tone_input.setPlaceholderText("e.g., Energetic and conversational")
        controls_layout.addWidget(tone_input)
        
        caption_button = QPushButton("Generate Caption")
        caption_button.setStyleSheet("""
            background-color: #6d28d9; 
            color: white; 
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
        """)
        controls_layout.addWidget(caption_button)
        
        # Generated caption display
        self.caption_display = QLabel("Your caption will appear here")
        self.caption_display.setStyleSheet("""
            background-color: #f3f4f6;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
        """)
        self.caption_display.setWordWrap(True)
        controls_layout.addWidget(self.caption_display)
        
        controls_layout.addStretch()
        content_layout.addWidget(controls_widget, 1)
        
        # Right column - Selected Media
        media_widget = QWidget()
        media_layout = QVBoxLayout(media_widget)
        
        media_label = QLabel("Selected Media:")
        media_layout.addWidget(media_label)
        
        self.selected_media_list = QListWidget()
        self.selected_media_list.setViewMode(QListWidget.IconMode)
        self.selected_media_list.setIconSize(QSize(150, 150))
        self.selected_media_list.setResizeMode(QListWidget.Adjust)
        self.selected_media_list.setWrapping(True)
        media_layout.addWidget(self.selected_media_list)
        
        save_button = QPushButton("Save Gallery")
        save_button.setStyleSheet("""
            background-color: #059669; 
            color: white; 
            padding: 10px;
            border-radius: 4px;
        """)
        media_layout.addWidget(save_button)
        
        content_layout.addWidget(media_widget, 2)
        
        layout.addWidget(content_widget)
    
    def upload_media(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Media Files",
            "",
            "Media Files (*.png *.jpg *.jpeg *.mp4 *.mov)"
        )
        
        if files:
            for file in files:
                filename = os.path.basename(file)
                # Determine file type
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    item = QListWidgetItem(filename)
                    self.photos_list.addItem(item)
                    self.statusBar().showMessage(f"Added photo: {filename}")
                elif file.lower().endswith(('.mp4', '.mov')):
                    item = QListWidgetItem(filename)
                    self.videos_list.addItem(item)
                    self.statusBar().showMessage(f"Added video: {filename}")
    
    def generate_gallery(self):
        # This would connect to AI features in a real implementation
        self.statusBar().showMessage("Generating gallery...")
        # For now, we'll just show a simple message
        self.caption_display.setText("Beautiful day out exploring nature! The perfect balance of adventure and relaxation. #NatureLovers #Wanderlust")
        self.statusBar().showMessage("Gallery generated")
        
        # Simulate adding selected media
        for i in range(3):  # Add 3 placeholder items
            item = QListWidgetItem(f"Selected Item {i+1}")
            self.selected_media_list.addItem(item)

def main():
    app = QApplication(sys.argv)
    window = CrowsEyeApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 