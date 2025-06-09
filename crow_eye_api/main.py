from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

import sys
import os

# Add the parent directory to the Python path to resolve imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# Import with proper module path
from crow_eye_api.core.config import settings
from crow_eye_api.api.api_v1.api import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

# Set specific loggers to INFO level for debugging
logging.getLogger("crow_eye_api.api.api_v1.dependencies").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)

async def create_db_and_tables():
    """
    Creates all database tables defined in the models.
    This is called on application startup.
    """
    try:
        from crow_eye_api.database import engine, Base
        from crow_eye_api import models  # Import models to ensure they are registered with Base
        
        async with engine.begin() as conn:
            # In a production scenario, you would use Alembic for migrations.
            # For this project, we'll just create all tables.
            # This will not drop or modify existing tables, only create new ones.
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Warning: Could not create database tables: {e}")
        # Don't fail the startup if database is not available
        pass

# Create FastAPI app instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.on_event("startup")
async def on_startup():
    """
    Event handler for application startup.
    """
    await create_db_and_tables()

# Set all CORS enabled origins
# In production, you should restrict this to your actual frontend domain
# For example: origins=["https://www.crowseye.com", "https://app.crowseye.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the main API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Root"])
async def read_root():
    """
    A simple root endpoint to confirm the API is running.
    """
    return {"message": f"Welcome to the {settings.PROJECT_NAME}!"}

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Simple health check that doesn't depend on database.
    """
    return {"status": "healthy", "service": settings.PROJECT_NAME} 