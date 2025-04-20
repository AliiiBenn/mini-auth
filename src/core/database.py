from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine
from src.core.config import get_settings # Import settings

# Get settings instance
settings = get_settings()

# Clean the DATABASE_URL to remove sslmode if present, as it's handled by connect_args
cleaned_db_url = settings.DATABASE_URL.split('?')[0]

# --- Async Configuration ---
async_engine = create_async_engine(
    cleaned_db_url, # Use cleaned URL
    echo=True,
    connect_args={"ssl": "require"}, # SSL handled via connect_args
    pool_recycle=1800
)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# --- Sync Configuration ---
# Construct sync URL by replacing the dialect part
if settings.DATABASE_URL.startswith("postgresql+asyncpg://"):
    sync_db_url_base = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
else: # Assume default or other, try replacing just postgresql:// if needed
    # This might need adjustment based on the actual DATABASE_URL format
    sync_db_url_base = settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# Remove query parameters like sslmode for psycopg2 DSN
sync_db_url = sync_db_url_base.split('?')[0]

sync_engine = create_engine(
    sync_db_url,
    echo=True,
    pool_recycle=1800
    # Note: psycopg2 handles sslmode within the DSN string itself or via service files/env vars,
    # it doesn't typically take connect_args like asyncpg for basic sslmode.
    # Ensure your DATABASE_URL correctly includes necessary components or rely on env vars (PGSSLMODE).
)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

# --- Base Class ---
class Base(AsyncAttrs, DeclarativeBase):
    pass

# --- Dependencies ---
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

def get_db_sync(): # Synchronous dependency
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_async_session_factory(): # Dependency for the async session factory
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