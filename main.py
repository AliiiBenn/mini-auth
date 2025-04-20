import os
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.core.database import get_db, init_db

from src.api.v1 import router as api_v1_router

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0", 
    description="A minimalist authentication API"
)

# Setup CORS middleware
# TODO: Replace "*" with your frontend origin in production
origins = [
    "*", # Allows all origins for development
    # Add your frontend URL here for production, e.g.:
    # "http://localhost:3000", 
    # "https://your-dashboard.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)

@app.on_event("startup")
async def on_startup():
    print("Starting up and initializing database...")
    await init_db()
    print("Database initialized.")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000)) 
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True # Reload should be False in production
    )




