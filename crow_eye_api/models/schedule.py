from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from crow_eye_api.database import Base

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    
    # Schedule timing
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    posts_per_day = Column(Integer)
    posting_times = Column(JSON)  # Array of HH:MM strings
    
    # Configuration
    platforms = Column(JSON)  # Array of platform names
    is_active = Column(Boolean, default=True)
    
    # Content sources
    content_sources = Column(JSON)  # Contains media_library, ai_generated, templates
    
    # Rules
    rules = Column(JSON)  # Contains skip_weekends, skip_holidays, minimum_interval
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key
    user_id = Column(String, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", back_populates="schedules")
    posts = relationship("Post", back_populates="schedule") 