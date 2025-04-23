from typing import Optional, cast
from fastapi import Depends, HTTPException, status, Cookie, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import logging # Import logging

from src.core.database import get_db
from src.core.security.jwt import decode_token, verify_token_type
from src.core.crud.user import get_user_by_id
from src.models.user import User

# Setup logger for this module
logger = logging.getLogger(__name__)

# Configuration du bearer token
oauth2_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
    access_token: Optional[str] = Cookie(None, alias="access_token")
) -> User:
    """
    Dépendance pour obtenir l'utilisateur actuel à partir du token JWT.
    Vérifie d'abord le header Authorization, puis le cookie access_token.
    """
    logger.debug("Attempting to get current user...")
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
        # Log the specific HTTPException detail from decode_token
        logger.warning(f"Token decoding failed: {e.detail}") 
        raise e # Re-raise the HTTPException
    except Exception as e:
        # Log unexpected errors during decoding
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
    
    # Récupérer l'utilisateur
    user: Optional[User] = None
    try:
        logger.debug(f"Fetching user with ID: {user_id} from database...")
        user = await get_user_by_id(db, user_id)
        logger.debug(f"Database fetch complete. User found: {bool(user)}")
    except Exception as e:
        # Log potential DB errors
        logger.exception(f"Database error while fetching user ID: {user_id}")
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
    
    # Stocker l'utilisateur dans l'état de la requête pour y accéder facilement
    # request.state.user = user # Avoid modifying request state directly unless necessary
    
    logger.debug(f"Successfully authenticated user: {user.id}")
    return user

async def validate_refresh_token(
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
    refresh_token: Optional[str] = Cookie(None, alias="refresh_token")
) -> User:
    """
    Dépendance pour valider un refresh token.
    Vérifie d'abord le header Authorization, puis le cookie refresh_token.
    """
    # Récupérer le token soit du header soit du cookie
    token = credentials.credentials if credentials else refresh_token
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Vérifier que c'est un refresh token
    if not verify_token_type(token, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Décoder le token
    payload = decode_token(token)
    user_id = cast(str, payload.get("sub"))
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Récupérer l'utilisateur
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def get_current_user_optional(
    current_user: Optional[User] = Depends(get_current_user)
) -> Optional[User]:
    """
    Dépendance pour obtenir l'utilisateur actuel de manière optionnelle.
    Ne lève pas d'exception si l'utilisateur n'est pas authentifié.
    """
    return current_user 