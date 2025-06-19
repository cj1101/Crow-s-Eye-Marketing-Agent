from fastapi import APIRouter, Depends

from crow_eye_api import models, schemas
from crow_eye_api.api.api_v1.endpoints import login, users, media, galleries, ai, posts, platforms, context_files, schedules, analytics, templates, webhooks, bulk, previews, platform_compliance, enhanced_compliance, google_photos, subscription, youtube, google_services, google_business
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
api_router.include_router(google_photos.router, prefix="/google-photos", tags=["Google Photos"])
api_router.include_router(subscription.router, tags=["Subscription"])
api_router.include_router(youtube.router, prefix="/youtube", tags=["YouTube"])
api_router.include_router(google_services.router, prefix="/google", tags=["Google Services"])
api_router.include_router(google_business.router, prefix="/google-business", tags=["Google My Business"])

# Test Endpoint for Authenticated Users
@api_router.get("/users/me", response_model=schemas.User)
async def read_users_me(
    current_user: models.User = Depends(get_current_active_user),
):
    """Fetch the current logged in user."""
    return current_user

# Auth endpoint for frontend compatibility
@api_router.get("/auth/me")
async def get_auth_me(
    current_user: models.User = Depends(get_current_active_user),
):
    """Get current user data for frontend - includes subscription_tier."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "subscription_tier": getattr(current_user, 'subscription_tier', 'pro'),
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None
    }

# Health check endpoint
@api_router.get("/health", tags=["Health"])
async def health_check():
    """Checks if the API is running."""
    return {"status": "ok"} 