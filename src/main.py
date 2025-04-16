from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import get_db, engine, Base
from api.v1 import router as api_v1_router
from core.middleware.auth import DashboardAuthMiddleware

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A minimalist authentication API built with FastAPI",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Dashboard Auth Middleware
app.add_middleware(DashboardAuthMiddleware)

# Include API v1 routes
app.include_router(api_v1_router)

# Create database tables
@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root(db: AsyncSession = Depends(get_db)):
    return {"message": "Welcome to Mini Auth API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True) 