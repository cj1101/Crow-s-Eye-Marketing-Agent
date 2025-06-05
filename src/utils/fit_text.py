"""
Text fitting utilities for adjusting font sizes to fit within widget bounds.
"""

import logging
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtCore import QRect


def fit_text_to_widget(widget: QWidget, text: str, max_font_size: int = 16, min_font_size: int = 8) -> None:
    """
    Automatically adjust the font size of a widget to fit the given text.
    
    Args:
        widget: The widget (typically a button or label) to adjust
        text: The text that needs to fit
        max_font_size: Maximum font size to try
        min_font_size: Minimum font size (won't go smaller)
    """
    if not text or not widget:
        return
    
    logger = logging.getLogger(__name__)
    
    # Get widget's available area (minus margins/padding)
    rect = widget.rect()
    if rect.width() <= 0 or rect.height() <= 0:
        # Widget not properly sized yet, skip fitting
        return
    
    # Account for padding/margins - reduce available space by a reasonable amount
    padding = 20  # pixels for padding/margins
    available_width = max(rect.width() - padding, 50)
    available_height = max(rect.height() - padding, 20)
    
    # Get current font and start with max size
    current_font = widget.font()
    test_font = QFont(current_font)
    
    # Try sizes from max down to min
    for size in range(max_font_size, min_font_size - 1, -1):
        test_font.setPointSize(size)
        metrics = QFontMetrics(test_font)
        
        # Check if text fits within available space
        text_rect = metrics.boundingRect(QRect(0, 0, available_width, available_height), 
                                       0, text)
        
        if (text_rect.width() <= available_width and 
            text_rect.height() <= available_height):
            # Text fits! Apply this font size
            current_font.setPointSize(size)
            widget.setFont(current_font)
            logger.debug(f"Set font size to {size} for text: '{text[:30]}...'")
            return
    
    # If no size worked, use minimum size
    current_font.setPointSize(min_font_size)
    widget.setFont(current_font)
    logger.warning(f"Using minimum font size {min_font_size} for text: '{text[:30]}...'")


def get_optimal_font_size(text: str, available_width: int, available_height: int, 
                         base_font: QFont, max_size: int = 16, min_size: int = 8) -> int:
    """
    Calculate the optimal font size for given text and dimensions.
    
    Args:
        text: The text to fit
        available_width: Available width in pixels
        available_height: Available height in pixels
        base_font: Base font to use for calculations
        max_size: Maximum font size to try
        min_size: Minimum font size
        
    Returns:
        int: The optimal font size
    """
    if not text:
        return max_size
    
    test_font = QFont(base_font)
    
    for size in range(max_size, min_size - 1, -1):
        test_font.setPointSize(size)
        metrics = QFontMetrics(test_font)
        
        text_rect = metrics.boundingRect(QRect(0, 0, available_width, available_height), 
                                       0, text)
        
        if (text_rect.width() <= available_width and 
            text_rect.height() <= available_height):
            return size
    
    return min_size 