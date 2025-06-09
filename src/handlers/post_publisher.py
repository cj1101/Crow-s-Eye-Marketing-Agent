"""
Post Publisher Handler - Manages publishing posts to various social media platforms.
"""
import logging
import os
import json
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from PySide6.QtCore import QObject, Signal

from ..api.instagram.instagram_api_handler import InstagramAPIHandler
from ..api.youtube.youtube_api_handler import YouTubeAPIHandler
from ..api.tiktok.tiktok_api_handler import TikTokAPIHandler
from ..config import constants as const

class PublishStatus(Enum):
    PENDING = "pending"
    PUBLISHING = "publishing"
    SUCCESS = "success"
    FAILED = "failed"
    QUEUED = "queued"

@dataclass
class PostJob:
    id: str
    media_path: str
    caption: str
    platforms: List[str]
    status: PublishStatus
    created_at: str
    scheduled_at: Optional[str] = None
    results: Dict[str, Any] = None
    error_message: Optional[str] = None

class PostPublisher(QObject):
    """Handles publishing posts to social media platforms."""
    
    # Signals
    publishing_started = Signal(str)  # job_id
    publishing_progress = Signal(str, str, int)  # job_id, platform, percentage
    publishing_success = Signal(str, str, dict)  # job_id, platform, result
    publishing_failed = Signal(str, str, str)  # job_id, platform, error
    publishing_completed = Signal(str)  # job_id
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize platform handlers
        self.handlers = {
            'instagram': InstagramAPIHandler(),
            'youtube': YouTubeAPIHandler(), 
            'tiktok': TikTokAPIHandler(),
        }
        
        # Job queue and history
        self.active_jobs: Dict[str, PostJob] = {}
        self.job_queue: List[str] = []
        self.job_history: List[PostJob] = []
        
        # Load saved jobs
        self._load_job_history()
        
        # Connect handler signals
        self._connect_handler_signals()
    
    def _connect_handler_signals(self):
        """Connect signals from platform handlers."""
        for platform, handler in self.handlers.items():
            if hasattr(handler, 'signals'):
                handler.signals.upload_started.connect(
                    lambda p=platform: self._on_platform_upload_started(p)
                )
                handler.signals.upload_progress.connect(
                    lambda msg, pct, p=platform: self._on_platform_upload_progress(p, msg, pct)
                )
                handler.signals.upload_success.connect(
                    lambda p, result, platform=platform: self._on_platform_upload_success(platform, result)
                )
                handler.signals.upload_error.connect(
                    lambda p, error, platform=platform: self._on_platform_upload_error(platform, error)
                )
    
    def publish_now(self, media_path: str, caption: str, platforms: List[str]) -> str:
        """
        Publish a post immediately to specified platforms.
        
        Args:
            media_path: Path to the media file
            caption: Post caption/description
            platforms: List of platform names to publish to
            
        Returns:
            Job ID for tracking the publish operation
        """
        import uuid
        from datetime import datetime
        
        job_id = str(uuid.uuid4())
        
        job = PostJob(
            id=job_id,
            media_path=media_path,
            caption=caption,
            platforms=platforms,
            status=PublishStatus.PUBLISHING,
            created_at=datetime.now().isoformat(),
            results={}
        )
        
        self.active_jobs[job_id] = job
        self.publishing_started.emit(job_id)
        
        # Start publishing to each platform
        self._publish_to_platforms(job)
        
        return job_id
    
    def add_to_queue(self, media_path: str, caption: str, platforms: List[str], 
                     scheduled_at: Optional[str] = None) -> str:
        """
        Add a post to the publishing queue.
        
        Args:
            media_path: Path to the media file
            caption: Post caption/description
            platforms: List of platform names to publish to
            scheduled_at: Optional scheduled publish time (ISO format)
            
        Returns:
            Job ID for tracking the queued post
        """
        import uuid
        from datetime import datetime
        
        job_id = str(uuid.uuid4())
        
        job = PostJob(
            id=job_id,
            media_path=media_path,
            caption=caption,
            platforms=platforms,
            status=PublishStatus.QUEUED,
            created_at=datetime.now().isoformat(),
            scheduled_at=scheduled_at,
            results={}
        )
        
        self.active_jobs[job_id] = job
        self.job_queue.append(job_id)
        
        self._save_job_history()
        
        return job_id
    
    def _publish_to_platforms(self, job: PostJob):
        """Publish a job to all specified platforms."""
        for platform in job.platforms:
            try:
                if platform not in self.handlers:
                    self.logger.warning(f"Handler not available for platform: {platform}")
                    self.publishing_failed.emit(job.id, platform, f"Platform {platform} not supported")
                    continue
                
                handler = self.handlers[platform]
                
                # Determine if media is video
                is_video = any(job.media_path.lower().endswith(ext) 
                              for ext in ['.mp4', '.mov', '.avi', '.mkv', '.wmv'])
                
                # Publish to platform
                success, message = handler.post_media(job.media_path, job.caption, is_video)
                
                if success:
                    job.results[platform] = {"status": "success", "message": message}
                    self.publishing_success.emit(job.id, platform, {"message": message})
                else:
                    job.results[platform] = {"status": "failed", "error": message}
                    self.publishing_failed.emit(job.id, platform, message)
                    
            except Exception as e:
                error_msg = f"Error publishing to {platform}: {str(e)}"
                self.logger.exception(error_msg)
                job.results[platform] = {"status": "failed", "error": error_msg}
                self.publishing_failed.emit(job.id, platform, error_msg)
        
        # Update job status
        successful_platforms = [p for p, r in job.results.items() if r.get("status") == "success"]
        failed_platforms = [p for p, r in job.results.items() if r.get("status") == "failed"]
        
        if len(successful_platforms) == len(job.platforms):
            job.status = PublishStatus.SUCCESS
        elif len(failed_platforms) == len(job.platforms):
            job.status = PublishStatus.FAILED
        else:
            job.status = PublishStatus.SUCCESS  # Partial success
        
        # Move to history
        self.job_history.append(job)
        if job.id in self.active_jobs:
            del self.active_jobs[job.id]
        
        self.publishing_completed.emit(job.id)
        self._save_job_history()
    
    def _on_platform_upload_started(self, platform: str):
        """Handle platform upload started."""
        # Find the active job for this platform
        for job in self.active_jobs.values():
            if platform in job.platforms:
                self.publishing_progress.emit(job.id, platform, 0)
                break
    
    def _on_platform_upload_progress(self, platform: str, message: str, percentage: int):
        """Handle platform upload progress."""
        for job in self.active_jobs.values():
            if platform in job.platforms:
                self.publishing_progress.emit(job.id, platform, percentage)
                break
    
    def _on_platform_upload_success(self, platform: str, result: dict):
        """Handle platform upload success."""
        # This is handled in _publish_to_platforms method
        pass
    
    def _on_platform_upload_error(self, platform: str, error: str):
        """Handle platform upload error."""
        # This is handled in _publish_to_platforms method
        pass
    
    def get_job_status(self, job_id: str) -> Optional[PostJob]:
        """Get the status of a specific job."""
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        
        for job in self.job_history:
            if job.id == job_id:
                return job
        
        return None
    
    def get_queue(self) -> List[PostJob]:
        """Get all queued jobs."""
        return [self.active_jobs[job_id] for job_id in self.job_queue 
                if job_id in self.active_jobs]
    
    def get_history(self, limit: int = 50) -> List[PostJob]:
        """Get job history."""
        return self.job_history[-limit:]
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued job."""
        if job_id in self.job_queue:
            self.job_queue.remove(job_id)
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                job.status = PublishStatus.FAILED
                job.error_message = "Job cancelled by user"
                self.job_history.append(job)
                del self.active_jobs[job_id]
            return True
        return False
    
    def is_platform_connected(self, platform: str) -> bool:
        """Check if a platform is properly connected."""
        if platform not in self.handlers:
            return False
        
        handler = self.handlers[platform]
        if hasattr(handler, 'test_connection'):
            success, _ = handler.test_connection()
            return success
        
        return False
    
    def get_connected_platforms(self) -> List[str]:
        """Get list of connected platforms."""
        connected = []
        for platform in self.handlers.keys():
            if self.is_platform_connected(platform):
                connected.append(platform)
        return connected
    
    def _save_job_history(self):
        """Save job history to file."""
        try:
            history_file = os.path.join(const.ROOT_DIR, 'data', 'post_history.json')
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            
            # Convert jobs to dictionaries for JSON serialization
            history_data = []
            for job in self.job_history:
                job_dict = {
                    'id': job.id,
                    'media_path': job.media_path,
                    'caption': job.caption,
                    'platforms': job.platforms,
                    'status': job.status.value,
                    'created_at': job.created_at,
                    'scheduled_at': job.scheduled_at,
                    'results': job.results,
                    'error_message': job.error_message
                }
                history_data.append(job_dict)
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error saving job history: {e}")
    
    def _load_job_history(self):
        """Load job history from file."""
        try:
            history_file = os.path.join(const.ROOT_DIR, 'data', 'post_history.json')
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                self.job_history = []
                for job_dict in history_data:
                    job = PostJob(
                        id=job_dict['id'],
                        media_path=job_dict['media_path'],
                        caption=job_dict['caption'],
                        platforms=job_dict['platforms'],
                        status=PublishStatus(job_dict['status']),
                        created_at=job_dict['created_at'],
                        scheduled_at=job_dict.get('scheduled_at'),
                        results=job_dict.get('results', {}),
                        error_message=job_dict.get('error_message')
                    )
                    self.job_history.append(job)
                    
        except Exception as e:
            self.logger.error(f"Error loading job history: {e}")
            self.job_history = [] 