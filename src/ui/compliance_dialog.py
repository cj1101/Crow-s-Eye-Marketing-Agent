"""
Compliance dialog for Meta Developer Platform requirements.
Provides user interface for data deletion, export, privacy settings, and factory reset.
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QTabWidget, QWidget, QScrollArea, QMessageBox, QProgressBar,
    QGroupBox, QCheckBox, QFormLayout, QLineEdit, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)
from PySide6.QtCore import Qt, Signal, QThread, QEvent
from PySide6.QtGui import QFont, QPixmap, QIcon

from .base_dialog import BaseDialog
from .components.adjustable_button import AdjustableButton
from ..handlers.compliance_handler import compliance_handler

class ComplianceWorker(QThread):
    """Worker thread for compliance operations."""
    
    progress_updated = Signal(str)
    operation_completed = Signal(bool, str)
    
    def __init__(self, operation: str, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def run(self):
        """Run the compliance operation."""
        try:
            if self.operation == "factory_reset":
                self.progress_updated.emit("Starting factory reset...")
                success = compliance_handler.factory_reset()
                self.operation_completed.emit(success, "Factory reset completed successfully" if success else "Factory reset failed")
            
            elif self.operation == "export_data":
                self.progress_updated.emit("Collecting user data...")
                export_path = compliance_handler.export_user_data()
                self.operation_completed.emit(True, f"Data exported to: {export_path}")
            
            else:
                self.operation_completed.emit(False, f"Unknown operation: {self.operation}")
                
        except Exception as e:
            self.logger.error(f"Error in compliance worker: {e}")
            self.operation_completed.emit(False, f"Operation failed: {str(e)}")

class ComplianceDialog(BaseDialog):
    """Dialog for Meta compliance features."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.worker = None
        
        self.setWindowTitle("Privacy & Data Compliance")
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        self._setup_ui()
        self._load_compliance_data()
        self.retranslateUi()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Privacy & Data Compliance")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(header_label)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_overview_tab()
        self._create_data_export_tab()
        self._create_privacy_settings_tab()
        self._create_deletion_requests_tab()
        self._create_factory_reset_tab()
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #666; margin: 5px;")
        layout.addWidget(self.status_label)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_btn = AdjustableButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_overview_tab(self):
        """Create the overview tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Meta compliance info
        info_group = QGroupBox("Meta Developer Platform Compliance")
        info_layout = QVBoxLayout(info_group)
        
        compliance_text = """
        <b>Your app complies with Meta Developer Platform requirements:</b><br><br>
        ✅ <b>Data Deletion Requests:</b> Automatic handling of user data deletion requests from Meta<br>
        ✅ <b>Privacy Policy:</b> Publicly accessible privacy policy with clear data usage descriptions<br>
        ✅ <b>User Data Export:</b> GDPR/CCPA compliant data export functionality<br>
        ✅ <b>Factory Reset:</b> Complete data deletion capability as required by Meta<br>
        ✅ <b>Data Security:</b> Industry-standard security measures for platform data<br>
        ✅ <b>Incident Reporting:</b> Automated security incident detection and reporting<br><br>
        <b>Data Retention Policy:</b><br>
        • Media files: Until manually deleted by user<br>
        • Scheduled posts: Until completed or cancelled<br>
        • Analytics cache: 24 hours maximum<br>
        • Knowledge base: Until manually deleted by user<br><br>
        <b>Third-Party Data Sharing:</b> None. All Meta platform data is used only for app functionality.
        """
        
        compliance_info = QLabel(compliance_text)
        compliance_info.setWordWrap(True)
        compliance_info.setStyleSheet("padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
        info_layout.addWidget(compliance_info)
        
        layout.addWidget(info_group)
        
        # Compliance status
        status_group = QGroupBox("Current Compliance Status")
        status_layout = QVBoxLayout(status_group)
        
        self.compliance_status_text = QTextEdit()
        self.compliance_status_text.setReadOnly(True)
        self.compliance_status_text.setMaximumHeight(150)
        status_layout.addWidget(self.compliance_status_text)
        
        refresh_btn = AdjustableButton("Refresh Status")
        refresh_btn.clicked.connect(self._refresh_compliance_status)
        status_layout.addWidget(refresh_btn)
        
        layout.addWidget(status_group)
        
        # Privacy policy link
        policy_group = QGroupBox("Privacy Policy")
        policy_layout = QVBoxLayout(policy_group)
        
        policy_info = QLabel("""
        Our full privacy policy is available at:<br>
        <a href="https://www.breadsmithbakery.com/privacy-policy">https://www.breadsmithbakery.com/privacy-policy</a><br><br>
        
        For questions about data usage or to report privacy concerns, contact:<br>
        Email: privacy@breadsmithbakery.com<br>
        Phone: (555) 123-4567
        """)
        policy_info.setOpenExternalLinks(True)
        policy_info.setWordWrap(True)
        policy_layout.addWidget(policy_info)
        
        layout.addWidget(policy_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Overview")
    
    def _create_data_export_tab(self):
        """Create the data export tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Export info
        info_label = QLabel("""
        <b>Export Your Data</b><br><br>
        
        You have the right to request a copy of all personal data we have about you. 
        This export includes all media files, settings, presets, and other data stored in the application.
        The export file will be in JSON format and can be used for data portability purposes.
        """)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("padding: 10px; background-color: #e8f4fd; border-radius: 5px; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # Export options
        export_group = QGroupBox("Export Options")
        export_layout = QVBoxLayout(export_group)
        
        # Full export button
        export_btn = AdjustableButton("Export All My Data")
        export_btn.setStyleSheet("background-color: #0084ff; color: white; padding: 10px; font-weight: bold;")
        export_btn.clicked.connect(self._export_user_data)
        export_layout.addWidget(export_btn)
        
        export_info = QLabel("This will create a comprehensive export of all your data including media files, settings, and preferences.")
        export_info.setWordWrap(True)
        export_info.setStyleSheet("color: #666; font-size: 12px; margin-top: 5px;")
        export_layout.addWidget(export_info)
        
        layout.addWidget(export_group)
        
        # Export history
        history_group = QGroupBox("Export History")
        history_layout = QVBoxLayout(history_group)
        
        self.export_history_table = QTableWidget()
        self.export_history_table.setColumnCount(3)
        self.export_history_table.setHorizontalHeaderLabels(["Date", "File", "Status"])
        self.export_history_table.horizontalHeader().setStretchLastSection(True)
        history_layout.addWidget(self.export_history_table)
        
        layout.addWidget(history_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Data Export")
    
    def _create_privacy_settings_tab(self):
        """Create the privacy settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Current settings
        settings_group = QGroupBox("Privacy Settings")
        settings_layout = QFormLayout(settings_group)
        
        # Data retention settings
        retention_label = QLabel("Data Retention")
        retention_label.setStyleSheet("font-weight: bold;")
        settings_layout.addRow(retention_label)
        
        self.media_retention = QCheckBox("Keep media files until manually deleted")
        self.media_retention.setChecked(True)
        self.media_retention.setEnabled(False)  # Read-only for now
        settings_layout.addRow("Media Files:", self.media_retention)
        
        self.analytics_retention = QCheckBox("Cache analytics for 24 hours")
        self.analytics_retention.setChecked(True)
        self.analytics_retention.setEnabled(False)  # Read-only for now
        settings_layout.addRow("Analytics:", self.analytics_retention)
        
        # Data sharing settings
        sharing_label = QLabel("Data Sharing")
        sharing_label.setStyleSheet("font-weight: bold; margin-top: 15px;")
        settings_layout.addRow(sharing_label)
        
        self.third_party_sharing = QCheckBox("Allow third-party data sharing")
        self.third_party_sharing.setChecked(False)
        self.third_party_sharing.setEnabled(False)  # Always disabled
        settings_layout.addRow("Third Parties:", self.third_party_sharing)
        
        self.analytics_sharing = QCheckBox("Share analytics with third parties")
        self.analytics_sharing.setChecked(False)
        self.analytics_sharing.setEnabled(False)  # Always disabled
        settings_layout.addRow("Analytics Sharing:", self.analytics_sharing)
        
        layout.addWidget(settings_group)
        
        # User rights
        rights_group = QGroupBox("Your Rights")
        rights_layout = QVBoxLayout(rights_group)
        
        rights_info = QLabel("""
        <b>Under GDPR, CCPA, and other privacy laws, you have the following rights:</b><br><br>
        
        <b>Right to Access:</b> Request a copy of your personal data (Data Export tab)<br>
        <b>Right to Rectification:</b> Request correction of inaccurate data<br>
        <b>Right to Erasure:</b> Request deletion of your personal data (Factory Reset tab)<br>
        <b>Right to Portability:</b> Receive your data in a machine-readable format<br>
        <b>Right to Withdraw Consent:</b> Withdraw consent for data processing at any time<br>
        <b>Right to Object:</b> Object to certain types of data processing<br><br>
        
        To exercise any of these rights, contact us at privacy@breadsmithbakery.com
        """)
        rights_info.setWordWrap(True)
        rights_layout.addWidget(rights_info)
        
        layout.addWidget(rights_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Privacy Settings")
    
    def _create_deletion_requests_tab(self):
        """Create the deletion requests tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Info
        info_label = QLabel("""
        <b>Data Deletion Requests</b><br><br>
        
        This tab shows data deletion requests received from Meta when users remove your app
        or request their data to be deleted. These requests are handled automatically.
        """)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("padding: 10px; background-color: #fff3cd; border-radius: 5px; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # Deletion requests table
        requests_group = QGroupBox("Recent Deletion Requests")
        requests_layout = QVBoxLayout(requests_group)
        
        self.deletion_requests_table = QTableWidget()
        self.deletion_requests_table.setColumnCount(4)
        self.deletion_requests_table.setHorizontalHeaderLabels(["Date", "User ID", "Status", "Confirmation Code"])
        self.deletion_requests_table.horizontalHeader().setStretchLastSection(True)
        requests_layout.addWidget(self.deletion_requests_table)
        
        refresh_requests_btn = AdjustableButton("Refresh Deletion Requests")
        refresh_requests_btn.clicked.connect(self._refresh_deletion_requests)
        requests_layout.addWidget(refresh_requests_btn)
        
        layout.addWidget(requests_group)
        
        # Manual deletion (for testing)
        manual_group = QGroupBox("Manual Data Deletion (Testing)")
        manual_layout = QVBoxLayout(manual_group)
        
        manual_info = QLabel("For testing purposes, you can simulate a data deletion request:")
        manual_layout.addWidget(manual_info)
        
        manual_btn = AdjustableButton("Simulate Deletion Request")
        manual_btn.clicked.connect(self._simulate_deletion_request)
        manual_layout.addWidget(manual_btn)
        
        layout.addWidget(manual_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Deletion Requests")
    
    def _create_factory_reset_tab(self):
        """Create the factory reset tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Warning
        warning_label = QLabel("⚠️ FACTORY RESET - PERMANENT DATA DELETION ⚠️")
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        warning_label.setStyleSheet("background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(warning_label)
        
        # Factory reset info
        info_group = QGroupBox("What is Factory Reset?")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel("""
        <b>Factory Reset completely removes ALL user data from the application.</b><br><br>
        
        This feature is required by Meta Developer Platform Terms to provide users with
        a way to completely delete all their data from your app.<br><br>
        
        <b>What will be deleted:</b><br>
        • All media files and galleries<br>
        • All scheduled posts<br>
        • All presets and settings<br>
        • All knowledge base files<br>
        • All cached data and analytics<br>
        • All Meta API credentials<br>
        • All configuration files<br><br>
        
        <b>⚠️ THIS ACTION CANNOT BE UNDONE!</b><br>
        Make sure to export your data first if you want to keep any of it.
        """)
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Factory reset button
        reset_group = QGroupBox("Perform Factory Reset")
        reset_layout = QVBoxLayout(reset_group)
        
        # Confirmation checkbox
        self.confirm_reset_checkbox = QCheckBox("I understand this will permanently delete ALL my data")
        reset_layout.addWidget(self.confirm_reset_checkbox)
        
        # Reset button
        self.factory_reset_btn = AdjustableButton("🗑️ FACTORY RESET - DELETE ALL DATA")
        self.factory_reset_btn.setStyleSheet("background-color: #dc3545; color: white; padding: 15px; font-weight: bold; font-size: 14px;")
        self.factory_reset_btn.setEnabled(False)
        self.factory_reset_btn.clicked.connect(self._factory_reset)
        reset_layout.addWidget(self.factory_reset_btn)
        
        # Enable/disable reset button based on checkbox
        self.confirm_reset_checkbox.toggled.connect(self.factory_reset_btn.setEnabled)
        
        layout.addWidget(reset_group)
        
        # Reset history
        history_group = QGroupBox("Factory Reset History")
        history_layout = QVBoxLayout(history_group)
        
        self.reset_history_table = QTableWidget()
        self.reset_history_table.setColumnCount(3)
        self.reset_history_table.setHorizontalHeaderLabels(["Date", "Reason", "Status"])
        self.reset_history_table.horizontalHeader().setStretchLastSection(True)
        history_layout.addWidget(self.reset_history_table)
        
        layout.addWidget(history_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Factory Reset")
    
    def _load_compliance_data(self):
        """Load and display compliance data."""
        self._refresh_compliance_status()
        self._refresh_deletion_requests()
        self._refresh_export_history()
        self._refresh_reset_history()
    
    def _refresh_compliance_status(self):
        """Refresh the compliance status display."""
        try:
            status = compliance_handler.get_compliance_status()
            
            status_text = f"""
Last Updated: {status.get('last_updated', 'Never')}

Data Deletion Requests: {status.get('deletion_requests_count', 0)}
Data Export Requests: {status.get('export_requests_count', 0)}
Factory Resets: {status.get('factory_resets_count', 0)}
Privacy Settings Changes: {status.get('privacy_changes_count', 0)}

Meta Compliance Features:
• Data Deletion Callback: {'✅ Enabled' if status.get('meta_compliance', {}).get('data_deletion_callback') else '❌ Disabled'}
• Privacy Policy: {'✅ Available' if status.get('meta_compliance', {}).get('privacy_policy') else '❌ Missing'}
• User Data Export: {'✅ Available' if status.get('meta_compliance', {}).get('user_data_export') else '❌ Missing'}
• Factory Reset: {'✅ Available' if status.get('meta_compliance', {}).get('factory_reset') else '❌ Missing'}
• Incident Reporting: {'✅ Enabled' if status.get('meta_compliance', {}).get('incident_reporting') else '❌ Disabled'}
            """
            
            self.compliance_status_text.setPlainText(status_text.strip())
            
        except Exception as e:
            self.logger.error(f"Error refreshing compliance status: {e}")
            self.compliance_status_text.setPlainText(f"Error loading status: {e}")
    
    def _refresh_deletion_requests(self):
        """Refresh the deletion requests table."""
        try:
            log_data = compliance_handler._load_compliance_log()
            requests = log_data.get("deletion_requests", [])
            
            self.deletion_requests_table.setRowCount(len(requests))
            
            for row, request in enumerate(requests):
                self.deletion_requests_table.setItem(row, 0, QTableWidgetItem(request.get("timestamp", "")[:10]))
                self.deletion_requests_table.setItem(row, 1, QTableWidgetItem(request.get("user_id", "")))
                self.deletion_requests_table.setItem(row, 2, QTableWidgetItem(request.get("status", "")))
                self.deletion_requests_table.setItem(row, 3, QTableWidgetItem(request.get("confirmation_code", "")))
                
        except Exception as e:
            self.logger.error(f"Error refreshing deletion requests: {e}")
    
    def _refresh_export_history(self):
        """Refresh the export history table."""
        try:
            log_data = compliance_handler._load_compliance_log()
            exports = log_data.get("export_requests", [])
            
            self.export_history_table.setRowCount(len(exports))
            
            for row, export in enumerate(exports):
                self.export_history_table.setItem(row, 0, QTableWidgetItem(export.get("timestamp", "")[:10]))
                self.export_history_table.setItem(row, 1, QTableWidgetItem(export.get("export_file", "")))
                self.export_history_table.setItem(row, 2, QTableWidgetItem(export.get("status", "")))
                
        except Exception as e:
            self.logger.error(f"Error refreshing export history: {e}")
    
    def _refresh_reset_history(self):
        """Refresh the factory reset history table."""
        try:
            log_data = compliance_handler._load_compliance_log()
            resets = log_data.get("factory_resets", [])
            
            self.reset_history_table.setRowCount(len(resets))
            
            for row, reset in enumerate(resets):
                self.reset_history_table.setItem(row, 0, QTableWidgetItem(reset.get("timestamp", "")[:10]))
                self.reset_history_table.setItem(row, 1, QTableWidgetItem(reset.get("reason", "")))
                self.reset_history_table.setItem(row, 2, QTableWidgetItem(reset.get("status", "")))
                
        except Exception as e:
            self.logger.error(f"Error refreshing reset history: {e}")
    
    def _export_user_data(self):
        """Export user data."""
        try:
            # Confirm the export
            reply = QMessageBox.question(
                self,
                "Export User Data",
                "This will create a comprehensive export of all your data. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            # Start worker
            self.worker = ComplianceWorker("export_data")
            self.worker.progress_updated.connect(self._update_progress)
            self.worker.operation_completed.connect(self._operation_completed)
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            self.worker.start()
            
        except Exception as e:
            self.logger.error(f"Error starting data export: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to start export: {e}")
    
    def _factory_reset(self):
        """Perform factory reset."""
        try:
            # Final confirmation
            reply = QMessageBox.critical(
                self,
                "⚠️ FACTORY RESET WARNING ⚠️",
                "This will PERMANENTLY DELETE ALL YOUR DATA!\n\n"
                "This includes:\n"
                "• All media files and galleries\n"
                "• All scheduled posts\n"
                "• All presets and settings\n"
                "• All knowledge base files\n"
                "• All cached data\n\n"
                "THIS CANNOT BE UNDONE!\n\n"
                "Are you absolutely sure you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            # Start worker
            self.worker = ComplianceWorker("factory_reset")
            self.worker.progress_updated.connect(self._update_progress)
            self.worker.operation_completed.connect(self._factory_reset_completed)
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            self.worker.start()
            
        except Exception as e:
            self.logger.error(f"Error starting factory reset: {e}")
            QMessageBox.critical(self, "Reset Error", f"Failed to start factory reset: {e}")
    
    def _simulate_deletion_request(self):
        """Simulate a data deletion request for testing."""
        try:
            # Create a fake signed request for testing
            test_user_id = f"test_user_{int(datetime.now().timestamp())}"
            
            # Simulate the deletion process
            confirmation_code = compliance_handler._generate_confirmation_code(test_user_id)
            
            deletion_request = {
                "user_id": test_user_id,
                "confirmation_code": confirmation_code,
                "timestamp": datetime.now().isoformat(),
                "status": "simulated_test",
                "completed": True
            }
            
            # Log the simulated request
            log_data = compliance_handler._load_compliance_log()
            log_data["deletion_requests"].append(deletion_request)
            compliance_handler._save_compliance_log(log_data)
            
            self._refresh_deletion_requests()
            
            QMessageBox.information(
                self,
                "Simulation Complete",
                f"Simulated deletion request for test user: {test_user_id}\n"
                f"Confirmation code: {confirmation_code}"
            )
            
        except Exception as e:
            self.logger.error(f"Error simulating deletion request: {e}")
            QMessageBox.critical(self, "Simulation Error", f"Failed to simulate request: {e}")
    
    def _update_progress(self, message: str):
        """Update progress display."""
        self.status_label.setText(message)
    
    def _operation_completed(self, success: bool, message: str):
        """Handle operation completion."""
        self.progress_bar.setVisible(False)
        self.status_label.setText("")
        
        if success:
            QMessageBox.information(self, "Operation Complete", message)
            self._load_compliance_data()  # Refresh data
        else:
            QMessageBox.critical(self, "Operation Failed", message)
    
    def _factory_reset_completed(self, success: bool, message: str):
        """Handle factory reset completion."""
        self.progress_bar.setVisible(False)
        self.status_label.setText("")
        
        if success:
            QMessageBox.information(
                self,
                "Factory Reset Complete",
                "Factory reset completed successfully.\n\n"
                "All user data has been permanently deleted.\n"
                "The application will now close."
            )
            # Close the entire application after factory reset
            self.accept()
            if self.parent():
                self.parent().close()
        else:
            QMessageBox.critical(self, "Factory Reset Failed", message)
    
    def retranslateUi(self):
        """Update UI text for translations."""
        # This would be implemented for i18n support
        pass
    
    def changeEvent(self, event):
        """Handle change events."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event) 