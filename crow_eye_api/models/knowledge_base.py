"""
Knowledge Base models for managing knowledge files and responder configurations.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .user import User
from ..database import Base

class KnowledgeFile(Base):
    """Knowledge file model for storing uploaded knowledge base files."""
    __tablename__ = "knowledge_files"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    file_type = Column(String, nullable=False)  # txt, md, pdf
    file_size = Column(Integer, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="knowledge_files")

class ResponderConfiguration(Base):
    """Responder configuration model for virtual assistant settings."""
    __tablename__ = "responder_configurations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False, default="Virtual Assistant")
    personality = Column(String, nullable=False, default="Professional, helpful, and friendly")
    capabilities = Column(JSON, nullable=False, default=list)
    business_info = Column(JSON, nullable=False, default=dict)
    knowledge_base = Column(JSON, nullable=False, default=dict)
    escalation_keywords = Column(JSON, nullable=False, default=list)
    response_style = Column(String, nullable=False, default="conversational_professional")
    max_response_length = Column(Integer, nullable=False, default=300)
    greeting_enabled = Column(Boolean, nullable=False, default=True)
    follow_up_enabled = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="responder_configurations")

class ResponderConversation(Base):
    """Responder conversation model for tracking conversations."""
    __tablename__ = "responder_conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    platform_user_id = Column(String, nullable=False)  # WhatsApp/platform user ID
    platform = Column(String, nullable=False)  # whatsapp, instagram, etc.
    conversation_data = Column(JSON, nullable=False, default=dict)
    status = Column(String, nullable=False, default="active")  # active, escalated, closed
    satisfaction_score = Column(Integer, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    escalated_at = Column(DateTime, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="responder_conversations")

class ResponderMessage(Base):
    """Responder message model for storing conversation messages."""
    __tablename__ = "responder_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("responder_conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    intent = Column(String, nullable=True)
    confidence = Column(Integer, nullable=True)
    message_metadata = Column(JSON, nullable=False, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    conversation = relationship("ResponderConversation", backref="messages")

# Add relationships to User model (this will need to be added to user.py)
# User.knowledge_files = relationship("KnowledgeFile", back_populates="user")
# User.responder_configurations = relationship("ResponderConfiguration", back_populates="user") 
# User.responder_conversations = relationship("ResponderConversation", back_populates="user") 