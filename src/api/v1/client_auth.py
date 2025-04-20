from typing import Annotated, Optional
from datetime import timedelta # Import timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request # Import Request
from sqlalchemy.ext.asyncio import AsyncSession

# Core components
from src.core.database import get_db
from src.core.crud.user import create_user, get_user_by_email, get_user_by_id # Added get_user_by_id
from src.core.security.password import hash_password, is_password_strong, verify_password # Import verify_password
from src.core.dependencies.project_auth import validate_api_key, get_current_client_user # Updated dependencies import
# Import JWT and auth CRUD functions
from src.core.security.jwt import create_access_token, create_refresh_token, decode_token, verify_token_type # Added decode/verify
from src.core.crud.auth import ( # Grouped imports
    create_refresh_token as create_db_refresh_token,
    get_refresh_token, # Added get_refresh_token
    revoke_refresh_token # Added revoke_refresh_token
)
from src.core.config import get_settings # Import settings

# Schemas and Models
from src.schemas.user import UserCreate, UserRead
from src.schemas.auth import Token, ClientLogin, TokenRefresh, TokenPayload # Added TokenRefresh and TokenPayload
from src.models.project import Project
from src.models.user import User

# Get settings instance once at module level
settings = get_settings()

# Define the router for client authentication endpoints
router = APIRouter(
    prefix="/client/auth",
    tags=["client-auth"] # Tag for OpenAPI documentation
)

# --- Client Authentication Endpoints --- 

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_project_user(
    user_data: UserCreate, # Reuse the UserCreate schema
    project: Annotated[Project, Depends(validate_api_key)], # Use dependency to get Project from API Key
    db: AsyncSession = Depends(get_db)
) -> UserRead:
    """Register a new end-user for the specific project identified by the API key."""
    
    # Check if email already exists within this specific project
    existing_user = await get_user_by_email(db, user_data.email, project_id=project.id)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email already registered in project {project.name}"
        )
    
    # Validate password match
    try:
        user_data.validate_passwords_match()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Validate password strength
    if not is_password_strong(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is not strong enough"
        )
    
    # Create the end-user associated with the project
    hashed_password = hash_password(user_data.password)
    # Pass the validated project.id to create_user
    new_user = await create_user(db, user_data, hashed_password, project_id=project.id)
    
    # Return the created user details (excluding password)
    return UserRead.model_validate(new_user)

@router.post("/login", response_model=Token)
async def login_project_user(
    request: Request, # Inject request to get headers
    login_data: ClientLogin, # Use the new ClientLogin schema
    project: Annotated[Project, Depends(validate_api_key)], # Get Project from API Key
    db: AsyncSession = Depends(get_db)
) -> Token:
    """Login an end-user for the specific project identified by the API key."""

    # Find user within the specific project
    user = await get_user_by_email(db, login_data.email, project_id=project.id)
    
    # Validate user and password
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password for this project",
            # No WWW-Authenticate header needed for client API?
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive in this project",
        )
    
    # Create JWT tokens (Access and Refresh)
    # Subject is the globally unique user ID
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    # Get User-Agent for storing refresh token context
    user_agent = request.headers.get("user-agent")

    # Store the refresh token in the database
    await create_db_refresh_token(
        db=db,
        user_id=user.id,
        token=refresh_token,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), # Use config for duration
        user_agent=user_agent,
        # project_id=project.id # Optional: Add project_id if RefreshToken model is scoped
    )
    
    # Return tokens in the response body (no cookies)
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.post("/refresh", response_model=Token)
async def refresh_client_token(
    refresh_data: TokenRefresh, # Get refresh token from body
    project: Annotated[Project, Depends(validate_api_key)], # Validate API Key for context
    db: AsyncSession = Depends(get_db)
) -> Token:
    """Get a new access token using a refresh token for a project end-user."""
    token = refresh_data.refresh_token

    # Check if the refresh token exists and is valid in DB
    db_refresh_token = await get_refresh_token(db, token)
    if not db_refresh_token:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Decode the refresh token to verify type and get user ID
    try:
        if not verify_token_type(token, "refresh"):
             raise HTTPException(status_code=401, detail="Invalid token type")
        payload = decode_token(token) # This also checks expiry
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except HTTPException as e:
        # If decode fails (expired, invalid), revoke from DB and raise
        await revoke_refresh_token(db, token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Refresh token invalid: {e.detail}"
        ) from e

    # Get the user associated with the token
    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # IMPORTANT CHECK: Ensure the user belongs to the project identified by the API Key
    if user.project_id != project.id:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Refresh token does not belong to the specified project",
        )
    
    # Issue a new access token
    new_access_token = create_access_token(subject=user.id)
    
    # No refresh token rotation for now, return original refresh token
    return Token(
        access_token=new_access_token,
        refresh_token=token, # Return the same refresh token
        token_type="bearer"
    )

@router.get("/user", response_model=UserRead)
async def get_client_user_info(
    current_user: Annotated[User, Depends(get_current_client_user)] # Use JWT dependency
) -> UserRead:
    """Get the current authenticated end-user's information."""
    # The dependency already validated the token and fetched the user
    return UserRead.model_validate(current_user)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_client_user(
    refresh_data: TokenRefresh, # Get refresh token from body
    project: Annotated[Project, Depends(validate_api_key)], # Validate API Key for context
    db: AsyncSession = Depends(get_db)
) -> None:
    """Logout end-user by revoking the provided refresh token within the project context."""
    token_to_revoke = refresh_data.refresh_token
    
    # Optional: Decode token to verify user belongs to project before revoking
    try:
        payload = decode_token(token_to_revoke) # Check expiry/validity first
        user_id = payload.get("sub")
        if not user_id:
             raise HTTPException(status_code=400, detail="Invalid token payload")
        
        user = await get_user_by_id(db, user_id)
        if not user or user.project_id != project.id:
             raise HTTPException(status_code=403, detail="Token does not belong to this project")
    except HTTPException:
        # Ignore decoding errors - if token is invalid/expired, just proceed
        # as it might already be invalid in DB or doesn't matter.
        pass 
        
    # Attempt to revoke the token from the database
    # revoke_refresh_token handles the case where the token doesn't exist gracefully
    await revoke_refresh_token(db, token_to_revoke)
    
    return None # Return 204 No Content

# TODO: Add routes like /update, /change-password, /reset-password etc. 