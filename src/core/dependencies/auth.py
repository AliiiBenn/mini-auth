from typing import Optional, cast
from fastapi import Depends, HTTPException, status, Cookie, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
import logging # Import logging

from src.core.database import get_async_session_factory
from src.core.security.jwt import decode_token, verify_token_type
from src.core.crud.user import get_user_by_id
from src.models.user import User

# Setup logger for this module
logger = logging.getLogger(__name__)

# Configuration du bearer token
oauth2_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    async_session_factory: async_sessionmaker[AsyncSession] = Depends(get_async_session_factory),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
    access_token: Optional[str] = Cookie(None, alias="access_token")
) -> User:
    """
    Dépendance pour obtenir l'utilisateur actuel à partir du token JWT.
    Vérifie d'abord le header Authorization, puis le cookie access_token.
    Crée sa propre session DB à partir de la factory.
    """
    logger.debug("Attempting to get current user (using factory-created session)...")
    # Récupérer le token soit du header soit du cookie
    token = credentials.credentials if credentials else access_token
    logger.debug(f"Token source: {'Header' if credentials else 'Cookie' if access_token else 'None'}")
    
    if not token:
        logger.warning("Authentication failed: No token provided.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Vérifier que c'est un access token
    logger.debug("Verifying token type...")
    is_access_token = verify_token_type(token, "access")
    logger.debug(f"Is access token: {is_access_token}")
    if not is_access_token:
        logger.warning("Authentication failed: Invalid token type (expected access).")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Décoder le token
    user_id: Optional[str] = None
    try:
        logger.debug("Decoding token...")
        payload = decode_token(token)
        user_id = cast(str, payload.get("sub"))
        logger.debug(f"Token decoded successfully. User ID: {user_id}")
    except HTTPException as e:
        logger.warning(f"Token decoding failed: {e.detail}") 
        raise e 
    except Exception as e:
        logger.exception("Unexpected error during token decoding.")
        raise HTTPException(
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             detail="Error processing token."
        )

    if not user_id:
        logger.warning("Authentication failed: No user ID (sub) in token payload.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Récupérer l'utilisateur en utilisant une session créée localement
    user: Optional[User] = None
    try:
        logger.debug(f"Creating local session from factory for user ID: {user_id}...")
        async with async_session_factory() as session:
            logger.debug(f"Fetching user with ID: {user_id} using local session...")
            user = await get_user_by_id(session, user_id) # Pass the local session
            logger.debug(f"Local session fetch complete. User found: {bool(user)}")
    except Exception as e:
        logger.exception(f"Database error while fetching user ID: {user_id} using local session")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error retrieving user."
        )

    if not user:
        logger.warning(f"Authentication failed: User with ID {user_id} not found in DB.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug(f"Checking if user {user_id} is active...")
    if not user.is_active:
        logger.warning(f"Authentication failed: User {user_id} is inactive.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug(f"Successfully authenticated user: {user.id}")
    return user

async def validate_refresh_token(
    async_session_factory: async_sessionmaker[AsyncSession] = Depends(get_async_session_factory),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
    refresh_token: Optional[str] = Cookie(None, alias="refresh_token")
) -> User:
    """
    Dépendance pour valider un refresh token.
    Vérifie d'abord le header Authorization, puis le cookie refresh_token.
    Crée sa propre session DB à partir de la factory.
    """
    logger.debug("Attempting to validate refresh token (using factory-created session)...")
    # Récupérer le token soit du header soit du cookie
    token = credentials.credentials if credentials else refresh_token
    logger.debug(f"Refresh Token source: {'Header' if credentials else 'Cookie' if refresh_token else 'None'}")
    
    if not token:
        logger.warning("Refresh token validation failed: No token provided.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Vérifier que c'est un refresh token
    logger.debug("Verifying token type is refresh...")
    is_refresh_token = verify_token_type(token, "refresh")
    logger.debug(f"Is refresh token: {is_refresh_token}")
    if not is_refresh_token:
        logger.warning("Refresh token validation failed: Invalid token type.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Décoder le token
    user_id: Optional[str] = None
    try:
        logger.debug("Decoding refresh token...")
        payload = decode_token(token)
        user_id = cast(str, payload.get("sub"))
        logger.debug(f"Refresh token decoded successfully. User ID: {user_id}")
    except HTTPException as e:
        logger.warning(f"Refresh token decoding failed: {e.detail}") 
        raise e
    except Exception as e:
        logger.exception("Unexpected error during refresh token decoding.")
        raise HTTPException(
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             detail="Error processing refresh token."
        )
    
    if not user_id:
        logger.warning("Refresh token validation failed: No user ID (sub) in token payload.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Récupérer l'utilisateur en utilisant une session créée localement
    user: Optional[User] = None
    try:
        logger.debug(f"Creating local session from factory for refresh token user ID: {user_id}...")
        async with async_session_factory() as session:
            logger.debug(f"Fetching user with ID: {user_id} using local session (for refresh token)...")
            user = await get_user_by_id(session, user_id) # Pass the local session
            logger.debug(f"Local session fetch complete for refresh token. User found: {bool(user)}")
    except Exception as e:
        logger.exception(f"Database error while fetching user ID: {user_id} using local session (for refresh token)")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error retrieving user."
        )

    if not user:
        logger.warning(f"Refresh token validation failed: User with ID {user_id} not found in DB.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug(f"Checking if refresh token user {user_id} is active...")
    if not user.is_active:
        logger.warning(f"Refresh token validation failed: User {user_id} is inactive.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug(f"Successfully validated refresh token for user: {user.id}")
    return user

def get_current_user_optional(
    current_user: Optional[User] = Depends(get_current_user)
) -> Optional[User]:
    """
    Dépendance pour obtenir l'utilisateur actuel de manière optionnelle.
    Ne lève pas d'exception si l'utilisateur n'est pas authentifié.
    """
    return current_user 