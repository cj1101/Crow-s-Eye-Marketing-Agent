from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from crow_eye_api.core.config import settings

# Create an asynchronous engine
# The 'check_same_thread' argument is only for SQLite
engine_args = {"echo": False}
if "sqlite" in settings.DATABASE_URL:
    engine_args["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(settings.DATABASE_URL, **engine_args)

# Create a configured "Session" class
# This will be the factory for new database sessions
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession
)

# Create a Base class for our models to inherit from
Base = declarative_base()

async def get_db() -> AsyncSession:
    """
    Dependency to get a database session.
    Ensures the session is always closed after the request.
    """
    async with SessionLocal() as session:
        yield session 