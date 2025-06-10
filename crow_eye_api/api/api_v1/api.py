from fastapi import APIRouter, Depends

from crow_eye_api import models, schemas
from crow_eye_api.api.api_v1.endpoints import login, users, media, galleries, ai, posts, platforms, context_files, schedules, analytics, templates, webhooks, bulk, previews, platform_compliance, enhanced_compliance
from crow_eye_api.api.api_v1.dependencies import get_current_active_user

api_router = APIRouter()

# Include Routers
api_router.include_router(login.router, tags=["Login"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(media.router, prefix="/media", tags=["Media"])
api_router.include_router(galleries.router, prefix="/galleries", tags=["Galleries"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])
api_router.include_router(posts.router, prefix="/posts", tags=["Posts"])
api_router.include_router(platforms.router, prefix="/platforms", tags=["Platforms"])
api_router.include_router(context_files.router, prefix="/context-files", tags=["Context Files"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["Schedules"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(bulk.router, prefix="/bulk", tags=["Bulk Operations"])
api_router.include_router(previews.router, prefix="/previews", tags=["Platform Previews"])
api_router.include_router(platform_compliance.router, tags=["Platform Compliance"])
api_router.include_router(enhanced_compliance.router, prefix="/compliance", tags=["Enhanced Platform Compliance"])

# Test Endpoint for Authenticated Users
@api_router.get("/users/me", response_model=schemas.User)
async def read_users_me(
    current_user: models.User = Depends(get_current_active_user),
):
    """Fetch the current logged in user."""
    return current_user

# Health check endpoint
@api_router.get("/health", tags=["Health"])
async def health_check():
    """Checks if the API is running."""
    return {"status": "ok"} 