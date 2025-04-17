from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from .core.config import get_settings
from .core.database import get_db, init_db
from .api.v1 import router as api_v1_router
from .api.v1.dashboard import router as dashboard_router
from .core.middleware.auth import DashboardAuthMiddleware

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: Clean up resources if needed
    pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A minimalist authentication API built with FastAPI",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a sub-application for dashboard routes with its own middleware
dashboard_app = FastAPI()
dashboard_app.add_middleware(DashboardAuthMiddleware)
dashboard_app.include_router(dashboard_router)

# Include API v1 routes
app.include_router(api_v1_router)
# Mount dashboard app with its middleware
app.mount("/api/v1/dashboard", dashboard_app)

@app.get("/")
async def root(db: AsyncSession = Depends(get_db)):
    return {"message": "Welcome to Mini Auth API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

# Export the app variable for Vercel
app = app 