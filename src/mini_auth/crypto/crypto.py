"""
Custom cryptographic implementations for mini-auth.
"""

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Dict, Final, Optional, Union

# Importer la classe PBKDF2HMAC
if __name__ == '__main__':
    from pbkdf2_hmac import PBKDF2HMAC
else:
    from .pbkdf2_hmac import PBKDF2HMAC

# Constants for password hashing
  # Length of the salt in bytes
ITERATIONS = 100000  # Number of iterations for PBKDF2
KEY_LENGTH = 32  # Length of the derived key in bytes





def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        str: The hashed password in the format: iterations:salt:hash (base64 encoded)
    """
    salt = os.urandom(16)  # Generate a random salt
    pbkdf2_hmac = PBKDF2HMAC(password.encode(), salt, ITERATIONS, KEY_LENGTH)
    pw_hash = pbkdf2_hmac.derive()
    
    # Format: iterations:salt:hash (all base64 encoded)
    return f"{ITERATIONS}:{base64.b64encode(salt).decode()}:{base64.b64encode(pw_hash).decode()}"

def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: The plain text password to verify
        stored_hash: The stored password hash to check against
        
    Returns:
        bool: True if the password matches, False otherwise
    """
    try:
        iterations_str, salt_b64, hash_b64 = stored_hash.split(':')
        iterations = int(iterations_str)
        salt = base64.b64decode(salt_b64)
        stored_pw_hash = base64.b64decode(hash_b64)
        
        pbkdf2_hmac = PBKDF2HMAC(password.encode(), salt, iterations, KEY_LENGTH)
        pw_hash = pbkdf2_hmac.derive()
        
        return hmac.compare_digest(pw_hash, stored_pw_hash)
    except (ValueError, TypeError):
        return False

def create_token(data: Dict, secret_key: str, expires_in: Optional[int] = None) -> str:
    """
    Create a custom token similar to JWT but using simple cryptography.
    
    Args:
        data: The data to encode in the token
        secret_key: The secret key to sign the token with
        expires_in: Optional number of seconds until the token expires
        
    Returns:
        str: The encoded token
    """
    payload = data.copy()
    if expires_in:
        payload['exp'] = int(time.time()) + expires_in
    
    # Convert payload to JSON and encode in base64
    json_data = json.dumps(payload, sort_keys=True)
    payload_b64 = base64.b64encode(json_data.encode()).decode()
    
    # Create signature using HMAC-SHA256
    signature = hmac.new(
        secret_key.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).digest()
    signature_b64 = base64.b64encode(signature).decode()
    
    # Format: payload.signature (both base64 encoded)
    return f"{payload_b64}.{signature_b64}"

def verify_token(token: str, secret_key: str) -> Union[Dict, None]:
    """
    Verify and decode a token.
    
    Args:
        token: The token to verify
        secret_key: The secret key used to sign the token
        
    Returns:
        Dict: The decoded token payload if valid
        None: If the token is invalid
    """
    try:
        # Split token into payload and signature
        if '.' not in token:
            return None
            
        payload_b64, signature_b64 = token.split('.')
        
        # Verify signature
        try:
            received_signature = base64.b64decode(signature_b64)
        except Exception:
            return None
            
        expected_signature = hmac.new(
            secret_key.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).digest()
        
        # Verify signature length and content
        if len(received_signature) != len(expected_signature) or \
           not hmac.compare_digest(expected_signature, received_signature):
            return None
        
        # Only decode payload if signature is valid
        try:
            payload_json = base64.b64decode(payload_b64).decode()
            payload = json.loads(payload_json)
        except Exception:
            return None
        
        # Check expiration
        if 'exp' in payload and payload['exp'] < time.time():
            return None
        
        return payload
    except (ValueError, json.JSONDecodeError, TypeError):
        return None 