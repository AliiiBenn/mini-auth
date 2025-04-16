from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.middleware.auth import verify_dashboard_token
from core.crud import project as project_crud
from core.crud import api_key as api_key_crud
from schemas.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectList,
    ProjectApiKey
)

router = APIRouter(
    prefix="/dashboard/projects",
    tags=["dashboard-projects"],
    dependencies=[Depends(verify_dashboard_token)]
)

@router.post("", response_model=Project)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db)
) -> Project:
    """Create a new project."""
    db_project = await project_crud.create_project(db, project_data)
    return Project.model_validate(db_project)

@router.get("", response_model=ProjectList)
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> ProjectList:
    """List all projects with pagination."""
    db_projects = await project_crud.get_projects(db, skip=skip, limit=limit)
    return ProjectList(
        total=len(db_projects),
        items=[Project.model_validate(p) for p in db_projects]
    )

@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Project:
    """Get a specific project by ID."""
    db_project = await project_crud.get_project(db, project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return Project.model_validate(db_project)

@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
) -> Project:
    """Update a project."""
    db_project = await project_crud.update_project(db, project_id, project_data)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return Project.model_validate(db_project)

@router.delete("/{project_id}", response_model=bool)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> bool:
    """Delete a project."""
    success = await project_crud.delete_project(db, project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return True 