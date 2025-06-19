from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

from crow_eye_api.database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    content = Column(Text, nullable=True)
    image_path = Column(String(500), nullable=True)
    video_path = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON string or comma-separated
    platforms = Column(JSON, nullable=True)  # ["instagram", "tiktok", etc.]
    status = Column(String(50), default="draft", nullable=False)  # draft, published, scheduled
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)

    # Foreign key to User
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="posts")

class FinishedContent(Base):
    """Storage for finished posts ready for social media"""
    __tablename__ = "finished_content"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Content details
    title = Column(String(255), nullable=False)
    content_type = Column(String(50), nullable=False)  # "post", "image", "video", "gallery"
    file_path = Column(String(500), nullable=True)  # Local file path
    caption = Column(Text, nullable=True)
    hashtags = Column(Text, nullable=True)
    
    # Platforms this content is optimized for
    target_platforms = Column(JSON, nullable=True)  # ["instagram", "tiktok", etc.]
    
    # Metadata (renamed to avoid SQLAlchemy conflict)
    meta_data = Column(JSON, nullable=True)
    
    # Auto-cleanup tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=30), nullable=False)
    
    # Status
    is_published = Column(Boolean, default=False, nullable=False)
    publish_date = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="finished_content") 