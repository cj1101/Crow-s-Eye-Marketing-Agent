from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from crow_eye_api.crud import crud_user
from crow_eye_api import schemas
from crow_eye_api.database import get_db

router = APIRouter()

@router.post("/", response_model=schemas.User)
async def create_user(
    user_in: schemas.UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new user.
    """
    user = await crud_user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = await crud_user.create_user(db=db, user=user_in)
    return user 