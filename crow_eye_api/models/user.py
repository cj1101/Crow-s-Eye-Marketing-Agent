from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from crow_eye_api.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean(), default=True, nullable=False)
    subscription_tier = Column(String(50), default="free", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # In a real app, you might have is_superuser, roles, etc.
    # is_superuser = Column(Boolean(), default=False) 
    
    # Relationships
    media_items = relationship("MediaItem", back_populates="user", cascade="all, delete-orphan")
    galleries = relationship("Gallery", back_populates="user", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    finished_content = relationship("FinishedContent", back_populates="user", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="user", cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="user", cascade="all, delete-orphan")
    analytics_summaries = relationship("AnalyticsSummary", back_populates="user", cascade="all, delete-orphan")
    google_photos_connection = relationship("GooglePhotosConnection", back_populates="user", uselist=False, cascade="all, delete-orphan") 