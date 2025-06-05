"""
Analytics Dashboard Dialog for Crow's Eye platform.
Displays post performance graphs and provides export functionality.
"""

import os
import logging
from typing import Dict, Any, List

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QTabWidget, QWidget,
    QGroupBox, QFormLayout, QMessageBox, QProgressBar,
    QComboBox, QSpinBox, QFileDialog, QTextEdit, QScrollArea
)
from PySide6.QtGui import QFont, QPixmap, QPainter, QPen, QBrush, QColor
from PySide6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QValueAxis, QBarCategoryAxis, QPieSeries

from ..base_dialog import BaseDialog
from ...handlers.analytics_handler import AnalyticsHandler
from ...utils.subscription_utils import (
    check_feature_access_with_dialog, check_usage_limit_with_dialog,
    requires_feature_qt, requires_usage_qt, show_upgrade_dialog
)
from ...features.subscription.access_control import Feature


class AnalyticsWorker(QThread):
    """Worker thread for analytics operations."""
    
    progress_updated = Signal(str)
    operation_completed = Signal(bool, str, str)  # success, operation, result_path
    
    def __init__(self, operation: str, analytics_handler: AnalyticsHandler, **kwargs):
        super().__init__()
        self.operation = operation
        self.analytics_handler = analytics_handler
        self.kwargs = kwargs
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def run(self):
        """Run the analytics operation."""
        try:
            if self.operation == "export_csv":
                self.progress_updated.emit("Exporting to CSV...")
                export_path = self.analytics_handler.export_to_csv()
                self.operation_completed.emit(bool(export_path), "export_csv", export_path)
            
            elif self.operation == "export_json":
                self.progress_updated.emit("Exporting to JSON...")
                export_path = self.analytics_handler.export_to_json()
                self.operation_completed.emit(bool(export_path), "export_json", export_path)
            
            elif self.operation == "simulate_data":
                self.progress_updated.emit("Generating sample data...")
                # Create some sample posts for demonstration
                sample_posts = [
                    ("sample_bread_1.jpg", "single", ["instagram", "facebook"]),
                    ("sample_bread_2.jpg", "carousel", ["instagram"]),
                    ("sample_video_1.mp4", "story", ["instagram", "facebook"]),
                    ("sample_gallery_1.jpg", "carousel", ["facebook"]),
                    ("sample_bread_3.jpg", "single", ["instagram"])
                ]
                
                for filename, post_type, platforms in sample_posts:
                    post_id = self.analytics_handler.track_post_creation(
                        f"sample_media/{filename}", post_type, platforms
                    )
                    if post_id:
                        self.analytics_handler.simulate_engagement(post_id)
                
                self.operation_completed.emit(True, "simulate_data", "Sample data generated")
            
            else:
                self.operation_completed.emit(False, self.operation, f"Unknown operation: {self.operation}")
                
        except Exception as e:
            self.logger.error(f"Error in analytics worker: {e}")
            self.operation_completed.emit(False, self.operation, f"Operation failed: {str(e)}")


class AnalyticsDashboardDialog(BaseDialog):
    """Dialog for viewing analytics and performance data."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Post Performance Analytics")
        self.setMinimumSize(900, 700)
        
        # Check permissions before initializing
        if not check_feature_access_with_dialog(Feature.PERFORMANCE_ANALYTICS, parent):
            self.reject()
            return
            
        self.analytics_handler = AnalyticsHandler()
        self.worker = None
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("📊 Post Performance Analytics")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFFFFF; margin-bottom: 15px;")
        layout.addWidget(title_label)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444;
                background-color: #2a2a2a;
            }
            QTabBar::tab {
                background-color: #3a3a3a;
                color: #FFFFFF;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #4a4a4a;
                border-bottom: 2px solid #3b82f6;
            }
        """)
        
        # Overview tab
        self.overview_tab = self._create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "Overview")
        
        # Posts tab
        self.posts_tab = self._create_posts_tab()
        self.tab_widget.addTab(self.posts_tab, "Posts Performance")
        
        # Trends tab
        self.trends_tab = self._create_trends_tab()
        self.tab_widget.addTab(self.trends_tab, "Trends")
        
        # Export tab
        self.export_tab = self._create_export_tab()
        self.tab_widget.addTab(self.export_tab, "Export Data")
        
        layout.addWidget(self.tab_widget)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 4px;
                text-align: center;
                color: #FFFFFF;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #CCCCCC; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Sample data button
        self.sample_data_button = QPushButton("Generate Sample Data")
        self.sample_data_button.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.sample_data_button.clicked.connect(self._generate_sample_data)
        button_layout.addWidget(self.sample_data_button)
        
        button_layout.addStretch()
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh Data")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.refresh_button.clicked.connect(self._load_data)
        button_layout.addWidget(self.refresh_button)
        
        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def _create_overview_tab(self):
        """Create the overview tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Summary stats group
        stats_group = QGroupBox("Summary Statistics")
        stats_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        stats_layout = QFormLayout(stats_group)
        
        self.total_posts_label = QLabel("0")
        self.total_posts_label.setStyleSheet("color: #FFFFFF; font-size: 14px;")
        stats_layout.addRow("Total Posts:", self.total_posts_label)
        
        self.total_galleries_label = QLabel("0")
        self.total_galleries_label.setStyleSheet("color: #FFFFFF; font-size: 14px;")
        stats_layout.addRow("Total Galleries:", self.total_galleries_label)
        
        self.total_videos_label = QLabel("0")
        self.total_videos_label.setStyleSheet("color: #FFFFFF; font-size: 14px;")
        stats_layout.addRow("Total Videos:", self.total_videos_label)
        
        self.avg_engagement_label = QLabel("0")
        self.avg_engagement_label.setStyleSheet("color: #FFFFFF; font-size: 14px;")
        stats_layout.addRow("Avg Engagement:", self.avg_engagement_label)
        
        self.top_post_label = QLabel("None")
        self.top_post_label.setStyleSheet("color: #FFFFFF; font-size: 14px;")
        stats_layout.addRow("Top Performing Post:", self.top_post_label)
        
        layout.addWidget(stats_group)
        
        # Performance chart placeholder
        chart_group = QGroupBox("Performance Overview")
        chart_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        chart_layout = QVBoxLayout(chart_group)
        
        self.overview_chart_label = QLabel("📊 Performance charts will be displayed here")
        self.overview_chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.overview_chart_label.setStyleSheet("""
            color: #CCCCCC; 
            font-size: 16px; 
            padding: 40px; 
            border: 2px dashed #444; 
            border-radius: 8px;
        """)
        chart_layout.addWidget(self.overview_chart_label)
        
        layout.addWidget(chart_group)
        
        return tab
    
    def _create_posts_tab(self):
        """Create the posts performance tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Posts table
        self.posts_table = QTableWidget()
        self.posts_table.setColumnCount(9)
        self.posts_table.setHorizontalHeaderLabels([
            "Filename", "Type", "Platforms", "Created", "Views", 
            "Likes", "Shares", "Comments", "Total Engagement"
        ])
        self.posts_table.setStyleSheet("""
            QTableWidget {
                background-color: #2a2a2a;
                color: #FFFFFF;
                gridline-color: #444;
                selection-background-color: #3b82f6;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: #FFFFFF;
                padding: 8px;
                border: 1px solid #444;
                font-weight: bold;
            }
        """)
        
        # Make table sortable
        self.posts_table.setSortingEnabled(True)
        
        layout.addWidget(self.posts_table)
        
        return tab
    
    def _create_trends_tab(self):
        """Create the trends analysis tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Trends controls
        controls_group = QGroupBox("Analysis Period")
        controls_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        controls_layout = QHBoxLayout(controls_group)
        
        controls_layout.addWidget(QLabel("Days to analyze:"))
        
        self.days_spinbox = QSpinBox()
        self.days_spinbox.setRange(1, 365)
        self.days_spinbox.setValue(30)
        self.days_spinbox.setStyleSheet("color: #FFFFFF; background-color: #2a2a2a; border: 1px solid #444; padding: 5px;")
        controls_layout.addWidget(self.days_spinbox)
        
        self.analyze_button = QPushButton("Analyze Trends")
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.analyze_button.clicked.connect(self._analyze_trends)
        controls_layout.addWidget(self.analyze_button)
        
        controls_layout.addStretch()
        
        layout.addWidget(controls_group)
        
        # Trends results
        self.trends_text = QTextEdit()
        self.trends_text.setReadOnly(True)
        self.trends_text.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                color: #FFFFFF;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Courier New', monospace;
            }
        """)
        layout.addWidget(self.trends_text)
        
        return tab
    
    def _create_export_tab(self):
        """Create the export tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Export info
        info_label = QLabel("""
        <b>Export Analytics Data</b><br><br>
        
        Export your post performance data in CSV or JSON format for external analysis.
        CSV format is ideal for spreadsheet applications, while JSON format preserves
        all data structure and is suitable for programmatic analysis.
        """)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("padding: 10px; background-color: #1a3a5c; border-radius: 5px; margin-bottom: 10px; color: #FFFFFF;")
        layout.addWidget(info_label)
        
        # Export options
        export_group = QGroupBox("Export Options")
        export_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        export_layout = QVBoxLayout(export_group)
        
        # CSV export
        csv_layout = QHBoxLayout()
        self.csv_export_button = QPushButton("Export to CSV")
        self.csv_export_button.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.csv_export_button.clicked.connect(self._export_csv)
        csv_layout.addWidget(self.csv_export_button)
        
        csv_info = QLabel("Exports post data in spreadsheet-compatible format")
        csv_info.setStyleSheet("color: #CCCCCC; font-size: 12px;")
        csv_layout.addWidget(csv_info)
        csv_layout.addStretch()
        
        export_layout.addLayout(csv_layout)
        
        # JSON export
        json_layout = QHBoxLayout()
        self.json_export_button = QPushButton("Export to JSON")
        self.json_export_button.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.json_export_button.clicked.connect(self._export_json)
        json_layout.addWidget(self.json_export_button)
        
        json_info = QLabel("Exports complete data structure with all metadata")
        json_info.setStyleSheet("color: #CCCCCC; font-size: 12px;")
        json_layout.addWidget(json_info)
        json_layout.addStretch()
        
        export_layout.addLayout(json_layout)
        
        layout.addWidget(export_group)
        
        # Export history
        history_group = QGroupBox("Recent Exports")
        history_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        history_layout = QVBoxLayout(history_group)
        
        self.export_history_label = QLabel("No exports yet")
        self.export_history_label.setStyleSheet("color: #CCCCCC; padding: 10px;")
        history_layout.addWidget(self.export_history_label)
        
        layout.addWidget(history_group)
        
        layout.addStretch()
        
        return tab
    
    def _load_data(self):
        """Load and display analytics data."""
        try:
            # Load summary stats
            summary = self.analytics_handler.get_summary_stats()
            
            self.total_posts_label.setText(str(summary.get("total_posts", 0)))
            self.total_galleries_label.setText(str(summary.get("total_galleries", 0)))
            self.total_videos_label.setText(str(summary.get("total_videos", 0)))
            self.avg_engagement_label.setText(str(summary.get("avg_engagement_per_post", 0)))
            self.top_post_label.setText(str(summary.get("top_performing_post", "None")))
            
            # Load posts data
            self._load_posts_table()
            
            self.status_label.setText(f"Data loaded - Last updated: {summary.get('last_updated', 'Never')}")
            
        except Exception as e:
            self.logger.error(f"Error loading analytics data: {e}")
            self.status_label.setText(f"Error loading data: {str(e)}")
    
    def _load_posts_table(self):
        """Load posts data into the table."""
        try:
            posts = self.analytics_handler.get_all_posts_performance()
            
            self.posts_table.setRowCount(len(posts))
            
            for row, post in enumerate(posts):
                metrics = post.get("metrics", {})
                total_engagement = sum(metrics.values())
                
                # Filename
                self.posts_table.setItem(row, 0, QTableWidgetItem(post.get("filename", "")))
                
                # Type
                self.posts_table.setItem(row, 1, QTableWidgetItem(post.get("post_type", "")))
                
                # Platforms
                platforms = ", ".join(post.get("platforms", []))
                self.posts_table.setItem(row, 2, QTableWidgetItem(platforms))
                
                # Created date
                created_at = post.get("created_at", "")[:10]  # Just the date part
                self.posts_table.setItem(row, 3, QTableWidgetItem(created_at))
                
                # Metrics
                self.posts_table.setItem(row, 4, QTableWidgetItem(str(metrics.get("views", 0))))
                self.posts_table.setItem(row, 5, QTableWidgetItem(str(metrics.get("likes", 0))))
                self.posts_table.setItem(row, 6, QTableWidgetItem(str(metrics.get("shares", 0))))
                self.posts_table.setItem(row, 7, QTableWidgetItem(str(metrics.get("comments", 0))))
                self.posts_table.setItem(row, 8, QTableWidgetItem(str(total_engagement)))
            
            # Resize columns to content
            self.posts_table.resizeColumnsToContents()
            
        except Exception as e:
            self.logger.error(f"Error loading posts table: {e}")
    
    def _analyze_trends(self):
        """Analyze performance trends."""
        try:
            days = self.days_spinbox.value()
            trends = self.analytics_handler.get_performance_trends(days)
            
            # Format trends data for display
            trends_text = f"📈 Performance Trends Analysis ({days} days)\n"
            trends_text += "=" * 50 + "\n\n"
            
            if "message" in trends:
                trends_text += trends["message"]
            else:
                trends_text += f"Total Posts: {trends.get('total_posts', 0)}\n"
                trends_text += f"Total Engagement: {trends.get('total_engagement', 0)}\n"
                trends_text += f"Average Engagement per Post: {trends.get('avg_engagement_per_post', 0)}\n"
                trends_text += f"Best Performing Type: {trends.get('best_performing_type', 'None')}\n\n"
                
                trends_text += "Performance by Post Type:\n"
                trends_text += "-" * 30 + "\n"
                
                for post_type, data in trends.get('performance_by_type', {}).items():
                    trends_text += f"{post_type.title()}:\n"
                    trends_text += f"  Posts: {data['count']}\n"
                    trends_text += f"  Total Engagement: {data['total_engagement']}\n"
                    trends_text += f"  Average Engagement: {data['avg_engagement']:.2f}\n\n"
            
            self.trends_text.setPlainText(trends_text)
            
        except Exception as e:
            self.logger.error(f"Error analyzing trends: {e}")
            self.trends_text.setPlainText(f"Error analyzing trends: {str(e)}")
    
    def _generate_sample_data(self):
        """Generate sample data for demonstration."""
        try:
            self.sample_data_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            self.worker = AnalyticsWorker("simulate_data", self.analytics_handler)
            self.worker.progress_updated.connect(self._update_progress)
            self.worker.operation_completed.connect(self._on_operation_completed)
            self.worker.start()
            
        except Exception as e:
            self.logger.error(f"Error generating sample data: {e}")
            self.status_label.setText(f"Error: {str(e)}")
            self.sample_data_button.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def _export_csv(self):
        """Export data to CSV format."""
        try:
            self.csv_export_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            
            self.worker = AnalyticsWorker("export_csv", self.analytics_handler)
            self.worker.progress_updated.connect(self._update_progress)
            self.worker.operation_completed.connect(self._on_operation_completed)
            self.worker.start()
            
        except Exception as e:
            self.logger.error(f"Error exporting CSV: {e}")
            self.status_label.setText(f"Export error: {str(e)}")
            self.csv_export_button.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def _export_json(self):
        """Export data to JSON format."""
        try:
            self.json_export_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            
            self.worker = AnalyticsWorker("export_json", self.analytics_handler)
            self.worker.progress_updated.connect(self._update_progress)
            self.worker.operation_completed.connect(self._on_operation_completed)
            self.worker.start()
            
        except Exception as e:
            self.logger.error(f"Error exporting JSON: {e}")
            self.status_label.setText(f"Export error: {str(e)}")
            self.json_export_button.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def _update_progress(self, message: str):
        """Update progress message."""
        self.status_label.setText(message)
    
    def _on_operation_completed(self, success: bool, operation: str, result: str):
        """Handle operation completion."""
        # Re-enable UI
        self.sample_data_button.setEnabled(True)
        self.csv_export_button.setEnabled(True)
        self.json_export_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            if operation == "simulate_data":
                self.status_label.setText("✓ Sample data generated successfully")
                self._load_data()  # Refresh the display
            elif operation in ["export_csv", "export_json"]:
                self.status_label.setText(f"✓ Export completed: {os.path.basename(result)}")
                self.export_history_label.setText(f"Last export: {os.path.basename(result)}")
                
                # Show success message with option to open file
                reply = QMessageBox.question(
                    self,
                    "Export Successful",
                    f"Data exported successfully!\n\nFile: {result}\n\nWould you like to open the export folder?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    import subprocess
                    import platform
                    
                    folder_path = os.path.dirname(result)
                    if platform.system() == "Windows":
                        subprocess.run(["explorer", folder_path])
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", folder_path])
                    else:  # Linux
                        subprocess.run(["xdg-open", folder_path])
        else:
            self.status_label.setText(f"✗ {operation} failed: {result}")
            QMessageBox.critical(self, "Operation Failed", f"Operation failed:\n\n{result}")
        
        # Clean up worker
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Operation in Progress",
                "An operation is currently running. Are you sure you want to close?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.terminate()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept() 