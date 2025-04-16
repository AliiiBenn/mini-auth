from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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

def project_to_dict(project) -> Dict[str, Any]:
    """Convert a Project SQLAlchemy model to a dictionary to prevent lazy loading issues."""
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "is_active": project.is_active,
        "api_keys": [
            {
                "id": key.id,
                "project_id": key.project_id,
                "key": key.key,
                "name": key.name,
                "created_at": key.created_at,
                "last_used_at": key.last_used_at,
                "is_active": key.is_active
            }
            for key in project.api_keys
        ]
    }

@router.post("", response_model=Project)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db)
) -> Project:
    """Create a new project."""
    db_project = await project_crud.create_project(db, project_data)
    project_dict = project_to_dict(db_project)
    return Project.model_validate(project_dict)

@router.get("", response_model=ProjectList)
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> ProjectList:
    """List all projects with pagination."""
    db_projects = await project_crud.get_projects(db, skip=skip, limit=limit)
    projects = [Project.model_validate(project_to_dict(p)) for p in db_projects]
    return ProjectList(total=len(projects), items=projects)

@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db)
) -> Project:
    """Get a specific project by ID."""
    db_project = await project_crud.get_project(db, project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_dict = project_to_dict(db_project)
    return Project.model_validate(project_dict)

@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
) -> Project:
    """Update a project."""
    db_project = await project_crud.update_project(db, project_id, project_data)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_dict = project_to_dict(db_project)
    return Project.model_validate(project_dict)

@router.delete("/{project_id}", response_model=bool)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db)
) -> bool:
    """Delete a project."""
    success = await project_crud.delete_project(db, project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return True