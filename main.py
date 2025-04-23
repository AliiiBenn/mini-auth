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
# Configure allowed origins
origins = [
    "http://127.0.0.1:3000", # Allow your local development frontend
    "http://localhost:3000",  # Also allow localhost commonly used for dev
    # Add your Vercel frontend deployment URL here when known
    # e.g., "https://your-dashboard-frontend.vercel.app"
    # Avoid using "*" in production if allow_credentials=True
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Use the configured list
    allow_credentials=True, # Allow cookies
    allow_methods=["*"], # Allow all standard methods
    allow_headers=["*"], # Allow all headers
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

@app.get("/")
async def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000)) 
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True # Reload should be False in production
    )




