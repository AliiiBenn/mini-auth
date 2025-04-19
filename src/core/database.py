from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

# Utilisation de SQLite pour le développement
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./mini_auth.db"

# Create async engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Important for async operation
)

# Create base class for declarative models
class Base(AsyncAttrs, DeclarativeBase):
    pass

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Initialize database
async def init_db():
    """Create all tables in the database."""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

# Export all models to ensure they are registered with Base.metadata
from src.models.user import User, RefreshToken
from src.models.project import Project, ProjectApiKey 