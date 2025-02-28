"""
mini-auth - A minimalist authentication library for Python applications
"""

__version__ = "0.1.0"
__author__ = "David"

from mini_auth.auth import (  # noqa: F401
    authenticate,
    create_token,
    verify_token,
    hash_password,
    verify_password,
)

from mini_auth.db import MiniAuth  # noqa: F401 