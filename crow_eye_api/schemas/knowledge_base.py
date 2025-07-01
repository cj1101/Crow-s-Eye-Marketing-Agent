"""
Schemas for Knowledge Base and Responder functionality.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# Knowledge File schemas
class KnowledgeFileBase(BaseModel):
    """Base schema for knowledge files."""
    original_filename: str
    file_type: str = Field(..., pattern="^(txt|md|pdf)$")

class KnowledgeFileCreate(KnowledgeFileBase):
    """Schema for creating knowledge files."""
    content: str
    file_size: int

class KnowledgeFileUpdate(BaseModel):
    """Schema for updating knowledge files."""
    content: Optional[str] = None
    original_filename: Optional[str] = None

class KnowledgeFileResponse(KnowledgeFileBase):
    """Schema for knowledge file responses."""
    id: str
    user_id: str
    filename: str
    file_size: int
    upload_timestamp: datetime
    content: Optional[str] = None  # Optional to avoid sending large content by default

    class Config:
        from_attributes = True

class KnowledgeFileListResponse(BaseModel):
    """Schema for knowledge file list responses."""
    files: List[KnowledgeFileResponse]
    total: int

# Responder Configuration schemas
class ResponderConfigurationBase(BaseModel):
    """Base schema for responder configuration."""
    name: str = "Virtual Assistant"
    personality: str = "Professional, helpful, and friendly"
    capabilities: List[str] = []
    business_info: Dict[str, Any] = {}
    knowledge_base: Dict[str, Any] = {}
    escalation_keywords: List[str] = []
    response_style: str = "conversational_professional"
    max_response_length: int = 300
    greeting_enabled: bool = True
    follow_up_enabled: bool = True
    is_active: bool = True

class ResponderConfigurationCreate(ResponderConfigurationBase):
    """Schema for creating responder configuration."""
    pass

class ResponderConfigurationUpdate(BaseModel):
    """Schema for updating responder configuration."""
    name: Optional[str] = None
    personality: Optional[str] = None
    capabilities: Optional[List[str]] = None
    business_info: Optional[Dict[str, Any]] = None
    knowledge_base: Optional[Dict[str, Any]] = None
    escalation_keywords: Optional[List[str]] = None
    response_style: Optional[str] = None
    max_response_length: Optional[int] = None
    greeting_enabled: Optional[bool] = None
    follow_up_enabled: Optional[bool] = None
    is_active: Optional[bool] = None

class ResponderConfigurationResponse(ResponderConfigurationBase):
    """Schema for responder configuration responses."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Responder Conversation schemas
class ResponderConversationBase(BaseModel):
    """Base schema for responder conversations."""
    platform_user_id: str
    platform: str
    conversation_data: Dict[str, Any] = {}
    status: str = "active"
    satisfaction_score: Optional[int] = None

class ResponderConversationCreate(ResponderConversationBase):
    """Schema for creating responder conversations."""
    pass

class ResponderConversationUpdate(BaseModel):
    """Schema for updating responder conversations."""
    status: Optional[str] = None
    satisfaction_score: Optional[int] = None
    conversation_data: Optional[Dict[str, Any]] = None

class ResponderConversationResponse(ResponderConversationBase):
    """Schema for responder conversation responses."""
    id: str
    user_id: str
    started_at: datetime
    last_activity: datetime
    escalated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Responder Message schemas
class ResponderMessageBase(BaseModel):
    """Base schema for responder messages."""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    intent: Optional[str] = None
    confidence: Optional[int] = None
    message_metadata: Dict[str, Any] = {}

class ResponderMessageCreate(ResponderMessageBase):
    """Schema for creating responder messages."""
    conversation_id: str

class ResponderMessageResponse(ResponderMessageBase):
    """Schema for responder message responses."""
    id: str
    conversation_id: str
    timestamp: datetime

    class Config:
        from_attributes = True

# Request/Response schemas for responder operations
class MessageProcessRequest(BaseModel):
    """Schema for processing incoming messages."""
    platform_user_id: str
    platform: str = "whatsapp"
    message: str
    context: Dict[str, Any] = {}

class MessageProcessResponse(BaseModel):
    """Schema for message processing responses."""
    response: str
    intent: str
    confidence: float
    escalated: bool
    conversation_id: str
    metadata: Dict[str, Any] = {}

class ConversationListResponse(BaseModel):
    """Schema for conversation list responses."""
    conversations: List[ResponderConversationResponse]
    total: int
    active_count: int
    escalated_count: int

class ConversationDetailResponse(BaseModel):
    """Schema for detailed conversation responses."""
    conversation: ResponderConversationResponse
    messages: List[ResponderMessageResponse]
    total_messages: int

# Knowledge Base Management schemas
class KnowledgeBaseUploadRequest(BaseModel):
    """Schema for knowledge base file upload requests."""
    file_content: str
    filename: str
    file_type: str = Field(..., pattern="^(txt|md|pdf)$")

class KnowledgeBaseSearchRequest(BaseModel):
    """Schema for knowledge base search requests."""
    query: str
    limit: int = 10

class KnowledgeBaseSearchResponse(BaseModel):
    """Schema for knowledge base search responses."""
    results: List[Dict[str, Any]]
    total: int
    query: str

# Bulk operations
class BulkKnowledgeFileDeleteRequest(BaseModel):
    """Schema for bulk deleting knowledge files."""
    file_ids: List[str]

class BulkKnowledgeFileDeleteResponse(BaseModel):
    """Schema for bulk delete responses."""
    deleted_count: int
    errors: List[str] = []

# Responder analytics
class ResponderAnalyticsRequest(BaseModel):
    """Schema for responder analytics requests."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    platform: Optional[str] = None

class ResponderAnalyticsResponse(BaseModel):
    """Schema for responder analytics responses."""
    total_conversations: int
    active_conversations: int
    escalated_conversations: int
    average_response_time: float
    satisfaction_scores: Dict[str, int]
    top_intents: List[Dict[str, Any]]
    platform_breakdown: Dict[str, int]
    period: Dict[str, Any] 