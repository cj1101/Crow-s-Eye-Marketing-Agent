from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError, OperationalError
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import time
import os

from .core.config import settings

# Create Base here to avoid circular imports
Base = declarative_base()

logger = logging.getLogger("crow_eye_api.database")

# Connection pool configuration based on environment
def get_pool_config():
    """Get database pool configuration based on database URL."""
    if "sqlite" in settings.DATABASE_URL:
        # SQLite doesn't need connection pooling
        return {
            "poolclass": NullPool,
            "connect_args": {"check_same_thread": False}
        }
    else:
        # PostgreSQL/other databases use async-compatible pooling
        return {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_pre_ping": True,
            "pool_recycle": 300,    # Recycle connections every 5 minutes
            "pool_timeout": 30,     # Wait 30 seconds for connection
        }

# Create async engine for PostgreSQL with enhanced configuration
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    **get_pool_config()
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Database health check with retry
async def check_database_health() -> bool:
    """Check if database is healthy and accessible."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            from sqlalchemy import text
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database health check passed")
            return True
        except OperationalError as e:
            logger.warning(f"Database health check failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            break
    
    logger.error("Database health check failed after all retries")
    return False

# Retry decorator for database operations
def with_db_retry(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry database operations with exponential backoff."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (SQLAlchemyError, DisconnectionError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(
                            f"Database operation failed (attempt {attempt + 1}/{max_retries}), "
                            f"retrying in {wait_time}s: {str(e)}"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Database operation failed after {max_retries} attempts: {str(e)}")
                        
            raise last_exception
        return wrapper
    return decorator

@asynccontextmanager
async def get_db_with_retry() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with automatic retry logic."""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Database session error, rolling back: {str(e)}")
        raise
    finally:
        await session.close()

async def get_db():
    """Dependency to get database session with enhanced error handling"""
    session = None
    try:
        session = AsyncSessionLocal()
        yield session
    except OperationalError as e:
        logger.error(f"Database operational error: {e}")
        if session:
            await session.rollback()
        raise SQLAlchemyError("Database connection failed")
    except Exception as e:
        logger.error(f"Database session error: {e}")
        if session:
            await session.rollback()
        raise
    finally:
        if session:
            await session.close()

@with_db_retry(max_retries=3, delay=1.0)
async def create_tables():
    """Create all tables in the database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")

@with_db_retry(max_retries=3, delay=1.0)
async def drop_tables():
    """Drop all tables in the database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("Database tables dropped successfully")

async def init_database():
    """Initialize database with proper error handling."""
    try:
        logger.info("Initializing database...")
        
        # Check if database is accessible
        if not await check_database_health():
            raise Exception("Database is not accessible")
        
        # Create tables
        await create_tables()
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

# Database metrics for monitoring
class DatabaseMetrics:
    """Simple metrics collection for database operations."""
    
    def __init__(self):
        self.connection_attempts = 0
        self.connection_failures = 0
        self.query_count = 0
        self.last_error = None
        self.last_error_time = None
    
    def record_connection_attempt(self):
        self.connection_attempts += 1
    
    def record_connection_failure(self, error: str):
        self.connection_failures += 1
        self.last_error = error
        self.last_error_time = time.time()
    
    def record_query(self):
        self.query_count += 1
    
    def get_metrics(self) -> dict:
        return {
            "connection_attempts": self.connection_attempts,
            "connection_failures": self.connection_failures,
            "success_rate": (
                (self.connection_attempts - self.connection_failures) / self.connection_attempts
                if self.connection_attempts > 0 else 0
            ),
            "query_count": self.query_count,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time
        }

# Global metrics instance
db_metrics = DatabaseMetrics()

# Enhanced session maker with metrics
class MetricsAsyncSession(AsyncSession):
    """AsyncSession with metrics collection."""
    
    async def execute(self, *args, **kwargs):
        db_metrics.record_query()
        return await super().execute(*args, **kwargs)

# Update session maker to use metrics  
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=MetricsAsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
) 