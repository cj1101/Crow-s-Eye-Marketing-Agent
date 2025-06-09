from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from crow_eye_api.crud import crud_user
from crow_eye_api import models, schemas
from crow_eye_api.core.config import settings
from crow_eye_api.database import get_db

# Set up logging
logger = logging.getLogger(__name__)

# Bearer token scheme for authentication - auto_error=False to handle errors gracefully
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> models.User:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        logger.error("No credentials provided")
        raise credentials_exception
    
    token = credentials.credentials
    logger.info(f"Attempting to decode token: {token[:20]}...")
    
    # Clean the token - remove any extra "Bearer" prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
        logger.info("Removed extra 'Bearer' prefix from token")
    
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        logger.info(f"Token decoded successfully, payload: {payload}")
        username: str = payload.get("sub")
        if username is None:
            logger.error("No 'sub' field found in token payload")
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
        logger.info(f"Looking up user: {username}")
    except JWTError as e:
        logger.error(f"JWT decoding error: {e}")
        raise credentials_exception
    except ValidationError as e:
        logger.error(f"Token data validation error: {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {e}")
        raise credentials_exception
    
    user = await crud_user.get_user_by_email(db, email=token_data.username)
    if user is None:
        logger.error(f"User not found: {token_data.username}")
        raise credentials_exception
    
    logger.info(f"User found: {user.email}, is_active: {user.is_active}")
    return user


async def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """Get the current active user (must be active)."""
    if not current_user.is_active:
        logger.error(f"User {current_user.email} is not active")
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user 