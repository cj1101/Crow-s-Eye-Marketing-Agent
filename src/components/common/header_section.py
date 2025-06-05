"""
Header section component for the main window
"""
import logging
from typing import List, Dict, Optional, Union, Any

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QComboBox, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor

from .adjustable_button import AdjustableButton
from ..base_widget import BaseWidget

class HeaderSection(BaseWidget):
    """Header section with app title, theme toggle, presets, and navigation buttons"""
    
    theme_toggled = Signal()
    preset_selected = Signal(int)
    save_preset_clicked = Signal()
    delete_preset_clicked = Signal()
    library_clicked = Signal()
    schedule_clicked = Signal()
    login_clicked = Signal()
    language_changed = Signal(str)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        # Always set gray mode to true
        self.dark_mode_active = True
        
        # Initialize UI components
        self.preset_combo: Optional[QComboBox] = None
        self.delete_preset_btn: Optional[AdjustableButton] = None
        self.save_preset_btn: Optional[AdjustableButton] = None
        self.theme_toggle_btn: Optional[AdjustableButton] = None
        self.library_btn: Optional[AdjustableButton] = None
        self.schedule_btn: Optional[AdjustableButton] = None
        self.login_btn: Optional[AdjustableButton] = None
        self.language_combo: Optional[QComboBox] = None
        
        # Create layout
        self._create_layout()
        self.retranslateUi() # Initial translation
        
    def _create_layout(self):
        """Create the header section layout"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # App title
        self.app_title_label = QLabel() # Changed to instance variable for retranslation
        self.app_title_label.setObjectName("appTitle")
        self.app_title_label.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: #000000; 
            background-color: #b0b0b0;
            padding: 5px;
            border-radius: 4px;
        """)
        layout.addWidget(self.app_title_label)
        
        # Add spacer to push buttons to the right
        layout.addStretch()
        
        # Presets section
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(8)
        
        # Preset label
        self.preset_label_widget = QLabel() # Changed to instance variable
        self.preset_label_widget.setObjectName("presetLabel")
        self.preset_label_widget.setStyleSheet("font-weight: bold; color: #000000; font-size: 14px;")
        preset_layout.addWidget(self.preset_label_widget)
        
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
        self.save_preset_btn = AdjustableButton() # Text set in retranslateUi
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
        self.delete_preset_btn = AdjustableButton() # Text set in retranslateUi
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
        self.login_btn = AdjustableButton() # Text set in retranslateUi / update_login_button
        self.login_btn.setObjectName("loginButton")
        # Styles will be set by update_login_button or retranslateUi for initial state
        self.login_btn.clicked.connect(self._on_login_clicked)
        layout.addWidget(self.login_btn)
        
        # Schedule button
        self.schedule_btn = AdjustableButton() # Text set in retranslateUi
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
        self.library_btn = AdjustableButton() # Text set in retranslateUi
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
        
        # Language selection dropdown
        self.language_combo = QComboBox()
        self.language_combo.setObjectName("languageCombo")
        self.language_combo.setFixedWidth(150) # Adjust width as needed
        self.language_combo.setStyleSheet("""
            background-color: #e0e0e0;
            color: #000000;
            border: 2px solid #505050;
            padding: 5px;
            font-weight: bold;
        """)
        
        # Language data: [("Native Name", "code"), ...]
        # Match the language codes from our translation files
        self.languages = [
            ("English", "en"),
            ("Español", "es"),
            ("中文", "zh"),
            ("हिन्दी", "hi"),
            ("Français", "fr"),
            ("العربية", "ar"),
            ("Português", "pt"),
            ("Русский", "ru"),
            ("日本語", "ja"),
            ("Deutsch", "de")
        ]
        
        for lang_name, lang_code in self.languages:
            self.language_combo.addItem(lang_name, userData=lang_code)
            
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        layout.addWidget(self.language_combo)
        
        # Theme toggle button - hidden in dark-only mode
        self.theme_toggle_btn = AdjustableButton() # Icon set, tooltip in retranslateUi
        self.theme_toggle_btn.setObjectName("themeToggleButton")
        self.theme_toggle_btn.setProperty("themeIcon", "dark")  # Start with dark mode icon
        self.theme_toggle_btn.setFixedSize(36, 36)
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
            AdjustableButton {
                background-color: #3498db;
                color: white;
                border: 2px solid #2980b9;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
            }
            AdjustableButton:hover {
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
        
    def _on_language_changed(self, index: int):
        """Handle language selection change"""
        selected_lang_code = self.language_combo.itemData(index)
        if selected_lang_code:
            self.logger.info(f"Language selected: {selected_lang_code}")
            # Switch language using i18n system
            from ...i18n import i18n
            i18n.switch(selected_lang_code)
            self.language_changed.emit(selected_lang_code)
        
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
        
        if self.preset_combo.count() > 0: # Ensure item 0 exists
            self.preset_combo.setItemText(0, "-- Select Preset --")
    
    def reset_selection(self):
        """Reset the preset selection to the default item"""
        self.preset_combo.setCurrentIndex(0)
        if self.preset_combo.count() > 0: # Ensure item 0 exists
            self.preset_combo.setItemText(0, "-- Select Preset --")
        
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
            self.login_btn.setText(self.tr("👤 {account_name}").format(account_name=account_name)) # Use self.tr with placeholder
            self.login_btn.setStyleSheet("""
                background-color: #16a085;
                color: white;
                border: 2px solid #1abc9c;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
            """)
            self.login_btn.setToolTip(self.tr("Logged in as {account_name}").format(account_name=account_name))
        else:
            self.login_btn.setText(self.tr("🔑 Login"))
            self.login_btn.setStyleSheet("""
                background-color: #2c3e50;
                color: white;
                border: 2px solid #34495e;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
            """)
            self.login_btn.setToolTip(self.tr("Log in to Meta Business Account"))

    def changeEvent(self, event):
        """Handle change events, particularly language changes."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)
        
    def retranslateUi(self):
        """Update all UI text elements to the current language."""
        # Don't translate the language selector items (they should show in native language)
        # But update all other UI elements
        
        # Main title
        self.app_title_label.setText(self.tr("Marketing Assistant"))
        
        # Language dropdown label won't be translated since it's just a globe icon
        
        # Presets section
        if hasattr(self, 'preset_label_widget'):
            self.preset_label_widget.setText(self.tr("Presets:"))
        
        if hasattr(self, 'preset_combo'):
            current_index = self.preset_combo.currentIndex()
            current_text = self.preset_combo.currentText()
            
            # Only translate the default item, keep user presets as-is
            if current_index == 0 or current_text == "-- Select Preset --":
                self.preset_combo.setItemText(0, self.tr("-- Select Preset --"))
        
        # Buttons
        if hasattr(self, 'save_preset_btn'):
            self.save_preset_btn.setText(self.tr("Save"))
        if hasattr(self, 'delete_preset_btn'):
            self.delete_preset_btn.setText(self.tr("Delete"))
        
        # Update login button text based on state
        if hasattr(self, 'is_logged_in') and self.is_logged_in:
            self.login_btn.setText(self.tr("Logged In"))
        else:
            self.login_btn.setText(self.tr("Login"))
            
        # Other section buttons
        self.schedule_btn.setText(self.tr("Schedule"))
        self.library_btn.setText(self.tr("Library"))
        
        # Theme toggle doesn't need translation as it's an icon