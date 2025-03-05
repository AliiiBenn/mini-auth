from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import secrets

from models.base import Admin
from schemas.admin import TokenData
from database import get_db

# Configuration
ACCESS_TOKEN_EXPIRE_MINUTES = 30
# Stockage temporaire des tokens (en production, utilisez une base de données Redis)
active_tokens = {}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/admins/token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(username: str) -> str:
    token = secrets.token_urlsafe(32)
    active_tokens[token] = {
        "username": username,
        "expires": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return token

async def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if token not in active_tokens:
        raise credentials_exception
        
    token_data = active_tokens[token]
    if datetime.utcnow() > token_data["expires"]:
        del active_tokens[token]
        raise credentials_exception
        
    admin = db.query(Admin).filter(Admin.username == token_data["username"]).first()
    if admin is None:
        raise credentials_exception
        
    return admin 