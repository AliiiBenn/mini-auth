from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .projects import router as projects_router
from .client_auth import router as client_auth_router
# from .dashboard import router as dashboard_router # Removed

router = APIRouter(prefix="/api/v1")

# Routes that don't need dashboard authentication
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(projects_router)
router.include_router(client_auth_router)
# router.include_router(dashboard_router) # Removed 