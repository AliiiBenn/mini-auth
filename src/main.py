from typing import Union

from fastapi import FastAPI
from api.auth import router as auth_router

# Import all models to ensure they're registered with Base
from models.user import User
from database import create_tables

# Create tables after all models are imported
create_tables()

app = FastAPI()

app.include_router(auth_router)


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}