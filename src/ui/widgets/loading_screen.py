"""
Cartoon-style loading screen widget for image processing operations.
"""
import math
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPixmap, QPainterPath
from PySide6.QtCore import QRect, QPoint


class CartoonLoadingScreen(QWidget):
    """A cartoon-style loading screen with animated elements."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 300)
        # Make it modal and stay on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Animation properties
        self._rotation = 0
        self._bounce_offset = 0
        self._pulse_scale = 1.0
        
        # Current message (initialize before setup_ui)
        self.current_message = "Processing your image..."
        
        # Setup UI
        self._setup_ui()
        
        # Initialize animation timers but don't start them yet
        self._setup_animation_timers()
        
    def _setup_ui(self):
        """Setup the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Main content area (will be custom painted)
        self.content_area = QWidget()
        self.content_area.setMinimumHeight(200)
        layout.addWidget(self.content_area)
        
        # Message label
        self.message_label = QLabel(self.current_message)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 16px;
                font-weight: bold;
                background: rgba(255, 255, 255, 200);
                border-radius: 10px;
                padding: 10px;
                border: 2px solid #3498db;
            }
        """)
        layout.addWidget(self.message_label)
        
    def _setup_animation_timers(self):
        """Initialize animation timers without starting them."""
        # Rotation animation for spinner
        self.rotation_timer = QTimer()
        self.rotation_timer.timeout.connect(self._update_rotation)
        
        # Bounce animation
        self.bounce_timer = QTimer()
        self.bounce_timer.timeout.connect(self._update_bounce)
        
        # Pulse animation
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self._update_pulse)
        
        # Animation counters
        self.rotation_counter = 0
        self.bounce_counter = 0
        self.pulse_counter = 0
        
    def _start_animations(self):
        """Start all animations."""
        self.rotation_timer.start(50)  # 20 FPS
        self.bounce_timer.start(100)  # 10 FPS
        self.pulse_timer.start(80)  # ~12 FPS
        
    def _stop_animations(self):
        """Stop all animations."""
        if hasattr(self, 'rotation_timer'):
            self.rotation_timer.stop()
        if hasattr(self, 'bounce_timer'):
            self.bounce_timer.stop()
        if hasattr(self, 'pulse_timer'):
            self.pulse_timer.stop()
        
    def _update_rotation(self):
        """Update rotation animation."""
        self.rotation_counter += 1
        self._rotation = (self.rotation_counter * 6) % 360
        self.update()
        
    def _update_bounce(self):
        """Update bounce animation."""
        self.bounce_counter += 1
        self._bounce_offset = math.sin(self.bounce_counter * 0.3) * 10
        self.update()
        
    def _update_pulse(self):
        """Update pulse animation."""
        self.pulse_counter += 1
        self._pulse_scale = 1.0 + math.sin(self.pulse_counter * 0.2) * 0.1
        self.update()
        
    def paintEvent(self, event):
        """Custom paint event for cartoon graphics."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background with rounded corners
        bg_rect = self.rect().adjusted(10, 10, -10, -10)
        painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
        painter.setPen(QPen(QColor(52, 152, 219), 3))
        painter.drawRoundedRect(bg_rect, 20, 20)
        
        # Draw cartoon elements
        self._draw_cartoon_elements(painter)
        
    def _draw_cartoon_elements(self, painter):
        """Draw the cartoon loading elements."""
        center_x = self.width() // 2
        center_y = self.height() // 2 - 30
        
        # Draw spinning gear/cog
        self._draw_spinning_gear(painter, center_x - 60, center_y - 20, 40)
        
        # Draw bouncing dots
        self._draw_bouncing_dots(painter, center_x + 20, center_y)
        
        # Draw pulsing circle
        self._draw_pulsing_circle(painter, center_x, center_y + 40)
        
        # Draw magic sparkles
        self._draw_sparkles(painter)
        
    def _draw_spinning_gear(self, painter, x, y, radius):
        """Draw a spinning gear."""
        painter.save()
        painter.translate(x, y)
        painter.rotate(self._rotation)
        
        # Gear body
        painter.setBrush(QBrush(QColor(52, 152, 219)))
        painter.setPen(QPen(QColor(41, 128, 185), 2))
        painter.drawEllipse(-radius//2, -radius//2, radius, radius)
        
        # Gear teeth
        teeth = 8
        for i in range(teeth):
            angle = (360 / teeth) * i
            painter.save()
            painter.rotate(angle)
            tooth_rect = QRect(-3, -radius//2 - 5, 6, 8)
            painter.drawRect(tooth_rect)
            painter.restore()
            
        # Center hole
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(-8, -8, 16, 16)
        
        painter.restore()
        
    def _draw_bouncing_dots(self, painter, x, y):
        """Draw bouncing dots."""
        colors = [QColor(231, 76, 60), QColor(46, 204, 113), QColor(241, 196, 15)]
        
        for i, color in enumerate(colors):
            dot_x = x + i * 20
            dot_y = y + math.sin(self.bounce_counter * 0.3 + i * 0.5) * 15
            
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(120), 2))
            painter.drawEllipse(dot_x - 8, int(dot_y) - 8, 16, 16)
            
    def _draw_pulsing_circle(self, painter, x, y):
        """Draw a pulsing circle."""
        radius = int(20 * self._pulse_scale)
        
        painter.setBrush(QBrush(QColor(155, 89, 182, 150)))
        painter.setPen(QPen(QColor(142, 68, 173), 2))
        painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)
        
    def _draw_sparkles(self, painter):
        """Draw animated sparkles around the loading area."""
        sparkle_positions = [
            (50, 80), (350, 100), (80, 180), (320, 160),
            (100, 50), (300, 220), (60, 140), (340, 70)
        ]
        
        painter.setBrush(QBrush(QColor(241, 196, 15)))
        painter.setPen(QPen(QColor(243, 156, 18), 1))
        
        for i, (sx, sy) in enumerate(sparkle_positions):
            # Animate sparkle size based on time and position
            sparkle_scale = 0.5 + 0.5 * math.sin(self.pulse_counter * 0.15 + i * 0.8)
            size = int(6 * sparkle_scale)
            
            if size > 2:  # Only draw if visible
                # Draw star shape
                self._draw_star(painter, sx, sy, size)
                
    def _draw_star(self, painter, x, y, size):
        """Draw a small star."""
        painter.save()
        painter.translate(x, y)
        
        # Simple star using lines
        painter.setPen(QPen(QColor(241, 196, 15), 2))
        painter.drawLine(-size, 0, size, 0)  # Horizontal line
        painter.drawLine(0, -size, 0, size)  # Vertical line
        painter.drawLine(-size//2, -size//2, size//2, size//2)  # Diagonal 1
        painter.drawLine(-size//2, size//2, size//2, -size//2)  # Diagonal 2
        
        painter.restore()
        
    def set_message(self, message):
        """Set the loading message."""
        self.current_message = message
        self.message_label.setText(message)
        
    def show_loading(self, message="Processing your image..."):
        """Show the loading screen with a message."""
        self.set_message(message)
        
        # Center the loading screen over the parent
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)
        
        # Start animations when showing
        self._start_animations()
        
        self.show()
        self.raise_()
        self.activateWindow()
        
    def hide_loading(self):
        """Hide the loading screen."""
        # Stop animations when hiding
        self._stop_animations()
        self.hide()
        
    def closeEvent(self, event):
        """Clean up timers when closing."""
        self._stop_animations()
        super().closeEvent(event) 