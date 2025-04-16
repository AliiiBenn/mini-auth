from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
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
)

# Create base class for declarative models
class Base(DeclarativeBase):
    pass

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close() 