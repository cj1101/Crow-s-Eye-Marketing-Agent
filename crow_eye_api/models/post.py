from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

from crow_eye_api.database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(String, primary_key=True, index=True)
    media_id = Column(String, index=True)
    caption = Column(Text)
    platforms = Column(JSON)  # Array of platform names
    custom_instructions = Column(Text, nullable=True)
    
    # Formatting options
    formatting = Column(JSON, nullable=True)  # Contains vertical_optimization, caption_overlay, etc.
    
    # Context and scheduling
    context_files = Column(JSON, nullable=True)  # Array of file IDs
    scheduled_time = Column(DateTime, nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurring_pattern = Column(String, nullable=True)  # daily, weekly, monthly
    recurring_end_date = Column(DateTime, nullable=True)
    
    # Status and timestamps
    status = Column(String, default="draft")  # draft, scheduled, published, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_time = Column(DateTime, nullable=True)
    
    # Media information
    media_type = Column(String)  # image, video, audio
    media_url = Column(String)
    
    # Analytics
    analytics = Column(JSON, nullable=True)  # Contains views, likes, comments, shares, engagement_rate
    
    # Foreign key relationships
    user_id = Column(String, ForeignKey("users.id"))
    schedule_id = Column(String, ForeignKey("schedules.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="posts")
    schedule = relationship("Schedule", back_populates="posts") 