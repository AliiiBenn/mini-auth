from typing import Annotated, Optional, cast

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials # Import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.crud.api_key import validate_project_api_key
# Import JWT decode/verify functions and user CRUD
from src.core.security.jwt import decode_token, verify_token_type
from src.core.crud.user import get_user_by_id 
from src.models.project import Project
from src.models.user import User # Import User model

# Shared HTTPBearer scheme
oauth2_scheme_client = HTTPBearer(auto_error=False)

async def validate_api_key(
    x_project_api_key: Annotated[str | None, Header()] = None, # Get key from header
    db: AsyncSession = Depends(get_db)
) -> Project:
    """Dependency to validate the X-Project-Api-Key header and return the active Project."""
    if not x_project_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Project-Api-Key header"
        )

    project = await validate_project_api_key(db, x_project_api_key)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, # Use 403 as the key exists but is invalid/inactive
            detail="Invalid or inactive Project API Key"
        )
    
    # TODO: Consider updating api key last_used_at timestamp here
    # await update_api_key_last_used(db, x_project_api_key) 
    
    return project 

async def get_current_client_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(oauth2_scheme_client)],
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency to get the current client user from JWT access token."""
    if not credentials:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    token = credentials.credentials
    
    # Verify it's an access token
    if not verify_token_type(token, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type, expected access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode token and get user ID
    try:
        payload = decode_token(token)
        user_id = cast(str, payload.get("sub"))
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload") # Re-raise specific error
    except HTTPException as e:
         # Propagate decoding/expiry errors
         raise e
    except Exception:
        # Catch potential general errors during decoding
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Retrieve user from database
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Note: We don't check project_id here. The token grants access based on user ID.
    # Route logic might need further checks if an action requires the user 
    # to belong to a specific project identified by another means (like validate_api_key).
    
    return user 