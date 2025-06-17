from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, func
from datetime import datetime, timedelta
from ..database import Base

class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class FinishedContent(Base):
    """Storage for finished posts ready for social media"""
    __tablename__ = "finished_content"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Content details
    title = Column(String(255), nullable=False)
    content_type = Column(String(50), nullable=False)  # "post", "image", "video", "gallery"
    file_path = Column(String(500), nullable=True)  # Local file path
    caption = Column(Text, nullable=True)
    hashtags = Column(Text, nullable=True)
    
    # Platforms this content is optimized for
    target_platforms = Column(JSON, nullable=True)  # ["instagram", "tiktok", etc.]
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Auto-cleanup tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=30), nullable=False)
    
    # Status
    is_published = Column(Boolean, default=False, nullable=False)
    publish_date = Column(DateTime, nullable=True)

class GooglePhotosConnection(Base):
    """Google Photos connection info"""
    __tablename__ = "google_photos_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    google_user_id = Column(String(255), nullable=True)
    google_email = Column(String(255), nullable=True)
    connection_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False) 