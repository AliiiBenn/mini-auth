from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.project import Project, ProjectApiKey
from schemas.project import ProjectCreate, ProjectUpdate
from core.security.tokens import generate_project_api_key

async def create_project(
    db: AsyncSession,
    project_data: ProjectCreate,
    initial_api_key_name: str = "Default"
) -> Project:
    """Create a new project with an initial API key."""
    # Create project
    db_project = Project(
        name=project_data.name,
        description=project_data.description,
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
        .where(Project.id == project_id)
    )
    result = await db.execute(query)
    db_project = result.scalar_one()
    
    return db_project

async def get_project(
    db: AsyncSession,
    project_id: str
) -> Optional[Project]:
    """Get a project by ID."""
    query = (
        select(Project)
        .options(selectinload(Project.api_keys))
        .where(Project.id == project_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_projects(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> List[Project]:
    """Get a list of projects with pagination."""
    query = (
        select(Project)
        .options(selectinload(Project.api_keys))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())

async def update_project(
    db: AsyncSession,
    project_id: str,
    project_data: ProjectUpdate
) -> Optional[Project]:
    """Update a project."""
    # Get project with relationships
    query = (
        select(Project)
        .options(selectinload(Project.api_keys))
        .where(Project.id == project_id)
    )
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
    # Don't use the expired project object
    query = (
        select(Project)
        .options(selectinload(Project.api_keys))
        .where(Project.id == project_id)
    )
    result = await db.execute(query)
    return result.scalar_one()

async def delete_project(
    db: AsyncSession,
    project_id: str
) -> bool:
    """Delete a project."""
    project = await get_project(db, project_id)
    if not project:
        return False
    
    await db.delete(project)
    await db.commit()
    return True 