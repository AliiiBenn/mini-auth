"""
Database integration for mini-auth.
"""

from typing import Optional, Union, Dict
from sqlalchemy import create_engine, Column, Integer, String, Table, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.sql import select

from .auth import hash_password, verify_password, create_token, verify_token

class MiniAuth:
    """
    MiniAuth class for handling authentication with SQLite database.
    """
    
    def __init__(self, db_url: str, secret_key: str):
        """
        Initialize MiniAuth with database connection and secret key.
        
        Args:
            db_url: SQLite database URL (e.g., 'sqlite:///auth.db')
            secret_key: Secret key for JWT token generation
        """
        self.engine = create_engine(db_url)
        self.secret_key = secret_key
        self.metadata = MetaData()
        
        # Define users table
        self.users = Table(
            'users',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('username', String(50), unique=True, nullable=False),
            Column('password_hash', String(128), nullable=False)
        )
        
        # Create tables if they don't exist
        self.metadata.create_all(self.engine)
    
    def create_user(self, username: str, password: str) -> bool:
        """
        Create a new user with the given username and password.
        
        Args:
            username: Username for the new user
            password: Password for the new user
            
        Returns:
            bool: True if user was created successfully, False if username already exists
        """
        try:
            with self.engine.connect() as conn:
                # Check if username already exists
                result = conn.execute(
                    select(self.users).where(self.users.c.username == username)
                ).first()
                
                if result is not None:
                    return False
                
                # Create new user
                conn.execute(
                    self.users.insert().values(
                        username=username,
                        password_hash=hash_password(password)
                    )
                )
                conn.commit()
                return True
        except Exception:
            return False
    
    def authenticate(self, username: str, password: str, token_expires_in: int = 3600) -> Optional[str]:
        """
        Authenticate a user and return a JWT token if successful.
        
        Args:
            username: Username to authenticate
            password: Password to verify
            token_expires_in: Token expiration time in seconds (default: 1 hour)
            
        Returns:
            Optional[str]: JWT token if authentication successful, None otherwise
        """
        with self.engine.connect() as conn:
            result = conn.execute(
                select(self.users).where(self.users.c.username == username)
            ).first()
            
            if result is None:
                return None
            
            if verify_password(password, result.password_hash):
                return create_token(
                    {'username': username, 'user_id': result.id},
                    self.secret_key,
                    expires_in=token_expires_in
                )
            return None
    
    def verify_auth_token(self, token: str) -> Union[Dict, None]:
        """
        Verify an authentication token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Union[Dict, None]: Token payload if valid, None otherwise
        """
        return verify_token(token, self.secret_key)
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        Change a user's password.
        
        Args:
            username: Username of the user
            old_password: Current password
            new_password: New password
            
        Returns:
            bool: True if password was changed successfully, False otherwise
        """
        with self.engine.connect() as conn:
            result = conn.execute(
                select(self.users).where(self.users.c.username == username)
            ).first()
            
            if result is None:
                return False
            
            if verify_password(old_password, result.password_hash):
                conn.execute(
                    self.users.update()
                    .where(self.users.c.username == username)
                    .values(password_hash=hash_password(new_password))
                )
                conn.commit()
                return True
            return False 