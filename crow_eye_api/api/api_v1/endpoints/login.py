from datetime import timedelta, datetime
from typing import Optional
import logging
import time

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

# Rate limiting for auth endpoints (more lenient)
auth_rate_limits = {}

def check_auth_rate_limit(request: Request, max_attempts: int = 10, window_minutes: int = 15) -> bool:
    """Check authentication rate limiting per IP - more lenient for production."""
    try:
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
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return False
        
        # Record this attempt
        auth_rate_limits[client_ip].append(current_time)
        return True
    except Exception as e:
        logger.error(f"Rate limiting check failed: {e}")
        # If rate limiting fails, allow the request to proceed
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
    Enhanced with comprehensive security checks and better error handling.
    """
    request_id = getattr(request.state, 'request_id', 'unknown')[:8] if request else 'unknown'
    
    try:
        # Rate limiting check (more lenient)
        if request and not check_auth_rate_limit(request, max_attempts=10, window_minutes=15):
            logger.warning(f"Registration rate limit exceeded [ID: {request_id}]")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many registration attempts. Please try again later."
            )
        
        # Input validation and sanitization
        email = user_data.get("email", "").strip().lower()
        password = user_data.get("password", "")
        name = security.sanitize_input(user_data.get("name", ""), max_length=100)
        
        logger.info(f"Registration attempt [ID: {request_id}] [Email: {security.hash_sensitive_data(email)}]")
        
        # Validate required fields
        if not email or not password:
            logger.info(f"Registration failed - missing fields [ID: {request_id}]")
            return {"success": False, "error": "Email and password are required"}
        
        # Validate email format
        if not security.validate_email(email):
            logger.info(f"Registration failed - invalid email [ID: {request_id}]")
            return {"success": False, "error": "Invalid email format"}
        
        # Validate password strength
        is_valid_password, password_error = security.validate_password_strength(password)
        if not is_valid_password:
            logger.info(f"Registration failed - weak password [ID: {request_id}] [Email: {security.hash_sensitive_data(email)}]")
            return {"success": False, "error": password_error}
        
        # Check if user already exists with better error handling
        try:
            existing_user = await crud_user.get_user_by_email(db, email=email)
            if existing_user:
                logger.info(f"Registration failed - user exists [ID: {request_id}] [Email: {security.hash_sensitive_data(email)}]")
                return {"success": False, "error": "User with this email already exists"}
        except SQLAlchemyError as e:
            logger.error(f"Database error checking existing user [ID: {request_id}]: {str(e)}")
            return {"success": False, "error": "Database connection error. Please try again."}
        except Exception as e:
            logger.error(f"Unexpected error checking existing user [ID: {request_id}]: {str(e)}")
            return {"success": False, "error": "Registration temporarily unavailable. Please try again."}
        
        # Create new user with better error handling
        try:
            user_create = schemas.UserCreate(
                email=email,
                password=password,
                full_name=name or email.split("@")[0]
            )
            user = await crud_user.create_user(db, user=user_create)
            
            logger.info(f"User created successfully [ID: {request_id}] [Email: {security.hash_sensitive_data(email)}]")
            
        except SQLAlchemyError as e:
            logger.error(f"Database error creating user [ID: {request_id}]: {str(e)}")
            await db.rollback()
            return {"success": False, "error": "Database error during registration. Please try again."}
        except Exception as e:
            logger.error(f"Unexpected error creating user [ID: {request_id}]: {str(e)}")
            await db.rollback()
            return {"success": False, "error": "Registration failed. Please try again."}
        
        # Generate tokens with error handling
        try:
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = security.create_access_token(
                data={"sub": user.email}, expires_delta=access_token_expires
            )
            refresh_token = security.create_access_token(
                data={"sub": user.email, "type": "refresh"}, 
                expires_delta=timedelta(days=30)
            )
        except Exception as e:
            logger.error(f"Token generation error [ID: {request_id}]: {str(e)}")
            return {"success": False, "error": "Registration completed but login failed. Please try logging in."}
        
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
        return {"success": False, "error": "Registration service temporarily unavailable. Please try again later."}

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
    Enhanced with security checks, monitoring, and better error handling.
    """
    request_id = getattr(request.state, 'request_id', 'unknown')[:8] if request else 'unknown'
    
    try:
        # Rate limiting check (more lenient for login)
        if request and not check_auth_rate_limit(request, max_attempts=10, window_minutes=15):
            logger.warning(f"Login rate limit exceeded [ID: {request_id}]")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )
        
        # Input validation and sanitization
        email = login_data.get("email", "").strip().lower()
        password = login_data.get("password", "")
        
        logger.info(f"Login attempt [ID: {request_id}] [Email: {security.hash_sensitive_data(email)}]")
        
        if not email or not password:
            logger.info(f"Login failed - missing credentials [ID: {request_id}]")
            return {"success": False, "error": "Email and password are required"}
        
        # Validate email format
        if not security.validate_email(email):
            logger.info(f"Login failed - invalid email format [ID: {request_id}]")
            return {"success": False, "error": "Invalid email format"}
        
        # Authenticate user with database error handling
        try:
            user = await crud_user.authenticate_user(db, email=email, password=password)
            if not user:
                logger.info(f"Login failed - invalid credentials [ID: {request_id}] [Email: {security.hash_sensitive_data(email)}]")
                return {"success": False, "error": "Invalid email or password"}
                
        except SQLAlchemyError as e:
            logger.error(f"Database error during login [ID: {request_id}]: {str(e)}")
            return {"success": False, "error": "Database connection error. Please try again."}
        except Exception as e:
            logger.error(f"Authentication error during login [ID: {request_id}]: {str(e)}")
            return {"success": False, "error": "Authentication service temporarily unavailable. Please try again."}
        
        # Generate tokens with error handling
        try:
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            # Include user_id and subscription_tier in JWT
            subscription_tier = getattr(user, 'subscription_tier', 'free')
            access_token = security.create_access_token(
                data={
                    "sub": user.email,
                    "user_id": str(user.id),
                    "subscription_tier": subscription_tier
                }, 
                expires_delta=access_token_expires
            )
            refresh_token = security.create_access_token(
                data={
                    "sub": user.email, 
                    "user_id": str(user.id),
                    "subscription_tier": subscription_tier,
                    "type": "refresh"
                }, 
                expires_delta=timedelta(days=30)
            )
        except Exception as e:
            logger.error(f"Token generation error during login [ID: {request_id}]: {str(e)}")
            return {"success": False, "error": "Login authentication failed. Please try again."}
        
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
        
        logger.info(f"Login successful [ID: {request_id}] [Email: {security.hash_sensitive_data(email)}]")
        
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
        return {"success": False, "error": "Login service temporarily unavailable. Please try again later."}

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
@router.get("/auth/test", tags=["Authentication"])
async def test_auth_endpoint():
    """Test endpoint to verify auth routes are accessible."""
    return {
        "success": True,
        "message": "Authentication endpoints are working",
        "timestamp": time.time()
    }

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
        subscription_tier = getattr(user, 'subscription_tier', 'free')
        access_token = security.create_access_token(
            data={
                "sub": user.email,
                "user_id": str(user.id),
                "subscription_tier": subscription_tier
            }, 
            expires_delta=access_token_expires
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

@router.get("/auth/me",
            tags=["Authentication"],
            summary="Get current user",
            description="Get current authenticated user information")
async def get_current_user_me(
    request: Request = None,
    current_user = Depends(get_current_active_user)
):
    """
    Get current user - Frontend expects /auth/me endpoint.
    Enhanced with full user data and subscription info.
    """
    request_id = getattr(request.state, 'request_id', 'unknown')[:8] if request else 'unknown'
    
    try:
        # Get full subscription details (defaulting to free for now)
        subscription_tier = getattr(current_user, 'subscription_tier', 'free')
        
        user_data = {
            "id": str(current_user.id),
            "email": current_user.email,
            "name": current_user.full_name or current_user.email.split("@")[0],
            "username": current_user.username if hasattr(current_user, 'username') else current_user.email.split("@")[0],
            "avatar_url": None,
            "subscription_tier": subscription_tier,
            "subscription_status": "active",
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "last_login": None,
            "is_verified": True,
            "usage_limits": {
                "posts_per_month": 10 if subscription_tier == 'free' else 100,
                "ai_generations": 50 if subscription_tier == 'free' else 500,
                "storage_mb": 100 if subscription_tier == 'free' else 1000
            },
            "plan_features": {
                "basic_posting": True,
                "ai_content": True,
                "analytics": subscription_tier != 'free',
                "team_collaboration": subscription_tier in ['pro', 'business'],
                "priority_support": subscription_tier == 'business'
            }
        }
        
        logger.info(f"Current user retrieved successfully [ID: {request_id}] [Email: {security.hash_sensitive_data(current_user.email)}]")
        return {"success": True, "data": user_data}
        
    except Exception as e:
        logger.error(f"Error getting current user [ID: {request_id}]: {str(e)}")
        return {"success": False, "error": "Failed to retrieve user information"} 