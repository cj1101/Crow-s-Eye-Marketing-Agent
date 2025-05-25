"""
Analytics handler for Crow's Eye platform.
Tracks internal post performance metrics and provides export functionality.
"""

import os
import json
import csv
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import uuid

from ..config import constants as const


class AnalyticsHandler:
    """Handles internal analytics and performance tracking."""
    
    def __init__(self):
        """Initialize the analytics handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.analytics_file = os.path.join(const.ROOT_DIR, "analytics_data.json")
        self.analytics_data = self._load_analytics_data()
        
    def _load_analytics_data(self) -> Dict[str, Any]:
        """Load analytics data from file."""
        try:
            if os.path.exists(self.analytics_file):
                with open(self.analytics_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading analytics data: {e}")
        
        # Return default structure
        return {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "posts": {},
            "galleries": {},
            "videos": {},
            "summary_stats": {
                "total_posts": 0,
                "total_galleries": 0,
                "total_videos": 0,
                "total_interactions": 0
            }
        }
    
    def _save_analytics_data(self) -> bool:
        """Save analytics data to file."""
        try:
            self.analytics_data["last_updated"] = datetime.now().isoformat()
            with open(self.analytics_file, 'w', encoding='utf-8') as f:
                json.dump(self.analytics_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Error saving analytics data: {e}")
            return False
    
    def track_post_creation(self, media_path: str, post_type: str = "single", 
                           platforms: List[str] = None) -> str:
        """
        Track when a post is created.
        
        Args:
            media_path: Path to the media file
            post_type: Type of post (single, carousel, story)
            platforms: List of platforms posted to
            
        Returns:
            str: Unique post ID for tracking
        """
        try:
            post_id = str(uuid.uuid4())
            platforms = platforms or []
            
            post_data = {
                "id": post_id,
                "media_path": media_path,
                "filename": os.path.basename(media_path),
                "post_type": post_type,
                "platforms": platforms,
                "created_at": datetime.now().isoformat(),
                "metrics": {
                    "views": 0,
                    "likes": 0,
                    "shares": 0,
                    "comments": 0,
                    "saves": 0,
                    "clicks": 0,
                    "reach": 0,
                    "impressions": 0
                },
                "engagement_history": [],
                "status": "created"
            }
            
            self.analytics_data["posts"][post_id] = post_data
            self.analytics_data["summary_stats"]["total_posts"] += 1
            self._save_analytics_data()
            
            self.logger.info(f"Tracked post creation: {post_id}")
            return post_id
            
        except Exception as e:
            self.logger.error(f"Error tracking post creation: {e}")
            return ""
    
    def track_gallery_creation(self, gallery_name: str, media_paths: List[str]) -> str:
        """
        Track when a gallery is created.
        
        Args:
            gallery_name: Name of the gallery
            media_paths: List of media paths in the gallery
            
        Returns:
            str: Unique gallery ID for tracking
        """
        try:
            gallery_id = str(uuid.uuid4())
            
            gallery_data = {
                "id": gallery_id,
                "name": gallery_name,
                "media_paths": media_paths,
                "media_count": len(media_paths),
                "created_at": datetime.now().isoformat(),
                "metrics": {
                    "views": 0,
                    "selections": 0,
                    "posts_created": 0,
                    "avg_engagement": 0
                },
                "usage_history": []
            }
            
            self.analytics_data["galleries"][gallery_id] = gallery_data
            self.analytics_data["summary_stats"]["total_galleries"] += 1
            self._save_analytics_data()
            
            self.logger.info(f"Tracked gallery creation: {gallery_id}")
            return gallery_id
            
        except Exception as e:
            self.logger.error(f"Error tracking gallery creation: {e}")
            return ""
    
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
    
    def update_post_metrics(self, post_id: str, metrics: Dict[str, int]) -> bool:
        """
        Update metrics for a specific post.
        
        Args:
            post_id: ID of the post to update
            metrics: Dictionary of metric updates
            
        Returns:
            bool: True if successful
        """
        try:
            if post_id not in self.analytics_data["posts"]:
                self.logger.warning(f"Post ID not found: {post_id}")
                return False
            
            post_data = self.analytics_data["posts"][post_id]
            
            # Update metrics
            for metric, value in metrics.items():
                if metric in post_data["metrics"]:
                    post_data["metrics"][metric] += value
            
            # Add to engagement history
            engagement_entry = {
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics.copy()
            }
            post_data["engagement_history"].append(engagement_entry)
            
            # Update total interactions
            total_new_interactions = sum(metrics.values())
            self.analytics_data["summary_stats"]["total_interactions"] += total_new_interactions
            
            self._save_analytics_data()
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating post metrics: {e}")
            return False
    
    def simulate_engagement(self, post_id: str) -> bool:
        """
        Simulate engagement metrics for demonstration purposes.
        
        Args:
            post_id: ID of the post to simulate engagement for
            
        Returns:
            bool: True if successful
        """
        try:
            import random
            
            # Generate realistic engagement numbers
            simulated_metrics = {
                "views": random.randint(50, 500),
                "likes": random.randint(5, 50),
                "shares": random.randint(0, 10),
                "comments": random.randint(0, 15),
                "saves": random.randint(0, 20),
                "clicks": random.randint(0, 25),
                "reach": random.randint(40, 400),
                "impressions": random.randint(60, 600)
            }
            
            return self.update_post_metrics(post_id, simulated_metrics)
            
        except Exception as e:
            self.logger.error(f"Error simulating engagement: {e}")
            return False
    
    def get_post_performance(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Get performance data for a specific post.
        
        Args:
            post_id: ID of the post
            
        Returns:
            Dict containing post performance data or None
        """
        try:
            if post_id in self.analytics_data["posts"]:
                return self.analytics_data["posts"][post_id].copy()
            return None
        except Exception as e:
            self.logger.error(f"Error getting post performance: {e}")
            return None
    
    def get_all_posts_performance(self) -> List[Dict[str, Any]]:
        """
        Get performance data for all posts.
        
        Returns:
            List of post performance data
        """
        try:
            return list(self.analytics_data["posts"].values())
        except Exception as e:
            self.logger.error(f"Error getting all posts performance: {e}")
            return []
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics.
        
        Returns:
            Dictionary of summary statistics
        """
        try:
            # Calculate additional stats
            posts = self.analytics_data["posts"]
            
            if posts:
                total_engagement = sum(
                    sum(post["metrics"].values()) 
                    for post in posts.values()
                )
                avg_engagement = total_engagement / len(posts)
                
                # Find top performing post
                top_post = max(
                    posts.values(),
                    key=lambda p: sum(p["metrics"].values()),
                    default=None
                )
            else:
                avg_engagement = 0
                top_post = None
            
            summary = self.analytics_data["summary_stats"].copy()
            summary.update({
                "avg_engagement_per_post": round(avg_engagement, 2),
                "top_performing_post": top_post["filename"] if top_post else "None",
                "last_updated": self.analytics_data.get("last_updated", "Never")
            })
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting summary stats: {e}")
            return {}
    
    def export_to_csv(self, export_path: str = None) -> str:
        """
        Export analytics data to CSV format.
        
        Args:
            export_path: Optional custom export path
            
        Returns:
            str: Path to the exported CSV file
        """
        try:
            if not export_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = os.path.join(const.OUTPUT_DIR, f"analytics_export_{timestamp}.csv")
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            
            with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'post_id', 'filename', 'post_type', 'platforms', 'created_at',
                    'views', 'likes', 'shares', 'comments', 'saves', 'clicks',
                    'reach', 'impressions', 'total_engagement'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for post_id, post_data in self.analytics_data["posts"].items():
                    metrics = post_data["metrics"]
                    total_engagement = sum(metrics.values())
                    
                    row = {
                        'post_id': post_id,
                        'filename': post_data["filename"],
                        'post_type': post_data["post_type"],
                        'platforms': ', '.join(post_data["platforms"]),
                        'created_at': post_data["created_at"],
                        'views': metrics["views"],
                        'likes': metrics["likes"],
                        'shares': metrics["shares"],
                        'comments': metrics["comments"],
                        'saves': metrics["saves"],
                        'clicks': metrics["clicks"],
                        'reach': metrics["reach"],
                        'impressions': metrics["impressions"],
                        'total_engagement': total_engagement
                    }
                    
                    writer.writerow(row)
            
            self.logger.info(f"Analytics data exported to CSV: {export_path}")
            return export_path
            
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {e}")
            return ""
    
    def export_to_json(self, export_path: str = None) -> str:
        """
        Export analytics data to JSON format.
        
        Args:
            export_path: Optional custom export path
            
        Returns:
            str: Path to the exported JSON file
        """
        try:
            if not export_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = os.path.join(const.OUTPUT_DIR, f"analytics_export_{timestamp}.json")
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            
            # Create export data with summary
            export_data = {
                "export_info": {
                    "exported_at": datetime.now().isoformat(),
                    "export_type": "full_analytics",
                    "version": "1.0"
                },
                "summary": self.get_summary_stats(),
                "posts": self.analytics_data["posts"],
                "galleries": self.analytics_data["galleries"],
                "videos": self.analytics_data["videos"]
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Analytics data exported to JSON: {export_path}")
            return export_path
            
        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {e}")
            return ""
    
    def get_performance_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Get performance trends over the specified number of days.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary containing trend data
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            recent_posts = []
            for post_data in self.analytics_data["posts"].values():
                created_at = datetime.fromisoformat(post_data["created_at"])
                if created_at >= cutoff_date:
                    recent_posts.append(post_data)
            
            if not recent_posts:
                return {"message": f"No posts found in the last {days} days"}
            
            # Calculate trends
            total_posts = len(recent_posts)
            total_engagement = sum(
                sum(post["metrics"].values()) 
                for post in recent_posts
            )
            avg_engagement = total_engagement / total_posts if total_posts > 0 else 0
            
            # Group by post type
            type_performance = {}
            for post in recent_posts:
                post_type = post["post_type"]
                if post_type not in type_performance:
                    type_performance[post_type] = {"count": 0, "total_engagement": 0}
                
                type_performance[post_type]["count"] += 1
                type_performance[post_type]["total_engagement"] += sum(post["metrics"].values())
            
            # Calculate averages for each type
            for post_type, data in type_performance.items():
                data["avg_engagement"] = data["total_engagement"] / data["count"]
            
            return {
                "period_days": days,
                "total_posts": total_posts,
                "total_engagement": total_engagement,
                "avg_engagement_per_post": round(avg_engagement, 2),
                "performance_by_type": type_performance,
                "best_performing_type": max(
                    type_performance.items(),
                    key=lambda x: x[1]["avg_engagement"],
                    default=("None", {})
                )[0]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance trends: {e}")
            return {"error": str(e)} 