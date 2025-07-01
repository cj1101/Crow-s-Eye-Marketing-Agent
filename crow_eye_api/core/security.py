from typing import Any, Optional, Dict
from datetime import datetime, timedelta, timezone
import re
import html
import secrets
import hashlib
from collections import defaultdict
import asyncio

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from crow_eye_api.core.config import settings
from crow_eye_api.schemas.user import TokenData

# Password hashing context using Bcrypt with increased rounds for security
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=12  # Increased from default 10 for better security
)

# Rate limiting storage (in production, use Redis)
rate_limit_storage = defaultdict(lambda: defaultdict(list))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain text password."""
    return pwd_context.hash(password)

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validates password strength according to security best practices.
    Returns (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password must be less than 128 characters long"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    # Check for common patterns
    common_patterns = [
        r"123456", r"password", r"qwerty", r"admin", r"letmein",
        r"welcome", r"monkey", r"dragon", r"master", r"hello"
    ]
    
    password_lower = password.lower()
    for pattern in common_patterns:
        if pattern in password_lower:
            return False, f"Password cannot contain common patterns like '{pattern}'"
    
    return True, ""

def sanitize_input(input_str: str, max_length: int = 1000) -> str:
    """
    Sanitizes user input to prevent XSS and injection attacks.
    """
    if not isinstance(input_str, str):
        return ""
    
    # Truncate to max length
    input_str = input_str[:max_length]
    
    # HTML escape
    input_str = html.escape(input_str)
    
    # Remove null bytes and control characters
    input_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', input_str)
    
    return input_str.strip()

def validate_email(email: str) -> bool:
    """Validates email format with comprehensive regex."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email)) and len(email) <= 254

def generate_secure_token(length: int = 32) -> str:
    """Generates a cryptographically secure random token."""
    return secrets.token_urlsafe(length)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a new JWT access token with enhanced security.
    """
    to_encode = data.copy()
    
    # Add security claims
    now = datetime.now(timezone.utc)
    to_encode.update({
        "iat": now,  # Issued at
        "nbf": now,  # Not before
        "jti": generate_secure_token(16),  # JWT ID for token tracking
    })
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[TokenData]:
    """
    Verifies JWT token and returns token data.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return TokenData(username=username)
    except JWTError:
        return None

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent abuse.
    """
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Check rate limit
        if not self.is_allowed(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        response = await call_next(request)
        return response
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers."""
        # Check for proxy headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if client is within rate limits."""
        now = datetime.now()
        
        # Clean old entries
        cutoff = now - timedelta(seconds=self.period)
        rate_limit_storage[client_ip] = [
            timestamp for timestamp in rate_limit_storage[client_ip] 
            if timestamp > cutoff
        ]
        
        # Check current request count
        if len(rate_limit_storage[client_ip]) >= self.calls:
            return False
        
        # Add current request
        rate_limit_storage[client_ip].append(now)
        return True

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to all responses.
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Enhanced Content Security Policy with Swagger UI support
        if request.url.path in ["/docs", "/redoc"]:
            # Relaxed CSP for API documentation pages only
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https: https://fastapi.tiangolo.com; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "object-src 'none'"
            )
            # Relaxed COEP for docs pages
            response.headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"
        else:
            # Strict CSP for all other pages
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "object-src 'none'"
            )
            # Strict COEP for other pages
            response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        
        # Additional security headers
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        # Strict Transport Security (HTTPS only)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

# Custom bearer token security
security = HTTPBearer(auto_error=False)

def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for logging purposes."""
    return hashlib.sha256(data.encode()).hexdigest()[:8]

def has_platform_access(subscription_tier: str) -> bool:
    """
    Check if user has platform access based on subscription tier.
    Only 'free' and 'unenrolled' tiers are blocked from platform features.
    """
    # Valid tiers that have platform access
    VALID_TIERS = {"pro", "growth", "creator", "payg"}
    return subscription_tier.lower() in VALID_TIERS 