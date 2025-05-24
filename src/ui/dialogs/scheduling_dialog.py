"""
Provides the UI components for managing post schedules.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from PySide6.QtCore import Qt, Signal, QObject, QEvent
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTimeEdit, QCalendarWidget, QCheckBox,
    QSpinBox, QLineEdit, QMessageBox, QWidget, QScrollArea,
    QFrame, QSizePolicy
)
from PySide6.QtWidgets import QApplication

from ...config import constants as const
from ...models.app_state import AppState
from ..base_dialog import BaseDialog

class ScheduleDialog(BaseDialog):
    """Dialog for creating and editing post schedules."""
    
    schedule_saved = Signal(dict)  # Emitted when a schedule is saved
    
    def __init__(self, parent=None, schedule_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.schedule_data = schedule_data or {}
        
        self._init_ui_elements()
        self._init_ui()
        self._load_schedule_data()
        self.retranslateUi()
        
    def _init_ui_elements(self):
        """Initialize UI elements that need to be instance attributes for retranslation."""
        self.title_label = QLabel()
        self.name_label = QLabel()
        self.name_edit = QLineEdit()
        self.mode_label = QLabel()
        self.mode_combo = QComboBox()
        self.mode_description = QLabel()
        self.basic_widgets = QWidget()
        self.days_title = QLabel()
        self.day_checkboxes = {}
        self.advanced_widgets = QWidget()
        self.advanced_description = QLabel()
        self.day_schedule_widgets = {}
        self.start_label = QLabel()
        self.start_date_display = QLabel()
        self.start_calendar = QCalendarWidget()
        self.end_label = QLabel()
        self.end_date_display = QLabel()
        self.end_calendar = QCalendarWidget()
        self.posts_label = QLabel()
        self.posts_spin = QSpinBox()
        self.time_inputs_container = QWidget()
        self.time_inputs_layout = QVBoxLayout(self.time_inputs_container)
        self.time_edits = []
        self.time_header_label = QLabel()
        self.cancel_button = QPushButton()
        self.save_button = QPushButton()
        
    def _init_ui(self) -> None:
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333333; padding-bottom: 10px;")
        layout.addWidget(self.title_label)
        
        name_layout = QHBoxLayout()
        self.name_label.setMinimumWidth(120)
        self.name_label.setStyleSheet("color: #333333; font-weight: bold;")
        self.name_edit.setStyleSheet("padding: 8px; border: 1px solid #cccccc; border-radius: 4px; color: black; background-color: white;")
        name_layout.addWidget(self.name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        mode_layout = QHBoxLayout()
        self.mode_label.setMinimumWidth(120)
        self.mode_label.setStyleSheet("color: #333333; font-weight: bold;")
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
        mode_layout.addWidget(self.mode_label)
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)
        
        self.mode_description.setWordWrap(True)
        self.mode_description.setStyleSheet("color: #333333; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(self.mode_description)
        
        container_style = """
            QWidget {
                background-color: #f9f9f9;
                border: 1px solid #dddddd;
                border-radius: 6px;
                padding: 10px;
            }
        """
        
        self.basic_widgets.setStyleSheet(container_style)
        basic_layout = QVBoxLayout(self.basic_widgets)
        
        days_container = QWidget()
        days_container.setStyleSheet("background-color: #f9f9f9; border: 1px solid #dddddd; border-radius: 6px; padding: 10px;")
        days_container_layout = QVBoxLayout(days_container)
        
        self.days_title.setStyleSheet("font-weight: bold; color: #333333; margin-bottom: 5px;")
        days_container_layout.addWidget(self.days_title)
        
        days_layout = QHBoxLayout()
        for day_key in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            checkbox = QCheckBox(self.tr(day_key))
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
            self.day_checkboxes[day_key] = checkbox
            days_layout.addWidget(checkbox)
        days_container_layout.addLayout(days_layout)
        basic_layout.addWidget(days_container)
        layout.addWidget(self.basic_widgets)
        
        self.advanced_widgets.setStyleSheet(container_style)
        advanced_layout = QVBoxLayout(self.advanced_widgets)
        
        self.advanced_description.setStyleSheet("margin-bottom: 10px; color: #333333;")
        advanced_layout.addWidget(self.advanced_description)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        for day_key in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            day_widget = DayScheduleWidget(day_key)
            self.day_schedule_widgets[day_key] = day_widget
            scroll_layout.addWidget(day_widget)
            
        scroll_area.setWidget(scroll_content)
        advanced_layout.addWidget(scroll_area)
        layout.addWidget(self.advanced_widgets)
        
        date_container = QWidget()
        date_container.setStyleSheet(container_style)
        date_container_layout = QVBoxLayout(date_container)
        date_layout = QHBoxLayout()
        
        today = datetime.now().date()
        self.start_calendar.setSelectedDate(today)
        self.start_calendar.clicked.connect(self._on_start_date_clicked)
        self.start_calendar.selectionChanged.connect(self._on_start_date_changed)
        
        self.end_calendar.setSelectedDate(today + timedelta(days=7))
        self.end_calendar.clicked.connect(self._on_end_date_clicked)
        self.end_calendar.selectionChanged.connect(self._on_end_date_changed)
        
        start_frame = QFrame()
        start_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Plain)
        start_frame_layout = QVBoxLayout(start_frame)
        self.start_label.setStyleSheet("font-weight: bold; color: black;")
        start_frame_layout.addWidget(self.start_label)
        
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
        self.end_label.setStyleSheet("font-weight: bold; color: black;")
        end_frame_layout.addWidget(self.end_label)
        
        end_date = today + timedelta(days=7)
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
        
        date_layout.addWidget(start_frame)
        date_layout.addWidget(end_frame)
        date_container_layout.addLayout(date_layout)
        layout.addWidget(date_container)
        
        posts_container = QWidget()
        posts_container.setStyleSheet(container_style)
        posts_container_layout = QVBoxLayout(posts_container)
        posts_layout = QHBoxLayout()
        self.posts_label.setStyleSheet("color: #333333; font-weight: bold;")
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
        self.posts_spin.valueChanged.connect(self._update_time_inputs)
        posts_layout.addWidget(self.posts_label)
        posts_layout.addWidget(self.posts_spin)
        posts_layout.addStretch()
        posts_container_layout.addLayout(posts_layout)
        
        self._create_time_inputs(self.posts_spin.value())
        posts_container_layout.addWidget(self.time_inputs_container)
        layout.addWidget(posts_container)
        
        button_layout_bottom = QHBoxLayout()
        self.cancel_button.setStyleSheet("""
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
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.setStyleSheet("""
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
        self.save_button.clicked.connect(self._save_schedule)
        button_layout_bottom.addStretch()
        button_layout_bottom.addWidget(self.cancel_button)
        button_layout_bottom.addWidget(self.save_button)
        layout.addLayout(button_layout_bottom)
        
        self._on_mode_changed(self.mode_combo.currentText())
        
    def _on_mode_changed(self, mode: str) -> None:
        """Handle mode selection change."""
        if mode == self.tr("Basic (Same time every day)"):
            self.basic_widgets.setVisible(True)
            self.advanced_widgets.setVisible(False)
            self.mode_description.setText(self.tr("Post at the same times on selected days of the week"))
        elif mode == self.tr("Advanced (Different times per day)"):
            self.basic_widgets.setVisible(False)
            self.advanced_widgets.setVisible(True)
            self.mode_description.setText(self.tr("Set different posting times for each day of the week"))
        else:
            self.basic_widgets.setVisible(False)
            self.advanced_widgets.setVisible(False)
        
    def _load_schedule_data(self) -> None:
        """Load existing schedule data into the UI."""
        if not self.schedule_data:
            return
            
        try:
            self.name_edit.setText(self.schedule_data.get("name", ""))
            self.mode_combo.setCurrentText(self.schedule_data.get("mode", "Basic"))
            
            posts_per_day = self.schedule_data.get("posts_per_day", 3)
            self.posts_spin.setValue(posts_per_day)
            
            start_date_str = self.schedule_data.get("start_date", "")
            if start_date_str:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                self.start_calendar.setSelectedDate(start_date)
                
            end_date_str = self.schedule_data.get("end_date", "")
            if end_date_str:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                self.end_calendar.setSelectedDate(end_date)
                
            if self.schedule_data.get("mode", "").lower() == "basic":
                days = self.schedule_data.get("days", [])
                for day, checkbox in self.day_checkboxes.items():
                    checkbox.setChecked(day in days)
                    
                posting_times = self.schedule_data.get("posting_times", [])
                if posting_times:
                    if len(posting_times) != len(self.time_edits):
                        self._create_time_inputs(len(posting_times))
                    
                    for i, time_str in enumerate(posting_times):
                        if i < len(self.time_edits):
                            try:
                                hours, minutes = map(int, time_str.split(":"))
                                self.time_edits[i].setTime(datetime.now().replace(hour=hours, minute=minutes).time())
                            except (ValueError, IndexError):
                                pass
                    
            else:
                day_schedules = self.schedule_data.get("day_schedules", {})
                for day, widget in self.day_schedule_widgets.items():
                    if day in day_schedules:
                        widget.load_data(day_schedules[day])
                        
        except Exception as e:
            self.logger.exception(f"Error loading schedule data: {e}")
            QMessageBox.warning(
                self,
                self.tr("Load Error"),
                self.tr("Failed to load schedule data: {error_message}").format(error_message=str(e))
            )
            
    def _save_schedule(self) -> None:
        """Save the schedule data."""
        try:
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, self.tr("Validation Error"), self.tr("Please enter a schedule name."))
                return
                
            mode = self.mode_combo.currentText().lower()
            
            schedule_data = {
                "id": self.schedule_data.get("id", ""),
                "name": name,
                "mode": mode,
                "posts_per_day": self.posts_spin.value(),
                "start_date": self.start_calendar.selectedDate().toString("yyyy-MM-dd"),
                "end_date": self.end_calendar.selectedDate().toString("yyyy-MM-dd")
            }
            
            self.logger.info(f"Saving schedule: {name}")
            self.logger.info(f"Schedule data: start_date={schedule_data['start_date']}, end_date={schedule_data['end_date']}")
            
            if mode == "basic":
                days = [day for day, checkbox in self.day_checkboxes.items() if checkbox.isChecked()]
                if not days:
                    QMessageBox.warning(self, self.tr("Validation Error"), self.tr("Please select at least one posting day."))
                    return
                
                posting_times = [time_edit.time().toString("HH:mm") for time_edit in self.time_edits]
                    
                schedule_data.update({
                    "days": days,
                    "posting_times": posting_times
                })
                
            else:
                day_schedules = {}
                for day, widget in self.day_schedule_widgets.items():
                    day_data = widget.get_data()
                    if day_data["enabled"]:
                        day_schedules[day] = day_data
                        
                if not day_schedules:
                    QMessageBox.warning(self, self.tr("Validation Error"), self.tr("Please enable at least one day schedule."))
                    return
                    
                schedule_data["day_schedules"] = day_schedules
            
            self.schedule_data = schedule_data
                
            self.schedule_saved.emit(schedule_data)
            self.accept()
            
        except Exception as e:
            self.logger.exception(f"Error saving schedule: {e}")
            QMessageBox.critical(
                self,
                self.tr("Save Error"),
                self.tr("Failed to save schedule: {error_message}").format(error_message=str(e))
            )
            
    def _on_start_date_clicked(self, date):
        """Handle click events on start calendar."""
        date_str = date.toString("yyyy-MM-dd")
        self.logger.info(f"Start date clicked: {date_str}")
        self.start_calendar.setSelectedDate(date)
        self.start_date_display.setText(date_str)
        self.start_calendar.repaint()
        if self.end_calendar.selectedDate() < date:
            self.end_calendar.setSelectedDate(date)
            self.end_date_display.setText(date_str)
        self.update()
            
    def _on_start_date_changed(self):
        """Handle selection changes on start calendar."""
        date = self.start_calendar.selectedDate()
        date_str = date.toString("yyyy-MM-dd")
        self.logger.info(f"Start date changed: {date_str}")
        self.start_date_display.setText(date_str)
        if self.end_calendar.selectedDate() < date:
            self.end_calendar.setSelectedDate(date)
            self.end_date_display.setText(date_str)
        self.update()
            
    def _on_end_date_clicked(self, date):
        """Handle click events on end calendar."""
        date_str = date.toString("yyyy-MM-dd")
        self.logger.info(f"End date clicked: {date_str}")
        self.end_calendar.setSelectedDate(date)
        self.end_date_display.setText(date_str)
        self.end_calendar.repaint()
        self.update()
        
    def _on_end_date_changed(self):
        """Handle selection changes on end calendar."""
        date = self.end_calendar.selectedDate()
        date_str = date.toString("yyyy-MM-dd")
        self.logger.info(f"End date changed: {date_str}")
        self.end_date_display.setText(date_str)
        self.update()
        
    def _update_time_inputs(self, value):
        """Update the number of time inputs based on posts per day value."""
        self._create_time_inputs(value)
        
    def _create_time_inputs(self, count):
        """Create the specified number of time inputs."""
        # Clear existing time input widgets first
        while self.time_inputs_layout.count():
            item = self.time_inputs_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.time_edits.clear()

        # Add the (now translated) header label for time inputs
        # self.time_header_label is already an instance attribute, text set in retranslateUi
        self.time_inputs_layout.addWidget(self.time_header_label)
        
        self.time_edits = [] # Re-initialize after clearing
        for i in range(count):
            time_layout = QHBoxLayout()
            time_label_text = self.tr("Time {index}:").format(index=i + 1)
            time_label = QLabel(time_label_text)
            time_label.setStyleSheet("color: #333333;")
            
            time_edit = QTimeEdit()
            time_edit.setDisplayFormat("HH:mm")
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
        
    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        """Update UI text elements when language changes."""
        self.setWindowTitle(self.tr("Schedule Post"))
        self.title_label.setText(self.tr("Schedule Post"))
        self.name_label.setText(self.tr("Schedule Name:"))
        self.mode_label.setText(self.tr("Schedule Mode:"))
        
        # Save current selection
        current_mode_index = self.mode_combo.currentIndex()
        
        # Clear and repopulate combo with translated text
        self.mode_combo.clear()
        self.mode_combo.addItem(self.tr("Basic (Same time every day)"))
        self.mode_combo.addItem(self.tr("Advanced (Different times per day)"))
        
        # Restore selection
        if current_mode_index >= 0:
            self.mode_combo.setCurrentIndex(current_mode_index)
        else:
            # If no previous selection, set to default and trigger change
            self.mode_combo.setCurrentIndex(0)
            self._on_mode_changed(self.mode_combo.currentText())
        
        # Update based on current mode
        current_mode = self.mode_combo.currentText()
        self._on_mode_changed(current_mode)
        
        self.days_title.setText(self.tr("Post on these days:"))
        for day_key in self.day_checkboxes:
            self.day_checkboxes[day_key].setText(self.tr(day_key))
        
        self.advanced_description.setText(self.tr("Set specific posting times for each day of the week."))
        
        for day_key, widget in self.day_schedule_widgets.items():
            # Update each day schedule widget by triggering its retranslateUi
            widget.retranslateUi()
        
        self.start_label.setText(self.tr("Start Date:"))
        self.end_label.setText(self.tr("End Date:"))
        self.posts_label.setText(self.tr("Posts per day:"))
        self.time_header_label.setText(self.tr("Post times:"))
        self.cancel_button.setText(self.tr("Cancel"))
        self.save_button.setText(self.tr("Save Schedule"))
        
        # Update date displays
        self._on_start_date_changed()
        self._on_end_date_changed()

class DayScheduleWidget(QFrame):
    """Widget for configuring posting times for a specific day."""
    
    def __init__(self, day_name: str, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{day_name}")
        self.day_name = day_name
        self.time_widgets = []
        self.enabled = True
        
        self.day_label = QLabel(self.tr(day_name))
        self.day_enabled_checkbox = QCheckBox(self.tr("Enabled"))
        self.day_enabled_checkbox.setChecked(True)
        self.day_enabled_checkbox.stateChanged.connect(self._on_day_enabled_changed)
        self.add_time_button = QPushButton(self.tr("Add Time"))
        self.add_time_button.clicked.connect(lambda: self._add_time_widget())
        
        self._setup_ui()
        self.retranslateUi()

    def _setup_ui(self):
        """Set up the day schedule widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Day header with checkbox
        header_layout = QHBoxLayout()
        header_layout.addWidget(self.day_label)
        header_layout.addWidget(self.day_enabled_checkbox)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Add time button
        layout.addWidget(self.add_time_button)
        
        # Time inputs container
        self.time_container = QWidget()
        self.time_layout = QVBoxLayout(self.time_container)
        layout.addWidget(self.time_container)
        
        # Add an initial time widget
        self._add_time_widget()
        
        # Style the widget
        self.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                margin-bottom: 5px;
            }
        """)

    def _on_day_enabled_changed(self, state):
        """Handle day enabled state change."""
        self.enabled = bool(state)
        self.time_container.setVisible(self.enabled)
        self.add_time_button.setEnabled(self.enabled)
        
    def _add_time_widget(self, time_str: Optional[str] = None) -> None:
        """Add a new time widget to the day schedule."""
        time_widget = QWidget()
        time_layout = QHBoxLayout(time_widget)
        
        time_edit = QTimeEdit()
        time_edit.setDisplayFormat("HH:mm")
        if time_str:
            try:
                h, m = map(int, time_str.split(':'))
                time_edit.setTime(datetime.now().replace(hour=h, minute=m).time())
            except ValueError:
                time_edit.setTime(datetime.now().time())
        else:
            time_edit.setTime(datetime.now().time())
        
        remove_button = QPushButton(self.tr("Remove"))
        remove_button.clicked.connect(lambda: self._remove_time_widget(time_widget))
        
        time_layout.addWidget(time_edit)
        time_layout.addWidget(remove_button)
        
        self.time_widgets.append(time_widget)
        self.time_layout.addWidget(time_widget)
        
    def _remove_time_widget(self, widget: QWidget) -> None:
        """Remove a time widget from the day schedule."""
        if len(self.time_widgets) > 1: 
            self.time_widgets.remove(widget)
            widget.deleteLater()
        elif len(self.time_widgets) == 1:
            self.time_widgets.remove(widget)
            widget.deleteLater()

    def get_data(self) -> Dict[str, Any]:
        """Get the schedule data for this day."""
        times = []
        for widget in self.time_widgets:
            time_edit = widget.findChild(QTimeEdit)
            if time_edit:
                times.append(time_edit.time().toString("HH:mm"))
        return {"enabled": self.day_enabled_checkbox.isChecked(), "times": times}

    def load_data(self, data: Dict[str, Any]) -> None:
        """Load schedule data into this day widget."""
        self.day_enabled_checkbox.setChecked(data.get("enabled", False))
        while self.time_widgets:
            widget = self.time_widgets.pop()
            widget.deleteLater()
        
        for time_str in data.get("times", []):
            self._add_time_widget(time_str)
        if not data.get("times"):
            self._add_time_widget()
            
    def changeEvent(self, event: QEvent) -> None:
        """Handle language change events."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)
    
    def retranslateUi(self):
        """Update UI text elements when language changes."""
        self.day_label.setText(self.tr(self.day_name))
        self.day_enabled_checkbox.setText(self.tr("Enabled"))
        self.add_time_button.setText(self.tr("Add Time"))
        
        # Find any time widgets with remove buttons and update them
        for widget in self.time_widgets:
            remove_button = widget.findChild(QPushButton)
            if remove_button:
                remove_button.setText(self.tr("Remove")) 