from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Mini Auth API"
    
    # Security
    # DASHBOARD_SECRET_KEY: str = "your-super-secret-key-for-dashboard" # Removed
    JWT_SECRET_KEY: str = "your-super-secret-key-for-jwt"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SECRET_KEY: str = "your-secret-key"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://YOUR_DB_USER:YOUR_DB_PASSWORD@YOUR_DB_HOST/YOUR_DB_NAME?sslmode=require"
    
    # Email Settings
    MAIL_USERNAME: str = "your-email@example.com"
    MAIL_PASSWORD: str = "your-email-password"
    MAIL_FROM: str = "your-email@example.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.example.com"
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = 'ignore'

@lru_cache()
def get_settings():
    return Settings() 