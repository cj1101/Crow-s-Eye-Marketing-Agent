"""
Video Thumbnail Generator - Utility for creating thumbnails from video files.
"""
import os
import logging
import tempfile
from typing import Optional, Tuple
import cv2
from PIL import Image
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt


class VideoThumbnailGenerator:
    """Utility class for generating video thumbnails."""
    
    def __init__(self):
        """Initialize the thumbnail generator."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.temp_dir = tempfile.gettempdir()
    
    def generate_thumbnail(self, video_path: str, timestamp: float = 1.0, 
                          size: Tuple[int, int] = (400, 300)) -> Optional[QPixmap]:
        """
        Generate a thumbnail from a video file.
        
        Args:
            video_path: Path to the video file
            timestamp: Time in seconds to capture the frame (default: 1.0)
            size: Tuple of (width, height) for the thumbnail size
            
        Returns:
            QPixmap object if successful, None otherwise
        """
        try:
            if not os.path.exists(video_path):
                self.logger.warning(f"Video file not found: {video_path}")
                return None
            
            # Open video with OpenCV
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                self.logger.error(f"Could not open video file: {video_path}")
                return None
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            # Adjust timestamp if it's beyond video duration
            if timestamp > duration:
                timestamp = duration * 0.1  # Use 10% into the video
            
            # Seek to the desired timestamp
            frame_number = int(timestamp * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            # Read the frame
            ret, frame = cap.read()
            cap.release()
            
            if not ret or frame is None:
                self.logger.error(f"Could not read frame at timestamp {timestamp}")
                return None
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(frame_rgb)
            
            # Resize to desired size while maintaining aspect ratio
            pil_image.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Create a new image with the exact size and center the thumbnail
            final_image = Image.new('RGB', size, (0, 0, 0))
            
            # Calculate position to center the thumbnail
            x = (size[0] - pil_image.width) // 2
            y = (size[1] - pil_image.height) // 2
            
            final_image.paste(pil_image, (x, y))
            
            # Convert to QPixmap
            # Save to temporary file first
            temp_path = os.path.join(self.temp_dir, f"video_thumb_{os.getpid()}.png")
            final_image.save(temp_path, "PNG")
            
            # Load as QPixmap
            pixmap = QPixmap(temp_path)
            
            # Clean up temporary file
            try:
                os.remove(temp_path)
            except:
                pass  # Ignore cleanup errors
            
            if pixmap.isNull():
                self.logger.error("Failed to create QPixmap from thumbnail")
                return None
            
            self.logger.info(f"Generated thumbnail for {os.path.basename(video_path)}")
            return pixmap
            
        except Exception as e:
            self.logger.exception(f"Error generating thumbnail for {video_path}: {e}")
            return None
    
    def generate_multiple_thumbnails(self, video_path: str, count: int = 3, 
                                   size: Tuple[int, int] = (200, 150)) -> list:
        """
        Generate multiple thumbnails from different points in the video.
        
        Args:
            video_path: Path to the video file
            count: Number of thumbnails to generate
            size: Tuple of (width, height) for each thumbnail
            
        Returns:
            List of QPixmap objects
        """
        thumbnails = []
        
        try:
            if not os.path.exists(video_path):
                return thumbnails
            
            # Get video duration
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return thumbnails
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            cap.release()
            
            if duration <= 0:
                return thumbnails
            
            # Generate timestamps evenly distributed across the video
            timestamps = []
            if count == 1:
                timestamps = [duration * 0.5]  # Middle of video
            else:
                for i in range(count):
                    # Start from 10% into video, end at 90%
                    progress = 0.1 + (0.8 * i / (count - 1))
                    timestamps.append(duration * progress)
            
            # Generate thumbnail for each timestamp
            for timestamp in timestamps:
                thumbnail = self.generate_thumbnail(video_path, timestamp, size)
                if thumbnail:
                    thumbnails.append(thumbnail)
            
        except Exception as e:
            self.logger.exception(f"Error generating multiple thumbnails: {e}")
        
        return thumbnails
    
    def create_video_preview_pixmap(self, video_path: str, 
                                  size: Tuple[int, int] = (400, 300)) -> QPixmap:
        """
        Create a video preview pixmap with fallback to text if thumbnail generation fails.
        
        Args:
            video_path: Path to the video file
            size: Tuple of (width, height) for the preview
            
        Returns:
            QPixmap object (either thumbnail or text-based preview)
        """
        # Try to generate thumbnail first
        thumbnail = self.generate_thumbnail(video_path, size=size)
        if thumbnail:
            return thumbnail
        
        # Fallback: create a text-based preview
        return self._create_text_preview(video_path, size)
    
    def _create_text_preview(self, video_path: str, 
                           size: Tuple[int, int] = (400, 300)) -> QPixmap:
        """
        Create a text-based video preview when thumbnail generation fails.
        
        Args:
            video_path: Path to the video file
            size: Tuple of (width, height) for the preview
            
        Returns:
            QPixmap with video information as text
        """
        try:
            # Create a simple text-based preview
            pixmap = QPixmap(size[0], size[1])
            pixmap.fill(Qt.GlobalColor.darkGray)
            
            # This would require QPainter to draw text, but for now return empty pixmap
            # The calling code should handle the fallback to text display
            return pixmap
            
        except Exception as e:
            self.logger.exception(f"Error creating text preview: {e}")
            # Return empty pixmap as last resort
            pixmap = QPixmap(size[0], size[1])
            pixmap.fill(Qt.GlobalColor.black)
            return pixmap 