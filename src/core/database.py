from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from src.core.config import get_settings # Import settings

# Get settings instance
settings = get_settings()

# Clean the DATABASE_URL to remove sslmode if present, as it's handled by connect_args
cleaned_db_url = settings.DATABASE_URL.split('?')[0]

# Create async engine using cleaned DATABASE_URL from settings
# Pass ssl argument via connect_args for asyncpg
engine = create_async_engine(
    cleaned_db_url,
    echo=True, # Set to False in production for less noise
    connect_args={"ssl": "require"}, # Correct way to pass ssl for asyncpg
    pool_pre_ping=True, # Added pool_pre_ping
    asyncio_mode="native" # Force native asyncio mode
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
        yield session # Just yield the session

# Initialize database
async def init_db():
    """Create all tables in the database if they don't exist."""
    async with engine.begin() as conn:
        # Create all tables defined inheriting from Base
        await conn.run_sync(Base.metadata.create_all)

# REMOVED: Export all models to ensure they are registered with Base.metadata
# This caused circular imports with Alembic.
# Models are imported in alembic/env.py for migration detection.
# from src.models.user import User, RefreshToken
# from src.models.project import Project, ProjectApiKey, ProjectMember 