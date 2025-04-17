from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, UUID4

class UserBase(BaseModel):
    """Base schema for user data"""
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    """Schema for user creation"""
    password: str = Field(..., min_length=8)
    confirm_password: str

    def validate_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    """Schema for user update"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)

class UserInDB(UserBase):
    """Schema for user in database"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    hashed_password: str

    class Config:
        from_attributes = True

class UserRead(UserBase):
    """Schema for user response"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 