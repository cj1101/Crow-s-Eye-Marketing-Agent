from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class TemplateVariable(BaseModel):
    name: str
    type: str  # text, number, date, select
    required: bool = True
    options: Optional[List[str]] = None  # For select type

class TemplateContent(BaseModel):
    caption_template: str
    hashtag_template: Optional[str] = None
    formatting: Optional[Dict[str, Any]] = None

class TemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    platforms: List[str]
    template: TemplateContent
    variables: List[TemplateVariable] = []

class TemplateCreate(TemplateBase):
    pass

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    platforms: Optional[List[str]] = None
    template: Optional[TemplateContent] = None
    variables: Optional[List[TemplateVariable]] = None

class Template(TemplateBase):
    id: str
    created_at: datetime
    updated_at: datetime
    user_id: str

    class Config:
        from_attributes = True

class TemplateApplyRequest(BaseModel):
    variables: Dict[str, Any]
    media_id: str

class TemplateApplyResponse(BaseModel):
    caption: str
    hashtags: Optional[str] = None
    formatted_content: Dict[str, Any] 