from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jwt.exceptions import PyJWTError

from dependencies import get_db
from models.user import User
from core.security import decode_token

# Point de terminaison pour l'authentification OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    """
    Récupère l'utilisateur actuel à partir du token JWT.
    
    Args:
        token: Token JWT d'authentification
        db: Session de base de données
        
    Returns:
        Utilisateur authentifié
        
    Raises:
        HTTPException: Si le token est invalide ou l'utilisateur n'existe pas
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None or payload.get("type") != "access":
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Vérifie que l'utilisateur actuel est actif.
    
    Args:
        current_user: Utilisateur authentifié
        
    Returns:
        Utilisateur actif
        
    Raises:
        HTTPException: Si l'utilisateur est inactif
    """
    if current_user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utilisateur inactif"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Vérifie que l'utilisateur actuel est vérifié.
    
    Args:
        current_user: Utilisateur authentifié et actif
        
    Returns:
        Utilisateur vérifié
        
    Raises:
        HTTPException: Si l'utilisateur n'est pas vérifié
    """
    if current_user.is_verified is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email non vérifié"
        )
    return current_user 