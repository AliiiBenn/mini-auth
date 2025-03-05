from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from models.base import Admin
from schemas.admin import Admin as AdminSchema, AdminCreate, Token
from database import get_db
from core import verify_password, get_password_hash, create_access_token, get_current_admin

router = APIRouter()

@router.post("/register", response_model=AdminSchema)
def register_admin(admin: AdminCreate, db: Session = Depends(get_db)):
    db_admin = db.query(Admin).filter(Admin.email == admin.email).first()
    if db_admin:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_admin = db.query(Admin).filter(Admin.username == admin.username).first()
    if db_admin:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_password = get_password_hash(admin.password)
    db_admin = Admin(
        email=admin.email,
        username=admin.username,
        hashed_password=hashed_password
    )
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    admin = db.query(Admin).filter(Admin.username == form_data.username).first()
    if not admin or not verify_password(form_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(str(admin.username))
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=AdminSchema)
async def read_admin_me(current_admin: Admin = Depends(get_current_admin)):
    return current_admin 