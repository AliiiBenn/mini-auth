from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, UUID4, Field

class ProjectApiKeyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)

class ProjectApiKeyCreate(ProjectApiKeyBase):
    pass

class ProjectApiKey(ProjectApiKeyBase):
    id: str
    project_id: str
    key: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = Field(None, max_length=200)

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    is_active: Optional[bool] = None

class Project(ProjectBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
    api_keys: List[ProjectApiKey] = []

    class Config:
        from_attributes = True

class ProjectList(BaseModel):
    total: int
    items: List[Project]

    class Config:
        from_attributes = True 