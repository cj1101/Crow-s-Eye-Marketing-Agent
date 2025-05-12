"""
Provides the scheduling panel UI component for the main window.
"""
import logging
import uuid
import os
import json
from typing import Dict, Any, Optional, List
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QMenu,
    QFrame, QSizePolicy, QDialog
)
from PySide6.QtGui import QPixmap

from ..config import constants as const
from ..models.app_state import AppState
from .scheduling_dialog import ScheduleDialog

class SchedulingPanel(QWidget):
    """Panel for managing post schedules in the main window."""
    
    schedule_updated = Signal()  # Emitted when schedules are updated
    
    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self._init_ui()
        self._load_schedules()
        
    def _init_ui(self) -> None:
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Schedule Posts")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333333;")
        header_layout.addWidget(title_label)
        
        # Add Schedule button with icon and styling
        add_button = QPushButton("Add Schedule")
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        add_button.setMinimumWidth(120)
        add_button.clicked.connect(self._add_schedule)
        header_layout.addWidget(add_button)
        
        layout.addLayout(header_layout)
        
        # Instruction label
        self.instruction_label = QLabel(
            "Create and manage schedules to automatically post to Instagram and Facebook."
            "\nYou can set up multiple schedules with different posting frequencies and time slots."
        )
        self.instruction_label.setStyleSheet("color: #555555; margin: 10px 0;")
        self.instruction_label.setWordWrap(True)
        layout.addWidget(self.instruction_label)
        
        # Empty state widget (shown when no schedules exist)
        self.empty_state = QWidget()
        empty_layout = QVBoxLayout(self.empty_state)
        
        # Calendar icon or placeholder
        empty_icon = QLabel()
        calendar_icon_path = "icons/calendar.png"
        if os.path.exists(calendar_icon_path):
            empty_icon.setPixmap(QPixmap(calendar_icon_path).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            # Create text-based icon if image doesn't exist
            empty_icon.setText("📅")
            empty_icon.setStyleSheet("font-size: 48px; color: #4CAF50;")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        empty_text = QLabel(
            "No schedules yet!\n"
            "Click 'Add Schedule' to create your first posting schedule."
            "\n\nYou can set up automatic posting on specific days and times,"
            "\nor create a queue to publish your posts in a specific order."
        )
        empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_text.setWordWrap(True)
        empty_text.setStyleSheet("color: #777777; font-size: 14px; margin: 20px;")
        
        empty_button = QPushButton("Create First Schedule")
        empty_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        empty_button.setFixedWidth(200)
        empty_button.clicked.connect(self._add_schedule)
        
        empty_layout.addStretch()
        empty_layout.addWidget(empty_icon)
        empty_layout.addWidget(empty_text)
        empty_layout.addWidget(empty_button, 0, Qt.AlignmentFlag.AlignCenter)
        empty_layout.addStretch()
        
        layout.addWidget(self.empty_state)
        
        # Schedules list
        self.schedules_list = QListWidget()
        self.schedules_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
                padding: 5px;
            }
            QListWidget::item {
                border-bottom: 1px solid #eeeeee;
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #e0f0e0;
                color: #333333;
            }
        """)
        self.schedules_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.schedules_list.customContextMenuRequested.connect(self._show_context_menu)
        self.schedules_list.itemClicked.connect(self._on_schedule_selected)
        layout.addWidget(self.schedules_list)
        
        # Action buttons for the selected schedule
        self.buttons_container = QWidget()
        buttons_layout = QHBoxLayout(self.buttons_container)
        
        # Edit button
        self.edit_button = QPushButton("Edit")
        self.edit_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #BBDEFB;
                color: #FFFFFF;
            }
        """)
        self.edit_button.clicked.connect(self._edit_selected_schedule)
        
        # Delete button
        self.delete_button = QPushButton("Delete")
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
            QPushButton:disabled {
                background-color: #FFCDD2;
                color: #FFFFFF;
            }
        """)
        self.delete_button.clicked.connect(self._delete_selected_schedule)
        
        # Activate/Deactivate button
        self.activate_button = QPushButton("Activate")
        self.activate_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #C8E6C9;
                color: #FFFFFF;
            }
        """)
        self.activate_button.clicked.connect(self._toggle_schedule_activation)
        
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.activate_button)
        
        layout.addWidget(self.buttons_container)
        
        # Initially disable all buttons until a schedule is selected
        self._update_button_states(None)
        
        # Status
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #555555; font-style: italic; margin-top: 5px;")
        layout.addWidget(self.status_label)
        
    def _load_schedules(self) -> None:
        """Load schedules from the app state."""
        try:
            self.schedules_list.clear()
            
            # Get schedules from presets file
            schedules = self._get_schedules()
            
            # Show/hide empty state
            self.empty_state.setVisible(not schedules)
            self.schedules_list.setVisible(bool(schedules))
            
            if not schedules:
                self.status_label.setText("Ready to create your first schedule.")
                return
                
            # Add schedules to list
            for schedule in schedules:
                self._add_schedule_to_list(schedule)
                
            self.status_label.setText(f"Loaded {len(schedules)} schedule(s)")
            
        except Exception as e:
            self.logger.exception(f"Error loading schedules: {e}")
            self.status_label.setText("Error loading schedules")
            QMessageBox.warning(
                self,
                "Load Error",
                f"Failed to load schedules: {str(e)}"
            )
            
    def _get_schedules(self) -> List[Dict[str, Any]]:
        """Get all schedules from the presets file."""
        try:
            if not os.path.exists(const.PRESETS_FILE):
                return []
                
            with open(const.PRESETS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('schedules', [])
                
        except Exception as e:
            self.logger.exception(f"Error getting schedules: {e}")
            return []
            
    def _save_schedules(self, schedules: List[Dict[str, Any]]) -> None:
        """Save schedules to the presets file."""
        try:
            # Load existing data
            data = {}
            if os.path.exists(const.PRESETS_FILE):
                with open(const.PRESETS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
            # Update schedules
            data['schedules'] = schedules
            
            # Save to file
            with open(const.PRESETS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
                
        except Exception as e:
            self.logger.exception(f"Error saving schedules: {e}")
            raise
            
    def _add_schedule_to_list(self, schedule: Dict[str, Any]) -> None:
        """Add a schedule to the list widget."""
        try:
            # Create list item
            item = QListWidgetItem()
            
            # Format schedule info
            name = schedule.get("name", "Unnamed Schedule")
            mode = schedule.get("mode", "basic").title()
            posts_per_day = schedule.get("posts_per_day", 3)
            is_active = schedule.get("active", False)
            
            start_date = schedule.get("start_date", "")
            end_date = schedule.get("end_date", "")
            
            # Set item text - add an indicator for active schedule
            status_icon = "✓ " if is_active else ""
            item.setText(f"{status_icon}{name} ({mode})")
            
            # Add styling for active schedule
            if is_active:
                item.setBackground(Qt.GlobalColor.lightGray)
                item.setForeground(Qt.GlobalColor.darkGreen)
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            
            item.setToolTip(
                f"Status: {'Active' if is_active else 'Inactive'}\n"
                f"Posts per day: {posts_per_day}\n"
                f"Start date: {start_date}\n"
                f"End date: {end_date}"
            )
            
            # Store schedule data
            item.setData(Qt.ItemDataRole.UserRole, schedule)
            
            # Add to list
            self.schedules_list.addItem(item)
            
        except Exception as e:
            self.logger.exception(f"Error adding schedule to list: {e}")
            
    def _add_schedule(self) -> None:
        """Add a new schedule."""
        try:
            # Create new schedule dialog
            dialog = ScheduleDialog(self)
            
            # Connect signals
            dialog.schedule_saved.connect(lambda data: self.logger.info(f"Schedule saved signal received: {data.get('name', 'Unknown')}"))
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Get schedule data
                schedule_data = dialog.schedule_data
                
                # Log the schedule data
                self.logger.info(f"Schedule data after dialog: {schedule_data.get('name', 'Unknown')}")
                
                # Generate ID if new schedule
                if not schedule_data.get("id"):
                    schedule_data["id"] = str(uuid.uuid4())
                    
                # Get current schedules
                schedules = self._get_schedules()
                
                # Determine if this should be active (first schedule or edit of an active schedule)
                is_first_schedule = len(schedules) == 0
                is_active_edit = False
                
                # Check if this is editing an existing active schedule
                schedule_id = schedule_data["id"]
                for schedule in schedules:
                    if schedule.get("id") == schedule_id:
                        is_active_edit = schedule.get("active", False)
                        break
                        
                # Set active status based on conditions
                if is_first_schedule:
                    # First schedule is automatically active
                    schedule_data["active"] = True
                elif is_active_edit:
                    # Keep active status if editing an active schedule
                    schedule_data["active"] = True
                else:
                    # New schedules start inactive unless specified otherwise
                    schedule_data["active"] = schedule_data.get("active", False)
                
                # If this schedule is being activated, deactivate all others
                if schedule_data.get("active", False):
                    for schedule in schedules:
                        if schedule.get("id") != schedule_id:
                            schedule["active"] = False
                
                # Add or update schedule
                for i, schedule in enumerate(schedules):
                    if schedule.get("id") == schedule_id:
                        schedules[i] = schedule_data
                        break
                else:
                    schedules.append(schedule_data)
                    
                # Save schedules
                self._save_schedules(schedules)
                
                # Reload list
                self._load_schedules()
                
                # Emit signal
                self.schedule_updated.emit()
                
                # Update status message
                if schedule_data.get("active", False):
                    self.status_label.setText(f"Schedule '{schedule_data.get('name')}' is now active.")
                else:
                    self.status_label.setText(f"Schedule '{schedule_data.get('name')}' was added (inactive).")
                
        except Exception as e:
            self.logger.exception(f"Error adding schedule: {e}")
            QMessageBox.critical(
                self,
                "Add Error",
                f"Failed to add schedule: {str(e)}"
            )
            
    def _edit_schedule(self, item: QListWidgetItem) -> None:
        """Edit an existing schedule."""
        try:
            # Get schedule data
            schedule_data = item.data(Qt.ItemDataRole.UserRole)
            if not schedule_data:
                return
                
            # Create edit dialog
            dialog = ScheduleDialog(self, schedule_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Get updated schedule data
                updated_data = dialog.schedule_data
                
                # Get current schedules
                schedules = self._get_schedules()
                
                # Update schedule
                schedule_id = updated_data["id"]
                for i, schedule in enumerate(schedules):
                    if schedule.get("id") == schedule_id:
                        schedules[i] = updated_data
                        break
                        
                # Save schedules
                self._save_schedules(schedules)
                
                # Reload list
                self._load_schedules()
                
                # Emit signal
                self.schedule_updated.emit()
                
        except Exception as e:
            self.logger.exception(f"Error editing schedule: {e}")
            QMessageBox.critical(
                self,
                "Edit Error",
                f"Failed to edit schedule: {str(e)}"
            )
            
    def _delete_schedule(self, item: QListWidgetItem) -> None:
        """Delete a schedule."""
        try:
            # Get schedule data
            schedule_data = item.data(Qt.ItemDataRole.UserRole)
            if not schedule_data:
                return
                
            # Confirm deletion
            name = schedule_data.get("name", "Unnamed Schedule")
            reply = QMessageBox.question(
                self,
                "Delete Schedule",
                f"Are you sure you want to delete the schedule '{name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Get current schedules
                schedules = self._get_schedules()
                
                # Remove schedule
                schedule_id = schedule_data["id"]
                schedules = [s for s in schedules if s.get("id") != schedule_id]
                
                # Save schedules
                self._save_schedules(schedules)
                
                # Reload list
                self._load_schedules()
                
                # Emit signal
                self.schedule_updated.emit()
                
        except Exception as e:
            self.logger.exception(f"Error deleting schedule: {e}")
            QMessageBox.critical(
                self,
                "Delete Error",
                f"Failed to delete schedule: {str(e)}"
            )
            
    def _show_context_menu(self, pos) -> None:
        """Show the context menu for a schedule item."""
        try:
            # Get item at position
            item = self.schedules_list.itemAt(pos)
            if not item:
                return
                
            # Create menu
            menu = QMenu(self)
            
            edit_action = menu.addAction("Edit Schedule")
            delete_action = menu.addAction("Delete Schedule")
            
            # Show menu
            action = menu.exec(self.schedules_list.mapToGlobal(pos))
            
            if action == edit_action:
                self._edit_schedule(item)
            elif action == delete_action:
                self._delete_schedule(item)
                
        except Exception as e:
            self.logger.exception(f"Error showing context menu: {e}")
            
    def update_status(self, status_text: str) -> None:
        """Update the status label with the given text."""
        self.status_label.setText(status_text)
        
    def _update_button_states(self, selected_item=None):
        """Update the enabled state of buttons based on the selected schedule."""
        has_selection = selected_item is not None
        
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        
        if has_selection:
            # Get the schedule data
            schedule_data = selected_item.data(Qt.ItemDataRole.UserRole)
            is_active = schedule_data.get("active", False)
            
            # Update the activate button text based on current state
            if is_active:
                self.activate_button.setText("Deactivate")
                self.activate_button.setStyleSheet("""
                    QPushButton {
                        background-color: #FF9800;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        font-weight: bold;
                        border-radius: 4px;
                        min-width: 100px;
                    }
                    QPushButton:hover {
                        background-color: #F57C00;
                    }
                """)
            else:
                self.activate_button.setText("Activate")
                self.activate_button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        font-weight: bold;
                        border-radius: 4px;
                        min-width: 100px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
            
            self.activate_button.setEnabled(True)
        else:
            self.activate_button.setText("Activate")
            self.activate_button.setEnabled(False)
            
        # Show/hide the buttons container
        self.buttons_container.setVisible(has_selection)
        
    def _on_schedule_selected(self, item):
        """Handle selection of a schedule item."""
        self._update_button_states(item)
        
    def _edit_selected_schedule(self):
        """Edit the currently selected schedule."""
        item = self.schedules_list.currentItem()
        if item:
            self._edit_schedule(item)
            
    def _delete_selected_schedule(self):
        """Delete the currently selected schedule."""
        item = self.schedules_list.currentItem()
        if item:
            self._delete_schedule(item)
            
    def _toggle_schedule_activation(self):
        """Toggle the active state of the selected schedule."""
        item = self.schedules_list.currentItem()
        if not item:
            return
            
        # Get all schedules and the selected schedule
        schedules = self._get_schedules()
        selected_data = item.data(Qt.ItemDataRole.UserRole)
        selected_id = selected_data.get("id")
        
        # If the schedule is already active, deactivate it
        if selected_data.get("active", False):
            # Update the selected schedule
            for schedule in schedules:
                if schedule.get("id") == selected_id:
                    schedule["active"] = False
                    break
                    
            self.status_label.setText(f"Schedule '{selected_data.get('name')}' has been deactivated.")
        else:
            # Deactivate all schedules first
            for schedule in schedules:
                schedule["active"] = (schedule.get("id") == selected_id)
                
            self.status_label.setText(f"Schedule '{selected_data.get('name')}' is now active.")
            
        # Save the updated schedules
        self._save_schedules(schedules)
        
        # Reload the schedules list
        self._load_schedules() 