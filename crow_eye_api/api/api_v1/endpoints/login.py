from datetime import timedelta, datetime
from typing import Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Body, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from crow_eye_api.crud import crud_user
from crow_eye_api import schemas
from crow_eye_api.core import security
from crow_eye_api.core.config import settings
from crow_eye_api.database import get_db
from crow_eye_api.api.api_v1.dependencies import get_current_active_user

router = APIRouter()
logger = logging.getLogger("crow_eye_api.auth")

# Rate limiting for auth endpoints (stricter than global)
auth_rate_limits = {}

def check_auth_rate_limit(request: Request, max_attempts: int = 5, window_minutes: int = 15) -> bool:
    """Check authentication rate limiting per IP."""
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    current_time = datetime.now()
    
    # Clean old attempts
    cutoff_time = current_time - timedelta(minutes=window_minutes)
    if client_ip in auth_rate_limits:
        auth_rate_limits[client_ip] = [
            attempt_time for attempt_time in auth_rate_limits[client_ip] 
            if attempt_time > cutoff_time
        ]
    else:
        auth_rate_limits[client_ip] = []
    
    # Check if limit exceeded
    if len(auth_rate_limits[client_ip]) >= max_attempts:
        return False
    
    # Record this attempt
    auth_rate_limits[client_ip].append(current_time)
    return True

# Frontend-expected authentication endpoints
@router.post("/auth/register", 
             tags=["Authentication"], 
             summary="Register new user",
             description="Register a new user account with email and password validation")
async def register_user(
    user_data: dict = Body(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user - Frontend expects this endpoint.
    Enhanced with comprehensive security checks.
    """
    request_id = getattr(request.state, 'request_id', 'unknown')[:8] if request else 'unknown'
    
    try:
        # Rate limiting check
        if request and not check_auth_rate_limit(request, max_attempts=3, window_minutes=15):
            logger.warning(f"Registration rate limit exceeded [ID: {request_id}]")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many registration attempts. Please try again later."
            )
        
        # Input validation and sanitization
        email = user_data.get("email", "").strip().lower()
        password = user_data.get("password", "")
        name = security.sanitize_input(user_data.get("name", ""), max_length=100)
        
        # Validate required fields
        if not email or not password:
            return {"success": False, "error": "Email and password are required"}
        
        # Validate email format
        if not security.validate_email(email):
            return {"success": False, "error": "Invalid email format"}
        
        # Validate password strength
        is_valid_password, password_error = security.validate_password_strength(password)
        if not is_valid_password:
            logger.info(f"Registration failed - weak password [ID: {request_id}] [Email: {security.hash_sensitive_data(email)}]")
            return {"success": False, "error": password_error}
        
        # Set default name if not provided
        if not name:
            name = email.split("@")[0]
        
        # Check if user already exists
        existing_user = await crud_user.get_user_by_email(db, email=email)
        if existing_user:
            logger.info(f"Registration failed - user exists [ID: {request_id}] [Email: {security.hash_sensitive_data(email)}]")
            return {"success": False, "error": "User with this email already exists"}
        
        # Create user schema
        user_create = schemas.UserCreate(
            email=email,
            password=password,
            full_name=name
        )
        
        # Create user with database error handling
        try:
            user = await crud_user.create_user(db=db, user=user_create)
        except SQLAlchemyError as e:
            logger.error(f"Database error during registration [ID: {request_id}]: {str(e)}")
            return {"success": False, "error": "Registration failed due to database error"}
        
        # Generate tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        refresh_token = security.create_access_token(
            data={"sub": user.email, "type": "refresh"}, expires_delta=timedelta(days=30)
        )
        
        # Format user data for frontend
        user_data = {
            "id": str(user.id),
            "email": user.email,
            "name": user.full_name or user.email.split("@")[0],
            "avatar_url": None,
            "subscription_tier": "free",
            "subscription_status": "active",
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "usage_limits": {
                "posts_per_month": 10,
                "ai_generations": 50,
                "storage_mb": 100
            },
            "plan_features": {
                "basic_posting": True,
                "ai_content": True,
                "analytics": False,
                "team_collaboration": False
            }
        }
        
        logger.info(f"User registered successfully [ID: {request_id}] [Email: {security.hash_sensitive_data(email)}]")
        
        return {
            "success": True,
            "data": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user_data
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration [ID: {request_id}]: {str(e)}")
        return {"success": False, "error": "Registration failed due to server error"}

@router.post("/auth/login",
             tags=["Authentication"],
             summary="User login", 
             description="Authenticate user with email and password")
async def login_user(
    login_data: dict = Body(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Login user - Frontend expects this endpoint.
    Enhanced with security checks and monitoring.
    """
    request_id = getattr(request.state, 'request_id', 'unknown')[:8] if request else 'unknown'
    
    try:
        # Rate limiting check (stricter for login)
        if request and not check_auth_rate_limit(request, max_attempts=5, window_minutes=15):
            logger.warning(f"Login rate limit exceeded [ID: {request_id}]")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )
        
        # Input validation and sanitization
        email = login_data.get("email", "").strip().lower()
        password = login_data.get("password", "")
        
        if not email or not password:
            return {"success": False, "error": "Email and password are required"}
        
        # Validate email format
        if not security.validate_email(email):
            return {"success": False, "error": "Invalid email format"}
        
        # Authenticate user with database error handling
        try:
            user = await crud_user.authenticate_user(db, email=email, password=password)
        except SQLAlchemyError as e:
            logger.error(f"Database error during login [ID: {request_id}]: {str(e)}")
            return {"success": False, "error": "Login failed due to database error"}
        
        if not user:
            logger.info(f"Login failed - invalid credentials [ID: {request_id}] [Email: {security.hash_sensitive_data(email)}]")
            return {"success": False, "error": "Invalid email or password"}
        
        if not user.is_active:
            logger.info(f"Login failed - inactive account [ID: {request_id}] [Email: {security.hash_sensitive_data(email)}]")
            return {"success": False, "error": "Account is deactivated"}
        
        # Generate tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        refresh_token = security.create_access_token(
            data={"sub": user.email, "type": "refresh"}, expires_delta=timedelta(days=30)
        )
        
        # Format user data for frontend
        user_data = {
            "id": str(user.id),
            "email": user.email,
            "name": user.full_name or user.email.split("@")[0],
            "avatar_url": None,
            "subscription_tier": "free",
            "subscription_status": "active",
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "usage_limits": {
                "posts_per_month": 10,
                "ai_generations": 50,
                "storage_mb": 100
            },
            "plan_features": {
                "basic_posting": True,
                "ai_content": True,
                "analytics": False,
                "team_collaboration": False
            }
        }
        
        logger.info(f"User logged in successfully [ID: {request_id}] [Email: {security.hash_sensitive_data(email)}]")
        
        return {
            "success": True,
            "data": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user_data
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login [ID: {request_id}]: {str(e)}")
        return {"success": False, "error": "Login failed due to server error"}

@router.get("/auth/user",
            tags=["Authentication"],
            summary="Get current user",
            description="Get current authenticated user information")
async def get_current_user(
    request: Request = None,
    current_user = Depends(get_current_active_user)
):
    """
    Get current user - Frontend expects this endpoint.
    Enhanced with error handling and logging.
    """
    request_id = getattr(request.state, 'request_id', 'unknown')[:8] if request else 'unknown'
    
    try:
        user_data = {
            "id": str(current_user.id),
            "email": current_user.email,
            "name": current_user.full_name or current_user.email.split("@")[0],
            "avatar_url": None,
            "subscription_tier": "free",
            "subscription_status": "active",
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "usage_limits": {
                "posts_per_month": 10,
                "ai_generations": 50,
                "storage_mb": 100
            },
            "plan_features": {
                "basic_posting": True,
                "ai_content": True,
                "analytics": False,
                "team_collaboration": False
            }
        }
        
        return {"success": True, "data": user_data}
        
    except Exception as e:
        logger.error(f"Error getting current user [ID: {request_id}]: {str(e)}")
        return {"success": False, "error": "Failed to retrieve user information"}

@router.post("/auth/logout",
             tags=["Authentication"],
             summary="User logout",
             description="Logout current user and invalidate session")
async def logout_user(request: Request = None):
    """
    Logout user - Frontend expects this endpoint.
    Enhanced with logging.
    """
    request_id = getattr(request.state, 'request_id', 'unknown')[:8] if request else 'unknown'
    
    try:
        logger.info(f"User logged out [ID: {request_id}]")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error during logout [ID: {request_id}]: {str(e)}")
        return {"success": False, "error": "Logout failed"}

# Keep the original OAuth2 endpoint for backward compatibility
@router.post("/login/access-token", response_model=schemas.Token)
async def login_for_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    Enhanced with security checks.
    """
    request_id = getattr(request.state, 'request_id', 'unknown')[:8] if request else 'unknown'
    
    try:
        # Rate limiting check
        if request and not check_auth_rate_limit(request):
            logger.warning(f"OAuth2 login rate limit exceeded [ID: {request_id}]")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )
        
        # Validate email format
        if not security.validate_email(form_data.username):
            raise HTTPException(
                status_code=400,
                detail="Invalid email format"
            )
        
        user = await crud_user.authenticate_user(
            db, email=form_data.username, password=form_data.password
        )
        if not user:
            logger.info(f"OAuth2 login failed [ID: {request_id}] [Email: {security.hash_sensitive_data(form_data.username)}]")
            raise HTTPException(
                status_code=400,
                detail="Incorrect email or password"
            )
        elif not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        logger.info(f"OAuth2 login successful [ID: {request_id}] [Email: {security.hash_sensitive_data(user.email)}]")
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during OAuth2 login [ID: {request_id}]: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Login failed due to server error"
        ) 