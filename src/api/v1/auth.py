import logging # Import logging
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security.password import hash_password, verify_password, is_password_strong
from src.core.security.jwt import create_access_token, create_refresh_token
from src.core.crud.user import get_user_by_email, create_user, get_user_by_id
from src.core.crud.auth import create_refresh_token as create_db_refresh_token
from src.core.crud.auth import revoke_refresh_token, revoke_user_refresh_tokens
from src.core.dependencies.auth import get_current_user, validate_refresh_token
from src.schemas.user import UserCreate, UserRead
from src.schemas.auth import Token
from src.models.user import User

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRead)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserRead:
    """Register a new platform user (project_id=None)."""
    # Check if email already exists for platform users (project_id=None)
    existing_user = await get_user_by_email(db, user_data.email, project_id=None)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered for platform user"
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
    
    # Create the platform user (project_id=None)
    hashed_password = hash_password(user_data.password)
    user = await create_user(db, user_data, hashed_password, project_id=None)
    
    return UserRead.model_validate(user)

@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    user_agent: Optional[str] = None # Consider getting user_agent from Request headers
) -> Token:
    """Login platform user (project_id=None) and return tokens."""
    logger.info(f"Attempting login for user: {form_data.username}")
    # Verify platform user (project_id=None)
    user = await get_user_by_email(db, form_data.username, project_id=None)
    logger.info(f"User found: {bool(user)}")
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Login failed: Incorrect email or password for {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"Password verified for user: {user.email}")
    if not user.is_active:
        logger.warning(f"Login failed: User {user.email} is inactive")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"User {user.email} is active. Creating tokens...")
    # Créer les tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    logger.info(f"Tokens created for user: {user.email}")
    
    # Stocker le refresh token en base
    logger.info(f"Storing refresh token for user: {user.email}")
    await create_db_refresh_token(
        db=db,
        user_id=user.id,
        token=refresh_token,
        expires_delta=timedelta(days=7),
        user_agent=user_agent
    )
    logger.info(f"Refresh token stored successfully for user: {user.email}")
    
    # Définir les cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True, # Set to True in production with HTTPS
        samesite="lax",
        max_age=3600  # 1 heure
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True, # Set to True in production with HTTPS
        samesite="lax",
        max_age=604800  # 7 jours
    )
    logger.info(f"Cookies set for user: {user.email}")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    user: User = Depends(validate_refresh_token), # validate_refresh_token uses get_user_by_id, which is fine
    refresh_token: str = "", # Needs to be extracted from cookie or header in validate_refresh_token
    db: AsyncSession = Depends(get_db)
) -> Token:
    """Get a new access token using refresh token for the platform user."""
    # Note: validate_refresh_token ensures the user exists and is active.
    # We might want to add checks here if refresh tokens become project-scoped.
    
    # Créer un nouveau access token
    access_token = create_access_token(subject=user.id)
    
    # Définir le cookie access_token
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True, # Set to True in production with HTTPS
        samesite="lax",
        max_age=3600  # 1 heure
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token if refresh_token else "", # Pass back the original refresh token
        token_type="bearer"
    )

@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: Optional[str] = None, # Needs to be extracted from cookie or header
    current_user: User = Depends(get_current_user), # Optional if only revoking provided token
    db: AsyncSession = Depends(get_db)
):
    """Logout platform user and revoke refresh token if provided."""
    # TODO: Get refresh_token reliably (e.g., from cookie in dependency)
    if refresh_token:
        await revoke_refresh_token(db, refresh_token) 
        # Consider project_id=None if RefreshToken is scoped
    
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
    """Logout platform user from all devices by revoking all their refresh tokens."""
    # revoke_user_refresh_tokens targets user_id, which is correct
    # Consider adding project_id=None if RefreshToken is scoped
    await revoke_user_refresh_tokens(db, current_user.id)
    
    # Supprimer les cookies
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    
    return {"detail": "Successfully logged out from all devices"} 