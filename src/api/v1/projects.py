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
from src.core.crud import api_key as api_key_crud
from src.schemas.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectList,
    ProjectMember,
    ProjectMemberCreate
)
from src.schemas.api_key import ProjectApiKey, ProjectApiKeyCreate
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
            detail="Project not found or not owned by user"
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
            detail="Project not found or not owned by user"
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
            detail="Project not found or not owned by user"
        )
    return {"detail": "Project successfully deleted"}

# Routes pour la gestion des membres du projet

@router.post("/{project_id}/api-keys", response_model=ProjectApiKey, status_code=status.HTTP_201_CREATED)
async def create_project_api_key(
    project_id: str,
    key_data: ProjectApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProjectApiKey:
    """Create a new API key for a project owned by the current user."""
    project = await get_project(db, project_id, owner_id=current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or not owned by user"
        )
    
    db_key = await api_key_crud.create_api_key(
        db=db,
        project_id=project.id,
        name=key_data.name
    )
    return ProjectApiKey.model_validate(db_key)

@router.get("/{project_id}/api-keys", response_model=List[ProjectApiKey])
async def list_project_api_keys(
    project_id: str,
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ProjectApiKey]:
    """List API keys for a project owned by the current user."""
    project = await get_project(db, project_id, owner_id=current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or not owned by user"
        )
        
    db_keys = await api_key_crud.get_project_api_keys(
        db, project_id, include_inactive
    )
    return [ProjectApiKey.model_validate(key) for key in db_keys]

@router.delete("/{project_id}/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_project_api_key(
    project_id: str,
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Deactivate an API key for a project owned by the current user."""
    project = await get_project(db, project_id, owner_id=current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or not owned by user"
        )
        
    success = await api_key_crud.deactivate_api_key(db, key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return None

# Helper function to check project access (owner or member)
async def check_project_access(db: AsyncSession, project_id: str, user_id: str) -> bool:
    project = await get_project(db, project_id)
    if not project:
        return False
    if project.owner_id == user_id:
        return True
    if not any(m.user_id == user_id for m in project.members):
        return False
    return True

@router.post("/{project_id}/members", response_model=ProjectMember)
async def add_member_to_project(
    project_id: str,
    member_data: ProjectMemberCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProjectMember:
    """Add a new member to a project. Requires project ownership."""
    project = await get_project(db, project_id, owner_id=current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add members to this project"
        )

    db_member = await add_project_member(
        db=db,
        project_id=project_id,
        member_data=member_data,
    )
    if not db_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add member (user might exist or not be found)"
        )
    return ProjectMember.model_validate(db_member)

@router.get("/{project_id}/members", response_model=List[ProjectMember])
async def list_project_members(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ProjectMember]:
    """List all members of a project. Requires ownership or membership."""
    project = await get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    is_owner = project.owner_id == current_user.id
    is_member = any(m.user_id == current_user.id for m in project.members) 

    if not is_owner and not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view members of this project"
        )
    
    members = await get_project_members(db, project_id)
    return [ProjectMember.model_validate(m) for m in members]

@router.delete("/{project_id}/members/{user_id}", response_model=Dict[str, str])
async def remove_member_from_project(
    project_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Remove a member from a project. Requires project ownership."""
    project = await get_project(db, project_id, owner_id=current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to remove members from this project"
        )
    
    if project.owner_id == user_id:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove project owner as a member"
        )

    success = await remove_project_member(
        db=db,
        project_id=project_id,
        user_id=user_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in project"
        )
    return {"detail": "Member successfully removed"}

@router.put("/{project_id}/members/{user_id}/role", response_model=ProjectMember)
async def update_member_role(
    project_id: str,
    user_id: str,
    role: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProjectMember:
    """Update a member's role in a project. Requires project ownership."""
    project = await get_project(db, project_id, owner_id=current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update member roles in this project"
        )
        
    if project.owner_id == user_id:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change project owner's role"
        )

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
    )
    if not db_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in project"
        )
    return ProjectMember.model_validate(db_member) 