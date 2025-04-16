from fastapi import APIRouter
from .dashboard.projects import router as projects_router
from .dashboard.api_keys import router as api_keys_router

router = APIRouter(prefix="/api/v1")

router.include_router(projects_router)
router.include_router(api_keys_router) 