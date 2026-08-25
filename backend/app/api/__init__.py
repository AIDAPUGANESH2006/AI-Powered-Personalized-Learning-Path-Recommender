from app.api.auth import router as auth_router
from app.api.catalog import router as catalog_router
from app.api.health import router as health_router
from app.api.profile import router as profile_router

__all__ = ["auth_router", "catalog_router", "health_router", "profile_router"]
