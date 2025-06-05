"""
Theme manager for handling light and dark mode
"""
import os
import logging
from typing import Optional, Dict, List, Any, Union, cast

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal

class ThemeManager(QObject):
    """Manages application theme (light/dark mode)"""
    
    theme_changed = Signal(bool)  # True for dark mode, False for light mode
    
    def __init__(self) -> None:
        """Initialize the theme manager."""
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize theme stylesheet containers
        self.base_theme: str = ""
        self.gray_theme: str = ""
        
        # Always use gray theme
        self.gray_mode_active: bool = True
        
    def load_stylesheet(self, stylesheet_path: str = "styles.qss") -> bool:
        """
        Load the application stylesheet.
        
        Args:
            stylesheet_path: Path to the stylesheet file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(stylesheet_path):
                self.logger.error(f"Stylesheet not found: {stylesheet_path}")
                return False
                
            # Load the stylesheet
            with open(stylesheet_path, "r") as f:
                style = f.read()
                
            # Store the base stylesheet
            self.base_theme = style
            self.gray_theme = style
            
            return True
        except Exception as e:
            self.logger.error(f"Error loading stylesheet: {e}")
            return False
    
    def apply_theme(self, dark_mode: bool = False) -> bool:
        """
        Apply the gray theme (ignoring dark_mode parameter).
        
        Args:
            dark_mode: Ignored parameter, kept for compatibility
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Always use gray theme
            self.gray_mode_active = True
            
            # Apply the theme
            if self.gray_theme:
                app = QApplication.instance()
                if app:
                    app.setStyleSheet(self.gray_theme)
                    self.logger.info("Gray theme applied")
                    
                    # Emit signal - we still emit True for compatibility with existing code
                    self.theme_changed.emit(True)
                    return True
            
            self.logger.error("No theme available to apply")
            return False
        except Exception as e:
            self.logger.error(f"Error applying theme: {e}")
            return False
    
    def toggle_theme(self) -> None:
        """Toggle between light and dark mode - now a no-op as we always use gray theme."""
        # Do nothing, we always stay in gray mode
        # Just ensure gray mode is active and emit signal to confirm
        self.gray_mode_active = True
        self.theme_changed.emit(True)
        
    def is_dark_mode(self) -> bool:
        """Return whether dark mode is active."""
        # Always return True for compatibility with existing code
        return True
        
    def add_runtime_style_additions(self) -> str:
        """
        Add runtime style additions to the theme.
        
        Returns:
            str: The updated theme
        """
        # Add custom runtime styles that can't be loaded from file - GRAY MODE
        additions = """
        /* Runtime style additions - Gray Theme */
        QMainWindow {
            background-color: #808080;
        }
        
        QWidget {
            background-color: #808080;
            color: #000000;
        }
        
        QLabel {
            color: #000000;
            background-color: transparent;
        }
        
        QTextEdit, QPlainTextEdit {
            background-color: #e0e0e0;
            color: #000000;
            border: 2px solid #505050;
        }
        
        QPushButton {
            background-color: #3498db;
            color: #ffffff;
            border: 2px solid #2980b9;
            border-radius: 4px;
            padding: 5px 10px;
            font-weight: bold;
        }
        
        /* Make sure all section titles are clearly visible */
        QLabel#sectionTitle {
            font-weight: bold;
            font-size: 14px;
            color: #000000;
            background-color: #b0b0b0;
            padding: 5px;
            border-bottom: 1px solid #3498db;
        }
        
        /* Make sure all preview frames have good contrast */
        QFrame#mediaPreviewFrame {
            background-color: #909090;
            border: 2px solid #505050;
        }
        
        /* Make sure all labels in preview frames are visible */
        QFrame#mediaPreviewFrame QLabel {
            color: #000000;
        }
        """
        
        # Add the runtime additions to the theme
        self.gray_theme += additions
        
        return self.gray_theme