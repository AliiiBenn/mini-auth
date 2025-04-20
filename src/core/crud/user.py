from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import logging

from src.models.user import User
from src.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)

async def get_user_by_email(
    db: AsyncSession,
    email: str,
    project_id: Optional[str] = None
) -> Optional[User]:
    """Get a user by email, scoped by project_id if provided."""
    logger.debug(f"Building query for user email={email}, project_id={project_id}")
    query = select(User).where(
        and_(
            User.email == email,
            User.project_id == project_id
        )
    )
    logger.debug(f"Executing query for user email={email}, project_id={project_id}")
    try:
        result = await db.execute(query)
        logger.debug(f"Query execution finished for user email={email}, project_id={project_id}. Fetching result.")
        user = result.scalar_one_or_none()
        logger.debug(f"Returning user: {bool(user)} for email={email}, project_id={project_id}")
        return user
    except Exception as e:
        logger.exception(f"Exception during get_user_by_email for {email}, project_id={project_id}: {e}")
        raise

async def get_user_by_id(
    db: AsyncSession,
    user_id: str
) -> Optional[User]:
    """Get a user by ID with relationships."""
    query = (
        select(User)
        .options(selectinload(User.refresh_tokens))
        .options(selectinload(User.projects_owned))
        .options(selectinload(User.project_memberships))
        .options(selectinload(User.project))
        .where(User.id == user_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_user(
    db: AsyncSession,
    user_data: UserCreate,
    hashed_password: str,
    project_id: Optional[str] = None
) -> User:
    """Create a new user, associating with project_id if provided."""
    db_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        project_id=project_id
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(
    db: AsyncSession,
    user: User,
    user_data: UserUpdate
) -> User:
    """Update a user's information."""
    update_data = user_data.model_dump(exclude_unset=True, exclude={'project_id'})
    
    for field, value in update_data.items():
        # Skip password as it needs special handling
        if field != "password":
            setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    return user

async def update_user_password(
    db: AsyncSession,
    user: User,
    hashed_password: str
) -> User:
    """Update a user's password."""
    user.hashed_password = hashed_password
    await db.commit()
    await db.refresh(user)
    return user

async def deactivate_user(
    db: AsyncSession,
    user: User
) -> User:
    """Deactivate a user."""
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    return user

async def get_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[str] = None
) -> List[User]:
    """Get a list of users, optionally filtering by project_id."""
    query = select(User).offset(skip).limit(limit)
    query = query.where(User.project_id == project_id)
        
    result = await db.execute(query)
    return list(result.scalars().all()) 