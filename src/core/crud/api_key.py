from typing import Optional, List
from datetime import datetime, UTC
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.project import ProjectApiKey, Project
from src.core.security.tokens import generate_project_api_key

async def create_api_key(
    db: AsyncSession,
    project_id: str,
    name: str
) -> ProjectApiKey:
    """Create a new API key for a project."""
    api_key = ProjectApiKey(
        project_id=project_id,
        key=generate_project_api_key(),
        name=name
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key

async def get_project_api_keys(
    db: AsyncSession,
    project_id: str,
    include_inactive: bool = False
) -> List[ProjectApiKey]:
    """Get all API keys for a project."""
    query = select(ProjectApiKey).where(ProjectApiKey.project_id == project_id)
    if not include_inactive:
        query = query.where(ProjectApiKey.is_active == True)
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_api_key(
    db: AsyncSession,
    key: str,
    load_project: bool = False
) -> Optional[ProjectApiKey]:
    """Get an API key by its value."""
    query = select(ProjectApiKey).where(ProjectApiKey.key == key)
    if load_project:
        query = query.options(selectinload(ProjectApiKey.project))
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def validate_project_api_key(
    db: AsyncSession,
    key: str
) -> Optional[Project]:
    """Validate a project API key and return the associated Project if active."""
    api_key_obj = await get_api_key(db, key, load_project=True)
    if not api_key_obj:
        return None
    if not api_key_obj.is_active:
        return None
    if not api_key_obj.project:
        return None
    if not api_key_obj.project.is_active:
        return None
    
    return api_key_obj.project

async def deactivate_api_key(
    db: AsyncSession,
    key_id: str
) -> bool:
    """Deactivate an API key."""
    query = update(ProjectApiKey).where(
        ProjectApiKey.id == key_id
    ).values(
        is_active=False
    )
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0

async def update_api_key_last_used(
    db: AsyncSession,
    key: str
) -> bool:
    """Update the last_used_at timestamp of an API key."""
    query = update(ProjectApiKey).where(
        ProjectApiKey.key == key
    ).values(
        last_used_at=datetime.now(UTC)
    )
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0 