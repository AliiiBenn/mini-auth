from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.middleware.auth import verify_dashboard_token
from src.core.crud import api_key as api_key_crud
from src.schemas.project import ProjectApiKey

router = APIRouter(
    prefix="/dashboard/projects/{project_id}/api-keys",
    tags=["dashboard-api-keys"],
    dependencies=[Depends(verify_dashboard_token)]
)

@router.post("", response_model=ProjectApiKey)
async def create_api_key(
    project_id: str,
    name: str,
    db: AsyncSession = Depends(get_db)
) -> ProjectApiKey:
    """Create a new API key for a project."""
    db_key = await api_key_crud.create_api_key(db, project_id, name)
    return ProjectApiKey.model_validate(db_key)

@router.get("", response_model=List[ProjectApiKey])
async def list_api_keys(
    project_id: str,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db)
) -> List[ProjectApiKey]:
    """List all API keys for a project."""
    db_keys = await api_key_crud.get_project_api_keys(
        db, project_id, include_inactive
    )
    return [ProjectApiKey.model_validate(key) for key in db_keys]

@router.delete("/{key_id}", response_model=bool)
async def deactivate_api_key(
    project_id: str,
    key_id: str,
    db: AsyncSession = Depends(get_db)
) -> bool:
    """Deactivate an API key."""
    success = await api_key_crud.deactivate_api_key(db, key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return True 