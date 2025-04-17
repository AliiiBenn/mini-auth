from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security.password import hash_password, verify_password, is_password_strong
from core.security.jwt import create_access_token, create_refresh_token
from core.crud.user import get_user_by_email, create_user, get_user_by_id
from core.crud.auth import create_refresh_token as create_db_refresh_token
from core.crud.auth import revoke_refresh_token, revoke_user_refresh_tokens
from core.dependencies.auth import get_current_user, validate_refresh_token
from schemas.user import UserCreate, UserRead
from schemas.auth import Token
from models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRead)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserRead:
    """Register a new user."""
    # Vérifier si l'email existe déjà
    if await get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Vérifier que les mots de passe correspondent
    try:
        user_data.validate_passwords_match()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Vérifier la force du mot de passe
    if not is_password_strong(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is not strong enough"
        )
    
    # Créer l'utilisateur
    hashed_password = hash_password(user_data.password)
    user = await create_user(db, user_data, hashed_password)
    
    return UserRead.model_validate(user)

@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    user_agent: Optional[str] = None
) -> Token:
    """Login user and return tokens."""
    # Vérifier l'utilisateur
    user = await get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Créer les tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    # Stocker le refresh token en base
    await create_db_refresh_token(
        db=db,
        user_id=user.id,
        token=refresh_token,
        expires_delta=timedelta(days=7),
        user_agent=user_agent
    )
    
    # Définir les cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600  # 1 heure
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=604800  # 7 jours
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    user: User = Depends(validate_refresh_token),
    refresh_token: str = "",
    db: AsyncSession = Depends(get_db)
) -> Token:
    """Get a new access token using refresh token."""
    # Créer un nouveau access token
    access_token = create_access_token(subject=user.id)
    
    # Définir le cookie access_token
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600  # 1 heure
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token if refresh_token else "",
        token_type="bearer"
    )

@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout user and revoke refresh token."""
    if refresh_token:
        await revoke_refresh_token(db, refresh_token)
    
    # Supprimer les cookies
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    
    return {"detail": "Successfully logged out"}

@router.post("/logout-all")
async def logout_all_devices(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout from all devices by revoking all refresh tokens."""
    await revoke_user_refresh_tokens(db, current_user.id)
    
    # Supprimer les cookies
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    
    return {"detail": "Successfully logged out from all devices"} 