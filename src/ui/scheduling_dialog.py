"""
Provides the UI components for managing post schedules.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTimeEdit, QCalendarWidget, QCheckBox,
    QSpinBox, QLineEdit, QMessageBox, QWidget, QScrollArea,
    QFrame, QSizePolicy
)

from ..config import constants as const
from ..models.app_state import AppState

class ScheduleDialog(QDialog):
    """Dialog for creating and editing post schedules."""
    
    schedule_saved = Signal(dict)  # Emitted when a schedule is saved
    
    def __init__(self, parent=None, schedule_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.schedule_data = schedule_data or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.setWindowTitle("Post Schedule")
        self.setMinimumWidth(600)
        self.setMinimumHeight(350)
        self.setStyleSheet("""
            QCalendarWidget {
                background-color: white;
                color: #333333;
            }
            QCalendarWidget QToolButton {
                color: #333333;
                background-color: #f5f5f5;
                border: 1px solid #cccccc;
                border-radius: 2px;
                padding: 3px;
            }
            QCalendarWidget QMenu {
                background-color: white;
                color: #333333;
            }
            QCalendarWidget QSpinBox {
                background-color: white;
                color: #333333;
                selection-background-color: #4CAF50;
                selection-color: white;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #333333;
                background-color: white;
                selection-background-color: #4CAF50;
                selection-color: white;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #808080;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #f5f5f5;
            }
        """)
        
        self._init_ui()
        self._load_schedule_data()
        
    def _init_ui(self) -> None:
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Dialog title
        title_label = QLabel("Create Posting Schedule")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333333; padding-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Schedule name
        name_layout = QHBoxLayout()
        name_label = QLabel("Schedule Name:")
        name_label.setMinimumWidth(120)
        name_label.setStyleSheet("color: #333333; font-weight: bold;")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter a name for this schedule")
        self.name_edit.setStyleSheet("padding: 8px; border: 1px solid #cccccc; border-radius: 4px; color: black; background-color: white;")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Schedule mode
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Schedule Mode:")
        mode_label.setMinimumWidth(120)
        mode_label.setStyleSheet("color: #333333; font-weight: bold;")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Basic", "Advanced"])
        self.mode_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                color: black;
                background-color: white;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border-left: 1px solid #cccccc;
            }
        """)
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)
        
        # Mode description
        self.mode_description = QLabel()
        self.mode_description.setWordWrap(True)
        self.mode_description.setStyleSheet("color: #333333; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(self.mode_description)
        
        # Mode containers with styling
        container_style = """
            QWidget {
                background-color: #f9f9f9;
                border: 1px solid #dddddd;
                border-radius: 6px;
                padding: 10px;
            }
        """
        
        # Restore the basic and advanced mode widgets
        # Basic mode widgets
        self.basic_widgets = QWidget()
        self.basic_widgets.setStyleSheet(container_style)
        basic_layout = QVBoxLayout(self.basic_widgets)
        
        # Day selection container
        days_container = QWidget()
        days_container.setStyleSheet("background-color: #f9f9f9; border: 1px solid #dddddd; border-radius: 6px; padding: 10px;")
        days_container_layout = QVBoxLayout(days_container)
        
        days_title = QLabel("Choose which days to post:")
        days_title.setStyleSheet("font-weight: bold; color: #333333; margin-bottom: 5px;")
        days_container_layout.addWidget(days_title)
        
        days_layout = QHBoxLayout()
        self.day_checkboxes = {}
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            checkbox = QCheckBox(day)
            checkbox.setStyleSheet("""
                QCheckBox {
                    spacing: 5px;
                    font-size: 12px;
                    color: #333333;
                    font-weight: bold;
                    padding: 2px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                }
                QCheckBox::indicator:checked {
                    background-color: #4CAF50;
                    border: 2px solid #4CAF50;
                }
            """)
            self.day_checkboxes[day] = checkbox
            days_layout.addWidget(checkbox)
        days_container_layout.addLayout(days_layout)
        
        # Add the day selection to the basic mode widget
        basic_layout.addWidget(days_container)
        
        layout.addWidget(self.basic_widgets)
        
        # Advanced mode widgets
        self.advanced_widgets = QWidget()
        self.advanced_widgets.setStyleSheet(container_style)
        advanced_layout = QVBoxLayout(self.advanced_widgets)
        
        advanced_description = QLabel("Set different posting times for each day of the week:")
        advanced_description.setStyleSheet("margin-bottom: 10px; color: #333333;")
        advanced_layout.addWidget(advanced_description)
        
        # Create a scroll area for day schedules
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Day schedules
        self.day_schedule_widgets = {}
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            day_widget = DayScheduleWidget(day)
            self.day_schedule_widgets[day] = day_widget
            scroll_layout.addWidget(day_widget)
            
        scroll_area.setWidget(scroll_content)
        advanced_layout.addWidget(scroll_area)
        
        layout.addWidget(self.advanced_widgets)
        
        # Date range with styling
        date_container = QWidget()
        date_container.setStyleSheet(container_style)
        date_container_layout = QVBoxLayout(date_container)
        
        date_layout = QHBoxLayout()
        
        # Start calendar
        self.start_calendar = QCalendarWidget()
        self.start_calendar.setMinimumDate(datetime.now().date())
        self.start_calendar.setMaximumHeight(200)
        self.start_calendar.setGridVisible(True)
        self.start_calendar.setNavigationBarVisible(True)
        self.start_calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.start_calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.SingleLetterDayNames)
        self.start_calendar.setSelectionMode(QCalendarWidget.SelectionMode.SingleSelection)
        # Make calendar cells actively interactive with highly visible text
        self.start_calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: white;
                color: black;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: black;
                background-color: white;
                selection-background-color: #4CAF50;
                selection-color: white;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #808080;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #f5f5f5;
            }
            QCalendarWidget QToolButton {
                color: black;
                font-weight: bold;
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
            }
            QCalendarWidget QMenu {
                color: black;
                background-color: white;
            }
            QCalendarWidget QSpinBox {
                color: black;
                background-color: white;
            }
            /* Make sure all day numbers are clearly visible */
            QCalendarWidget QTableView {
                alternate-background-color: #f9f9f9;
            }
        """)
        # Set a default selected date (today)
        today = datetime.now().date()
        self.start_calendar.setSelectedDate(today)
        # Connect signals
        self.start_calendar.clicked.connect(self._on_start_date_clicked)
        self.start_calendar.selectionChanged.connect(self._on_start_date_changed)
        
        # End calendar
        self.end_calendar = QCalendarWidget()
        self.end_calendar.setMinimumDate(datetime.now().date())
        self.end_calendar.setMaximumHeight(200)
        self.end_calendar.setGridVisible(True)
        self.end_calendar.setNavigationBarVisible(True)
        self.end_calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.end_calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.SingleLetterDayNames)
        self.end_calendar.setSelectionMode(QCalendarWidget.SelectionMode.SingleSelection)
        # Make calendar cells actively interactive with highly visible text
        self.end_calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: white;
                color: black;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: black;
                background-color: white;
                selection-background-color: #4CAF50;
                selection-color: white;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #808080;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #f5f5f5;
            }
            QCalendarWidget QToolButton {
                color: black;
                font-weight: bold;
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
            }
            QCalendarWidget QMenu {
                color: black;
                background-color: white;
            }
            QCalendarWidget QSpinBox {
                color: black;
                background-color: white;
            }
            /* Make sure all day numbers are clearly visible */
            QCalendarWidget QTableView {
                alternate-background-color: #f9f9f9;
            }
        """)
        # Set a default selected date (one week from today)
        self.end_calendar.setSelectedDate(today + timedelta(days=7))
        # Connect signals
        self.end_calendar.clicked.connect(self._on_end_date_clicked)
        self.end_calendar.selectionChanged.connect(self._on_end_date_changed)
        
        # Create frames with headers for the calendars
        start_frame = QFrame()
        start_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Plain)
        start_frame_layout = QVBoxLayout(start_frame)
        start_label = QLabel("Start Date:")
        start_label.setStyleSheet("font-weight: bold; color: black;")
        start_frame_layout.addWidget(start_label)
        
        # Add a visible date display label
        self.start_date_display = QLabel(today.strftime("%Y-%m-%d"))
        self.start_date_display.setStyleSheet("""
            background-color: white; 
            color: black;
            padding: 8px;
            border: 2px solid #4CAF50;
            border-radius: 4px;
            font-weight: bold;
            font-size: 14px;
        """)
        self.start_date_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        start_frame_layout.addWidget(self.start_date_display)
        start_frame_layout.addWidget(self.start_calendar)
        
        end_frame = QFrame()
        end_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Plain)
        end_frame_layout = QVBoxLayout(end_frame)
        end_label = QLabel("End Date:")
        end_label.setStyleSheet("font-weight: bold; color: black;")
        end_frame_layout.addWidget(end_label)
        
        # Add a visible date display label
        end_date = today + timedelta(days=7)
        self.end_date_display = QLabel(end_date.strftime("%Y-%m-%d"))
        self.end_date_display.setStyleSheet("""
            background-color: white; 
            color: black;
            padding: 8px;
            border: 2px solid #4CAF50;
            border-radius: 4px;
            font-weight: bold;
            font-size: 14px;
        """)
        self.end_date_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        end_frame_layout.addWidget(self.end_date_display)
        end_frame_layout.addWidget(self.end_calendar)
        
        # Add frames to layout
        date_layout.addWidget(start_frame)
        date_layout.addWidget(end_frame)
        
        date_container_layout.addLayout(date_layout)
        layout.addWidget(date_container)
        
        # Posts per day with styling
        posts_container = QWidget()
        posts_container.setStyleSheet(container_style)
        posts_container_layout = QVBoxLayout(posts_container)
        
        posts_layout = QHBoxLayout()
        posts_label = QLabel("Posts per Day:")
        posts_label.setStyleSheet("color: #333333; font-weight: bold;")
        self.posts_spin = QSpinBox()
        self.posts_spin.setMinimum(1)
        self.posts_spin.setMaximum(7)
        self.posts_spin.setValue(3)
        self.posts_spin.setStyleSheet("""
            QSpinBox {
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                min-width: 80px;
                color: black;
                background-color: white;
            }
        """)
        # Connect the spinbox change to update time inputs
        self.posts_spin.valueChanged.connect(self._update_time_inputs)
        
        posts_layout.addWidget(posts_label)
        posts_layout.addWidget(self.posts_spin)
        posts_layout.addStretch()
        posts_container_layout.addLayout(posts_layout)
        
        # Create a container for the multiple time inputs
        self.time_inputs_container = QWidget()
        self.time_inputs_layout = QVBoxLayout(self.time_inputs_container)
        
        # Initialize time inputs based on default value
        self._create_time_inputs(self.posts_spin.value())
        
        posts_container_layout.addWidget(self.time_inputs_container)
        layout.addWidget(posts_container)
        
        # Buttons with styling
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #f0f0f0;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        
        save_button = QPushButton("Save Schedule")
        save_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_button.clicked.connect(self._save_schedule)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        layout.addLayout(button_layout)
        
        # Set initial mode
        self._on_mode_changed(self.mode_combo.currentText())
        
    def _on_mode_changed(self, mode: str) -> None:
        """Handle mode change between basic and advanced scheduling."""
        is_basic = mode == "Basic"
        self.basic_widgets.setVisible(is_basic)
        self.advanced_widgets.setVisible(not is_basic)
        
        # Update description based on mode
        if is_basic:
            self.mode_description.setText(
                "Basic mode: Choose specific days and a single posting time for all posts."
            )
        else:
            self.mode_description.setText(
                "Advanced mode: Set different posting times for each day of the week."
            )
        
    def _load_schedule_data(self) -> None:
        """Load existing schedule data into the UI."""
        if not self.schedule_data:
            return
            
        try:
            # Set basic fields
            self.name_edit.setText(self.schedule_data.get("name", ""))
            self.mode_combo.setCurrentText(self.schedule_data.get("mode", "Basic"))
            
            # Set posts per day
            posts_per_day = self.schedule_data.get("posts_per_day", 3)
            self.posts_spin.setValue(posts_per_day)
            
            # Set dates
            start_date_str = self.schedule_data.get("start_date", "")
            if start_date_str:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                self.start_calendar.setSelectedDate(start_date)
                
            end_date_str = self.schedule_data.get("end_date", "")
            if end_date_str:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                self.end_calendar.setSelectedDate(end_date)
                
            # Set mode-specific data
            if self.schedule_data.get("mode", "").lower() == "basic":
                # Set days
                days = self.schedule_data.get("days", [])
                for day, checkbox in self.day_checkboxes.items():
                    checkbox.setChecked(day in days)
                    
                # Set posting times
                posting_times = self.schedule_data.get("posting_times", [])
                if posting_times:
                    # Recreate time inputs if needed to match the number of posting times
                    if len(posting_times) != len(self.time_edits):
                        self._create_time_inputs(len(posting_times))
                    
                    # Set each time
                    for i, time_str in enumerate(posting_times):
                        if i < len(self.time_edits):
                            try:
                                hours, minutes = map(int, time_str.split(":"))
                                self.time_edits[i].setTime(datetime.now().replace(hour=hours, minute=minutes).time())
                            except (ValueError, IndexError):
                                pass
                    
            else:
                # Set day schedules
                day_schedules = self.schedule_data.get("day_schedules", {})
                for day, widget in self.day_schedule_widgets.items():
                    if day in day_schedules:
                        widget.load_data(day_schedules[day])
                        
        except Exception as e:
            self.logger.exception(f"Error loading schedule data: {e}")
            QMessageBox.warning(
                self,
                "Load Error",
                f"Failed to load schedule data: {str(e)}"
            )
            
    def _save_schedule(self) -> None:
        """Save the schedule data."""
        try:
            # Validate required fields
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Validation Error", "Please enter a schedule name.")
                return
                
            # Get mode
            mode = self.mode_combo.currentText().lower()
            
            # Build schedule data
            schedule_data = {
                "id": self.schedule_data.get("id", ""),  # Preserve ID if editing
                "name": name,
                "mode": mode,
                "posts_per_day": self.posts_spin.value(),
                "start_date": self.start_calendar.selectedDate().toString("yyyy-MM-dd"),
                "end_date": self.end_calendar.selectedDate().toString("yyyy-MM-dd")
            }
            
            # Log the data to be saved
            self.logger.info(f"Saving schedule: {name}")
            self.logger.info(f"Schedule data: start_date={schedule_data['start_date']}, end_date={schedule_data['end_date']}")
            
            # Add mode-specific data
            if mode == "basic":
                # Get selected days
                days = [day for day, checkbox in self.day_checkboxes.items() if checkbox.isChecked()]
                if not days:
                    QMessageBox.warning(self, "Validation Error", "Please select at least one posting day.")
                    return
                
                # Get all posting times
                posting_times = [time_edit.time().toString("HH:mm") for time_edit in self.time_edits]
                    
                schedule_data.update({
                    "days": days,
                    "posting_times": posting_times
                })
                
            else:
                # Get day schedules
                day_schedules = {}
                for day, widget in self.day_schedule_widgets.items():
                    day_data = widget.get_data()
                    if day_data["enabled"]:
                        day_schedules[day] = day_data
                        
                if not day_schedules:
                    QMessageBox.warning(self, "Validation Error", "Please enable at least one day schedule.")
                    return
                    
                schedule_data["day_schedules"] = day_schedules
            
            # Store the data in the object for access
            self.schedule_data = schedule_data
                
            # Emit signal with schedule data
            self.schedule_saved.emit(schedule_data)
            self.accept()
            
        except Exception as e:
            self.logger.exception(f"Error saving schedule: {e}")
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save schedule: {str(e)}"
            )
            
    def _on_start_date_clicked(self, date):
        """Handle click events on start calendar."""
        date_str = date.toString("yyyy-MM-dd")
        self.logger.info(f"Start date clicked: {date_str}")
        self.start_calendar.setSelectedDate(date)
        # Update the display label
        self.start_date_display.setText(date_str)
        # Forcefully update the calendar display
        self.start_calendar.repaint()
        # Update end date minimum if needed
        if self.end_calendar.selectedDate() < date:
            self.end_calendar.setSelectedDate(date)
            self.end_date_display.setText(date_str)
        self.update()
            
    def _on_start_date_changed(self):
        """Handle selection changes on start calendar."""
        date = self.start_calendar.selectedDate()
        date_str = date.toString("yyyy-MM-dd")
        self.logger.info(f"Start date changed: {date_str}")
        # Update the display label
        self.start_date_display.setText(date_str)
        # Update end date minimum if needed
        if self.end_calendar.selectedDate() < date:
            self.end_calendar.setSelectedDate(date)
            self.end_date_display.setText(date_str)
        self.update()
            
    def _on_end_date_clicked(self, date):
        """Handle click events on end calendar."""
        date_str = date.toString("yyyy-MM-dd")
        self.logger.info(f"End date clicked: {date_str}")
        self.end_calendar.setSelectedDate(date)
        # Update the display label
        self.end_date_display.setText(date_str)
        # Forcefully update the calendar display
        self.end_calendar.repaint()
        self.update()
        
    def _on_end_date_changed(self):
        """Handle selection changes on end calendar."""
        date = self.end_calendar.selectedDate()
        date_str = date.toString("yyyy-MM-dd")
        self.logger.info(f"End date changed: {date_str}")
        # Update the display label
        self.end_date_display.setText(date_str)
        self.update()
        
    def _update_time_inputs(self, value):
        """Update the number of time inputs based on posts per day value."""
        self._create_time_inputs(value)
        
    def _create_time_inputs(self, count):
        """Create the specified number of time inputs."""
        # Clear existing time inputs
        while self.time_inputs_layout.count():
            item = self.time_inputs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Add time inputs header
        time_header = QLabel("Posting Times:")
        time_header.setStyleSheet("color: #333333; font-weight: bold; margin-top: 10px;")
        self.time_inputs_layout.addWidget(time_header)
        
        # Add new time inputs
        self.time_edits = []
        for i in range(count):
            time_layout = QHBoxLayout()
            time_label = QLabel(f"Time {i+1}:")
            time_label.setStyleSheet("color: #333333;")
            
            time_edit = QTimeEdit()
            time_edit.setDisplayFormat("HH:mm")
            # Set staggered default times (9:00, 12:00, 15:00, etc.)
            base_time = datetime.now().replace(hour=9, minute=0)
            time_edit.setTime((base_time + timedelta(hours=i*3)).time())
            time_edit.setStyleSheet("""
                QTimeEdit {
                    padding: 8px;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    color: black;
                    background-color: white;
                    min-width: 80px;
                }
            """)
            
            self.time_edits.append(time_edit)
            time_layout.addWidget(time_label)
            time_layout.addWidget(time_edit)
            time_layout.addStretch()
            
            self.time_inputs_layout.addLayout(time_layout)
        
class DayScheduleWidget(QFrame):
    """Widget for configuring a single day's schedule in advanced mode."""
    
    def __init__(self, day_name: str, parent=None):
        super().__init__(parent)
        self.day_name = day_name
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(self)
        
        # Day header
        header_layout = QHBoxLayout()
        self.enabled_checkbox = QCheckBox(day_name)
        header_layout.addWidget(self.enabled_checkbox)
        layout.addLayout(header_layout)
        
        # Times list
        self.times_layout = QVBoxLayout()
        layout.addLayout(self.times_layout)
        
        # Add time button
        add_time_button = QPushButton("Add Posting Time")
        add_time_button.clicked.connect(self._add_time_widget)
        layout.addWidget(add_time_button)
        
        # Add initial time widget
        self._add_time_widget()
        
    def _add_time_widget(self) -> None:
        """Add a new time widget to the day schedule."""
        time_widget = QWidget()
        time_layout = QHBoxLayout(time_widget)
        
        time_edit = QTimeEdit()
        time_edit.setDisplayFormat("HH:mm")
        time_edit.setTime(datetime.now().time())
        
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(lambda: self._remove_time_widget(time_widget))
        
        time_layout.addWidget(time_edit)
        time_layout.addWidget(remove_button)
        
        self.times_layout.addWidget(time_widget)
        
    def _remove_time_widget(self, widget: QWidget) -> None:
        """Remove a time widget from the day schedule."""
        if self.times_layout.count() > 1:  # Keep at least one time
            self.times_layout.removeWidget(widget)
            widget.deleteLater()
            
    def load_data(self, data: Dict[str, Any]) -> None:
        """Load day schedule data into the widget."""
        try:
            self.enabled_checkbox.setChecked(data.get("enabled", False))
            
            # Clear existing time widgets
            while self.times_layout.count():
                item = self.times_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                    
            # Add time widgets
            times = data.get("times", [])
            if not times:
                self._add_time_widget()
            else:
                for time_str in times:
                    time_widget = QWidget()
                    time_layout = QHBoxLayout(time_widget)
                    
                    time_edit = QTimeEdit()
                    time_edit.setDisplayFormat("HH:mm")
                    try:
                        hours, minutes = map(int, time_str.split(":"))
                        time_edit.setTime(datetime.now().replace(hour=hours, minute=minutes).time())
                    except ValueError:
                        time_edit.setTime(datetime.now().time())
                        
                    remove_button = QPushButton("Remove")
                    remove_button.clicked.connect(lambda: self._remove_time_widget(time_widget))
                    
                    time_layout.addWidget(time_edit)
                    time_layout.addWidget(remove_button)
                    
                    self.times_layout.addWidget(time_widget)
                    
        except Exception as e:
            logging.getLogger(self.__class__.__name__).exception(f"Error loading day schedule data: {e}")
            
    def get_data(self) -> Dict[str, Any]:
        """Get the day schedule data from the widget."""
        try:
            times = []
            for i in range(self.times_layout.count()):
                item = self.times_layout.itemAt(i)
                if item and item.widget():
                    time_edit = item.widget().findChild(QTimeEdit)
                    if time_edit:
                        times.append(time_edit.time().toString("HH:mm"))
                        
            return {
                "enabled": self.enabled_checkbox.isChecked(),
                "times": times
            }
            
        except Exception as e:
            logging.getLogger(self.__class__.__name__).exception(f"Error getting day schedule data: {e}")
            return {"enabled": False, "times": []} 