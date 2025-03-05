from fastapi import FastAPI
from api.v1 import admins

from models.base import Base
from database import engine

# Créer les tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Inclure les routeurs
app.include_router(admins.router, prefix="/api/v1/admins", tags=["admins"])

@app.get("/")
async def read_root():
    return {"Hello": "World"}



