import logging # Import logging
from datetime import timedelta
from typing import Optional, cast
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
# Remove sync session imports if no longer needed elsewhere
# from sqlalchemy.orm import Session 
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.asyncio import async_sessionmaker 

# Use get_db for async session, remove sync and factory dependencies
from src.core.database import get_db 
from src.core.security.password import hash_password, verify_password, is_password_strong
from src.core.security.jwt import create_access_token, create_refresh_token, decode_token, verify_token_type
# Use async get_user_by_email
from src.core.crud.user import get_user_by_email, create_user, get_user_by_id 
from src.core.crud.auth import (
    create_refresh_token as create_db_refresh_token,
    get_refresh_token,
    revoke_refresh_token,
    revoke_user_refresh_tokens
)
from src.core.dependencies.auth import get_current_user
from src.schemas.user import UserCreate, UserRead
from src.schemas.auth import Token, TokenRefresh
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
    # Arguments without defaults first
    response: Response, 
    request: Request,
    # Arguments with defaults (Depends provides a default factory)
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db), 
) -> Token:
    """Login platform user (project_id=None) and return tokens."""
    user_agent: Optional[str] = request.headers.get("user-agent")
    try:
        logger.info(f"Attempting login for user: {form_data.username}")
        # Verify platform user using the standard async session
        user = await get_user_by_email(db, form_data.username, project_id=None) # Use async db and function
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
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        logger.info(f"Tokens created for user: {user.email}")
        
        # Store the refresh token using the standard async session
        # Remove the 'async with async_session_factory()' block
        logger.info(f"Storing refresh token for user: {user.email} using standard async session")
        await create_db_refresh_token(
            db=db, # Pass the standard async session from Depends(get_db)
            user_id=user.id,
            token=refresh_token,
            expires_delta=timedelta(days=7), # TODO: Use settings
            user_agent=user_agent
        )
        logger.info(f"Refresh token stored successfully for user: {user.email}")
                
        logger.info(f"Returning tokens in response body for user: {user.email}")
    
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    except Exception as e:
        # Log any unexpected exception before raising HTTP 500
        logger.exception(f"Unexpected error during login for {form_data.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during login."
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    # Remove response: Response
    # Accept refresh token from body using TokenRefresh schema
    refresh_data: TokenRefresh, 
    db: AsyncSession = Depends(get_db)
) -> Token:
    """Get a new access token using refresh token provided in the request body."""
    token = refresh_data.refresh_token

    # 1. Check if the refresh token exists and is valid in DB
    db_refresh_token = await get_refresh_token(db, token)
    if not db_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token (DB check)",
        )

    # 2. Decode the refresh token to verify type and get user ID
    try:
        if not verify_token_type(token, "refresh"):
            # Should not happen if DB check passed, but for safety
            raise HTTPException(status_code=401, detail="Invalid token type") 
        payload = decode_token(token) # Checks expiry as well
        user_id = cast(str, payload.get("sub"))
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except HTTPException as e:
        # If decode fails (e.g., expired), revoke from DB and raise
        # This handles cases where the token might be expired but not yet cleaned up
        await revoke_refresh_token(db, token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Refresh token invalid: {e.detail}"
        ) from e

    # 3. Get the user associated with the token
    user = await get_user_by_id(db, user_id)
    # Check user existence and activity (db_refresh_token confirms token validity)
    if not user or not user.is_active:
        # If user is gone or inactive, the refresh token is effectively invalid
        await revoke_refresh_token(db, token) # Revoke the now useless token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # 4. Platform users specific check (ensure user is NOT project-scoped)
    # This check is specific to the platform auth vs client auth
    if user.project_id is not None:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Refresh token belongs to a project user, use client refresh endpoint.",
        )

    # 5. Issue a new access token
    new_access_token = create_access_token(subject=user.id)
    
    # REMOVE Cookie setting
    # response.set_cookie(
    #     key="access_token",
    #     value=access_token,
    #     httponly=True,
    #     secure=True, # Set to True in production with HTTPS
    #     samesite="lax", # Or None if needed, but maybe not required for refresh?
    #     max_age=3600  # 1 heure
    # )
    
    # 6. Return new access token and original refresh token in body
    return Token(
        access_token=new_access_token,
        refresh_token=token, # Return the same refresh token
        token_type="bearer"
    )

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    # Remove response: Response
    # Accept refresh token from body using TokenRefresh schema
    refresh_data: TokenRefresh, 
    # Remove current_user dependency, not needed to revoke a specific token
    # current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None: # Return None for 204 No Content
    """Logout platform user by revoking the provided refresh token."""
    token_to_revoke = refresh_data.refresh_token
    
    # Attempt to revoke the token from the database
    # revoke_refresh_token handles the case where the token doesn't exist gracefully
    revoked = await revoke_refresh_token(db, token_to_revoke)
    logger.info(f"Logout attempt for refresh token: {token_to_revoke[:10]}... Revoked: {revoked}")
    
    # REMOVE Cookie deletion
    # response.delete_cookie(key="access_token")
    # response.delete_cookie(key="refresh_token")
    
    # Return nothing for 204 No Content
    return None

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