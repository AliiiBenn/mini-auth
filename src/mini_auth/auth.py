"""
Core authentication functionality for mini-auth.
"""

import datetime
from typing import Dict, Optional, Union

from .crypto.crypto import (
    hash_password,
    verify_password,
    create_token,
    verify_token
)

def authenticate(
    username: str,
    password: str,
    stored_password_hash: str,
    secret_key: str,
    token_expires_in: int = 3600
) -> Union[str, None]:
    """
    Authenticate a user and return a token if successful.
    
    Args:
        username: The username to authenticate
        password: The password to verify
        stored_password_hash: The stored hash to check against
        secret_key: The secret key for token generation
        token_expires_in: Seconds until token expiration (default: 1 hour)
        
    Returns:
        str: JWT token if authentication successful
        None: If authentication fails
    """
    if verify_password(password, stored_password_hash):
        return create_token(
            {'username': username},
            secret_key,
            expires_in=token_expires_in
        )
    return None 