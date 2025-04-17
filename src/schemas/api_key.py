from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

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