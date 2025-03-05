from pydantic import BaseModel, EmailStr
from typing import Optional

class AdminBase(BaseModel):
    email: EmailStr
    username: str

class AdminCreate(AdminBase):
    password: str

class Admin(AdminBase):
    id: int
    is_active: bool = True

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None 