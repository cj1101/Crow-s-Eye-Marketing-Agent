from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from crow_eye_api.database import Base

class Template(Base):
    __tablename__ = "templates"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    category = Column(String, index=True)
    
    # Platform configuration
    platforms = Column(JSON)  # Array of platform names
    
    # Template content
    template = Column(JSON)  # Contains caption_template, hashtag_template, formatting
    
    # Variables definition
    variables = Column(JSON)  # Array of variable definitions with name, type, required, options
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key
    user_id = Column(String, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", back_populates="templates") 