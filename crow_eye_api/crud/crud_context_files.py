from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from crow_eye_api import schemas


class CRUDContextFiles:
    async def get_context_file(self, db: AsyncSession, *, file_id: str, user_id: str) -> Optional[Any]:
        """Get a context file by ID (stub implementation)"""
        return None

    async def create_context_file(self, db: AsyncSession, *, file: schemas.ContextFileCreate, user_id: str) -> Any:
        """Create a context file (stub implementation)"""
        return None

    async def get_context_files(self, db: AsyncSession, *, user_id: str, skip: int = 0, limit: int = 50) -> List[Any]:
        """Get context files (stub implementation)"""
        return []


crud_context_files = CRUDContextFiles() 