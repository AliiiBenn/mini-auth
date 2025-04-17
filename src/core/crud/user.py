from datetime import datetime
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.user import User
from schemas.user import UserCreate, UserUpdate

async def get_user_by_email(
    db: AsyncSession,
    email: str
) -> Optional[User]:
    """Get a user by email."""
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_user_by_id(
    db: AsyncSession,
    user_id: str
) -> Optional[User]:
    """Get a user by ID with relationships."""
    query = (
        select(User)
        .options(selectinload(User.refresh_tokens))
        .options(selectinload(User.projects))
        .where(User.id == user_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_user(
    db: AsyncSession,
    user_data: UserCreate,
    hashed_password: str
) -> User:
    """Create a new user."""
    db_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password
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
    update_data = user_data.model_dump(exclude_unset=True)
    
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
    limit: int = 100
) -> List[User]:
    """Get a list of users."""
    query = (
        select(User)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all()) 