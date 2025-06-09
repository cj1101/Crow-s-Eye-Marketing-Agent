from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from crow_eye_api.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)
    # In a real app, you might have is_superuser, roles, etc.
    # is_superuser = Column(Boolean(), default=False) 
    
    # Relationships
    media_items = relationship("MediaItem", back_populates="user", cascade="all, delete-orphan")
    galleries = relationship("Gallery", back_populates="user", cascade="all, delete-orphan") 