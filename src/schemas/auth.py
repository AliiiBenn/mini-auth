from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

class ClientLogin(BaseModel):
    """Schema for client login request"""
    email: EmailStr
    password: str

class Token(BaseModel):
    """Schema for access token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    """Schema for JWT token payload"""
    sub: str  # user_id
    exp: datetime
    type: str  # "access" or "refresh"

class TokenRefresh(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str 