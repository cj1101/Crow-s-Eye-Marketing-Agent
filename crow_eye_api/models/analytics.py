from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from crow_eye_api.database import Base

class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(String, primary_key=True, index=True)
    post_id = Column(String, ForeignKey("posts.id"))
    platform = Column(String, index=True)
    
    # Metrics
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    
    # Additional metrics (platform-specific)
    additional_metrics = Column(JSON, nullable=True)
    
    # Timestamps
    recorded_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    post = relationship("Post", backref="analytics_records")

class AnalyticsSummary(Base):
    __tablename__ = "analytics_summaries"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    platform = Column(String, index=True)
    
    # Date range
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Summary metrics
    total_posts = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    total_likes = Column(Integer, default=0)
    total_comments = Column(Integer, default=0)
    total_shares = Column(Integer, default=0)
    average_engagement_rate = Column(Float, default=0.0)
    
    # Top performing post
    top_performing_post_id = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="analytics_summaries") 