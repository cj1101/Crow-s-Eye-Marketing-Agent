from pydantic import BaseModel, Field, ValidationError, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Union
import os, sys, logging

logger = logging.getLogger("crow_eye_api.config")

class Settings(BaseSettings):
    """
    Application settings.
    
    Uses pydantic-settings to load from .env file.
    """
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'),
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # Database - Using PostgreSQL for production  
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:crowseye2024@/crowseye_db?host=/cloudsql/crows-eye-website:us-central1:crowseye-postgres",
        env="DATABASE_URL"
    )

    # JWT Authentication
    JWT_SECRET_KEY: str = "pfxyGkNmRtHqLvWdZbJcEuPnSgKjDhGfTrYwMxBvNmQpLkJhGfDsEtRyUiOpAsWxCvBnMjKhGfDsEr"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # API details
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Crow's Eye API - PostgreSQL"
    
    # Cleanup settings
    CLEANUP_ENABLED: bool = True
    CONTENT_RETENTION_DAYS: int = 30
    CLEANUP_HOUR: int = 2  # Run cleanup at 2 AM daily
    
    # Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    GOOGLE_CLOUD_STORAGE_BUCKET: Optional[str] = None
    
    # Google AI Services
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Google Photos OAuth2 Configuration
    GOOGLE_PHOTOS_CLIENT_ID: Optional[str] = None
    GOOGLE_PHOTOS_CLIENT_SECRET: Optional[str] = None
    GOOGLE_PHOTOS_REDIRECT_URI: str = "http://localhost:8080/auth/google-photos/callback"

    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None

    # Social Media APIs
    META_APP_ID: Optional[str] = None
    META_APP_SECRET: Optional[str] = None
    TIKTOK_CLIENT_KEY: Optional[str] = None
    PINTEREST_APP_ID: Optional[str] = None

    @validator("JWT_SECRET_KEY")
    def validate_jwt_secret(cls, v):
        """Validate JWT secret key strength and security."""
        if not v:
            logger.error("CRITICAL: JWT_SECRET_KEY is not set!")
            raise ValueError("JWT_SECRET_KEY is required and cannot be empty")
        
        if len(v) < 32:
            logger.error("CRITICAL: JWT_SECRET_KEY is too short!")
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        
        # Check for common weak patterns
        weak_patterns = [
            "secret", "key", "password", "123", "abc", "test", "demo", 
            "default", "change", "your-", "please-change", "example",
            "changeme", "unsafe", "insecure", "weak"
        ]
        
        v_lower = v.lower()
        for pattern in weak_patterns:
            if pattern in v_lower:
                logger.error(f"CRITICAL: JWT_SECRET_KEY contains weak pattern: {pattern}")
                raise ValueError(f"JWT_SECRET_KEY cannot contain weak patterns like '{pattern}'")
        
        # Check for sufficient entropy
        unique_chars = len(set(v))
        if unique_chars < 16:
            logger.error("CRITICAL: JWT_SECRET_KEY lacks sufficient entropy")
            raise ValueError("JWT_SECRET_KEY must have at least 16 unique characters")
        
        logger.info("✅ JWT_SECRET_KEY validation passed")
        return v
    
    @validator("ACCESS_TOKEN_EXPIRE_MINUTES")
    def validate_token_expiry(cls, v):
        """Validate token expiry time is reasonable."""
        if v < 5:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be at least 5 minutes")
        if v > 1440:  # 24 hours
            logger.warning("ACCESS_TOKEN_EXPIRE_MINUTES is very long (>24h), consider shorter expiry")
        return v
    
    @validator("ALGORITHM")
    def validate_algorithm(cls, v):
        """Validate JWT algorithm is secure."""
        secure_algorithms = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
        if v not in secure_algorithms:
            raise ValueError(f"ALGORITHM must be one of: {secure_algorithms}")
        return v

    @staticmethod
    def _critical_env(var: Optional[str], name: str):
        if not var or var.startswith("changeme"):
            logger.error("Critical environment variable %s is not set correctly.", name)
            raise ValueError(f"Environment variable {name} must be set for production")

    def __init__(self, **values):
        super().__init__(**values)

        # Log database configuration for debugging
        logger.info(f"Database URL configured: {self.DATABASE_URL[:50]}...")
        
        # Warn (but don't fail) if GCP vars missing; some local modes don't need them
        if not self.GOOGLE_CLOUD_PROJECT or not self.GOOGLE_CLOUD_STORAGE_BUCKET:
            logger.warning("Google Cloud project / bucket not configured – media uploads disabled.")


settings = Settings() 