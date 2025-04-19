from fastapi import APIRouter
from .projects import router as projects_router
from .api_keys import router as api_keys_router

router = APIRouter()

router.include_router(projects_router)
router.include_router(api_keys_router) 