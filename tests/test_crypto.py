"""
Tests for custom cryptographic implementations.
"""

import time
from mini_auth.crypto.crypto import (
    hash_password,
    verify_password,
    create_token,
    verify_token,
    ITERATIONS,
    KEY_LENGTH
)

def test_password_hashing():
    # Test basic hashing and verification
    password = "mysecretpassword"
    hashed = hash_password(password)
    
    # Verify format: iterations:salt:hash
    parts = hashed.split(':')
    assert len(parts) == 3
    assert int(parts[0]) == ITERATIONS
    
    # Test successful verification
    assert verify_password(password, hashed)
    
    # Test failed verification
    assert not verify_password("wrongpassword", hashed)
    
    # Test different passwords produce different hashes
    hashed2 = hash_password(password)
    assert hashed != hashed2  # Different salt should produce different hash

def test_password_hash_security():
    # Test invalid hash format
    assert not verify_password("password", "invalid_hash")
    assert not verify_password("password", ":")
    assert not verify_password("password", ":::")
    
    # Test with invalid base64 in hash
    assert not verify_password("password", f"{ITERATIONS}:invalid:invalid")

def test_token_creation_and_verification():
    secret_key = "test-secret-key"
    data = {"username": "testuser", "id": 123}
    
    # Test token creation and verification
    token = create_token(data, secret_key)
    payload = verify_token(token, secret_key)
    assert payload is not None
    assert payload["username"] == "testuser"
    assert payload["id"] == 123
    
    # Test token with expiration
    token = create_token(data, secret_key, expires_in=1)
    payload = verify_token(token, secret_key)
    assert payload is not None
    
    # Test expired token
    time.sleep(2)
    assert verify_token(token, secret_key) is None

def test_token_security():
    secret_key = "test-secret-key"
    data = {"username": "testuser"}
    token = create_token(data, secret_key)
    
    # Test wrong secret key
    assert verify_token(token, "wrong-secret") is None
    
    # Test invalid token format
    assert verify_token("invalid_token", secret_key) is None
    assert verify_token("invalid.token", secret_key) is None
    
    # Test tampered payload
    payload_b64, signature = token.split('.')
    tampered_token = payload_b64 + "tampered" + "." + signature
    assert verify_token(tampered_token, secret_key) is None
    
    # Test tampered signature
    tampered_token = payload_b64 + "." + signature + "tampered"
    assert verify_token(tampered_token, secret_key) is None 