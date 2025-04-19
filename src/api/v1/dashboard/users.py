from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.middleware.auth import verify_dashboard_token
from src.core.crud import user as user_crud
from src.schemas.user import UserRead

router = APIRouter(
    prefix="/dashboard/users",
    tags=["dashboard-users"],
    dependencies=[Depends(verify_dashboard_token)]
)

@router.get("", response_model=List[UserRead])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[UserRead]:
    """List all users with pagination."""
    db_users = await user_crud.get_users(db, skip=skip, limit=limit)
    return [UserRead.model_validate(user) for user in db_users] 