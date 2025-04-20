from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.project import Project, ProjectApiKey, ProjectMember
from src.models.user import User
from src.schemas.project import ProjectCreate, ProjectUpdate, ProjectMemberCreate, ProjectBase
from src.core.security.tokens import generate_project_api_key

async def create_project(
    db: AsyncSession,
    project_data: ProjectBase,
    owner_id: str,
    initial_api_key_name: str = "Default"
) -> Project:
    """Create a new project with an initial API key."""
    # Create project
    db_project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=owner_id
    )
    db.add(db_project)
    await db.flush()
    
    # Save the ID before commit
    project_id = db_project.id
    
    # Create initial API key
    api_key = ProjectApiKey(
        project_id=project_id,
        key=generate_project_api_key(),
        name=initial_api_key_name
    )
    db.add(api_key)
    
    # Commit to save both project and API key
    await db.commit()
    
    # Re-query the project with eager loading to ensure all attributes are loaded
    # Use the previously saved ID instead of accessing it from the expired object
    query = (
        select(Project)
        .options(selectinload(Project.api_keys))
        .options(selectinload(Project.owner))
        .options(selectinload(Project.members))
        .where(Project.id == project_id)
    )
    result = await db.execute(query)
    db_project = result.scalar_one()
    
    return db_project

async def get_project(
    db: AsyncSession,
    project_id: str,
    owner_id: Optional[str] = None
) -> Optional[Project]:
    """Get a project by ID. If owner_id is provided, verify ownership."""
    query = (
        select(Project)
        .options(selectinload(Project.api_keys))
        .options(selectinload(Project.owner))
        .options(selectinload(Project.members))
        .where(Project.id == project_id)
    )
    
    if owner_id:
        query = query.where(Project.owner_id == owner_id)
    
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_user_projects(
    db: AsyncSession,
    owner_id: str,
    skip: int = 0,
    limit: int = 100
) -> List[Project]:
    """Get a list of projects for a specific user."""
    query = (
        select(Project)
        .options(selectinload(Project.api_keys))
        .options(selectinload(Project.owner))
        .options(selectinload(Project.members))
        .where(Project.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_projects(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> List[Project]:
    """Get a list of all projects."""
    query = (
        select(Project)
        .options(selectinload(Project.api_keys))
        .options(selectinload(Project.owner))
        .options(selectinload(Project.members))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())

async def update_project(
    db: AsyncSession,
    project_id: str,
    project_data: ProjectUpdate,
    owner_id: Optional[str] = None
) -> Optional[Project]:
    """Update a project. If owner_id is provided, verify ownership."""
    # Get project with relationships
    query = (
        select(Project)
        .options(selectinload(Project.api_keys))
        .options(selectinload(Project.owner))
        .options(selectinload(Project.members))
        .where(Project.id == project_id)
    )
    
    if owner_id:
        query = query.where(Project.owner_id == owner_id)
    
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        return None
    
    # Update fields
    for field, value in project_data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    
    # Commit changes
    await db.commit()
    
    # Re-query to get a fresh instance with all relationships
    query = (
        select(Project)
        .options(selectinload(Project.api_keys))
        .options(selectinload(Project.owner))
        .options(selectinload(Project.members))
        .where(Project.id == project_id)
    )
    result = await db.execute(query)
    return result.scalar_one()

async def delete_project(
    db: AsyncSession,
    project_id: str,
    owner_id: Optional[str] = None
) -> bool:
    """Delete a project. If owner_id is provided, verify ownership."""
    project = await get_project(db, project_id, owner_id)
    if not project:
        return False
    
    await db.delete(project)
    await db.commit()
    return True

async def add_project_member(
    db: AsyncSession,
    project_id: str,
    member_data: ProjectMemberCreate
) -> Optional[ProjectMember]:
    """Add a new member to a project. Assumes caller has verified ownership."""
    # Vérifier que l'utilisateur existe
    user_result = await db.execute(select(User).where(User.id == member_data.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        # Indicate user not found specifically
        # Raise exception or return a specific value? Returning None for now.
        return None

    # Vérifier si l'utilisateur est déjà membre
    existing_member_result = await db.execute(
        select(ProjectMember).where(
            and_(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == member_data.user_id
            )
        )
    )
    if existing_member_result.scalar_one_or_none():
        # Indicate member already exists
        # Raise exception or return a specific value? Returning None for now.
        return None

    # Créer le nouveau membre
    db_member = ProjectMember(
        project_id=project_id,
        user_id=member_data.user_id,
        role=member_data.role
    )
    db.add(db_member)
    await db.commit()
    await db.refresh(db_member)
    return db_member

async def get_project_members(
    db: AsyncSession,
    project_id: str
) -> List[ProjectMember]:
    """Get all members of a project."""
    query = (
        select(ProjectMember)
        .options(selectinload(ProjectMember.user))
        .where(ProjectMember.project_id == project_id)
    )
    result = await db.execute(query)
    return list(result.scalars().all())

async def remove_project_member(
    db: AsyncSession,
    project_id: str,
    user_id: str
) -> bool:
    """Remove a member from a project. Assumes caller has verified ownership."""
    # Supprimer le membre
    member_result = await db.execute(
        select(ProjectMember)
        .where(
            and_(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            )
        )
    )
    member = member_result.scalar_one_or_none()

    if not member:
        return False # Member not found

    await db.delete(member)
    await db.commit()
    return True

async def update_project_member_role(
    db: AsyncSession,
    project_id: str,
    user_id: str,
    new_role: str
) -> Optional[ProjectMember]:
    """Update a project member's role. Assumes caller has verified ownership."""
    # Mettre à jour le rôle du membre
    member_result = await db.execute(
        select(ProjectMember)
        .where(
            and_(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            )
        )
    )
    member = member_result.scalar_one_or_none()

    if not member:
        return None # Member not found

    member.role = new_role
    await db.commit()
    await db.refresh(member)
    return member 