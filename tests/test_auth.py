import pytest
from mini_auth.auth import (
    hash_password,
    verify_password,
    create_token,
    verify_token,
    authenticate,
)

def test_password_hashing():
    password = "mysecretpassword"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)

def test_token_creation_and_verification():
    secret_key = "test-secret-key"
    data = {"username": "testuser"}
    
    # Test token creation
    token = create_token(data, secret_key)
    assert token is not None
    
    # Test token verification
    decoded = verify_token(token, secret_key)
    assert decoded is not None
    assert decoded["username"] == "testuser"
    
    # Test invalid token
    assert verify_token("invalid-token", secret_key) is None
    assert verify_token(token, "wrong-secret") is None

def test_authentication():
    password = "mysecretpassword"
    username = "testuser"
    secret_key = "test-secret-key"
    
    # Hash the password as it would be stored in a database
    stored_hash = hash_password(password)
    
    # Test successful authentication
    token = authenticate(username, password, stored_hash, secret_key)
    assert token is not None
    decoded = verify_token(token, secret_key)
    assert decoded["username"] == username
    
    # Test failed authentication
    assert authenticate(username, "wrongpassword", stored_hash, secret_key) is None 