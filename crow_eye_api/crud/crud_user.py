from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from crow_eye_api.core.security import get_password_hash, verify_password
from crow_eye_api.models.user import User
from crow_eye_api.schemas.user import UserCreate

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """
    Fetches a user from the database by their email address.
    """
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
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
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user 