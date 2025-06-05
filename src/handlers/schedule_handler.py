"""
Handler for scheduling posts.
"""
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

class Scheduler:
    """Handles post scheduling functionality."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Define scheduler paths
        self.scheduler_dir = Path("scheduler")
        self.data_dir = self.scheduler_dir / "data"
        self.schedules_file = self.data_dir / "schedules.json"
        self.posts_file = self.data_dir / "scheduled_posts.json"
        
        # Ensure directories exist
        self.scheduler_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load data
        self.schedules = self._load_schedules()
        self.scheduled_posts = self._load_scheduled_posts()
    
    def _load_schedules(self) -> Dict[str, Any]:
        """Load schedules from the JSON file."""
        try:
            if self.schedules_file.exists():
                with open(self.schedules_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Initialize with empty structure
                initial_data = {
                    "schedules": {}
                }
                self._save_schedules(initial_data)
                return initial_data
                
        except Exception as e:
            self.logger.error(f"Error loading schedules: {e}")
            # Return empty structure on error
            return {
                "schedules": {}
            }
    
    def _save_schedules(self, data: Dict[str, Any]) -> bool:
        """Save schedules to the JSON file."""
        try:
            with open(self.schedules_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"Error saving schedules: {e}")
            return False
    
    def _load_scheduled_posts(self) -> Dict[str, Any]:
        """Load scheduled posts from the JSON file."""
        try:
            if self.posts_file.exists():
                with open(self.posts_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Initialize with empty structure
                initial_data = {
                    "posts": {}
                }
                self._save_scheduled_posts(initial_data)
                return initial_data
                
        except Exception as e:
            self.logger.error(f"Error loading scheduled posts: {e}")
            # Return empty structure on error
            return {
                "posts": {}
            }
    
    def _save_scheduled_posts(self, data: Dict[str, Any]) -> bool:
        """Save scheduled posts to the JSON file."""
        try:
            with open(self.posts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"Error saving scheduled posts: {e}")
            return False
    
    def add_or_update_schedule(self, schedule_data: Dict[str, Any]) -> bool:
        """
        Add or update a schedule.
        
        Args:
            schedule_data: Schedule data dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get schedule ID
            schedule_id = schedule_data.get("id")
            
            # Generate new ID if not provided
            if not schedule_id:
                schedule_id = f"schedule_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                schedule_data["id"] = schedule_id
            
            # Add or update schedule
            self.schedules["schedules"][schedule_id] = schedule_data
            
            # Save schedules
            self._save_schedules(self.schedules)
            
            self.logger.info(f"Schedule saved: {schedule_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding/updating schedule: {e}")
            return False
    
    def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a schedule by ID.
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            dict: Schedule data, or None if not found
        """
        try:
            return self.schedules["schedules"].get(schedule_id)
        except Exception as e:
            self.logger.error(f"Error getting schedule {schedule_id}: {e}")
            return None
    
    def get_all_schedules(self) -> List[Dict[str, Any]]:
        """
        Get all schedules.
        
        Returns:
            list: List of all schedule data
        """
        try:
            return list(self.schedules["schedules"].values())
        except Exception as e:
            self.logger.error(f"Error getting all schedules: {e}")
            return []
    
    def delete_schedule(self, schedule_id: str) -> bool:
        """
        Delete a schedule.
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if schedule_id in self.schedules["schedules"]:
                del self.schedules["schedules"][schedule_id]
                self._save_schedules(self.schedules)
                self.logger.info(f"Schedule deleted: {schedule_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting schedule {schedule_id}: {e}")
            return False 