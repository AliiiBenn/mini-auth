from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies.auth import get_current_user
from src.core.crud.project import (
    create_project,
    get_project,
    get_user_projects,
    update_project,
    delete_project,
    add_project_member,
    get_project_members,
    remove_project_member,
    update_project_member_role
)
from src.schemas.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectList,
    ProjectMember,
    ProjectMemberCreate
)
from src.models.user import User

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("", response_model=Project)
async def create_user_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Project:
    """Create a new project for the current user."""
    db_project = await create_project(
        db=db,
        project_data=project_data,
        owner_id=current_user.id
    )
    return Project.model_validate(db_project)

@router.get("", response_model=ProjectList)
async def list_user_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProjectList:
    """List all projects owned by the current user."""
    projects = await get_user_projects(
        db=db,
        owner_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return ProjectList(
        total=len(projects),
        items=[Project.model_validate(p) for p in projects]
    )

@router.get("/{project_id}", response_model=Project)
async def get_user_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Project:
    """Get a specific project owned by the current user."""
    db_project = await get_project(db, project_id, current_user.id)
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return Project.model_validate(db_project)

@router.put("/{project_id}", response_model=Project)
async def update_user_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Project:
    """Update a specific project owned by the current user."""
    db_project = await update_project(
        db=db,
        project_id=project_id,
        project_data=project_data,
        owner_id=current_user.id
    )
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return Project.model_validate(db_project)

@router.delete("/{project_id}", response_model=Dict[str, str])
async def delete_user_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Delete a specific project owned by the current user."""
    success = await delete_project(
        db=db,
        project_id=project_id,
        owner_id=current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return {"detail": "Project successfully deleted"}

# Routes pour la gestion des membres du projet

@router.post("/{project_id}/members", response_model=ProjectMember)
async def add_member_to_project(
    project_id: str,
    member_data: ProjectMemberCreate,
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db)
) -> ProjectMember:
    """Add a new member to a project using API key authentication."""
    db_member = await add_project_member(
        db=db,
        project_id=project_id,
        member_data=member_data,
        api_key=x_api_key
    )
    if not db_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or invalid API key or user already a member"
        )
    return ProjectMember.model_validate(db_member)

@router.get("/{project_id}/members", response_model=List[ProjectMember])
async def list_project_members(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ProjectMember]:
    """List all members of a project."""
    # Vérifier que l'utilisateur est propriétaire ou membre du projet
    project = await get_project(db, project_id)
    if not project or (
        project.owner_id != current_user.id and
        not any(m.user_id == current_user.id for m in project.members)
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    members = await get_project_members(db, project_id)
    return [ProjectMember.model_validate(m) for m in members]

@router.delete("/{project_id}/members/{user_id}", response_model=Dict[str, str])
async def remove_member_from_project(
    project_id: str,
    user_id: str,
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Remove a member from a project using API key authentication."""
    success = await remove_project_member(
        db=db,
        project_id=project_id,
        user_id=user_id,
        api_key=x_api_key
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or invalid API key or member not found"
        )
    return {"detail": "Member successfully removed"}

@router.put("/{project_id}/members/{user_id}/role", response_model=ProjectMember)
async def update_member_role(
    project_id: str,
    user_id: str,
    role: str,
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db)
) -> ProjectMember:
    """Update a member's role in a project using API key authentication."""
    if role not in ["member", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'member' or 'admin'"
        )
    
    db_member = await update_project_member_role(
        db=db,
        project_id=project_id,
        user_id=user_id,
        new_role=role,
        api_key=x_api_key
    )
    if not db_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or invalid API key or member not found"
        )
    return ProjectMember.model_validate(db_member) 