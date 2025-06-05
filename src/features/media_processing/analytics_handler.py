"""
Analytics handler for media processing operations.
Tracks video processing metrics and performance data.
"""

import os
import json
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from ...config import constants as const


class AnalyticsHandler:
    """Handles analytics and performance tracking for media processing."""
    
    def __init__(self):
        """Initialize the analytics handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.analytics_file = os.path.join(const.DATA_DIR, "media_analytics.json")
        self.analytics_data = self._load_analytics_data()
        
    def _load_analytics_data(self) -> Dict[str, Any]:
        """Load analytics data from file."""
        try:
            if os.path.exists(self.analytics_file):
                with open(self.analytics_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Create default structure
                return {
                    "videos": {},
                    "images": {},
                    "summary_stats": {
                        "total_videos": 0,
                        "total_images": 0,
                        "total_processing_time": 0,
                        "success_rate": 100
                    }
                }
        except Exception as e:
            self.logger.error(f"Error loading analytics data: {e}")
            return {
                "videos": {},
                "images": {},
                "summary_stats": {
                    "total_videos": 0,
                    "total_images": 0,
                    "total_processing_time": 0,
                    "success_rate": 100
                }
            }
    
    def _save_analytics_data(self):
        """Save analytics data to file."""
        try:
            os.makedirs(os.path.dirname(self.analytics_file), exist_ok=True)
            with open(self.analytics_file, 'w', encoding='utf-8') as f:
                json.dump(self.analytics_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving analytics data: {e}")
    
    def track_video_processing(self, video_path: str, process_type: str, 
                              output_path: str = "") -> str:
        """
        Track video processing operations.
        
        Args:
            video_path: Path to the original video
            process_type: Type of processing (highlight_reel, story_clips, thumbnail)
            output_path: Path to the processed output
            
        Returns:
            str: Unique processing ID for tracking
        """
        try:
            process_id = str(uuid.uuid4())
            
            process_data = {
                "id": process_id,
                "original_video": video_path,
                "process_type": process_type,
                "output_path": output_path,
                "created_at": datetime.now().isoformat(),
                "metrics": {
                    "processing_time": 0,
                    "output_size": 0,
                    "usage_count": 0,
                    "success_rate": 100
                }
            }
            
            self.analytics_data["videos"][process_id] = process_data
            self.analytics_data["summary_stats"]["total_videos"] += 1
            self._save_analytics_data()
            
            self.logger.info(f"Tracked video processing: {process_id}")
            return process_id
            
        except Exception as e:
            self.logger.error(f"Error tracking video processing: {e}")
            return ""
    
    def track_image_processing(self, image_path: str, process_type: str, 
                              output_path: str = "") -> str:
        """
        Track image processing operations.
        
        Args:
            image_path: Path to the original image
            process_type: Type of processing (edit, enhance, filter)
            output_path: Path to the processed output
            
        Returns:
            str: Unique processing ID for tracking
        """
        try:
            process_id = str(uuid.uuid4())
            
            process_data = {
                "id": process_id,
                "original_image": image_path,
                "process_type": process_type,
                "output_path": output_path,
                "created_at": datetime.now().isoformat(),
                "metrics": {
                    "processing_time": 0,
                    "output_size": 0,
                    "usage_count": 0,
                    "success_rate": 100
                }
            }
            
            self.analytics_data["images"][process_id] = process_data
            self.analytics_data["summary_stats"]["total_images"] += 1
            self._save_analytics_data()
            
            self.logger.info(f"Tracked image processing: {process_id}")
            return process_id
            
        except Exception as e:
            self.logger.error(f"Error tracking image processing: {e}")
            return ""
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.analytics_data.get("summary_stats", {})
    
    def get_video_history(self) -> Dict[str, Any]:
        """Get video processing history."""
        return self.analytics_data.get("videos", {})
    
    def get_image_history(self) -> Dict[str, Any]:
        """Get image processing history."""
        return self.analytics_data.get("images", {}) 