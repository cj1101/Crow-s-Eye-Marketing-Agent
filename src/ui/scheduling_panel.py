"""
Provides the scheduling panel UI component for the main window.
"""
import logging
import uuid
import os
import json
from typing import Dict, Any, Optional, List
from PySide6.QtCore import Qt, Signal, QObject, QEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QMenu,
    QFrame, QSizePolicy, QDialog, QApplication
)
from PySide6.QtGui import QPixmap

from ..config import constants as const
from ..models.app_state import AppState
from .dialogs.scheduling_dialog import ScheduleDialog

class SchedulingPanel(QWidget):
    """Panel for managing post schedules in the main window."""
    
    schedule_updated = Signal()  # Emitted when a schedule is updated/added/deleted
    
    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize key UI elements so they're available for retranslation
        self.title_label = QLabel()
        self.instruction_label = QLabel()
        self.schedules_list = QListWidget()
        self.empty_container = QWidget()
        self.empty_icon = QLabel()
        self.empty_text = QLabel()
        self.empty_button = QPushButton()
        self.add_button = QPushButton()
        self.buttons_container = QWidget()
        self.edit_button = QPushButton()
        self.delete_button = QPushButton()
        self.activate_button = QPushButton()
        self.view_posts_button = QPushButton()
        self.status_label = QLabel()
        
        self._init_ui()
        self._connect_signals()
        self._load_schedules()
        
        # Check for application translator and current language
        app = QApplication.instance()
        if app:
            # Get the current language from application property
            current_language = app.property("current_language")
            if current_language:
                self.logger.info(f"SchedulingPanel created with current language: {current_language}")
                
            # Apply translations to this panel
            self.retranslateUi()
        
    def _init_ui(self) -> None:
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333333;")
        layout.addWidget(self.title_label)
        
        header_layout = QHBoxLayout()
        self.add_button.setStyleSheet("""
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
        self.add_button.setMinimumWidth(120)
        self.add_button.clicked.connect(self._add_schedule)
        header_layout.addStretch()
        header_layout.addWidget(self.add_button)
        layout.addLayout(header_layout)
        
        self.instruction_label.setStyleSheet("color: #555555; margin: 10px 0;")
        self.instruction_label.setWordWrap(True)
        layout.addWidget(self.instruction_label)
        
        empty_layout = QVBoxLayout(self.empty_container)
        
        calendar_icon_path = "icons/calendar.png"
        if os.path.exists(calendar_icon_path):
            self.empty_icon.setPixmap(QPixmap(calendar_icon_path).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.empty_icon.setText("📅")
            self.empty_icon.setStyleSheet("font-size: 48px; color: #4CAF50;")
        self.empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(self.empty_icon)
        
        self.empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_text.setWordWrap(True)
        self.empty_text.setStyleSheet("color: #777777; font-size: 14px; margin: 20px;")
        empty_layout.addWidget(self.empty_text)
        
        self.empty_button.setStyleSheet("""
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
        self.empty_button.setFixedWidth(200)
        self.empty_button.clicked.connect(self._add_schedule)
        empty_layout.addStretch()
        empty_layout.addWidget(self.empty_button, 0, Qt.AlignmentFlag.AlignCenter)
        empty_layout.addStretch()
        layout.addWidget(self.empty_container)
        
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
        
        buttons_layout = QHBoxLayout(self.buttons_container)
        
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
        
        self.view_posts_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.view_posts_button.clicked.connect(self._view_scheduled_posts)
        
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.activate_button)
        buttons_layout.addWidget(self.view_posts_button)
        
        layout.addWidget(self.buttons_container)
        
        self._update_button_states()
        
        # Status
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #555555; font-style: italic; margin-top: 5px;")
        layout.addWidget(self.status_label)
        
    def _connect_signals(self):
        """Connect UI signals to slots."""
        # Connect buttons
        self.add_button.clicked.connect(self._on_add_schedule)
        self.edit_button.clicked.connect(self._on_edit_schedule)
        self.delete_button.clicked.connect(self._on_delete_schedule)
        self.view_posts_button.clicked.connect(self._on_view_posts)
        self.empty_button.clicked.connect(self._on_add_schedule)
        
        # Connect list widget
        self.schedules_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.schedules_list.itemDoubleClicked.connect(self._on_edit_schedule)
        
    def _load_schedules(self) -> None:
        """Load schedules from the app state."""
        try:
            self.schedules_list.clear()
            
            # Get schedules from presets file
            schedules = self._get_schedules()
            
            # Show/hide empty state
            self.empty_container.setVisible(not schedules)
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
            dialog = ScheduleDialog(self)
            dialog.schedule_saved.connect(lambda data: self.logger.info(f"Schedule saved signal received: {data.get('name', 'Unknown')}"))
            
            # Remove the event posting, call retranslateUi directly
            # QApplication.instance().postEvent(dialog, QEvent(QEvent.Type.LanguageChange))
            dialog.retranslateUi() # Directly translate the dialog UI
            
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
                self.tr("Add Error"),
                self.tr("Failed to add schedule: {error_message}").format(error_message=str(e))
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
            
            # Remove the event posting, call retranslateUi directly
            # QApplication.instance().postEvent(dialog, QEvent(QEvent.Type.LanguageChange))
            dialog.retranslateUi() # Directly translate the dialog UI
            
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
                self.tr("Edit Error"),
                self.tr("Failed to edit schedule: {error_message}").format(error_message=str(e))
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
                self.tr("Delete Schedule"),
                self.tr("Are you sure you want to delete the schedule '{schedule_name}'?").format(schedule_name=name),
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
                self.tr("Delete Error"),
                self.tr("Failed to delete schedule: {error_message}").format(error_message=str(e))
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
            
            edit_action = menu.addAction(self.tr("Edit Schedule"))
            delete_action = menu.addAction(self.tr("Delete Schedule"))
            
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
        self.view_posts_button.setEnabled(has_selection)
        
        if has_selection:
            # Get the schedule data
            schedule_data = selected_item.data(Qt.ItemDataRole.UserRole)
            is_active = schedule_data.get("active", False)
            
            # Update the activate button text based on current state
            if is_active:
                self.activate_button.setText(self.tr("Deactivate"))
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
                self.activate_button.setText(self.tr("Activate"))
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
            self.activate_button.setText(self.tr("Activate"))
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

    def _load_schedules_from_file(self) -> List[Dict[str, Any]]:
        """Load schedules from the JSON file."""
        # Ensure this method exists or is correctly named
        if not os.path.exists(const.SCHEDULES_FILE):
            return []
        try:
            with open(const.SCHEDULES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            self.logger.error(f"Error loading schedules: {e}")
            return []

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        """Retranslate all UI elements in SchedulingPanel."""
        self.title_label.setText(self.tr("Manage Posting Schedules"))
        self.instruction_label.setText(self.tr(
            "Create and manage schedules to automatically post to Instagram and Facebook."
            "\nYou can set up multiple schedules with different posting frequencies and time slots."
        ))
        self.empty_text.setText(self.tr(
            "No schedules yet!\n"
            "Click 'Add Schedule' to create your first posting schedule."
            "\n\nYou can set up automatic posting on specific days and times,"
            "\nor create a queue to publish your posts in a specific order."
        ))
        self.empty_button.setText(self.tr("Create First Schedule"))
        self.add_button.setText(self.tr("Add Schedule"))
        
        # Buttons in self.buttons_container
        self.edit_button.setText(self.tr("Edit"))
        self.delete_button.setText(self.tr("Delete"))
        self.view_posts_button.setText(self.tr("View Scheduled Posts"))

        # Reload schedules to update list items if their text construction involves self.tr()
        self._load_schedules() 
        # Ensure dependent methods like _update_button_states are called if needed after retranslation
        self._update_button_states(self.schedules_list.currentItem())

    def _update_list_item_text(self, item: QListWidgetItem, schedule_data: Dict[str, Any]) -> None:
        """Update the display text of a list item."""
        name = schedule_data.get("name", self.tr("Unnamed Schedule"))
        mode = schedule_data.get("mode", "N/A") # Mode itself might need translation if keys are like "basic", "advanced"
        mode_display = self.tr(mode.capitalize()) if mode else self.tr("N/A") # Translate the mode for display
        status = self.tr("Active") if schedule_data.get("active") else self.tr("Inactive")
        item_text = f"{name} ({mode_display}) - {status}"
        item.setText(item_text)
        item.setData(Qt.ItemDataRole.UserRole, schedule_data)

    def _view_scheduled_posts(self) -> None:
        """Show a dialog with posts generated for the active schedule (placeholder)."""
        active_schedule = None
        schedules = self._get_schedules()
        for schedule in schedules:
            if schedule.get("active"):
                active_schedule = schedule
                break
        
        if active_schedule:
            QMessageBox.information(
                self, 
                self.tr("View Posts"), 
                self.tr("Showing posts for schedule: {schedule_name}\n(This is a placeholder feature.)").format(schedule_name=active_schedule.get("name", self.tr("Unnamed Schedule")))
            )
        else:
            QMessageBox.warning(self, self.tr("View Posts"), self.tr("No active schedule selected to view posts."))

    def _on_add_schedule(self):
        """Handle add schedule button click."""
        try:
            from .scheduling_dialog import ScheduleDialog
            dialog = ScheduleDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.schedule_data:
                self._add_schedule(dialog.schedule_data)
        except Exception as e:
            self.logger.exception(f"Failed to add schedule: {e}")
            QMessageBox.critical(self, self.tr("Add Error"), self.tr(f"Failed to add schedule: {e}"))

    def _on_edit_schedule(self):
        """Handle edit schedule button click."""
        try:
            selected_items = self.schedules_list.selectedItems()
            if not selected_items:
                return
                
            selected_item = selected_items[0]
            schedule_id = selected_item.data(Qt.ItemDataRole.UserRole)
            if not schedule_id:
                return
                
            schedule_data = self.app_state.get_schedule(schedule_id)
            if schedule_data:
                from .scheduling_dialog import ScheduleDialog
                dialog = ScheduleDialog(self, schedule_data)
                if dialog.exec() == QDialog.DialogCode.Accepted and dialog.schedule_data:
                    self._update_schedule(schedule_id, dialog.schedule_data)
        except Exception as e:
            self.logger.exception(f"Failed to edit schedule: {e}")
            QMessageBox.critical(self, self.tr("Edit Error"), self.tr(f"Failed to edit schedule: {e}"))

    def _on_delete_schedule(self):
        """Handle delete schedule button click."""
        try:
            selected_items = self.schedules_list.selectedItems()
            if not selected_items:
                return
                
            selected_item = selected_items[0]
            schedule_id = selected_item.data(Qt.ItemDataRole.UserRole)
            schedule_name = selected_item.text().strip()
            
            # Confirm deletion
            confirm = QMessageBox.question(
                self,
                self.tr("Delete Schedule"),
                self.tr(f"Are you sure you want to delete the schedule '{schedule_name}'?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if confirm == QMessageBox.StandardButton.Yes:
                self._delete_schedule(schedule_id)
        except Exception as e:
            self.logger.exception(f"Failed to delete schedule: {e}")
            QMessageBox.critical(self, self.tr("Delete Error"), self.tr(f"Failed to delete schedule: {e}"))
    
    def _on_view_posts(self):
        """Handle view posts button click."""
        try:
            selected_items = self.schedules_list.selectedItems()
            if not selected_items:
                return
                
            selected_item = selected_items[0]
            schedule_id = selected_item.data(Qt.ItemDataRole.UserRole)
            schedule_name = selected_item.text().strip()
            
            # This is just a placeholder for now
            QMessageBox.information(
                self,
                self.tr("View Posts"),
                self.tr(f"Showing posts for schedule: {schedule_name}\n(This is a placeholder feature.)")
            )
        except Exception as e:
            self.logger.exception(f"Failed to view posts: {e}")
            
    def _on_selection_changed(self):
        """Handle selection change in the schedules list."""
        selected_items = self.schedules_list.selectedItems()
        enable_buttons = len(selected_items) > 0
        
        self.edit_button.setEnabled(enable_buttons)
        self.delete_button.setEnabled(enable_buttons)
        self.view_posts_button.setEnabled(enable_buttons) 