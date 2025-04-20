from datetime import datetime, UTC
import uuid
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.project import Project, ProjectMember

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[Optional[str]] = mapped_column(
        String(36), 
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True, 
        index=True 
    )
    email: Mapped[str] = mapped_column(
        String(255), nullable=False 
    )
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        UniqueConstraint('project_id', 'email', name='_project_email_uc'),
    )

    project: Mapped[Optional["Project"]] = relationship(
        "Project", 
        foreign_keys=[project_id]
    )
    
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    projects_owned: Mapped[List["Project"]] = relationship(
        "Project", 
        back_populates="owner", 
        foreign_keys="Project.owner_id",
        cascade="all, delete-orphan"
    )
    project_memberships: Mapped[List["ProjectMember"]] = relationship(
        "ProjectMember", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    token: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_revoked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens") 