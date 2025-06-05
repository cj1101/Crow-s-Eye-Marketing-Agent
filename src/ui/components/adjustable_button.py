from PySide6.QtWidgets import QPushButton, QSizePolicy
from PySide6.QtGui import QFontMetrics, QPainter
from PySide6.QtCore import Qt, QEvent

class AdjustableButton(QPushButton):
    """
    A QPushButton that adjusts its font size to fit the text within the button's width.
    """
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._original_font_size = self.font().pointSize()
        if self._original_font_size <= 0: # Point size might be -1 if pixel size is used
            self._original_font_size = self.font().pixelSize() * 0.75 # Approximate conversion
        self._adjusting_font_internally = False # Initialize the flag

    def resizeEvent(self, event):
        """
        Adjust font size when the button is resized.
        """
        super().resizeEvent(event)
        self._adjust_font_size()

    def setText(self, text):
        """
        Override setText to readjust font size when text changes.
        """
        super().setText(text)
        self._adjust_font_size() # Adjust font after text is set

    def _adjust_font_size(self):
        """
        Adjusts the font size of the button text to fit the button's width.
        """
        if self._adjusting_font_internally: # Prevent recursion
            return
        
        self._adjusting_font_internally = True
        try:
            if not self.text():
                return

            current_font = self.font()
            # Start with original font size for recalculation
            current_font.setPointSize(self._original_font_size if self._original_font_size > 0 else 10) # default to 10 if original is invalid
            super().setFont(current_font) # Call super().setFont directly to avoid setFont override recursion here

            # Calculate the available width for text (button width - padding)
            try:
                padding_left = int(self.style().styleHint(self.style().SH_BUTTON_TEXT_MARGIN, None, self, None) or 0)
                padding_right = padding_left
            except:
                padding_left = 10
                padding_right = 10

            available_width = self.width() - (padding_left + padding_right)
            
            font_metrics = QFontMetrics(current_font)
            text_width = font_metrics.horizontalAdvance(self.text())
            target_width = available_width * 0.95

            while text_width > target_width and current_font.pointSize() > 1:
                current_font.setPointSize(current_font.pointSize() - 1)
                if current_font.pointSize() <= 1:
                    break
                super().setFont(current_font) # Call super().setFont directly
                font_metrics = QFontMetrics(current_font)
                text_width = font_metrics.horizontalAdvance(self.text())
            
            if current_font.pointSize() < self._original_font_size:
                while text_width < target_width and current_font.pointSize() < self._original_font_size:
                    prospective_font_size = current_font.pointSize() + 1
                    current_font.setPointSize(prospective_font_size)
                    super().setFont(current_font) # Call super().setFont directly
                    font_metrics = QFontMetrics(current_font)
                    text_width_after_increase = font_metrics.horizontalAdvance(self.text())
                    if text_width_after_increase > target_width:
                        current_font.setPointSize(prospective_font_size - 1)
                        super().setFont(current_font) # Call super().setFont directly
                        break
                    text_width = text_width_after_increase
                    if prospective_font_size == self._original_font_size:
                        break
            self.update()
        finally:
            self._adjusting_font_internally = False
    
    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if self._adjusting_font_internally: # Combined guard for all relevant event types
            return

        if event.type() == QEvent.Type.StyleChange:
            new_font = self.font()
            self._original_font_size = new_font.pointSize()
            if self._original_font_size <= 0:
                self._original_font_size = new_font.pixelSize() * 0.75 
            self._adjust_font_size()
        elif event.type() == QEvent.Type.FontChange:
            current_font = self.font()
            self._original_font_size = current_font.pointSize()
            if self._original_font_size <= 0:
                self._original_font_size = current_font.pixelSize() * 0.75
            self._adjust_font_size()

    def setFont(self, font):
        """Override setFont to track internal adjustments and allow external calls to trigger resize."""
        # Set flag true ONLY if this setFont call is NOT already within an adjustment operation
        # This allows external setFont calls to correctly trigger _adjust_font_size
        # while preventing recursion if setFont is called from _adjust_font_size itself.
        
        # If we are already adjusting, just call super and return
        if self._adjusting_font_internally:
            super().setFont(font)
            return

        # If called externally, behave as before, allowing it to trigger changeEvent and _adjust_font_size
        super().setFont(font)
        # The FontChange event will be emitted by super().setFont(), caught by changeEvent,
        # which will then call _adjust_font_size. _adjust_font_size will set the flag.

# Example Usage (can be run independently for testing):
if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

    app = QApplication(sys.argv)

    window = QWidget()
    layout = QVBoxLayout(window)

    # Button with short text
    button1 = AdjustableButton("Short")
    layout.addWidget(button1)

    # Button with medium text
    button2 = AdjustableButton("Medium Length Text")
    layout.addWidget(button2)
    
    # Button with very long text that will need to shrink
    button3 = AdjustableButton("This is a Very Long Text String for the Button")
    layout.addWidget(button3)

    # Button with text that might change
    button4 = AdjustableButton("Initial Text")
    layout.addWidget(button4)
    
    # Simulate text change after a delay (e.g. language change)
    from PySide6.QtCore import QTimer
    def change_text():
        button4.setText("New Longer Text After Update")
    QTimer.singleShot(2000, change_text)


    window.setGeometry(100, 100, 300, 200) # x, y, width, height
    window.setWindowTitle("AdjustableButton Test")
    window.show()

    sys.exit(app.exec()) 