import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any

from passlib.context import CryptContext
import jwt
from jwt.exceptions import PyJWTError

# Configuration pour le hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration pour JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-development-only")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe en clair correspond au mot de passe haché."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Génère un hash sécurisé pour le mot de passe."""
    return pwd_context.hash(password)


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un token JWT d'accès.
    
    Args:
        subject: Identifiant de l'utilisateur (généralement user_id)
        expires_delta: Durée de validité du token (optionnel)
        
    Returns:
        Token JWT encodé
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any]) -> str:
    """
    Crée un token JWT de rafraîchissement.
    
    Args:
        subject: Identifiant de l'utilisateur (généralement user_id)
        
    Returns:
        Token JWT encodé
    """
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Décode un token JWT.
    
    Args:
        token: Token JWT à décoder
        
    Returns:
        Contenu décodé du token
        
    Raises:
        PyJWTError: Si le token est invalide
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except PyJWTError:
        raise ValueError("Token invalide")


def create_email_verification_token(email: str) -> str:
    """
    Crée un token pour la vérification d'email.
    
    Args:
        email: Email à vérifier
        
    Returns:
        Token de vérification
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode = {"exp": expire, "sub": email, "type": "email_verification"}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_password_reset_token(email: str) -> str:
    """
    Crée un token pour la réinitialisation de mot de passe.
    
    Args:
        email: Email de l'utilisateur
        
    Returns:
        Token de réinitialisation
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    to_encode = {"exp": expire, "sub": email, "type": "password_reset"}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt 