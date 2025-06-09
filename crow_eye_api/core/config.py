from pydantic_settings import BaseSettings, SettingsConfigDict
import os

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

    # Database
    # Example for PostgreSQL: postgresql+asyncpg://user:password@host:port/dbname
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/crow_eye.db"

    # JWT Authentication
    JWT_SECRET_KEY: str = "a_very_secret_key_that_should_be_changed"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # API details
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Crow's Eye API"
    
    # Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT: str = "your-project-id"
    GOOGLE_CLOUD_STORAGE_BUCKET: str = "your-bucket-name"
    
    # Google AI Services
    GOOGLE_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    # OpenAI Configuration
    OPENAI_API_KEY: str | None = None

    # Social Media APIs
    META_APP_ID: str | None = None
    META_APP_SECRET: str | None = None
    TIKTOK_CLIENT_KEY: str | None = None
    PINTEREST_APP_ID: str | None = None


settings = Settings() 