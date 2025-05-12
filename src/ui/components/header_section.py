"""
Header section component for the main window
"""
import logging
from typing import List, Dict, Optional, Union, Any

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, 
    QComboBox, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor

class HeaderSection(QWidget):
    """Header section with app title, theme toggle, presets, and navigation buttons"""
    
    theme_toggled = Signal()
    preset_selected = Signal(int)
    save_preset_clicked = Signal()
    delete_preset_clicked = Signal()
    library_clicked = Signal()
    knowledge_clicked = Signal()
    schedule_clicked = Signal()
    login_clicked = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        # Always set gray mode to true
        self.dark_mode_active = True
        
        # Initialize UI components
        self.preset_combo: Optional[QComboBox] = None
        self.delete_preset_btn: Optional[QPushButton] = None
        self.save_preset_btn: Optional[QPushButton] = None
        self.theme_toggle_btn: Optional[QPushButton] = None
        self.library_btn: Optional[QPushButton] = None
        self.knowledge_btn: Optional[QPushButton] = None
        self.schedule_btn: Optional[QPushButton] = None
        self.login_btn: Optional[QPushButton] = None
        
        # Create layout
        self._create_layout()
        
    def _create_layout(self):
        """Create the header section layout"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # App title
        app_title = QLabel("Marketing Assistant")
        app_title.setObjectName("appTitle")
        app_title.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: #000000; 
            background-color: #b0b0b0;
            padding: 5px;
            border-radius: 4px;
        """)
        layout.addWidget(app_title)
        
        # Add spacer to push buttons to the right
        layout.addStretch()
        
        # Presets section
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(8)
        
        # Preset label
        preset_label = QLabel("Presets:")
        preset_label.setObjectName("presetLabel")
        preset_label.setStyleSheet("font-weight: bold; color: #000000; font-size: 14px;")
        preset_layout.addWidget(preset_label)
        
        # Preset combo box
        self.preset_combo = QComboBox()
        self.preset_combo.setObjectName("presetCombo")
        self.preset_combo.setFixedWidth(200)
        self.preset_combo.setStyleSheet("""
            background-color: #e0e0e0;
            color: #000000;
            border: 2px solid #505050;
            padding: 5px;
            font-weight: bold;
        """)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        preset_layout.addWidget(self.preset_combo)
        
        # Save preset button
        self.save_preset_btn = QPushButton("Save")
        self.save_preset_btn.setObjectName("savePresetButton")
        self.save_preset_btn.setStyleSheet("""
            background-color: #3498db;
            color: white;
            border: 2px solid #2980b9;
            border-radius: 4px;
            padding: 5px 10px;
            font-weight: bold;
        """)
        self.save_preset_btn.clicked.connect(self._on_save_preset)
        preset_layout.addWidget(self.save_preset_btn)
        
        # Delete preset button
        self.delete_preset_btn = QPushButton("Delete")
        self.delete_preset_btn.setObjectName("deletePresetButton")
        self.delete_preset_btn.setStyleSheet("""
            background-color: #e74c3c;
            color: white;
            border: 2px solid #c0392b;
            border-radius: 4px;
            padding: 5px 10px;
            font-weight: bold;
        """)
        self.delete_preset_btn.clicked.connect(self._on_delete_preset)
        preset_layout.addWidget(self.delete_preset_btn)
        
        layout.addLayout(preset_layout)
        
        # Add spacer for separation
        layout.addSpacing(20)
        
        # Login button
        self.login_btn = QPushButton("🔑 Login")
        self.login_btn.setObjectName("loginButton")
        self.login_btn.setStyleSheet("""
            background-color: #2c3e50;
            color: white;
            border: 2px solid #34495e;
            border-radius: 4px;
            padding: 5px 10px;
            font-weight: bold;
        """)
        self.login_btn.clicked.connect(self._on_login_clicked)
        layout.addWidget(self.login_btn)
        
        # Schedule button
        self.schedule_btn = QPushButton("📅 Schedule")
        self.schedule_btn.setObjectName("scheduleButton")
        self.schedule_btn.setStyleSheet("""
            background-color: #9b59b6;
            color: white;
            border: 2px solid #8e44ad;
            border-radius: 4px;
            padding: 5px 10px;
            font-weight: bold;
        """)
        self.schedule_btn.clicked.connect(self._on_schedule_clicked)
        layout.addWidget(self.schedule_btn)
        
        # Library button
        self.library_btn = QPushButton("Library")
        self.library_btn.setObjectName("libraryButton")
        self.library_btn.setStyleSheet("""
            background-color: #27ae60;
            color: white;
            border: 2px solid #219653;
            border-radius: 4px;
            padding: 5px 10px;
            font-weight: bold;
        """)
        self.library_btn.clicked.connect(self._on_library_clicked)
        layout.addWidget(self.library_btn)
        
        # Knowledge button
        self.knowledge_btn = QPushButton("Knowledge")
        self.knowledge_btn.setObjectName("knowledgeButton")
        self.knowledge_btn.setStyleSheet("""
            background-color: #f39c12;
            color: white;
            border: 2px solid #e67e22;
            border-radius: 4px;
            padding: 5px 10px;
            font-weight: bold;
        """)
        self.knowledge_btn.clicked.connect(self._on_knowledge_clicked)
        layout.addWidget(self.knowledge_btn)
        
        # Theme toggle button - hidden in dark-only mode
        self.theme_toggle_btn = QPushButton("☾")
        self.theme_toggle_btn.setObjectName("themeToggleButton")
        self.theme_toggle_btn.setProperty("themeIcon", "dark")  # Start with dark mode icon
        self.theme_toggle_btn.setFixedSize(36, 36)
        self.theme_toggle_btn.setToolTip("Switch theme")
        self.theme_toggle_btn.clicked.connect(self._on_theme_toggle)
        self.theme_toggle_btn.setVisible(False)  # Hide the button
        layout.addWidget(self.theme_toggle_btn)
        
        # Set fixed height
        self.setFixedHeight(60)
        
        # Set gray style with high contrast
        self.setStyleSheet("""
            HeaderSection {
                background-color: #808080;
                border-bottom: 2px solid #505050;
            }
            QLabel {
                color: #000000;
                background-color: transparent;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: 2px solid #2980b9;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
    def _on_preset_selected(self, index):
        """Handle preset selection"""
        self.preset_selected.emit(index)
        
    def _on_save_preset(self):
        """Handle save preset button click"""
        self.save_preset_clicked.emit()
        
    def _on_delete_preset(self):
        """Handle delete preset button click"""
        self.delete_preset_clicked.emit()
        
    def _on_theme_toggle(self):
        """Handle theme toggle button click"""
        self.theme_toggled.emit()
        
    def _on_library_clicked(self):
        """Handle library button click"""
        self.library_clicked.emit()
    
    def _on_knowledge_clicked(self):
        """Handle knowledge button click"""
        self.knowledge_clicked.emit()
        
    def _on_schedule_clicked(self):
        """Handle schedule button click"""
        self.logger.info("Schedule button clicked")
        # Emit the signal
        self.schedule_clicked.emit()
        
    def _on_login_clicked(self):
        """Handle login button click"""
        self.logger.info("Login button clicked")
        # Emit the signal
        self.login_clicked.emit()
        
    def update_theme_button(self):
        """Update the theme toggle button icon based on current mode"""
        # No-op since button is always hidden
        pass
        
    def set_presets(self, preset_names):
        """
        Set available presets in the combo box.
        
        Args:
            preset_names: List of preset names
        """
        # Store current index
        current_index = self.preset_combo.currentIndex()
        
        # Clear and repopulate
        self.preset_combo.clear()
        self.preset_combo.addItem("-- Select Preset --")
        
        for name in preset_names:
            self.preset_combo.addItem(name)
            
        # Restore selection if possible
        if current_index < self.preset_combo.count():
            self.preset_combo.setCurrentIndex(current_index)
        else:
            self.preset_combo.setCurrentIndex(0)
    
    def reset_selection(self):
        """Reset the preset selection to the default item"""
        self.preset_combo.setCurrentIndex(0)
        
    def populate_preset_combo(self, presets):
        """Populate the preset combo box with available presets.
        
        Args:
            presets: Dictionary of presets
        """
        # Clear and repopulate
        self.preset_combo.clear()
        self.preset_combo.addItem("-- Select Preset --")
        
        # Add preset names to combo box
        for preset_name in presets.keys():
            self.preset_combo.addItem(preset_name)
            
    def _update_button_text_colors(self):
        """Update button text colors to ensure contrast with background"""
        # No-op as we're using explicit styling for all buttons
        pass
        
    def set_dark_mode(self, is_dark_mode):
        """
        Update the header for dark mode.
        
        Args:
            is_dark_mode: Whether dark mode is active
        """
        # No-op since we're always using our custom gray styling
        pass
        
    def update_login_button(self, is_logged_in: bool, account_name: Optional[str] = None):
        """
        Update the login button text and appearance based on login status.
        
        Args:
            is_logged_in: Whether the user is logged in
            account_name: The name of the logged-in account (if any)
        """
        if is_logged_in and account_name:
            self.login_btn.setText(f"👤 {account_name}")
            self.login_btn.setStyleSheet("""
                background-color: #16a085;
                color: white;
                border: 2px solid #1abc9c;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
            """)
            self.login_btn.setToolTip(f"Logged in as {account_name}")
        else:
            self.login_btn.setText("🔑 Login")
            self.login_btn.setStyleSheet("""
                background-color: #2c3e50;
                color: white;
                border: 2px solid #34495e;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
            """)
            self.login_btn.setToolTip("Log in to Meta Business Account")