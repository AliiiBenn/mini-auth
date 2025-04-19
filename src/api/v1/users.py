from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies.auth import get_current_user
from src.core.middleware.auth import verify_dashboard_token
from src.core.crud.user import get_user_by_id, update_user, update_user_password, get_users
from src.core.security.password import hash_password, verify_password, is_password_strong
from src.schemas.user import UserRead, UserUpdate
from src.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserRead)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserRead:
    """Get current user information."""
    return UserRead.model_validate(current_user)

@router.put("/me", response_model=UserRead)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserRead:
    """Update current user information."""
    # Si un nouveau mot de passe est fourni
    if user_data.password:
        # Vérifier la force du mot de passe
        if not is_password_strong(user_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is not strong enough"
            )
        # Mettre à jour le mot de passe
        hashed_password = hash_password(user_data.password)
        await update_user_password(db, current_user, hashed_password)
        
        # Supprimer le mot de passe du dict de mise à jour
        user_data.password = None
    
    # Mettre à jour les autres informations
    updated_user = await update_user(db, current_user, user_data)
    return UserRead.model_validate(updated_user)

@router.get("/{user_id}", response_model=UserRead)
async def get_user_info(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserRead:
    """Get user information by ID."""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserRead.model_validate(user)

@router.post("/me/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password."""
    # Vérifier le mot de passe actuel
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Vérifier que le nouveau mot de passe est différent
    if current_password == new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    # Vérifier la force du nouveau mot de passe
    if not is_password_strong(new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password is not strong enough"
        )
    
    # Mettre à jour le mot de passe
    hashed_password = hash_password(new_password)
    await update_user_password(db, current_user, hashed_password)
    
    return {"detail": "Password successfully updated"}

@router.get("/all", response_model=List[UserRead], dependencies=[Depends(verify_dashboard_token)])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[UserRead]:
    """Get all users (dashboard only)."""
    users = await get_users(db, skip=skip, limit=limit)
    return [UserRead.model_validate(user) for user in users] 