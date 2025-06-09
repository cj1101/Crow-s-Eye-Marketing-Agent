from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from crow_eye_api.database import Base


class MediaItem(Base):
    """Database model for media items."""
    __tablename__ = "media_items"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    gcs_path = Column(String(500), nullable=False, unique=True)  # Google Cloud Storage path
    thumbnail_path = Column(String(500), nullable=True)
    
    # Media metadata
    media_type = Column(String(50), nullable=False, index=True)  # image, video, audio
    file_size = Column(Integer, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)  # For videos/audio in seconds
    
    # Content metadata
    caption = Column(Text, nullable=True)
    ai_tags = Column(JSON, nullable=True, default=list)  # List of {tag: str, confidence: float}
    is_post_ready = Column(Boolean, default=False, index=True)
    
    # Timestamps
    upload_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="media_items")
    
    # Gallery relationships (many-to-many through association table)
    galleries = relationship("Gallery", secondary="gallery_media", back_populates="media_items")


class Gallery(Base):
    """Database model for galleries."""
    __tablename__ = "galleries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    caption = Column(Text, nullable=True)
    
    # Timestamps
    created_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="galleries")
    
    # Media relationships (many-to-many through association table)
    media_items = relationship("MediaItem", secondary="gallery_media", back_populates="galleries")


# Association table for many-to-many relationship between Gallery and MediaItem
from sqlalchemy import Table
gallery_media = Table(
    'gallery_media',
    Base.metadata,
    Column('gallery_id', Integer, ForeignKey('galleries.id'), primary_key=True),
    Column('media_id', Integer, ForeignKey('media_items.id'), primary_key=True)
) 