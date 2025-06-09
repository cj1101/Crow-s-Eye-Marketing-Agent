from fastapi import APIRouter, Depends

from crow_eye_api import models, schemas
from .endpoints import login, users, media, galleries, ai
from .dependencies import get_current_active_user

api_router = APIRouter()

# --- Include Routers ---
api_router.include_router(login.router, tags=["Login"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(media.router, prefix="/media", tags=["Media"])
api_router.include_router(galleries.router, prefix="/galleries", tags=["Galleries"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])


# --- Test Endpoint for Authenticated Users ---
@api_router.get("/users/me", response_model=schemas.User)
async def read_users_me(
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Fetch the current logged in user.
    """
    return current_user

# For now, we can add a simple health check endpoint to test things.
@api_router.get("/health", tags=["Health"])
async def health_check():
    """
    Checks if the API is running.
    """
    return {"status": "ok"} 