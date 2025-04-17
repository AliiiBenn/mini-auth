from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from .api_key import ProjectApiKey

class ProjectMemberBase(BaseModel):
    role: str = Field(default="member", pattern="^(member|admin)$")

class ProjectMemberCreate(ProjectMemberBase):
    user_id: str

class ProjectMember(ProjectMemberBase):
    id: str
    project_id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)

class ProjectCreate(ProjectBase):
    pass

class DashboardProjectCreate(ProjectBase):
    owner_id: str

class ProjectUpdate(ProjectBase):
    pass

class Project(ProjectBase):
    id: str
    owner_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
    api_keys: List[ProjectApiKey] = []
    members: List[ProjectMember] = []

    class Config:
        from_attributes = True

class ProjectList(BaseModel):
    items: List[Project]
    total: int 