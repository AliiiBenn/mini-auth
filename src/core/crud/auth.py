from datetime import datetime, timedelta, UTC
from typing import Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import RefreshToken

async def create_refresh_token(
    db: AsyncSession,
    user_id: str,
    token: str,
    expires_delta: timedelta,
    user_agent: Optional[str] = None
) -> RefreshToken:
    """Create a new refresh token."""
    db_token = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=datetime.now(UTC) + expires_delta,
        user_agent=user_agent
    )
    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)
    return db_token

async def get_refresh_token(
    db: AsyncSession,
    token: str
) -> Optional[RefreshToken]:
    """Get a refresh token by its value."""
    query = (
        select(RefreshToken)
        .where(
            and_(
                RefreshToken.token == token,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.now(UTC)
            )
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def revoke_refresh_token(
    db: AsyncSession,
    token: str
) -> bool:
    """Revoke a refresh token."""
    db_token = await get_refresh_token(db, token)
    if not db_token:
        return False
    
    db_token.is_revoked = True
    await db.commit()
    return True

async def revoke_user_refresh_tokens(
    db: AsyncSession,
    user_id: str,
    exclude_token: Optional[str] = None
) -> int:
    """Revoke all refresh tokens for a user."""
    query = select(RefreshToken).where(
        and_(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        )
    )
    
    if exclude_token:
        query = query.where(RefreshToken.token != exclude_token)
    
    result = await db.execute(query)
    tokens = result.scalars().all()
    
    for token in tokens:
        token.is_revoked = True
    
    await db.commit()
    return len(tokens)

async def cleanup_expired_tokens(
    db: AsyncSession
) -> int:
    """Delete expired or revoked refresh tokens."""
    query = select(RefreshToken).where(
        or_(
            RefreshToken.expires_at <= datetime.now(UTC),
            RefreshToken.is_revoked == True
        )
    )
    result = await db.execute(query)
    tokens = result.scalars().all()
    
    for token in tokens:
        await db.delete(token)
    
    await db.commit()
    return len(tokens) 