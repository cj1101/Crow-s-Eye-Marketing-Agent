from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class ContextFileCreate(BaseModel):
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    text_content: str
    description: Optional[str] = None

class ContextFileResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=str(obj.id),
            user_id=str(obj.user_id),
            filename=obj.filename,
            original_filename=obj.original_filename,
            content_type=obj.content_type,
            file_size=obj.file_size,
            description=obj.description,
            created_at=obj.created_at,
            updated_at=obj.updated_at
        ) 