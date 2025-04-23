from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from src.core.config import get_settings # Import settings

# Get settings instance
settings = get_settings()

# --- Async Configuration with psycopg --- 

# Ensure DATABASE_URL starts with postgresql+psycopg://
if not settings.DATABASE_URL.startswith("postgresql+psycopg://"):
    # Basic attempt to convert from asyncpg or standard postgresql URL
    # You might need to adjust this logic or ensure the env var is set correctly
    async_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    async_db_url = async_db_url.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    async_db_url = settings.DATABASE_URL

async_engine = create_async_engine(
    async_db_url, 
    echo=False, 
    # connect_args might not be needed, psycopg handles SSL via DSN/env vars
    # connect_args={"ssl": "require"}, 
    pool_recycle=1800,
    pool_pre_ping=True, # Keep pre-ping
    pool_size=5,       
    max_overflow=0     
)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# --- Base Class ---
class Base(AsyncAttrs, DeclarativeBase):
    pass

# --- Dependencies ---
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

def get_async_session_factory():
    return AsyncSessionLocal

# Initialize database (using async engine)
async def init_db():
    """Create all tables in the database if they don't exist."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# REMOVED: Export all models to ensure they are registered with Base.metadata
# This caused circular imports with Alembic.
# Models are imported in alembic/env.py for migration detection.
# from src.models.user import User, RefreshToken
# from src.models.project import Project, ProjectApiKey, ProjectMember 