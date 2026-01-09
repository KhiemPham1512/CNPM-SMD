"""
Werkzeug-based password hasher implementation.

This is the infrastructure implementation of IPasswordHasher
using werkzeug.security for password hashing.
"""
from werkzeug.security import generate_password_hash, check_password_hash
from domain.services.password_hasher import IPasswordHasher


class WerkzeugPasswordHasher(IPasswordHasher):
    """Werkzeug-based password hasher implementation."""
    
    def hash_password(self, plain_password: str) -> str:
        """Hash a plain text password using werkzeug."""
        return generate_password_hash(plain_password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain text password against a hashed password using werkzeug."""
        return check_password_hash(hashed_password, plain_password)
