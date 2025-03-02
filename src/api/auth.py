from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from dependencies import get_db
from schemas.user import UserCreate, UserLogin
from models.user import User
from core.security import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    create_refresh_token,
    create_email_verification_token,
    create_password_reset_token
)
from core.auth_dependencies import get_current_user, get_current_active_user

router = APIRouter()

@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Enregistre un nouvel utilisateur.
    """
    # Vérifier si l'email existe déjà
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email déjà enregistré"
        )
    
    # Créer un nouvel utilisateur avec mot de passe haché
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email, 
        hashed_password=hashed_password,
        is_active=True,
        is_verified=False
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur lors de l'enregistrement"
        )
    
    # Générer un token de vérification d'email (à implémenter l'envoi d'email)
    verification_token = create_email_verification_token(user.email)
    
    # Retourner l'utilisateur sans le mot de passe
    return {
        "id": db_user.id,
        "email": db_user.email,
        "is_active": db_user.is_active,
        "is_verified": db_user.is_verified,
        "verification_token": verification_token  # En production, ne pas retourner ce token
    }

@router.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authentifie un utilisateur et retourne un token JWT.
    """
    # Rechercher l'utilisateur par email
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Vérifier si l'utilisateur existe et si le mot de passe est correct
    if not user or not verify_password(form_data.password, str(user.hashed_password)):  # Conversion en str pour résoudre l'erreur de linter
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Vérifier si l'utilisateur est actif
    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé"
        )
    
    # Générer les tokens d'accès et de rafraîchissement
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/auth/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """
    Déconnecte l'utilisateur actuel.
    
    Note: Avec JWT, la déconnexion côté serveur nécessite une liste noire de tokens.
    Cette implémentation est simplifiée et ne révoque pas réellement le token.
    """
    return {"message": "Déconnexion réussie"}

@router.post("/auth/refresh-token")
async def refresh_token(token: str, db: Session = Depends(get_db)):
    """
    Rafraîchit le token d'accès à l'aide du token de rafraîchissement.
    """
    # Implémenter la logique de rafraîchissement du token
    pass

@router.post("/auth/reset-password")
async def reset_password(email: str, db: Session = Depends(get_db)):
    """
    Envoie un email de réinitialisation de mot de passe.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Ne pas révéler si l'email existe ou non pour des raisons de sécurité
        return {"message": "Si l'email existe, un lien de réinitialisation a été envoyé"}
    
    # Générer un token de réinitialisation
    reset_token = create_password_reset_token(email)
    
    # Ici, vous implémenteriez l'envoi d'email avec le token
    
    return {"message": "Si l'email existe, un lien de réinitialisation a été envoyé"}

@router.post("/auth/reset-password/{token}")
async def reset_password_with_token(token: str, new_password: str, db: Session = Depends(get_db)):
    """
    Réinitialise le mot de passe avec un token valide.
    """
    # Implémenter la logique de réinitialisation du mot de passe
    pass

@router.post("/auth/verify-email/{token}")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Vérifie l'email d'un utilisateur avec un token valide.
    """
    # Implémenter la logique de vérification d'email
    pass


