"""
Toast notification component
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QGraphicsOpacityEffect,
    QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QPainter, QColor

class ToastNotification(QWidget):
    """Toast notification widget that appears and fades out"""
    
    def __init__(self, parent=None, duration=3000):
        """
        Initialize the toast notification.
        
        Args:
            parent: Parent widget
            duration: Duration to show the toast in milliseconds
        """
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.duration = duration
        self.opacity_effect = None
        self.fade_animation = None
        self.timer = None
        
        # Style settings
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        # Create the layout
        self._create_layout()
        
        # Set up opacity effect for fade animation
        self._setup_opacity()
        
    def _create_layout(self):
        """Create the toast layout"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Toast message label
        self.message_label = QLabel("")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet("""
            color: white;
            background-color: transparent;
            font-size: 14px;
        """)
        layout.addWidget(self.message_label)
        
        # Style the widget
        self.setStyleSheet("""
            ToastNotification {
                background-color: rgba(60, 60, 60, 220);
                border-radius: 8px;
            }
        """)
        
    def _setup_opacity(self):
        """Set up opacity effect and animation"""
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)
        
        # Create fade-in animation
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Create timer for auto-hide
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._start_fade_out)
        
    def _start_fade_out(self):
        """Start the fade-out animation"""
        fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_out.setDuration(300)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        fade_out.finished.connect(self.hide)
        fade_out.start()
        
    def show_message(self, message, duration=None):
        """
        Show a toast message.
        
        Args:
            message: Message to display
            duration: Optional custom duration in milliseconds
        """
        # Update message
        self.message_label.setText(message)
        
        # Adjust size to fit content
        self.adjustSize()
        
        # Position the toast at the bottom center of the parent
        if self.parent():
            parent_rect = self.parent().rect()
            x = (parent_rect.width() - self.width()) // 2
            y = parent_rect.height() - self.height() - 20  # 20px from bottom
            self.move(x, y)
        
        # Show with fade-in animation
        self.show()
        self.fade_animation.start()
        
        # Start timer for auto-hide
        use_duration = duration if duration is not None else self.duration
        self.timer.start(use_duration)
        
    def paintEvent(self, event):
        """Custom paint event for rounded corners"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Set background color
        painter.setBrush(QColor(60, 60, 60, 220))
        
        # Draw rounded rectangle
        painter.drawRoundedRect(self.rect(), 8, 8)
        
    def sizeHint(self):
        """Return a good default size"""
        return QSize(300, 50) 