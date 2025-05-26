"""
Gallery Item Widget for displaying saved galleries in the Finished Galleries tab.
"""
import os
from typing import Dict, Any
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QPixmap

from ...features.media_processing.media_handler import MediaHandler, pil_to_qpixmap
from ..base_widget import BaseWidget


class GalleryItemWidget(BaseWidget):
    """Widget to display a single saved gallery in the Finished Galleries tab."""
    view_edit_requested = Signal(dict) # gallery_data
    add_media_requested = Signal(dict) # gallery_data

    def __init__(self, gallery_data: Dict[str, Any], media_handler: MediaHandler, parent=None):
        super().__init__(parent)
        self.gallery_data = gallery_data
        self.media_handler = media_handler
        self._setup_ui()
        self.retranslateUi() # Initial translation

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Gallery name
        name = self.gallery_data.get('name', 'Untitled Gallery')
        self.name_label = QLabel(name)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFFFFF;")
        layout.addWidget(self.name_label)
        
        # Gallery description/caption
        caption = self.gallery_data.get('caption', '')
        if caption:
            caption_label = QLabel(caption[:100] + "..." if len(caption) > 100 else caption)
            caption_label.setWordWrap(True)
            caption_label.setStyleSheet("color: #CCCCCC; font-size: 11px;")
            layout.addWidget(caption_label)
        
        # Gallery info (media count and creation date)
        media_paths = self.gallery_data.get('media_paths', [])
        info_text = f"{len(media_paths)} item{'s' if len(media_paths) != 1 else ''}"
        created_at = self.gallery_data.get('created_at', '')
        if created_at:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                info_text += f" • Created {dt.strftime('%b %d, %Y')}"
            except:
                pass
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #999999; font-size: 10px;")
        layout.addWidget(info_label)
        
        # Thumbnail preview (show first few images)
        if media_paths:
            thumbnail_frame = QFrame()
            thumbnail_layout = QHBoxLayout(thumbnail_frame)
            thumbnail_layout.setContentsMargins(0, 5, 0, 5)
            
            # Show up to 3 thumbnails
            for i, media_path in enumerate(media_paths[:3]):
                if i >= 3:
                    break
                    
                thumb_label = QLabel()
                thumb_label.setFixedSize(60, 60)
                thumb_label.setStyleSheet("background-color: #2D2D2D; border: 1px solid #444; border-radius: 3px;")
                thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                try:
                    img = self.media_handler.load_image(media_path)
                    if img:
                        img.thumbnail((60, 60))
                        pixmap = pil_to_qpixmap(img)
                        if not pixmap.isNull():
                            thumb_label.setPixmap(pixmap)
                            thumb_label.setScaledContents(True)
                        else:
                            thumb_label.setText("IMG")
                    else:
                        thumb_label.setText("IMG")
                except Exception:
                    thumb_label.setText("IMG")
                
                thumbnail_layout.addWidget(thumb_label)
            
            # Show count if more than 3 images
            if len(media_paths) > 3:
                more_label = QLabel(f"+{len(media_paths) - 3}")
                more_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
                more_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                thumbnail_layout.addWidget(more_label)
            
            thumbnail_layout.addStretch()
            layout.addWidget(thumbnail_frame)
        
        # Action buttons
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 5, 0, 0)
        
        self.view_edit_button = QPushButton() # Text set in retranslateUi
        self.view_edit_button.clicked.connect(self._on_view_edit_clicked)
        self.view_edit_button.setStyleSheet("""
            QPushButton {
                background-color: #6d28d9;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5b21b6;
            }
        """)
        button_layout.addWidget(self.view_edit_button)
        
        # Add Media button
        self.add_media_button = QPushButton() # Text set in retranslateUi
        self.add_media_button.clicked.connect(self._on_add_media_clicked)
        self.add_media_button.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #047857;
            }
        """)
        button_layout.addWidget(self.add_media_button)
        
        button_layout.addStretch()
        
        layout.addWidget(button_frame)
        
        # Overall styling
        self.setStyleSheet("""
            GalleryItemWidget {
                background-color: #3D3D3D;
                border: 1px solid #555555;
                border-radius: 6px;
                margin: 2px;
            }
            GalleryItemWidget:hover {
                background-color: #4D4D4D;
                border-color: #6d28d9;
            }
        """)

    def _on_view_edit_clicked(self):
        """Emit signal to view/edit this gallery."""
        self.view_edit_requested.emit(self.gallery_data)

    def _on_add_media_clicked(self):
        """Emit signal to add media to this gallery."""
        self.add_media_requested.emit(self.gallery_data)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.view_edit_button.setText(self.tr("View/Edit"))
        self.add_media_button.setText(self.tr("Add Media")) 