from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from crow_eye_api.core.security import get_password_hash, verify_password
from crow_eye_api.models.user import User
from crow_eye_api.schemas.user import UserCreate

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Fetches a user from the database by their email address.
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user.
    """
    user = await get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """
    Creates a new user in the database.
    """
    hashed_password = get_password_hash(user.password)
    # Generate username from email if not provided
    username = user.email.split("@")[0]
    
    # Special handling for specific email addresses
    if user.email.lower() == "charlie@suarezhouse.net":
        subscription_tier = "pro"
    else:
        subscription_tier = "free"
    
    db_user = User(
        email=user.email,
        username=username,
        full_name=user.full_name,
        hashed_password=hashed_password,
        subscription_tier=subscription_tier,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user 