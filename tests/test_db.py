"""
Tests for the MiniAuth database integration.
"""

import pytest
from mini_auth.db import MiniAuth

@pytest.fixture
def auth():
    """Create a MiniAuth instance with an in-memory SQLite database."""
    return MiniAuth('sqlite:///:memory:', 'test-secret-key')

def test_create_user(auth):
    # Test successful user creation
    assert auth.create_user('testuser', 'password123')
    
    # Test duplicate username
    assert not auth.create_user('testuser', 'different_password')

def test_authenticate(auth):
    # Create a test user
    auth.create_user('authuser', 'password123')
    
    # Test successful authentication
    token = auth.authenticate('authuser', 'password123')
    assert token is not None
    
    # Test failed authentication with wrong password
    assert auth.authenticate('authuser', 'wrongpassword') is None
    
    # Test failed authentication with non-existent user
    assert auth.authenticate('nonexistent', 'password123') is None

def test_verify_auth_token(auth):
    # Create a test user and get token
    auth.create_user('tokenuser', 'password123')
    token = auth.authenticate('tokenuser', 'password123')
    
    # Test token verification
    payload = auth.verify_auth_token(token)
    assert payload is not None
    assert payload['username'] == 'tokenuser'
    assert 'user_id' in payload
    
    # Test invalid token
    assert auth.verify_auth_token('invalid-token') is None

def test_change_password(auth):
    # Create a test user
    auth.create_user('pwuser', 'oldpassword')
    
    # Test successful password change
    assert auth.change_password('pwuser', 'oldpassword', 'newpassword')
    
    # Verify old password no longer works
    assert auth.authenticate('pwuser', 'oldpassword') is None
    
    # Verify new password works
    assert auth.authenticate('pwuser', 'newpassword') is not None
    
    # Test failed password change with wrong old password
    assert not auth.change_password('pwuser', 'wrongpassword', 'newpassword')
    
    # Test failed password change with non-existent user
    assert not auth.change_password('nonexistent', 'oldpassword', 'newpassword') 