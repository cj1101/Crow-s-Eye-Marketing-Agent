"""
Handles all scheduling and automation functionality.
"""
import logging
import json
import os
import random
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from PySide6.QtCore import QObject, Signal, QTimer

from ..config import constants as const
from ..models.app_state import AppState

class SchedulingSignals(QObject):
    """Signal definitions for scheduling operations."""
    status_update = Signal(str)  # General status updates
    error = Signal(str, str)  # Error title, message
    warning = Signal(str, str)  # Warning title, message
    info = Signal(str, str)  # Info title, message
    schedule_updated = Signal()  # Schedule was updated
    post_scheduled = Signal(dict)  # New post was scheduled
    post_published = Signal(dict)  # Post was published

class PostScheduler:
    """Handles scheduling and publishing of posts."""
    
    def __init__(self, app_state: AppState, signals: Optional[SchedulingSignals] = None):
        """
        Initialize the scheduler.
        
        Args:
            app_state: Application state
            signals: Scheduling signals object (optional)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.app_state = app_state
        self.signals = signals or SchedulingSignals()
        
        # Timer for checking schedule
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_schedule)
        
        # Scheduler state
        self.is_running = False
        self.check_interval = 60000  # Check every minute (60000 ms)
        
        # Load schedules
        self.schedules = self._load_schedules()
        self.scheduled_posts = self._load_scheduled_posts()
        
    def _load_schedules(self) -> List[Dict[str, Any]]:
        """
        Load schedules from presets file.
        
        Returns:
            List[Dict]: List of schedule data
        """
        try:
            if os.path.exists(const.PRESETS_FILE):
                with open(const.PRESETS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("schedules", [])
            return []
        except Exception as e:
            self.logger.error(f"Error loading schedules: {e}")
            return []
            
    def _save_schedules(self, schedules: List[Dict[str, Any]]) -> bool:
        """
        Save schedules to presets file.
        
        Args:
            schedules: List of schedule data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load existing data
            data = {}
            if os.path.exists(const.PRESETS_FILE):
                with open(const.PRESETS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
            # Update schedules
            data["schedules"] = schedules
            
            # Save to file
            with open(const.PRESETS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
                
            return True
        except Exception as e:
            self.logger.error(f"Error saving schedules: {e}")
            return False
            
    def _load_scheduled_posts(self) -> List[Dict[str, Any]]:
        """
        Load scheduled posts from app state.
        
        Returns:
            List[Dict]: List of scheduled post data
        """
        return self.app_state.scheduled_posts
        
    def _save_scheduled_posts(self, posts: List[Dict[str, Any]]) -> None:
        """
        Save scheduled posts to app state.
        
        Args:
            posts: List of scheduled post data
        """
        self.app_state.scheduled_posts = posts
        
    def start(self) -> None:
        """Start the scheduler."""
        if not self.is_running:
            self.is_running = True
            self.timer.start(self.check_interval)
            self.logger.info("Scheduler started")
            self.signals.status_update.emit("Scheduler started")
            
            # Schedule posts for the first time
            self.schedule_posts()
            
    def stop(self) -> None:
        """Stop the scheduler."""
        if self.is_running:
            self.is_running = False
            self.timer.stop()
            self.logger.info("Scheduler stopped")
            self.signals.status_update.emit("Scheduler stopped")
            
    def _check_schedule(self) -> None:
        """Check for posts that need to be published."""
        if not self.is_running:
            return
            
        try:
            current_time = datetime.now()
            
            # Check for posts to publish
            posts_to_remove = []
            for i, post in enumerate(self.scheduled_posts):
                scheduled_time = datetime.fromisoformat(post.get("scheduled_time", ""))
                
                # If the scheduled time has passed, publish the post
                if scheduled_time <= current_time:
                    self._publish_post(post)
                    posts_to_remove.append(i)
                    
            # Remove published posts from the list
            if posts_to_remove:
                for i in sorted(posts_to_remove, reverse=True):
                    self.scheduled_posts.pop(i)
                self._save_scheduled_posts(self.scheduled_posts)
                
            # Check if we need to schedule more posts
            self.schedule_posts()
                
        except Exception as e:
            self.logger.error(f"Error checking schedule: {e}")
            self.signals.error.emit("Schedule Error", f"Failed to check schedule: {str(e)}")
            
    def _publish_post(self, post: Dict[str, Any]) -> bool:
        """
        Publish a post.
        This is a placeholder for actual publishing functionality.
        
        Args:
            post: Post data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Log the post
            self.logger.info(f"Publishing post: {post.get('media_path')}")
            self.signals.status_update.emit(f"Publishing post: {post.get('media_path')}")
            
            # Emit signal
            self.signals.post_published.emit(post)
            
            return True
        except Exception as e:
            self.logger.error(f"Error publishing post: {e}")
            self.signals.error.emit("Publish Error", f"Failed to publish post: {str(e)}")
            return False
            
    def schedule_posts(self) -> None:
        """Schedule posts based on the defined schedules."""
        try:
            # Load schedules
            self.schedules = self._load_schedules()
            
            # Process each schedule
            for schedule in self.schedules:
                self._process_schedule(schedule)
                
        except Exception as e:
            self.logger.error(f"Error scheduling posts: {e}")
            self.signals.error.emit("Schedule Error", f"Failed to schedule posts: {str(e)}")
            
    def _process_schedule(self, schedule: Dict[str, Any]) -> None:
        """Process a single schedule and add posts to the schedule."""
        schedule_id = schedule.get("id", "")
        schedule_name = schedule.get("name", "Unnamed Schedule")
        posts_per_week = schedule.get("posts_per_week", 3)
        
        # Parse start and end dates
        start_date_str = schedule.get("start_date", "")
        end_date_str = schedule.get("end_date", "")
        
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else datetime.now()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else datetime.now() + timedelta(days=30)
            
            # If start date is in the future, don't schedule yet
            if start_date > datetime.now():
                self.logger.info(f"Schedule '{schedule_name}' starts in the future ({start_date_str})")
                return
                
            # If end date is in the past, don't schedule
            if end_date < datetime.now():
                self.logger.info(f"Schedule '{schedule_name}' has ended ({end_date_str})")
                return
                
            # Calculate posts for the next week
            schedule_end = min(end_date, datetime.now() + timedelta(days=7))
            
            # Get available posting times
            posting_times = self._get_posting_times(schedule, datetime.now(), schedule_end, posts_per_week)
            
            if not posting_times:
                self.logger.warning(f"No valid posting times found for schedule '{schedule_name}'")
                return
                
            # Get available media items
            available_items = self._get_available_items()
            
            if not available_items:
                self.logger.warning("No available items to schedule")
                return
                
            # Schedule posts
            for posting_time in posting_times:
                # Check if we already have a post scheduled at this time
                if any(post.get("scheduled_time") == posting_time.isoformat() for post in self.scheduled_posts):
                    continue
                    
                # Select a random media item
                if not available_items:
                    self.logger.warning("Ran out of media items to schedule")
                    break
                    
                media_item = random.choice(available_items)
                available_items.remove(media_item)
                
                # Create post data
                post_data = {
                    "id": f"{schedule_id}_{posting_time.isoformat()}",
                    "schedule_id": schedule_id,
                    "schedule_name": schedule_name,
                    "media_path": media_item,
                    "scheduled_time": posting_time.isoformat(),
                    "created_time": datetime.now().isoformat(),
                    "status": "scheduled"
                }
                
                # Add to scheduled posts
                self.scheduled_posts.append(post_data)
                self._save_scheduled_posts(self.scheduled_posts)
                
                # Emit signal
                self.signals.post_scheduled.emit(post_data)
                
            # Log success
            if posting_times:
                self.logger.info(f"Scheduled {len(posting_times)} posts for '{schedule_name}'")
                self.signals.status_update.emit(f"Scheduled {len(posting_times)} posts for '{schedule_name}'")
                
        except Exception as e:
            self.logger.error(f"Error processing schedule '{schedule_name}': {e}")
            self.signals.error.emit("Schedule Error", f"Failed to process schedule '{schedule_name}': {str(e)}")
            
    def _get_posting_times(self, schedule: Dict[str, Any], start_date: datetime, end_date: datetime, posts_per_week: int) -> List[datetime]:
        """
        Calculate posting times based on schedule and date range.
        
        Args:
            schedule: Schedule data
            start_date: Start date
            end_date: End date
            posts_per_week: Number of posts per week
            
        Returns:
            List[datetime]: List of posting times
        """
        # This is a simplified implementation
        posting_times = []
        current_date = start_date
        
        while current_date <= end_date:
            # Get hour as a random value between 9 AM and 5 PM
            hour = random.randint(9, 17)
            minute = random.randint(0, 59)
            
            posting_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Skip if the posting time is in the past
            if posting_time > datetime.now():
                posting_times.append(posting_time)
                
            # Move to next day
            current_date += timedelta(days=1)
            
            # Limit to posts_per_week
            if len(posting_times) >= posts_per_week:
                break
                
        return posting_times
        
    def _get_available_items(self) -> List[str]:
        """
        Get available media items for scheduling.
        
        Returns:
            List[str]: List of media file paths
        """
        try:
            media_files = []
            for filename in os.listdir(const.MEDIA_LIBRARY_DIR):
                filepath = os.path.join(const.MEDIA_LIBRARY_DIR, filename)
                if os.path.isfile(filepath):
                    _, ext = os.path.splitext(filename)
                    if ext.lower() in const.SUPPORTED_MEDIA_FORMATS:
                        media_files.append(filepath)
                        
            return media_files
        except Exception as e:
            self.logger.error(f"Error getting available media items: {e}")
            return []
            
    def post_now(self, post_data: Dict[str, Any]) -> bool:
        """
        Post immediately to selected platforms.
        
        Args:
            post_data: Post data including platforms to post to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            platforms = post_data.get("platforms", [])
            if not platforms:
                self.logger.warning("No platforms selected for posting")
                self.signals.warning.emit("Post Error", "No platforms selected for posting")
                return False
                
            media_path = post_data.get("media_path", "")
            if not media_path or not os.path.exists(media_path):
                self.logger.warning(f"Media file not found: {media_path}")
                self.signals.warning.emit("Post Error", "Media file not found")
                return False
                
            caption = post_data.get("caption", "")
            
            # Log the post
            self.logger.info(f"Posting to {', '.join(platforms)}: {media_path}")
            self.signals.status_update.emit(f"Posting to {', '.join(platforms)}: {os.path.basename(media_path)}")
            
            # Placeholder for actual posting logic
            # In a real implementation, this would call the API for each platform
            for platform in platforms:
                # Simulate posting delay
                time.sleep(0.5)
                self.logger.info(f"Posted to {platform}: {media_path}")
                
            # Create result data
            result_data = {
                "id": post_data.get("id", str(uuid.uuid4())),
                "media_path": media_path,
                "caption": caption,
                "platforms": platforms,
                "posted_time": datetime.now().isoformat(),
                "status": "published"
            }
            
            # Emit signal
            self.signals.post_published.emit(result_data)
            self.signals.info.emit("Post Successful", f"Posted to {', '.join(platforms)}")
            
            return True
            
        except Exception as e:
            self.logger.exception(f"Error posting now: {e}")
            self.signals.error.emit("Post Error", f"Failed to post: {str(e)}")
            return False
            
    def add_to_queue(self, post_data: Dict[str, Any]) -> bool:
        """
        Add a post to the next available slot in the queue.
        
        Args:
            post_data: Post data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate post data
            media_path = post_data.get("media_path", "")
            if not media_path or not os.path.exists(media_path):
                self.logger.warning(f"Media file not found: {media_path}")
                self.signals.warning.emit("Queue Error", "Media file not found")
                return False
                
            # Find the next available slot
            # For simplicity, we'll add it to tomorrow at a random time
            tomorrow = datetime.now() + timedelta(days=1)
            # Random time between 9 AM and 5 PM
            posting_time = tomorrow.replace(
                hour=random.randint(9, 17),
                minute=random.randint(0, 59),
                second=0, 
                microsecond=0
            )
            
            # Create post data
            queue_id = str(uuid.uuid4())
            queued_post = {
                "id": queue_id,
                "schedule_id": "manual_queue",
                "schedule_name": "Manual Queue",
                "media_path": media_path,
                "caption": post_data.get("caption", ""),
                "scheduled_time": posting_time.isoformat(),
                "created_time": datetime.now().isoformat(),
                "status": "scheduled",
                "platforms": post_data.get("platforms", ["facebook", "instagram"])
            }
            
            # Add to scheduled posts
            self.scheduled_posts.append(queued_post)
            self._save_scheduled_posts(self.scheduled_posts)
            
            # Sort scheduled posts by scheduled_time
            self.scheduled_posts.sort(key=lambda x: x.get("scheduled_time", ""))
            
            # Emit signal
            self.signals.post_scheduled.emit(queued_post)
            self.signals.info.emit(
                "Queue Successful", 
                f"Post added to queue for {posting_time.strftime('%Y-%m-%d %H:%M')}"
            )
            
            return True
            
        except Exception as e:
            self.logger.exception(f"Error adding to queue: {e}")
            self.signals.error.emit("Queue Error", f"Failed to add to queue: {str(e)}")
            return False 