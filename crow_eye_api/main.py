from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import time
import uuid
import traceback
import sys
import os
from contextlib import asynccontextmanager

# Add the parent directory to the Python path to resolve imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# Import with proper module path
from crow_eye_api.core.config import settings
from crow_eye_api.api.api_v1.api import api_router
from crow_eye_api.core.security import RateLimitMiddleware, SecurityHeadersMiddleware, hash_sensitive_data

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/tmp/crow_eye_api.log") if os.access("/tmp", os.W_OK) else logging.NullHandler()
    ]
)

# Set specific loggers to appropriate levels
logging.getLogger("crow_eye_api.api.api_v1.dependencies").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)  # Reduce SQL noise
logger = logging.getLogger("crow_eye_api.main")

# Global error tracking
error_counts = {}

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
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Warning: Could not create database tables: {e}")
        # Don't fail the startup if database is not available
        pass

async def health_check_dependencies():
    """Check health of critical dependencies."""
    health_status = {"database": "unknown", "storage": "unknown"}
    
    try:
        # Test database connection
        from crow_eye_api.database import engine
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        health_status["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = "unhealthy"
    
    try:
        # Test storage if configured
        if settings.GOOGLE_CLOUD_PROJECT and settings.GOOGLE_CLOUD_STORAGE_BUCKET:
            from google.cloud import storage
            client = storage.Client(project=settings.GOOGLE_CLOUD_PROJECT)
            bucket = client.bucket(settings.GOOGLE_CLOUD_STORAGE_BUCKET)
            bucket.exists()  # This will raise if bucket doesn't exist or no access
            health_status["storage"] = "healthy"
        else:
            health_status["storage"] = "not_configured"
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        health_status["storage"] = "unhealthy"
    
    return health_status

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME}")
    logger.info(f"Environment: {'production' if 'appspot.com' in os.environ.get('GAE_SERVICE', '') else 'development'}")
    
    await create_db_and_tables()
    
    # Check dependencies health
    health_status = await health_check_dependencies()
    logger.info(f"Dependency health check: {health_status}")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.PROJECT_NAME}")

# Create FastAPI app instance with lifespan management
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add security middleware first (order matters)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)  # 100 requests per minute
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses

# CORS middleware with production-ready configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "https://localhost:3000",
        "https://localhost:3001",
        "https://crow-eye-api-dot-crows-eye-website.uc.r.appspot.com",
        "https://crows-eye-website.uc.r.appspot.com"
    ] if settings.PROJECT_NAME == "Crow's Eye API - Production" else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

# Request tracking middleware
@app.middleware("http")
async def request_tracking_middleware(request: Request, call_next):
    """Add request tracking and comprehensive logging."""
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Start timing
    start_time = time.time()
    
    # Log request details (sanitize sensitive data)
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    user_agent = request.headers.get("User-Agent", "")[:100]  # Truncate long user agents
    
    logger.info(
        f"Request started: {request.method} {request.url.path} "
        f"[ID: {request_id[:8]}] [IP: {hash_sensitive_data(client_ip)}] "
        f"[UA: {user_agent}]"
    )
    
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add headers to response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        
        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"[ID: {request_id[:8]}] [Status: {response.status_code}] "
            f"[Time: {process_time:.4f}s]"
        )
        
        return response
        
    except Exception as exc:
        # Log errors with request context
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} "
            f"[ID: {request_id[:8]}] [Error: {str(exc)}] "
            f"[Time: {process_time:.4f}s]"
        )
        
        # Track error frequency
        error_key = f"{type(exc).__name__}:{str(exc)[:50]}"
        error_counts[error_key] = error_counts.get(error_key, 0) + 1
        
        raise

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "request_id": request_id[:8],
            "timestamp": time.time()
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    # Create user-friendly error messages
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(x) for x in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation failed",
            "details": errors,
            "request_id": request_id[:8],
            "timestamp": time.time()
        }
    )

@app.exception_handler(StarletteHTTPException)
async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle Starlette HTTP exceptions."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail if hasattr(exc, 'detail') else "Internal server error",
            "request_id": request_id[:8],
            "timestamp": time.time()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    # Log the full traceback for debugging
    logger.error(f"Unhandled exception [ID: {request_id[:8]}]: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "request_id": request_id[:8],
            "timestamp": time.time()
        }
    )

# Include the main API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Root"])
async def read_root():
    """
    A simple root endpoint to confirm the API is running.
    """
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME}!",
        "success": True,
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Comprehensive health check that verifies system status.
    """
    try:
        health_status = await health_check_dependencies()
        
        overall_health = "healthy" if all(
            status in ["healthy", "not_configured"] 
            for status in health_status.values()
        ) else "degraded"
        
        return {
            "success": True,
            "status": overall_health,
            "service": settings.PROJECT_NAME,
            "timestamp": time.time(),
            "dependencies": health_status,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "service": settings.PROJECT_NAME,
            "error": str(e),
            "timestamp": time.time()
        }

@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """
    Basic metrics endpoint for monitoring.
    """
    return {
        "success": True,
        "metrics": {
            "error_counts": dict(list(error_counts.items())[-10:]),  # Last 10 error types
            "total_errors": sum(error_counts.values()),
            "uptime": time.time(),  # This would be more meaningful with actual uptime tracking
        }
    }

@app.get("/test", tags=["Test"])
async def simple_test():
    """
    Very basic test endpoint.
    """
    return {
        "message": "API is working", 
        "status": "ok", 
        "success": True,
        "timestamp": time.time()
    }

# Export for Google App Engine (ASGI)
application = app 