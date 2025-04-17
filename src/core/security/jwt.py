from datetime import datetime, timedelta, UTC
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status

from core.config import get_settings

settings = get_settings()

def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    :param subject: Usually the user ID
    :param expires_delta: Optional expiration time
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.now(UTC) + expires_delta
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "access"
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt

def create_refresh_token(
    subject: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    :param subject: Usually the user ID
    :param expires_delta: Optional expiration time
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    expire = datetime.now(UTC) + expires_delta
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh"
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt

def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    Raises HTTPException if token is invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Vérifier que le token n'est pas expiré
        exp = payload.get("exp")
        if not exp or datetime.fromtimestamp(exp, UTC) < datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_token_type(token: str, expected_type: str) -> bool:
    """
    Verify that a token is of the expected type (access or refresh).
    """
    try:
        payload = decode_token(token)
        return payload.get("type") == expected_type
    except HTTPException:
        return False 